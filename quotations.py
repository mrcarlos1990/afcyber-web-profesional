"""Durable quotations and a bounded outbox using the configured mail helper."""
import hashlib
import hmac
import os
import secrets
import time
from datetime import timedelta
from zoneinfo import ZoneInfo
import click
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import update, delete
from extensions import db
from models import QuoteRequest, QuoteMail, PublicRateBucket, ContactMessage, utc_now

STATES = {'RECIBIDA', 'EN_REVISION', 'RESPONDIDA', 'CERRADA'}
DEFAULT_CONTACT_RECIPIENT = 'info@afcybersolutions.com.do'
DEFAULT_SUPPORT_RECIPIENT = 'soporte@afcybersolutions.com.do'
SUPPORT_TERMS = ('soporte', 'mantenimiento', 'incidente', 'asistencia', 'ayuda', 'reparacion', 'reparación')


def rate_limit(scope, limit, seconds):
    now = int(time.time())
    identity = request.remote_addr or 'unknown'
    key = hmac.new(current_app.secret_key.encode(), f'{scope}:{identity}:{now//seconds}'.encode(), hashlib.sha256).hexdigest()
    table = PublicRateBucket.__table__
    dialect = db.engine.dialect.name
    if dialect == 'postgresql':
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    db.session.execute(insert(table).values(key=key, count=0, expires_at=now+seconds*2).on_conflict_do_nothing(index_elements=['key']))
    changed = db.session.execute(update(table).where(table.c.key==key,table.c.count<limit).values(count=table.c.count+1)).rowcount
    db.session.execute(delete(table).where(table.c.expires_at < now))
    db.session.commit()
    return changed == 1


def submission_key(nonce):
    return hashlib.sha256(nonce.encode()).hexdigest()


def default_notification_recipient(service='', channel='contact'):
    normalized = (service or '').strip().lower()
    if channel == 'quotation':
        return os.getenv('QUOTATION_RECIPIENT', '').strip() or os.getenv('CONTACT_RECIPIENT', '').strip() or DEFAULT_CONTACT_RECIPIENT
    if any(term in normalized for term in SUPPORT_TERMS):
        return os.getenv('SUPPORT_RECIPIENT', '').strip() or DEFAULT_SUPPORT_RECIPIENT
    return (
        os.getenv('CONTACT_RECIPIENT', '').strip()
        or os.getenv('COMPANY_NOTIFICATION_EMAIL', '').strip()
        or DEFAULT_CONTACT_RECIPIENT
    )


def create_quote(fields, nonce):
    existing = QuoteRequest.query.filter_by(submission_key=submission_key(nonce)).first()
    if existing:
        return existing, False
    quote = QuoteRequest(submission_key=submission_key(nonce), **fields)
    db.session.add(quote)
    # Preserve the old Messages workflow as well as the new quotation panel.
    db.session.add(ContactMessage(name=quote.name, company=quote.company, phone=quote.phone, email=quote.email,
                                  requested_service=quote.requested_service,
                                  message=quote.description + '\n\n[Consentimiento: Política de Privacidad aceptada para gestionar esta consulta.]'))
    try:
        db.session.flush()
        db.session.add(QuoteMail(quote_id=quote.id, kind='administrador'))
        if quote.email:
            db.session.add(QuoteMail(quote_id=quote.id, kind='cliente'))
        db.session.commit()  # Always save the request AND outbox before touching SMTP.
        return quote, True
    except IntegrityError:
        db.session.rollback()
        existing = QuoteRequest.query.filter_by(submission_key=submission_key(nonce)).first()
        if existing:
            return existing, False
        raise


