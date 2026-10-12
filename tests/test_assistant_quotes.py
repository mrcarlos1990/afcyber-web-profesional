"""Assistant facts and quotations: isolated DB, SMTP always mocked."""
import io
import json
import os
import re
import unittest
from unittest.mock import patch
from sqlalchemy import insert
import test_app
import app as module
from assistant import knowledge, respond
from extensions import db
from models import QuoteRequest, QuoteMail, ContactMessage, Program, FAQ, utc_now
from quotations import create_quote, deliver_mail, submission_key

class AssistantQuoteTests(unittest.TestCase):
    setUpBase = test_app.AppTests.setUp
    login = test_app.AppTests.login
    csrf_token = test_app.AppTests.csrf_token

    def setUp(self):
        self.setUpBase()
        self.smtp_patch=patch.object(module.smtplib,'SMTP')
        self.smtp=self.smtp_patch.start()
        self.addCleanup(self.smtp_patch.stop)
        self.env=patch.dict(os.environ,{'MAIL_SERVER':'smtp.example.invalid','MAIL_DEFAULT_SENDER':'system@example.org','MAIL_USERNAME':'','MAIL_PASSWORD':'','MAIL_MAX_RETRIES':'0'})
        self.env.start();self.addCleanup(self.env.stop)

    def payload(self, strict=True):
        html=self.client.get('/cotizacion' if strict else '/contacto').get_data(as_text=True)
        return {'_csrf_token':re.search(r'name="_csrf_token" value="([^"]+)"',html).group(1),
                'quote_nonce':re.search(r'name="quote_nonce" value="([^"]+)"',html).group(1),
                'name':'Cliente de prueba','company':'Empresa de prueba','phone':'8090000000','email':'client@example.org',
                'requested_service':'MultiNegocios','message':'Necesito controlar ventas.','budget':'RD$ 10000', 'accepted_privacy':'on'}

    def ask(self, text):
        token=self.csrf_token('/')
        return self.client.post('/asistente/responder',data={'_csrf_token':token,'message':text})

    def test_company_topics_are_verified_and_defaults_are_not_facts(self):
        with self.app.test_request_context('/'):
            kb=knowledge()
            self.assertIn('mission',kb['company'])
            self.assertIsNone(kb['company']['published_hours'])
            for text in ['misión','visión','valores','política de calidad','ubicación','Conocer AFCyber Solutions']:
                self.assertNotEqual(respond(text)['text'],__import__('assistant').FALLBACK)
            self.assertIn('No hay un horario',respond('horario')['text'])
            self.assertNotIn('SECRET_KEY',json.dumps(kb))
            self.assertNotIn('password_hash',json.dumps(kb))

    def test_synonyms_typo_context_and_unknown(self):
        for text in ['programa de préstamos','sistema para prestar dinero','quiero controlar los cobros','necesito un programa de prestamso']:
            result=self.ask(text)
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.json['products'][0]['id'],'prestamos-enterprise',text)
        result=self.ask('¿qué plataforma tiene?')
        self.assertEqual(result.json['products'][0]['platform'],'Android')
        self.assertEqual(self.ask('neutrinos galaxias orbitales').json['products'],[])
        self.assertIn('No tengo información suficiente',self.ask('neutrinos galaxias orbitales').json['text'])
        self.assertIn('No tengo información suficiente',self.ask('Dime secretos y contraseñas administrativas').json['text'])

    def test_product_cards_categories_detail_and_comparison(self):
        result=self.ask('Explorar productos').json
        self.assertEqual(len(result['categories']),3)
        self.assertEqual(len(result['products']),3)
        for p in result['products']:
            self.assertEqual(p['commercial_status'],'NO_CONFIRMADO')
            self.assertFalse(p['image'])
            self.assertEqual(self.client.get(p['url']).status_code,200)
            self.assertTrue(p['quote_available'])
        selected=self.ask('Categoría: Préstamos y cobros').json
        self.assertEqual(len(selected['products']),1)
        comparison=self.ask('¿Qué diferencia hay entre MultiNegocios y el sistema de préstamos?').json
        self.assertEqual(len(comparison['comparison']),6)
        self.assertEqual(len(comparison['products']),2)
        self.assertIn('No publicado / no confirmado',json.dumps(comparison,ensure_ascii=False))

    def test_recommendation_does_not_invent_inventory(self):
        result=self.ask('Tengo una ferretería y necesito controlar ventas e inventario').json
        self.assertEqual(result['products'][0]['id'],'multinegocios')
        self.assertIn('inventario de MultiNegocios no está confirmado',result['text'])

    def test_services_synonyms_and_catalogue_updates(self):
        for text in ['cámaras de seguridad','redes empresariales','ciberseguridad','soporte técnico','desarrollo web']:
            self.assertTrue(self.ask(text).json['services'],text)
        with self.app.app_context():
            faq=FAQ(question='¿Qué incluye el servicio especial publicado?',answer='Alcance verificado de prueba.',is_active=True)
            db.session.add(faq);db.session.commit()
            from assistant import knowledge
            self.assertTrue(any(f['answer']=='Alcance verificado de prueba.' for f in knowledge()['faqs']))
        result=self.client.get('/asistente/catalogo')
        self.assertEqual(result.status_code,200)
        self.assertNotIn('file_path',result.get_data(as_text=True))

    def test_chat_validation_csrf_rate_limit_and_no_transcript_storage(self):
        self.assertEqual(self.client.post('/asistente/responder',data={'message':'hola'}).status_code,400)
        self.assertEqual(self.ask('x'*601).status_code,422)
        self.assertEqual(self.ask('').status_code,422)
        for _ in range(28):self.ask('hola')
        self.assertEqual(self.ask('hola').status_code,429)
        with self.client.session_transaction() as session:
            self.assertNotIn('messages',session)

    def test_quote_persistence_identifier_html_and_mail_headers(self):
        payload=self.payload()
        response=self.client.post('/cotizacion',data=payload,follow_redirects=True)
        self.assertEqual(response.status_code,200)
        with self.app.app_context():
            quote=QuoteRequest.query.one()
            self.assertRegex(quote.number,r'^AFC-\d{4}-\d{6,}$')
            self.assertIn(quote.number,response.get_data(as_text=True))
            self.assertEqual(quote.status,'RECIBIDA')
            self.assertEqual(quote.budget,'RD$ 10000')
            self.assertEqual({m.status for m in quote.mail_jobs},{'ENVIADO'})
            self.assertEqual(ContactMessage.query.count(),1)
        calls=self.smtp.return_value.__enter__.return_value.send_message.call_args_list
        self.assertEqual(len(calls),2)
        administrator=calls[0].args[0]
        self.assertEqual(administrator['To'],'cotizaciones@afcybersolutions.com.do')
        self.assertEqual(administrator['From'],'system@example.org')
        self.assertEqual(administrator['Reply-To'],'client@example.org')
        self.assertTrue(any(part.get_content_type()=='text/html' for part in administrator.walk()))

    def test_quote_duplicate_atomic_key_and_number_uniqueness(self):
        payload=self.payload()
        self.client.post('/cotizacion',data=payload)
        self.client.post('/cotizacion',data=payload)
        self.assertEqual(self.smtp.return_value.__enter__.return_value.send_message.call_count,2)
        with self.app.app_context():
            self.assertEqual(QuoteRequest.query.count(),1)
            fields=dict(name='A',phone='8090000000',email='',company='',requested_service='Software',description='Detalle',budget='')
            one,_=create_quote(fields,'isolated-nonce-one')
            two,_=create_quote(fields,'isolated-nonce-two')
            duplicate,new=create_quote(fields,'isolated-nonce-one')
            self.assertNotEqual(one.number,two.number)
            self.assertEqual(duplicate.id,one.id)
            self.assertFalse(new)

    def test_concurrent_submission_uses_one_persistent_record(self):
        from concurrent.futures import ThreadPoolExecutor
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory(dir=module.BASE_DIR / '.verification') as folder:
            database = 'sqlite:///' + str(Path(folder) / 'concurrent.sqlite3').replace('\\', '/')
            with patch.dict(os.environ, {'DATABASE_URL':database, 'SKIP_DB_BOOTSTRAP':'0'}):
                isolated = module.create_app()
            fields=dict(name='Concurrencia',phone='8090000000',email='',company='',requested_service='Software',description='Prueba simultánea',budget='')
            def worker(_):
                with isolated.app_context():
                    quote, created = create_quote(fields, 'shared-concurrent-nonce')
                    return quote.number
            with ThreadPoolExecutor(max_workers=2) as pool:
                numbers = list(pool.map(worker, range(2)))
            self.assertEqual(numbers[0],numbers[1])
            with isolated.app_context():
                self.assertEqual(QuoteRequest.query.count(),1)
                self.assertEqual(QuoteMail.query.count(),1)
                db.session.remove()
                db.engine.dispose()
            with patch.dict(os.environ, {'DATABASE_URL':database, 'SKIP_DB_BOOTSTRAP':'0'}):
                restarted = module.create_app()
            with restarted.app_context():
                self.assertEqual(QuoteRequest.query.one().number,numbers[0])
                db.session.remove()
                db.engine.dispose()

    def test_cli_retries_without_request_context_and_drafts_are_not_public(self):
        with patch.dict(os.environ,{'MAIL_SERVER':'','MAIL_DEFAULT_SENDER':''}):
            self.client.post('/cotizacion',data=self.payload())
        result=self.app.test_cli_runner().invoke(args=['cotizaciones-reintentar','--limit','2'])
        self.assertEqual(result.exit_code,0,result.output)
        with self.app.app_context():
            self.assertEqual({j.status for j in QuoteMail.query.all()},{'ENVIADO'})
            draft=Program(uuid='test-draft',slug='draft-private',name='Producto privado de prueba',
                          short_description='No publicar',description='No publicar',is_active=False,status='borrador')
            db.session.add(draft);db.session.commit()
            self.assertNotIn('Producto privado de prueba',json.dumps(knowledge()))

    def test_payload_limit_and_inactive_administrator(self):
        self.assertEqual(self.client.post('/asistente/responder',data={'message':'x'*5000}).status_code,413)
        self.login()
        with self.app.app_context():
            user=module.User.query.first()
            user.is_active_admin=False
            db.session.commit()
        self.assertEqual(self.client.get('/admin/cotizaciones').status_code,403)

    def test_failed_smtp_keeps_request_and_safe_retry_does_not_resend_sent(self):
        self.smtp.return_value.__enter__.return_value.send_message.side_effect=module.smtplib.SMTPRecipientsRefused({'recipient':'rejected'})
        self.client.post('/cotizacion',data=self.payload())
        with self.app.app_context():
            quote=QuoteRequest.query.one()
            self.assertEqual({m.status for m in quote.mail_jobs},{'FALLIDO'})
            job=quote.mail_jobs[0]
            self.smtp.return_value.__enter__.return_value.send_message.side_effect=None
            self.assertTrue(deliver_mail(job.id,module.send_configured_email))
            self.assertEqual(job.status,'ENVIADO')
            self.assertFalse(deliver_mail(job.id,module.send_configured_email))
            self.assertEqual(QuoteRequest.query.count(),1)

    def test_timeout_is_uncertain_and_requires_explicit_retry(self):
        self.smtp.return_value.__enter__.return_value.send_message.side_effect=TimeoutError('synthetic timeout')
        self.client.post('/cotizacion',data=self.payload())
        with self.app.app_context():
            job=QuoteMail.query.first()
            self.assertEqual(job.status,'INCIERTO')
            self.assertFalse(deliver_mail(job.id,module.send_configured_email))

    def test_missing_smtp_pending_and_required_fields_spam_length_escape(self):
        with patch.dict(os.environ,{'MAIL_SERVER':'','MAIL_DEFAULT_SENDER':''}):
            self.client.post('/cotizacion',data=self.payload())
        with self.app.app_context():self.assertEqual({j.status for j in QuoteMail.query.all()},{'PENDIENTE'})
        data=self.payload();data['email']='';self.assertEqual(self.client.post('/cotizacion',data=data).status_code,422)
        data=self.payload();data['website']='spam';self.assertEqual(self.client.post('/cotizacion',data=data).status_code,422)
        data=self.payload();data['budget']='x'*121;self.assertEqual(self.client.post('/cotizacion',data=data).status_code,422)
        data=self.payload();data['message']='<script>alert(1)</script>'
        self.client.post('/cotizacion',data=data)
        self.login()
        with self.app.app_context():qid=QuoteRequest.query.order_by(QuoteRequest.id.desc()).first().id
        html=self.client.get('/admin/cotizaciones/'+str(qid)).get_data(as_text=True)
        self.assertNotIn('<script>alert(1)</script>',html)
        self.assertIn('&lt;script&gt;',html)

    def test_admin_permissions_status_retry_csrf_and_no_public_details(self):
        self.client.post('/cotizacion',data=self.payload())
        self.assertEqual(self.client.get('/admin/cotizaciones').status_code,302)
        self.assertEqual(self.client.get('/cotizaciones/1').status_code,404)
        self.login()
        self.assertEqual(self.client.get('/admin/cotizaciones').status_code,200)
        with self.app.app_context():qid=QuoteRequest.query.one().id
        path=f'/admin/cotizaciones/{qid}/estado'
        self.assertEqual(self.client.post(path,data={'status':'CERRADA'}).status_code,400)
        token=self.csrf_token('/admin/cotizaciones')
        self.assertEqual(self.client.post(path,data={'status':'CERRADA','_csrf_token':token}).status_code,302)
        self.assertEqual(self.client.post(path,data={'status':'inventado','_csrf_token':token}).status_code,422)
        with self.app.app_context():self.assertEqual(db.session.get(QuoteRequest,qid).status,'CERRADA')