def deliver_mail(job_id, sender, allow_uncertain=False, recipient_for=None):
    job = db.session.get(QuoteMail, job_id)
    if not job:
        return False
    allowed = ['PENDIENTE', 'FALLIDO'] + (['INCIERTO'] if allow_uncertain else [])
    changed = db.session.execute(update(QuoteMail).where(QuoteMail.id==job_id, QuoteMail.status.in_(allowed),
                                                       QuoteMail.attempts<5).values(status='ENVIANDO', attempts=QuoteMail.attempts+1,
                                                                                  updated_at=utc_now())).rowcount
    db.session.commit()  # Atomic claim: another worker/retry cannot claim this job.
    if not changed:
        return False
    db.session.expire_all()
    job = db.session.get(QuoteMail, job_id)
    quote = job.quote
    admin = job.kind == 'administrador'
    recipient_for = recipient_for or default_notification_recipient
    recipient = recipient_for(quote.requested_service, 'quotation') if admin else quote.email
    timestamp = quote.created_at.replace(tzinfo=__import__('datetime').timezone.utc).astimezone(ZoneInfo('America/Santo_Domingo'))
    body = (f'Solicitud {quote.number}\nFecha: {timestamp:%d/%m/%Y %H:%M} (República Dominicana)\n'
            f'Nombre: {quote.name}\nEmpresa: {quote.company or "No indicada"}\nTeléfono: {quote.phone or "No indicado"}\n'
            f'Correo: {quote.email or "No indicado"}\nProducto/servicio: {quote.requested_service}\n'
            f'Descripción: {quote.description}\nPresupuesto estimado: {quote.budget or "No indicado"}')
    subject = 'Nueva solicitud de cotización - AFCyber Solutions' if admin else f'Solicitud recibida {quote.number} - AFCyber Solutions'
    message_id = f'<afcyber-quote-{quote.id}-{job.kind}@afcybersolutions.com.do>'
    try:
        html_body = current_app.jinja_env.get_template('email/quotation.html').render(
            quote=quote,
            admin=admin,
            timestamp=timestamp,
            recipient=recipient,
        )
        delivery = sender(recipient, subject, body, 'quotation_' + job.kind,
                          html_body=html_body, reply_to=quote.email if admin else None,
                          message_id=message_id, max_retries_override=0,
                          existing_delivery=job.delivery)
        db.session.flush()
        job.delivery_id = delivery.id
        if delivery.status in {'enviado', 'aceptado'}:
            job.status = 'ENVIADO'
        elif delivery.status == 'omitido':
            job.status = 'PENDIENTE'
            job.attempts -= 1  # No transport attempted; allow later configuration.
        else:
            # SMTP may accept a message before a timeout. Never auto-resend an ambiguous result.
            job.status = 'INCIERTO' if any(t in (delivery.error or '') for t in ['Timeout', 'Disconnected', 'OSError']) else 'FALLIDO'
        job.updated_at = utc_now()
        db.session.commit()
    except Exception:
        db.session.rollback()
        job = db.session.get(QuoteMail, job_id)
        job.status = 'INCIERTO'
        job.updated_at = utc_now()
        db.session.commit()
        current_app.logger.warning('quotation_mail_uncertain job=%s', job_id)  # No recipient, body or credentials.
    return True


def deliver_quote(quote, sender, recipient_for=None):
    for job in list(quote.mail_jobs):
        deliver_mail(job.id, sender, recipient_for=recipient_for)


def register_quotes(app, sender, normalize_email, recipient_for=None):
    bp = Blueprint('quotes', __name__)
    recipient_for = recipient_for or default_notification_recipient

    @bp.get('/cotizacion')
    def form():
        session.setdefault('quote_nonce', secrets.token_urlsafe(24))
        return render_template('public/quotation.html', page_title='Solicitar cotización | AFCyber Solutions', corporate_layout=True)

    @bp.post('/cotizacion')
    def submit():
        return process_submission(sender, normalize_email, strict=True)

    def admin_check():
        from flask import abort
        if not current_user.is_active_admin:
            abort(403)

    @bp.get('/admin/cotizaciones')
    @login_required
    def admin_list():
        admin_check()
        page = max(1, request.args.get('page', 1, type=int))
        items = QuoteRequest.query.order_by(QuoteRequest.id.desc()).paginate(page=page, per_page=30, error_out=False)
        return render_template('admin/quotations.html', items=items)

    @bp.get('/admin/cotizaciones/<int:quote_id>')
    @login_required
    def admin_detail(quote_id):
        admin_check()
        quote = db.get_or_404(QuoteRequest, quote_id)
        return render_template('admin/quotation-detail.html', quote=quote, states=sorted(STATES))

    @bp.post('/admin/cotizaciones/<int:quote_id>/estado')
    @login_required
    def status(quote_id):
        from flask import abort
        admin_check()
        value = request.form.get('status')
        if value not in STATES:
            abort(422)
        quote = db.get_or_404(QuoteRequest, quote_id)
        quote.status = value
        db.session.commit()
        return redirect(url_for('quotes.admin_detail', quote_id=quote.id))

    @bp.post('/admin/cotizaciones/correo/<int:job_id>/reintentar')
    @login_required
    def retry(job_id):
        admin_check()
        job = db.get_or_404(QuoteMail, job_id)
        # A crash may leave ENVIANDO. Recover only after a bounded lease has expired.
        if job.status == 'ENVIANDO' and job.updated_at < utc_now().replace(tzinfo=None) - timedelta(minutes=5):
            job.status = 'INCIERTO'
            db.session.commit()
        deliver_mail(
            job.id,
            sender,
            allow_uncertain=request.form.get('confirm_uncertain') == 'on',
            recipient_for=recipient_for,
        )
        return redirect(url_for('quotes.admin_detail', quote_id=job.quote_id))

    @app.cli.command('cotizaciones-reintentar')
    @click.option('--limit', default=20, type=click.IntRange(1,100))
    def retry_pending(limit):
        """Retry safe pending/failed jobs only; never ambiguous or already-sent mail."""
        jobs = QuoteMail.query.filter(QuoteMail.status.in_(['PENDIENTE','FALLIDO']), QuoteMail.attempts<5).order_by(QuoteMail.id).limit(limit).all()
        for job in jobs:
            deliver_mail(job.id, sender, recipient_for=recipient_for)
        click.echo(f'Procesados: {len(jobs)}. Los resultados se consultan en el panel.')

    app.register_blueprint(bp)


def process_submission(sender, normalize_email, strict=False, social_links=None, recipient_for=None):
    values = request.form
    nonce = values.get('quote_nonce','')
    valid_session = nonce and (hmac.compare_digest(nonce,session.get('quote_nonce','')) or nonce in session.get('quote_completed',[]))
    existing = QuoteRequest.query.filter_by(submission_key=submission_key(nonce)).first() if valid_session else None
    if existing:
        flash(f'Esta solicitud ya está guardada: {existing.number}. No se ha creado un duplicado.', 'info')
        return redirect(url_for('quotes.form') + '#quoteForm')
    try:
        allowed = rate_limit('quotation', 5, 600)
    except SQLAlchemyError:
        db.session.rollback()
        return render_template('public/quotation.html', quote_errors=['No pudimos guardar tu solicitud. Inténtalo de nuevo o contacta por WhatsApp.'], quote_values=values, corporate_layout=True), 503
    if not allowed:
        return render_template('public/quotation.html', quote_errors=['Demasiadas solicitudes. Espera diez minutos.'], quote_values=values, corporate_layout=True), 429, {'Retry-After':'600'}
    fields = {key:values.get(key,'').strip() for key in ['name','company','phone','email','requested_service','message','budget']}
    email = normalize_email(fields['email'])
    errors = []
    if not valid_session:
        errors.append('La sesión del formulario cambió. Recarga la página e inténtalo de nuevo.')
    if values.get('website'):
        errors.append('No se pudo procesar la solicitud.')
    if not fields['name'] or not fields['requested_service'] or not fields['message']:
        errors.append('Completa nombre, servicio y descripción de la necesidad.')
    if email is None or (not email and not fields['phone']) or (strict and (not email or not fields['phone'])):
        errors.append('Indica un correo válido y teléfono.' if strict else 'Indica un correo válido o un teléfono de contacto.')
    if fields['phone'] and not __import__('re').fullmatch(r'[+()\d\s.-]{6,60}',fields['phone']):
        errors.append('Revisa el teléfono de contacto.')
    limits = dict(name=160,company=160,phone=60,email=160,requested_service=160,message=5000,budget=120)
    if any(len(fields[k])>limit for k,limit in limits.items()):
        errors.append('Uno de los campos supera la longitud permitida.')
    if values.get('accepted_privacy')!='on':
        errors.append('Acepta la Política de Privacidad para enviar tu consulta.')
    template = 'public/quotation.html' if strict else 'public/contact.html'
    if errors:
        return render_template(template, quote_errors=errors, quote_values=values, social_links=social_links or [], corporate_layout=True), 422
    try:
        quote, created = create_quote(dict(name=fields['name'],company=fields['company'],phone=fields['phone'],email=email,
                                           requested_service=fields['requested_service'],description=fields['message'],budget=fields['budget']), nonce)
    except SQLAlchemyError:
        db.session.rollback()
        return render_template(template, quote_errors=['No pudimos guardar tu solicitud. Inténtalo de nuevo o contacta por WhatsApp.'],
                               quote_values=values, social_links=social_links or [], corporate_layout=True), 503
    session['quote_completed'] = (session.get('quote_completed',[]) + [nonce])[-8:]
    session['quote_nonce'] = secrets.token_urlsafe(24)
    if created:
        deliver_quote(quote, sender, recipient_for=recipient_for)
    flash(f'Solicitud guardada para revisión: {quote.number}. Esta confirmación no acredita la entrega de un correo.', 'success')
    return redirect(url_for('quotes.form' if strict else 'contact_page') + '#quoteForm')
