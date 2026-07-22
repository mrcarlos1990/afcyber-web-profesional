import os
import re
import secrets
import hashlib
import html
import hmac
import mimetypes
import smtplib
import ssl
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parseaddr
from io import BytesIO
from pathlib import Path
from time import time
from urllib.parse import urlparse
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, Response, abort, flash, has_request_context, redirect, render_template, request, send_file, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import inspect as sa_inspect
from werkzeug.utils import secure_filename

try:
    from flask_migrate import Migrate
except ImportError:  # pragma: no cover - la dependencia se instala en produccion/staging.
    Migrate = None

try:
    import qrcode
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ImportError:  # pragma: no cover - respaldo local si faltan librerias PDF.
    qrcode = None
    colors = None
    TA_CENTER = None
    letter = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    inch = None
    Image = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None

try:
    from email_validator import EmailNotValidError, validate_email
except ImportError:  # pragma: no cover - respaldo para entornos locales sin dependencias instaladas.
    class EmailNotValidError(ValueError):
        pass

    class _ValidatedEmail:
        def __init__(self, normalized):
            self.normalized = normalized

    def validate_email(value, check_deliverability=False):
        parsed_name, parsed_email = parseaddr(value)
        if parsed_name or not parsed_email or parsed_email != value or not EMAIL_RE.fullmatch(parsed_email):
            raise EmailNotValidError(value)
        return _ValidatedEmail(parsed_email.lower())

from extensions import db, login_manager
from models import (
    AboutSection,
    Attachment,
    CEOProfile,
    ContactMessage,
    Customer,
    DocumentTemplate,
    DocumentVersion,
    DownloadEvent,
    ElectronicSignature,
    EmailDelivery,
    FAQ,
    HeroSection,
    Manual,
    Plan,
    PortfolioProject,
    Program,
    Service,
    ServiceDocument,
    ServiceRequest,
    SignatureAuditEvent,
    SignatureRequest,
    SiteSettings,
    SocialLink,
    Testimonial,
    User,
    utc_now,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
PRIVATE_STORAGE_ROOT_ENV = os.getenv("PRIVATE_STORAGE_ROOT", "").strip()
PRIVATE_STORAGE = Path(PRIVATE_STORAGE_ROOT_ENV).expanduser() if PRIVATE_STORAGE_ROOT_ENV else BASE_DIR / "storage"
if not PRIVATE_STORAGE.is_absolute():
    PRIVATE_STORAGE = BASE_DIR / PRIVATE_STORAGE
PRIVATE_STORAGE = PRIVATE_STORAGE.resolve()
DOWNLOAD_STORAGE = PRIVATE_STORAGE / "downloads"
INSTALLER_STORAGE = PRIVATE_STORAGE / "installers"
MANUAL_STORAGE = PRIVATE_STORAGE / "manuals"
DOCUMENT_STORAGE = PRIVATE_STORAGE / "documents"
SIGNED_PDF_STORAGE = PRIVATE_STORAGE / "signed-pdfs"
ATTACHMENT_STORAGE = PRIVATE_STORAGE / "attachments"
LOG_STORAGE = PRIVATE_STORAGE / "logs"
ALLOWED_IMAGES = {"jpg", "jpeg", "png", "webp", "ico"}
ALLOWED_DOCS = {"pdf"}
ALLOWED_PROGRAM_FILES = {"exe", "msi", "zip"}
ALLOWED_MANUAL_FILES = {"pdf"}
ALLOWED_ATTACHMENT_FILES = {"pdf", "jpg", "jpeg", "png", "webp", "zip"}
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
GOOGLE_TAG_RE = re.compile(r"^(G|GT|UA|AW)-[A-Za-z0-9-]{4,}$")
CONSENT_VERSION = "2026-07"
OTP_TTL_MINUTES = 15
OTP_MAX_ATTEMPTS = 5
SIGNATURE_TOKEN_TTL_HOURS = 72
SIGNED_DOCUMENT_STATUSES = {"firmado_cliente", "firmado_afcyber", "firmado_por_ambas_partes"}
REQUIRED_PRODUCTION_TABLES = {
    "user",
    "site_settings",
    "manual",
    "program",
    "customer",
    "service_request",
    "service_document",
    "document_version",
    "signature_request",
    "electronic_signature",
    "signature_audit_event",
    "email_delivery",
    "attachment",
}


def is_debug_mode():
    return os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes", "on"}


def is_production_mode():
    return not is_debug_mode()


def path_is_relative_to(child, parent):
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def should_auto_create_db():
    return is_debug_mode() or os.getenv("AUTO_CREATE_DB", "0").lower() in {"1", "true", "yes", "on"}


def is_migration_command():
    args = [arg.lower() for arg in sys.argv[1:]]
    return "db" in args or os.getenv("SKIP_DB_BOOTSTRAP", "0") == "1"


def require_production_runtime(database_url):
    if not is_production_mode():
        return
    if not os.getenv("DATABASE_URL", "").strip():
        raise RuntimeError("DATABASE_URL es obligatorio en produccion.")
    if database_url.startswith("sqlite"):
        raise RuntimeError("Produccion debe usar PostgreSQL mediante DATABASE_URL; SQLite queda reservado para desarrollo.")
    if not os.getenv("BASE_URL", "").strip():
        raise RuntimeError("BASE_URL es obligatorio en produccion para enlaces de firma y verificacion.")
    if not PRIVATE_STORAGE_ROOT_ENV:
        raise RuntimeError("PRIVATE_STORAGE_ROOT es obligatorio en produccion para guardar archivos privados fuera del repositorio.")
    if path_is_relative_to(PRIVATE_STORAGE, BASE_DIR):
        raise RuntimeError("PRIVATE_STORAGE_ROOT debe apuntar a almacenamiento persistente externo al repositorio.")
    if path_is_relative_to(PRIVATE_STORAGE, UPLOAD_FOLDER):
        raise RuntimeError("Los documentos privados no pueden guardarse dentro de static/uploads.")
    if os.getenv("REQUIRE_SMTP", "1") == "1":
        if not os.getenv("MAIL_SERVER", "").strip() or not os.getenv("MAIL_DEFAULT_SENDER", "").strip():
            raise RuntimeError("MAIL_SERVER y MAIL_DEFAULT_SENDER son obligatorios en produccion.")


def validate_database_schema():
    inspector = sa_inspect(db.engine)
    missing = sorted(table for table in REQUIRED_PRODUCTION_TABLES if not inspector.has_table(table))
    if missing:
        raise RuntimeError(
            "La base no esta migrada. Ejecuta 'flask db upgrade' en staging/produccion. "
            f"Tablas faltantes: {', '.join(missing)}"
        )


def get_secret_key():
    secret_key = os.getenv("SECRET_KEY", "").strip()
    if secret_key and secret_key != "change-this-secret-key" and len(secret_key) >= 32:
        return secret_key
    if is_debug_mode():
        return secrets.token_urlsafe(32)
    raise RuntimeError("Configura SECRET_KEY con un valor seguro de al menos 32 caracteres.")


def get_initial_admin_password():
    password = os.getenv("ADMIN_PASSWORD", "").strip()
    if not password:
        if is_debug_mode():
            return secrets.token_urlsafe(18)
        raise RuntimeError("Configura ADMIN_PASSWORD antes del primer arranque en produccion.")
    if not is_debug_mode() and (password == "Admin12345!" or len(password) < 12):
        raise RuntimeError("ADMIN_PASSWORD debe cambiarse por una contraseña fuerte antes de producción.")
    return password


def create_app():
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'afcyber_platform.db'}")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    require_production_runtime(database_url)
    secure_cookie = os.getenv("SESSION_COOKIE_SECURE", "0" if is_debug_mode() else "1") == "1"
    engine_options = {"pool_pre_ping": True} if database_url.startswith("postgresql") else {}

    app.config["SECRET_KEY"] = get_secret_key()
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "60")) * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
    app.config["PRIVATE_STORAGE_ROOT"] = str(PRIVATE_STORAGE)
    app.config["PREFERRED_URL_SCHEME"] = "https" if is_production_mode() else "http"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = secure_cookie
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"
    app.config["REMEMBER_COOKIE_SECURE"] = secure_cookie
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

    (BASE_DIR / "instance").mkdir(exist_ok=True)
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    for folder in [DOWNLOAD_STORAGE, INSTALLER_STORAGE, MANUAL_STORAGE, DOCUMENT_STORAGE, SIGNED_PDF_STORAGE, ATTACHMENT_STORAGE, LOG_STORAGE]:
        folder.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    if Migrate:
        Migrate(app, db)
    login_manager.init_app(app)

    register_filters(app)
    register_security(app)
    register_routes(app)

    with app.app_context():
        if not is_migration_command():
            if should_auto_create_db():
                db.create_all()
            else:
                validate_database_schema()
            seed_database()

    return app


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def register_filters(app):
    @app.template_filter("asset")
    def asset(path):
        if not path:
            return ""
        if path.startswith("http"):
            return path
        return url_for("static", filename=f"uploads/{path}")

    @app.template_filter("lines")
    def lines(value):
        return [line.strip() for line in (value or "").splitlines() if line.strip()]

    @app.template_filter("filesize")
    def filesize(value):
        return file_size_label(value)


def register_security(app):
    @app.before_request
    def csrf_protect():
        session.setdefault("_csrf_token", secrets.token_urlsafe(32))
        if request.method == "POST":
            token = session.get("_csrf_token")
            form_token = request.form.get("_csrf_token")
            if not token or not form_token or not secrets.compare_digest(token, form_token):
                abort(400)

    @app.context_processor
    def inject_csrf():
        session.setdefault("_csrf_token", secrets.token_urlsafe(32))
        return {"csrf_token": session["_csrf_token"]}

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.path.startswith("/admin"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response


def get_or_create(model):
    item = model.query.first()
    if not item:
        item = model()
        db.session.add(item)
        db.session.commit()
    return item


def get_settings():
    return get_or_create(SiteSettings)


def get_hero():
    return get_or_create(HeroSection)


def get_about():
    return get_or_create(AboutSection)


def get_ceo():
    return get_or_create(CEOProfile)


def checkbox_value(name):
    return request.form.get(name) == "on"


def form_text(name, max_length=None):
    value = request.form.get(name, "").strip()
    if max_length and len(value) > max_length:
        return value[:max_length]
    return value


def form_int(name, label, default=0, min_value=None, max_value=None):
    raw = request.form.get(name, "").strip()
    if raw == "":
        value = default
    else:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            flash(f"{label} debe ser un número válido.", "danger")
            return None
    if min_value is not None and value < min_value:
        flash(f"{label} no puede ser menor que {min_value}.", "danger")
        return None
    if max_value is not None and value > max_value:
        flash(f"{label} no puede ser mayor que {max_value}.", "danger")
        return None
    return value


def normalize_email(value, required=False):
    value = (value or "").strip().lower()
    if not value:
        return None if required else ""
    try:
        return validate_email(value, check_deliverability=False).normalized
    except EmailNotValidError:
        flash("El correo electrónico no tiene un formato válido.", "danger")
        return None


def password_is_strong(password):
    return (
        len(password or "") >= 12
        and any(char.islower() for char in password)
        and any(char.isupper() for char in password)
        and any(char.isdigit() for char in password)
    )


def clean_url(value, *, allow_fragment=False, allow_relative=False):
    value = (value or "").strip()
    if not value:
        return ""
    if allow_fragment and value.startswith("#"):
        return value
    if allow_relative and value.startswith("/") and not value.startswith("//"):
        return value
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value
    flash("Se ignoró una URL inválida o potencialmente insegura.", "warning")
    return ""


def clean_color(value, fallback):
    value = (value or "").strip()
    if HEX_COLOR_RE.fullmatch(value):
        return value
    flash("Se restauró un color inválido a su valor anterior.", "warning")
    return fallback


def allowed_file(filename, allow_pdf=False):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in (ALLOWED_IMAGES | (ALLOWED_DOCS if allow_pdf else set()))


def detect_upload_type(file):
    position = file.stream.tell()
    header = file.stream.read(512)
    file.stream.seek(position)
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    if header.startswith(b"\x00\x00\x01\x00"):
        return "ico"
    if header.startswith(b"%PDF-"):
        return "pdf"
    return None


def upload_matches_extension(ext, detected, allow_pdf=False):
    if ext in {"jpg", "jpeg"}:
        return detected == "jpg"
    if ext in {"png", "webp", "ico"}:
        return detected == ext
    if allow_pdf and ext == "pdf":
        return detected == "pdf"
    return False


def save_upload(file, allow_pdf=False):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename, allow_pdf=allow_pdf):
        flash("Archivo no permitido. Usa jpg, jpeg, png, webp, ico o PDF cuando aplique.", "danger")
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    detected = detect_upload_type(file)
    if not upload_matches_extension(ext, detected, allow_pdf=allow_pdf):
        flash("El contenido del archivo no coincide con su extensión.", "danger")
        return None
    safe_name = secure_filename(file.filename.rsplit(".", 1)[0])[:64] or "archivo"
    filename = f"{safe_name}-{uuid4().hex[:10]}.{ext}"
    file.save(UPLOAD_FOLDER / filename)
    return filename


def slugify(value):
    value = (value or "").strip().lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n",
        "ü": "u",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or f"item-{uuid4().hex[:8]}"


def unique_slug(model, value, current_id=None):
    base = slugify(value)
    slug = base
    counter = 2
    while True:
        query = model.query.filter_by(slug=slug)
        if current_id:
            query = query.filter(model.id != current_id)
        if not query.first():
            return slug
        slug = f"{base}-{counter}"
        counter += 1


def make_uuid():
    return str(uuid4())


def make_public_code(prefix):
    return f"{prefix}-{secrets.token_hex(4).upper()}"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def app_secret_bytes():
    return str(current_app_secret()).encode("utf-8")


def current_app_secret():
    return os.getenv("SIGNING_SECRET") or os.getenv("SECRET_KEY") or "local-dev-secret"


def hash_token(value):
    return hmac.new(app_secret_bytes(), (value or "").encode("utf-8"), hashlib.sha256).hexdigest()


def request_fingerprint(value):
    if not value:
        return ""
    return hmac.new(app_secret_bytes(), value.encode("utf-8", errors="ignore"), hashlib.sha256).hexdigest()


def request_ip_hash():
    return request_fingerprint(request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip())


def request_user_agent_hash():
    return request_fingerprint(request.headers.get("User-Agent", ""))


def file_size_label(size):
    size = int(size or 0)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024
    return "0 B"


def parse_date(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        flash("La fecha indicada no tiene un formato válido.", "danger")
        return None


def as_utc(value):
    if not value:
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def managed_upload_type(file):
    position = file.stream.tell()
    header = file.stream.read(1024)
    file.stream.seek(position)
    if header.startswith(b"MZ"):
        return "exe"
    if header.startswith(b"PK\x03\x04") or header.startswith(b"PK\x05\x06") or header.startswith(b"PK\x07\x08"):
        return "zip"
    if header.startswith(b"\xd0\xcf\x11\xe0"):
        return "msi"
    if header.startswith(b"%PDF-"):
        return "pdf"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    return None


def upload_matches_kind(ext, detected):
    if ext in {"jpg", "jpeg"}:
        return detected == "jpg"
    return ext == detected


def save_private_upload(file, allowed_exts, folder):
    if not file or not file.filename:
        return None
    if "." not in file.filename:
        flash("El archivo necesita extensión.", "danger")
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in allowed_exts:
        flash("Tipo de archivo no permitido para esta sección.", "danger")
        return None
    detected = managed_upload_type(file)
    if not upload_matches_kind(ext, detected):
        flash("El contenido del archivo no coincide con su extensión.", "danger")
        return None
    safe_name = secure_filename(file.filename.rsplit(".", 1)[0])[:64] or "archivo"
    filename = f"{safe_name}-{uuid4().hex[:10]}.{ext}"
    target = folder / filename
    digest = hashlib.sha256()
    size = 0
    file.stream.seek(0)
    with target.open("wb") as handle:
        for chunk in iter(lambda: file.stream.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
            handle.write(chunk)
    return {
        "relative_path": str(target.relative_to(PRIVATE_STORAGE)).replace("\\", "/"),
        "size": size,
        "sha256": digest.hexdigest(),
    }


def private_path(relative_path):
    candidate = (PRIVATE_STORAGE / (relative_path or "")).resolve()
    if not path_is_relative_to(candidate, PRIVATE_STORAGE):
        abort(404)
    return candidate


def first_active_template():
    template = DocumentTemplate.query.filter_by(is_active=True).order_by(DocumentTemplate.id).first()
    if template:
        return template
    template = DocumentTemplate(
        uuid=make_uuid(),
        name="Solicitud de servicio",
        document_type="Solicitud de servicio",
        version=1,
        body=(
            "Documento de solicitud de servicio para AFCyber Solutions.\n\n"
            "Cliente: {{customer_name}}\n"
            "Servicio solicitado: {{service}}\n"
            "Necesidad: {{need}}\n\n"
            "Este documento registra una solicitud inicial y no sustituye un contrato definitivo. "
            "Las condiciones comerciales, alcance final, precios, impuestos y garantías deben ser revisados y aprobados por ambas partes."
        ),
        status="publicada",
        is_active=True,
    )
    db.session.add(template)
    db.session.flush()
    return template


def render_document_content(template, service_request):
    customer = service_request.customer
    replacements = {
        "{{customer_name}}": customer.full_name,
        "{{customer_email}}": customer.email,
        "{{customer_phone}}": customer.phone,
        "{{company}}": customer.company or "No indicada",
        "{{service}}": service_request.requested_service,
        "{{need}}": service_request.need_description,
        "{{modality}}": service_request.modality,
        "{{priority}}": service_request.priority,
    }
    content = template.body
    for key, value in replacements.items():
        content = content.replace(key, value or "")
    return content


def pdf_escape(value):
    return (value or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_simple_pdf(title, lines):
    wrapped = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(textwrap.wrap(str(line), width=92) or [""])
    content_lines = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    for index, line in enumerate([title, ""] + wrapped[:65]):
        if index:
            content_lines.append("T*")
        content_lines.append(f"({pdf_escape(line)}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(pdf.tell())
        pdf.write(f"{index} 0 obj\n".encode())
        pdf.write(obj)
        pdf.write(b"\nendobj\n")
    xref = pdf.tell()
    pdf.write(f"xref\n0 {len(objects)+1}\n".encode())
    pdf.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode())
    pdf.write(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return pdf.getvalue()


def paragraph(text, style):
    safe = html.escape(str(text or "")).replace("\n", "<br/>")
    return Paragraph(safe, style)


def build_professional_pdf(document, version, verification_url, signatures, audit_events, watermark=None):
    if not all([qrcode, SimpleDocTemplate, Paragraph, Table, TableStyle, Image, colors, inch, letter]):
        return None

    buffer = BytesIO()
    pdf_doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f"{document.code} - AFCyber Solutions",
        author="AFCyber Solutions",
        subject=document.document_type,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="AFTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=17, leading=21, spaceAfter=8))
    styles.add(ParagraphStyle(name="AFSmall", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#475569")))

    qr_buffer = BytesIO()
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    base_hash = version.sha256 or document.final_sha256 or "Pendiente de calculo"
    story = [
        paragraph("AFCyber Solutions", styles["AFTitle"]),
        paragraph(document.title, styles["Heading2"]),
    ]
    meta_rows = [
        ["Numero de documento", document.code],
        ["Tipo", document.document_type or ""],
        ["Version", str(version.version_number if version else document.current_version)],
        ["Estado", document.status],
        ["Fecha de emision", document.created_at.strftime("%d/%m/%Y %H:%M UTC") if document.created_at else ""],
        ["Hash SHA-256 de version", base_hash],
        ["Verificacion", verification_url],
    ]
    meta_table = Table(
        [[paragraph(label, styles["AFSmall"]), paragraph(value, styles["AFSmall"])] for label, value in meta_rows],
        colWidths=[1.7 * inch, 4.35 * inch],
    )
    meta_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef6ff")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    qr_image = Image(qr_buffer, width=1.45 * inch, height=1.45 * inch)
    header = Table([[meta_table, qr_image]], colWidths=[6.25 * inch, 1.55 * inch])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.extend([header, Spacer(1, 0.2 * inch)])

    if watermark:
        story.extend([paragraph(watermark, styles["AFSmall"]), Spacer(1, 0.1 * inch)])

    story.extend([
        paragraph("Contenido del documento", styles["Heading3"]),
        paragraph(version.content if version else "", styles["BodyText"]),
        Spacer(1, 0.18 * inch),
    ])

    signature_rows = [["Rol", "Firmante", "Correo", "Fecha", "Hash firmado"]]
    for sig in signatures:
        signature_rows.append([
            sig.signer_role,
            sig.signer_name,
            sig.signer_email,
            sig.created_at.strftime("%d/%m/%Y %H:%M UTC") if sig.created_at else "",
            sig.signed_hash,
        ])
    if len(signature_rows) == 1:
        signature_rows.append(["Pendiente", "Sin firmas registradas para esta version", "", "", ""])
    sig_table = Table(
        [[paragraph(cell, styles["AFSmall"]) for cell in row] for row in signature_rows],
        colWidths=[0.75 * inch, 1.35 * inch, 1.55 * inch, 1.15 * inch, 2.3 * inch],
        repeatRows=1,
    )
    sig_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.extend([paragraph("Firmas electronicas", styles["Heading3"]), sig_table, Spacer(1, 0.18 * inch)])

    audit_rows = [["Evento", "Detalle", "Fecha"]]
    for event in audit_events[:12]:
        audit_rows.append([
            event.event_type,
            event.detail or "",
            event.created_at.strftime("%d/%m/%Y %H:%M UTC") if event.created_at else "",
        ])
    audit_table = Table(
        [[paragraph(cell, styles["AFSmall"]) for cell in row] for row in audit_rows],
        colWidths=[1.45 * inch, 4.2 * inch, 1.45 * inch],
        repeatRows=1,
    )
    audit_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#164e63")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.extend([paragraph("Auditoria tecnica", styles["Heading3"]), audit_table, Spacer(1, 0.16 * inch)])
    story.append(paragraph(
        "Este documento registra firma electronica con trazabilidad tecnica. No se declara firma digital certificada o cualificada sin revision legal aplicable.",
        styles["AFSmall"],
    ))
    pdf_doc.build(story)
    return buffer.getvalue()


def create_document_pdf(document, version=None, watermark=None):
    version = version or DocumentVersion.query.filter_by(document_id=document.id).order_by(DocumentVersion.version_number.desc()).first()
    version_number = version.version_number if version else document.current_version
    signatures = ElectronicSignature.query.filter_by(document_id=document.id, version_number=version_number).order_by(ElectronicSignature.created_at).all()
    audit_events = SignatureAuditEvent.query.filter_by(document_id=document.id).order_by(SignatureAuditEvent.created_at.desc()).all()
    verification_url = url_for("verify_document", codigo=document.verification_code, _external=True)
    lines = [
        f"Código: {document.code}",
        f"Tipo: {document.document_type}",
        f"Estado: {document.status}",
        f"Fecha de emisión: {document.created_at.strftime('%d/%m/%Y %H:%M') if document.created_at else ''}",
        f"Verificación: {verification_url}",
        f"Hash actual: {version.sha256 if version else document.final_sha256 or 'Pendiente'}",
        "",
        "Contenido:",
        version.content if version else "",
        "",
        "Firmas electrónicas registradas:",
    ]
    if signatures:
        for sig in signatures:
            lines.append(f"- {sig.signer_role}: {sig.signer_name} <{sig.signer_email}> el {sig.created_at.strftime('%d/%m/%Y %H:%M')} UTC. Hash: {sig.signed_hash}")
    else:
        lines.append("- Pendiente de firma.")
    if watermark:
        lines.extend(["", f"Marca: {watermark}"])
    lines.extend([
        "",
        "Nota: este sistema registra una firma electrónica con trazabilidad técnica. No se declara como firma digital certificada o cualificada sin revisión legal.",
    ])
    professional_pdf = build_professional_pdf(document, version, verification_url, signatures, audit_events, watermark=watermark)
    data = professional_pdf if professional_pdf is not None else build_simple_pdf(f"AFCyber Solutions - {document.title}", lines)
    filename = f"{document.code.lower()}-v{document.current_version}-{uuid4().hex[:8]}.pdf"
    path = SIGNED_PDF_STORAGE / filename
    path.write_bytes(data)
    return str(path.relative_to(PRIVATE_STORAGE)).replace("\\", "/"), sha256_bytes(data)


def log_signature_event(event_type, document=None, signature_request=None, detail=""):
    db.session.add(SignatureAuditEvent(
        uuid=make_uuid(),
        document_id=document.id if document else None,
        signature_request_id=signature_request.id if signature_request else None,
        event_type=event_type,
        detail=detail,
        ip_hash=request_ip_hash() if has_request_context() else "",
        user_agent_hash=request_user_agent_hash() if has_request_context() else "",
    ))


def safe_mail_error(exc):
    message = f"{exc.__class__.__name__}: {exc}"
    for secret in [os.getenv("MAIL_PASSWORD", ""), os.getenv("MAIL_USERNAME", "")]:
        if secret:
            message = message.replace(secret, "[redacted]")
    return message[:1000]


def send_configured_email(recipient, subject, body, email_type, attachment_path=None):
    delivery = EmailDelivery(uuid=make_uuid(), recipient=recipient, subject=subject, email_type=email_type, status="pendiente")
    db.session.add(delivery)
    server = os.getenv("MAIL_SERVER", "").strip()
    sender = os.getenv("MAIL_DEFAULT_SENDER", "").strip()
    username = os.getenv("MAIL_USERNAME", "").strip()
    password = os.getenv("MAIL_PASSWORD", "").strip()
    if not server or not sender:
        delivery.status = "omitido"
        delivery.error = "Correo no configurado por variables de entorno."
        return delivery

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    if attachment_path:
        path = private_path(attachment_path)
        if path.exists():
            message.add_attachment(path.read_bytes(), maintype="application", subtype="pdf", filename=path.name)

    port = int(os.getenv("MAIL_PORT", "587"))
    use_tls = os.getenv("MAIL_USE_TLS", "1") == "1"
    max_retries = max(0, min(int(os.getenv("MAIL_MAX_RETRIES", "2")), 5))
    for attempt in range(max_retries + 1):
        try:
            with smtplib.SMTP(server, port, timeout=15) as smtp:
                if use_tls:
                    smtp.starttls(context=ssl.create_default_context())
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(message)
            delivery.status = "enviado"
            delivery.retries = attempt
            delivery.sent_at = utc_now()
            delivery.error = None
            return delivery
        except Exception as exc:  # pragma: no cover - depende de proveedor externo.
            delivery.status = "error"
            delivery.retries = attempt
            delivery.error = safe_mail_error(exc)
    return delivery


def create_signature_request(document, role, signer_name, signer_email, include_sign_link=True):
    token = secrets.token_urlsafe(32)
    otp = f"{secrets.randbelow(1000000):06d}"
    signature_request = SignatureRequest(
        uuid=make_uuid(),
        document_id=document.id,
        version_number=document.current_version,
        signer_role=role,
        signer_name=signer_name,
        signer_email=signer_email,
        token_hash=hash_token(token),
        expires_at=utc_now() + timedelta(hours=SIGNATURE_TOKEN_TTL_HOURS),
        otp_hash=hash_token(otp),
        otp_expires_at=utc_now() + timedelta(minutes=OTP_TTL_MINUTES),
        status="pendiente",
    )
    db.session.add(signature_request)
    db.session.flush()
    sign_url = url_for("sign_document", token=token, _external=True)
    if not include_sign_link:
        send_configured_email(
            signer_email,
            f"Firma pendiente - {document.code}",
            (
                f"Hola {signer_name},\n\n"
                f"Codigo OTP para firmar como representante AFCyber el documento {document.code}: {otp}\n"
                f"Vence en {OTP_TTL_MINUTES} minutos.\n\n"
                "Ingresa el codigo desde el panel administrativo."
            ),
            "signature_otp",
        )
        log_signature_event("signature_request_created", document, signature_request, f"Solicitud creada para {role}.")
        return signature_request, token
    send_configured_email(
        signer_email,
        f"Firma pendiente - {document.code}",
        (
            f"Hola {signer_name},\n\n"
            f"Revisa y firma el documento {document.code} en:\n{sign_url}\n\n"
            f"Código OTP: {otp}\nVence en {OTP_TTL_MINUTES} minutos.\n\n"
            "Si no solicitaste este documento, ignora este correo."
        ),
        "signature_otp",
    )
    log_signature_event("signature_request_created", document, signature_request, f"Solicitud creada para {role}.")
    return signature_request, token


def create_service_document(service_request):
    template = first_active_template()
    document = ServiceDocument(
        uuid=make_uuid(),
        code=make_public_code("DOC"),
        service_request_id=service_request.id,
        template_id=template.id,
        title=f"Solicitud de servicio - {service_request.requested_service}",
        document_type=template.document_type,
        status="pendiente_firma_cliente",
        current_version=1,
        verification_code=secrets.token_urlsafe(12),
        expires_at=utc_now() + timedelta(days=15),
    )
    db.session.add(document)
    db.session.flush()
    content = render_document_content(template, service_request)
    version = DocumentVersion(uuid=make_uuid(), document_id=document.id, version_number=1, content=content)
    db.session.add(version)
    db.session.flush()
    path, digest = create_document_pdf(document, version, watermark="Pendiente de firma")
    version.pdf_path = path
    version.sha256 = digest
    document.final_pdf_path = path
    document.final_sha256 = digest
    create_signature_request(document, "cliente", service_request.customer.full_name, service_request.customer.email)
    log_signature_event("document_created", document, detail="Documento generado desde solicitud de servicio.")
    return document


def has_signature_for_version(document, version_number, role):
    return ElectronicSignature.query.filter_by(
        document_id=document.id,
        version_number=version_number,
        signer_role=role,
    ).first() is not None


def refresh_document_signature_status(document, version_number=None):
    version_number = version_number or document.current_version
    has_client = has_signature_for_version(document, version_number, "cliente")
    has_afcyber = has_signature_for_version(document, version_number, "afcyber")
    if has_client and has_afcyber:
        document.status = "firmado_por_ambas_partes"
    elif has_client:
        document.status = "firmado_cliente"
    elif has_afcyber:
        document.status = "firmado_afcyber"
    else:
        document.status = "pendiente_firma_cliente"
    return document.status


def invalidate_pending_signature_requests(document, reason):
    for pending in SignatureRequest.query.filter_by(document_id=document.id, status="pendiente").all():
        pending.status = "invalidado_por_nueva_version"
        pending.reject_reason = reason


def create_new_document_version(document, content, reason=""):
    current_version = DocumentVersion.query.filter_by(
        document_id=document.id,
        version_number=document.current_version,
    ).first()
    if current_version and current_version.content == content:
        return current_version, False

    if current_version:
        current_version.status = "superada"
    invalidate_pending_signature_requests(document, reason or "Documento actualizado desde panel administrativo.")
    next_number = (document.current_version or 0) + 1
    version = DocumentVersion(
        uuid=make_uuid(),
        document_id=document.id,
        version_number=next_number,
        content=content,
        status="vigente",
    )
    db.session.add(version)
    document.current_version = next_number
    document.status = "pendiente_firma_cliente"
    db.session.flush()
    path, digest = create_document_pdf(document, version, watermark="Nueva version pendiente de firma")
    version.pdf_path = path
    version.sha256 = digest
    document.final_pdf_path = path
    document.final_sha256 = digest
    if document.service_request and document.service_request.customer:
        create_signature_request(document, "cliente", document.service_request.customer.full_name, document.service_request.customer.email)
    log_signature_event("document_version_created", document, detail=reason or f"Version {next_number} creada.")
    return version, True


def serve_download(item, item_type):
    if item.external_url:
        event = DownloadEvent(
            uuid=make_uuid(),
            item_type=item_type,
            item_id=item.id,
            item_slug=item.slug,
            ip_hash=request_ip_hash(),
            user_agent_hash=request_user_agent_hash(),
        )
        item.download_count = (item.download_count or 0) + 1
        item.last_downloaded_at = utc_now()
        db.session.add(event)
        db.session.commit()
        return redirect(item.external_url)
    if not item.file_path:
        return render_template("public/error.html", code=404, title="Archivo no disponible", message="El archivo aún no está configurado para descarga."), 404
    path = private_path(item.file_path)
    if not path.exists() or not path.is_file():
        return render_template("public/error.html", code=404, title="Archivo no encontrado", message="El archivo solicitado no está disponible en el almacenamiento."), 404
    digest = sha256_file(path)
    if item.sha256 and digest != item.sha256:
        log_signature_event("download_hash_mismatch", detail=f"{item_type}:{item.slug}")
        db.session.commit()
        return render_template("public/error.html", code=409, title="Archivo retenido", message="La verificación de integridad del archivo no coincide. Contacta a soporte."), 409
    item.download_count = (item.download_count or 0) + 1
    item.last_downloaded_at = utc_now()
    db.session.add(DownloadEvent(
        uuid=make_uuid(),
        item_type=item_type,
        item_id=item.id,
        item_slug=item.slug,
        ip_hash=request_ip_hash(),
        user_agent_hash=request_user_agent_hash(),
    ))
    db.session.commit()
    extension = path.suffix.lower()
    safe_download_name = secure_filename(f"{getattr(item, 'name', getattr(item, 'title', 'descarga'))}-{getattr(item, 'version', '1.0')}{extension}")
    return send_file(
        path,
        mimetype=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        as_attachment=True,
        download_name=safe_download_name,
        conditional=True,
    )


def seed_database():
    settings = get_settings()
    get_hero()
    get_about()
    get_ceo()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@afcybersolutions.com.do")
    if not User.query.filter_by(email=admin_email).first():
        user = User(email=admin_email, name="Administrador AFCyber")
        user.set_password(get_initial_admin_password())
        db.session.add(user)

    if Service.query.count() == 0:
        services = [
            ("Software empresarial", "Desarrollo de sistemas a medida, dashboards, inventario, facturación y gestión operativa.", "fa-solid fa-layer-group"),
            ("Sistemas POS / ERP", "Puntos de venta, control de caja, inventario, clientes, proveedores y reportes.", "fa-solid fa-cash-register"),
            ("Landing pages y webs", "Páginas web profesionales para empresas, catálogos digitales y presencia online.", "fa-solid fa-laptop-code"),
            ("Ciberseguridad básica", "Protección de equipos, buenas prácticas, revisión de vulnerabilidades, respaldos y seguridad de acceso.", "fa-solid fa-shield-halved"),
            ("CCTV y control de acceso", "Cámaras IP, acceso remoto, grabación, biometría y seguridad física.", "fa-solid fa-video"),
            ("Mantenimiento de computadoras", "Diagnóstico, limpieza, optimización, formateo y mejora de rendimiento.", "fa-solid fa-screwdriver-wrench"),
            ("Instalación de software", "Instalación de programas, drivers, antivirus y herramientas de trabajo.", "fa-solid fa-download"),
            ("Automatización empresarial", "Flujos digitales, reportes, herramientas internas y reducción de tareas repetitivas.", "fa-solid fa-gears"),
        ]
        for index, (name, description, icon) in enumerate(services, 1):
            db.session.add(Service(name=name, description=description, icon=icon, position=index))

    if Plan.query.count() == 0:
        plans = [
            ("Plan Básico", "A cotizar", "Presencia digital inicial para negocios que necesitan una página profesional.", "Página informativa\nBotón de WhatsApp\nDiseño responsive\nSEO inicial", False, 1),
            ("Plan Profesional", "A cotizar", "Web avanzada para marcas que buscan una presencia profesional y mejor captación.", "Página avanzada\nDominio y hosting\nSEO básico\nSecciones corporativas\nIntegración WhatsApp", True, 2),
            ("Plan Empresarial", "A cotizar", "Soluciones a medida para operaciones que requieren sistemas, paneles o automatización.", "Sistema personalizado\nPanel administrativo\nAutomatización\nSoporte técnico\nReportes", False, 3),
        ]
        for name, price, description, features, featured, position in plans:
            db.session.add(Plan(name=name, price=price, description=description, features=features, is_featured=featured, position=position))

    # El portafolio no se rellena con ejemplos para evitar publicar proyectos no verificados.

    if FAQ.query.count() == 0:
        faqs = [
            ("¿Qué servicios ofrece AFCyber Solutions?", "Ofrecemos desarrollo web, sistemas POS/ERP, soporte técnico, CCTV, ciberseguridad básica, mantenimiento y automatización.", 1),
            ("¿Cómo solicito una cotización?", "Puedes enviar el formulario o escribir por WhatsApp. Revisamos la necesidad y respondemos con los próximos pasos.", 2),
            ("¿Puedo solicitar un sistema personalizado?", "Sí. Evaluamos el proceso, definimos alcance y construimos una solución ajustada a la operación.", 3),
            ("¿Cómo empieza un proyecto?", "Primero revisamos la necesidad, aclaramos el alcance y luego preparamos una propuesta con entregables y próximos pasos.", 4),
        ]
        for question, answer, position in faqs:
            db.session.add(FAQ(question=question, answer=answer, position=position))

    if SocialLink.query.count() == 0:
        db.session.add(SocialLink(name="LinkedIn", icon="fa-brands fa-linkedin-in", url="#", position=1))
        db.session.add(SocialLink(name="Instagram", icon="fa-brands fa-instagram", url="#", position=2))
        db.session.add(SocialLink(name="Facebook", icon="fa-brands fa-facebook-f", url="#", position=3))

    update_known_default_content()
    db.session.commit()
    return settings


def update_known_default_content():
    def replace(item, field, replacements):
        current = getattr(item, field, None)
        if current in replacements:
            setattr(item, field, replacements[current])

    settings = get_settings()
    replace(settings, "company_name", {"AFCyber SOLUTIONS": "AFCyber Solutions"})
    replace(settings, "slogan", {
        "Soluciones tecnologicas modernas para empresas y emprendedores": "Tecnología, seguridad y soporte para negocios que quieren crecer",
    })
    replace(settings, "short_description", {
        "Servicios premium de desarrollo web, ciberseguridad, soporte, redes, sistemas empresariales y automatizacion.": "Desarrollo web, sistemas POS/ERP, CCTV, soporte técnico, automatización y ciberseguridad básica para empresas y hogares.",
    })
    replace(settings, "meta_title", {
        "AFCyber SOLUTIONS | Servicios tecnologicos premium": "AFCyber Solutions | Desarrollo Web, Sistema POS, CCTV y Soporte Técnico",
    })
    replace(settings, "meta_description", {
        "AFCyber SOLUTIONS ofrece desarrollo web, sistemas POS, CMMS, soporte tecnico, redes, camaras, ciberseguridad y automatizacion.": "AFCyber Solutions ofrece desarrollo web, sistemas POS/ERP, CCTV, soporte técnico, automatización y ciberseguridad básica en República Dominicana.",
    })
    replace(settings, "meta_keywords", {
        "AFCyber SOLUTIONS, desarrollo web, ciberseguridad, POS, CMMS, soporte tecnico, redes, camaras": "AFCyber Solutions, desarrollo web, sistemas POS, ERP, CCTV, soporte técnico, ciberseguridad, automatización, República Dominicana",
    })
    replace(settings, "footer_text", {"Desarrollado por AFCyber SOLUTIONS": "Desarrollado por AFCyber Solutions"})

    hero = get_hero()
    replace(hero, "title", {"AFCyber SOLUTIONS": "Soluciones tecnológicas para negocios que quieren crecer"})
    replace(hero, "subtitle", {
        "Soluciones tecnologicas modernas para empresas y emprendedores": "Software, web, CCTV, soporte técnico y ciberseguridad básica",
    })
    replace(hero, "description", {
        "Disenamos, implementamos y damos soporte a plataformas digitales, sistemas empresariales, redes, seguridad y automatizacion para negocios que necesitan tecnologia confiable.": "Desarrollo web, sistemas POS/ERP, ciberseguridad, CCTV, soporte técnico, automatización y servicios tecnológicos para empresas y hogares.",
    })
    replace(hero, "primary_button_text", {"Solicitar servicio": "Solicitar cotización"})
    replace(hero, "secondary_button_text", {"Contactar por WhatsApp": "Escribir por WhatsApp"})
    replace(hero, "secondary_button_message", {
        "Hola AFCyber SOLUTIONS, quiero solicitar informacion.": "Hola AFCyber Solutions, quiero solicitar información sobre sus servicios.",
    })

    about = get_about()
    replace(about, "history", {
        "AFCyber SOLUTIONS acompana a empresas y emprendedores en su transformacion digital con soluciones modernas, funcionales y seguras.": "AFCyber Solutions acompaña a empresas y emprendedores en su transformación digital con soluciones modernas, funcionales y seguras.",
    })
    replace(about, "mission", {
        "Crear soluciones tecnologicas claras, seguras y profesionales que impulsen la productividad de cada cliente.": "Crear soluciones tecnológicas claras, seguras y profesionales que impulsen la productividad de cada cliente.",
    })
    replace(about, "vision", {
        "Ser una marca tecnologica reconocida por diseno premium, soporte confiable e innovacion practica.": "Ser una marca tecnológica reconocida por diseño profesional, soporte confiable e innovación práctica.",
    })
    replace(about, "values", {
        "Responsabilidad, innovacion, seguridad, transparencia, atencion personalizada y mejora continua.": "Responsabilidad, innovación, seguridad, transparencia, atención personalizada y mejora continua.",
    })
    replace(about, "experience", {
        "Experiencia en desarrollo web, sistemas empresariales, redes, soporte tecnico, camaras, automatizacion y ciberseguridad basica.": "Experiencia en desarrollo web, sistemas empresariales, redes, soporte técnico, cámaras, automatización y ciberseguridad básica.",
    })

    ceo = get_ceo()
    replace(ceo, "role", {"CEO & Fundador de AFCyber SOLUTIONS": "CEO & Fundador de AFCyber Solutions"})
    replace(ceo, "tagline", {"Transformando ideas en soluciones tecnologicas modernas y seguras.": "Transformando ideas en soluciones tecnológicas modernas y seguras."})
    replace(ceo, "bio", {
        "Ingeniero en Ciberseguridad con experiencia en soporte tecnologico, automatizacion, desarrollo de sistemas empresariales, redes, seguridad informatica y soluciones digitales para empresas y emprendedores.": "Ingeniero en Ciberseguridad con experiencia en soporte tecnológico, automatización, desarrollo de sistemas empresariales, redes, seguridad informática y soluciones digitales para empresas y emprendedores.",
    })
    replace(ceo, "experience", {
        "Desarrollo de sistemas POS\nDesarrollo de sistemas CMMS\nDesarrollo web\nRedes, soporte tecnico, camaras IP y analogicas\nAutomatizacion empresarial\nSeguridad informatica\nImplementacion tecnologica": "Desarrollo de sistemas POS\nDesarrollo de sistemas CMMS\nDesarrollo web\nRedes, soporte técnico, cámaras IP y analógicas\nAutomatización empresarial\nSeguridad informática\nImplementación tecnológica",
    })
    replace(ceo, "certifications", {
        "Ciberseguridad\nSoporte tecnologico\nImplementacion de soluciones empresariales": "Ciberseguridad\nSoporte tecnológico\nImplementación de soluciones empresariales",
    })
    replace(ceo, "skills", {
        "Python\nFlask\nSQLite\nRedes\nCiberseguridad\nSoporte empresarial\nHTML/CSS/JS\nRender\nGitHub\nLinux basico/intermedio\nAutomatizacion\nSistemas administrativos": "Python\nFlask\nSQLite\nRedes\nCiberseguridad\nSoporte empresarial\nHTML/CSS/JS\nRender\nGitHub\nLinux básico/intermedio\nAutomatización\nSistemas administrativos",
    })
    replace(ceo, "whatsapp_message", {
        "Hola Ing. Amauri Feliz, quiero conversar sobre un proyecto tecnologico.": "Hola Ing. Amauri Feliz, quiero conversar sobre un proyecto tecnológico.",
    })

    service_updates = {
        ("Desarrollo web", "Paginas corporativas premium, landing pages, sitios rapidos y experiencias digitales responsive."): ("Landing pages y webs", "Páginas web profesionales para empresas, catálogos digitales y presencia online.", "fa-solid fa-laptop-code"),
        ("Ciberseguridad basica", "Revision inicial, buenas practicas, proteccion de cuentas, endpoints y orientacion preventiva."): ("Ciberseguridad básica", "Protección de equipos, buenas prácticas, revisión de vulnerabilidades, respaldos y seguridad de acceso.", "fa-solid fa-shield-halved"),
        ("Soporte tecnico", "Asistencia remota y presencial para usuarios, equipos, software y continuidad operativa."): ("Soporte técnico", "Asistencia remota y presencial para usuarios, equipos, software y continuidad operativa.", "fa-solid fa-headset"),
        ("Camaras de seguridad", "Instalacion y configuracion de camaras IP, analogicas, DVR/NVR y acceso remoto."): ("CCTV y control de acceso", "Cámaras IP, acceso remoto, grabación, biometría y seguridad física.", "fa-solid fa-video"),
        ("Redes empresariales", "Cableado, configuracion, optimizacion y documentacion de redes para empresas."): ("Redes empresariales", "Cableado, configuración, optimización y documentación de redes para empresas.", "fa-solid fa-network-wired"),
        ("Correos corporativos", "Correos profesionales, dominios, firmas, configuracion y seguridad basica."): ("Correos corporativos", "Correos profesionales, dominios, firmas, configuración y seguridad básica.", "fa-solid fa-envelope-circle-check"),
        ("Sistemas POS", "Sistemas para ventas, inventario, usuarios, reportes y control comercial."): ("Sistemas POS / ERP", "Puntos de venta, control de caja, inventario, clientes, proveedores y reportes.", "fa-solid fa-cash-register"),
        ("Sistemas CMMS", "Gestion de activos, mantenimiento, tecnicos, ordenes de trabajo e historial."): ("Sistemas CMMS", "Gestión de activos, mantenimiento, técnicos, órdenes de trabajo e historial.", "fa-solid fa-screwdriver-wrench"),
        ("Sistemas de citas", "Agenda digital, reservas, confirmaciones y gestion de clientes."): ("Sistemas de citas", "Agenda digital, reservas, confirmaciones y gestión de clientes.", "fa-solid fa-calendar-check"),
        ("Automatizacion de procesos", "Flujos digitales, reportes, herramientas internas y reduccion de tareas repetitivas."): ("Automatización de procesos", "Flujos digitales, reportes, herramientas internas y reducción de tareas repetitivas.", "fa-solid fa-gears"),
    }
    for service in Service.query.all():
        update = service_updates.get((service.name, service.description))
        if update:
            service.name, service.description, service.icon = update

    plan_updates = {
        "Plan Basico": "Plan Básico",
        "Presencia digital inicial para negocios que necesitan una pagina profesional.": "Presencia digital inicial para negocios que necesitan una página profesional.",
        "Pagina informativa\nBoton de WhatsApp\nDiseno responsive\nSEO inicial": "Página informativa\nBotón de WhatsApp\nDiseño responsive\nSEO inicial",
        "Web avanzada para marcas que buscan una presencia premium y mejor captacion.": "Web avanzada para marcas que buscan una presencia profesional y mejor captación.",
        "Pagina avanzada\nDominio y hosting\nSEO basico\nSecciones corporativas\nIntegracion WhatsApp": "Página avanzada\nDominio y hosting\nSEO básico\nSecciones corporativas\nIntegración WhatsApp",
        "Soluciones a medida para operaciones que requieren sistemas, paneles o automatizacion.": "Soluciones a medida para operaciones que requieren sistemas, paneles o automatización.",
        "Sistema personalizado\nPanel administrativo\nAutomatizacion\nSoporte tecnico\nReportes": "Sistema personalizado\nPanel administrativo\nAutomatización\nSoporte técnico\nReportes",
    }
    for plan in Plan.query.all():
        replace(plan, "name", plan_updates)
        replace(plan, "description", plan_updates)
        replace(plan, "features", plan_updates)

    faq_updates = {
        "Que servicios ofrece AFCyber SOLUTIONS?": "¿Qué servicios ofrece AFCyber Solutions?",
        "Ofrecemos desarrollo web, POS, CMMS, soporte tecnico, redes, camaras, correos, ciberseguridad basica y automatizacion.": "Ofrecemos desarrollo web, sistemas POS/ERP, soporte técnico, CCTV, ciberseguridad básica, mantenimiento y automatización.",
        "Puedo solicitar un sistema personalizado?": "¿Puedo solicitar un sistema personalizado?",
        "Si. Evaluamos el proceso, definimos alcance y construimos una solucion ajustada a la operacion.": "Sí. Evaluamos el proceso, definimos alcance y construimos una solución ajustada a la operación.",
        "La web se puede editar desde admin?": "¿Cómo solicito una cotización?",
        "Si. Esta plataforma permite editar contenido, servicios, planes, portafolio, FAQ, SEO, redes y mensajes.": "Puedes enviar el formulario o escribir por WhatsApp. Revisamos la necesidad y respondemos con los próximos pasos.",
        "Se puede desplegar en Render?": "¿Cómo empieza un proyecto?",
        "Si. El proyecto incluye Procfile, render.yaml y gunicorn para despliegue.": "Primero revisamos la necesidad, aclaramos el alcance y luego preparamos una propuesta con entregables y próximos pasos.",
    }
    for faq in FAQ.query.all():
        replace(faq, "question", faq_updates)
        replace(faq, "answer", faq_updates)

    process_faqs = [faq for faq in FAQ.query.order_by(FAQ.position, FAQ.id).all() if faq.question == "¿Cómo empieza un proyecto?"]
    if len(process_faqs) > 1:
        process_faqs[0].question = "¿Cómo solicito una cotización?"
        process_faqs[0].answer = "Puedes enviar el formulario o escribir por WhatsApp. Revisamos la necesidad y respondemos con los próximos pasos."


def register_routes(app):
    @app.context_processor
    def inject_globals():
        return {"settings": get_settings(), "hero": get_hero()}

    @app.get("/")
    def index():
        settings = get_settings()
        return render_template(
            "public/index.html",
            settings=settings,
            hero=get_hero(),
            about=get_about(),
            ceo=get_ceo(),
            services=Service.query.filter_by(is_active=True).order_by(Service.position, Service.id).all(),
            plans=Plan.query.filter_by(is_active=True).order_by(Plan.position, Plan.id).all(),
            projects=get_public_projects(),
            testimonials=get_public_testimonials(),
            faqs=FAQ.query.filter_by(is_active=True).order_by(FAQ.position, FAQ.id).all(),
            social_links=get_public_social_links(),
        )

    @app.get("/robots.txt")
    def robots_txt():
        lines = [
            "User-agent: *",
            "Allow: /",
            f"Sitemap: {request.url_root.rstrip('/')}/sitemap.xml",
        ]
        return Response("\n".join(lines), mimetype="text/plain")

    @app.get("/sitemap.xml")
    def sitemap_xml():
        base_url = request.url_root.rstrip("/")
        urls = [base_url + "/", base_url + "/descargas", base_url + "/solicitar-servicio"]
        body = "\n".join(f"  <url><loc>{url}</loc></url>" for url in urls)
        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>'
        return Response(xml, mimetype="application/xml")

    @app.get("/favicon.ico")
    def favicon_ico():
        return redirect(url_for("static", filename="img/og-afcyber.svg"))

    @app.get("/descargas")
    @app.get("/descargas/programas")
    @app.get("/descargas/manuales")
    def downloads():
        section = "todo"
        if request.path.endswith("/programas"):
            section = "programas"
        elif request.path.endswith("/manuales"):
            section = "manuales"
        programs = Program.query.filter_by(is_active=True, status="publicado", deleted_at=None).order_by(Program.is_featured.desc(), Program.updated_at.desc()).all()
        manuals = Manual.query.filter_by(is_active=True, status="publicado", deleted_at=None).order_by(Manual.updated_at.desc()).all()
        return render_template("public/downloads.html", section=section, programs=programs, manuals=manuals)

    @app.get("/programas/<slug>")
    def program_detail(slug):
        item = Program.query.filter_by(slug=slug, is_active=True, status="publicado", deleted_at=None).first_or_404()
        return render_template("public/download_detail.html", kind="programa", item=item)

    @app.get("/manuales/<slug>")
    def manual_detail(slug):
        item = Manual.query.filter_by(slug=slug, is_active=True, status="publicado", deleted_at=None).first_or_404()
        return render_template("public/download_detail.html", kind="manual", item=item)

    @app.get("/descargar/programa/<slug>")
    def download_program(slug):
        item = Program.query.filter_by(slug=slug, is_active=True, status="publicado", deleted_at=None).first_or_404()
        return serve_download(item, "programa")

    @app.get("/descargar/manual/<slug>")
    def download_manual(slug):
        item = Manual.query.filter_by(slug=slug, is_active=True, status="publicado", deleted_at=None).first_or_404()
        return serve_download(item, "manual")

    @app.route("/solicitar-servicio", methods=["GET", "POST"])
    def request_service():
        services = Service.query.filter_by(is_active=True).order_by(Service.position, Service.id).all()
        if request.method == "POST":
            email = normalize_email(form_text("email", 180), required=True)
            required = {
                "full_name": form_text("full_name", 180),
                "phone": form_text("phone", 80),
                "requested_service": form_text("requested_service", 180),
                "need_description": form_text("need_description", 6000),
            }
            if not email or any(not value for value in required.values()):
                flash("Completa nombre, correo, teléfono, servicio y descripción de la necesidad.", "danger")
                return redirect(url_for("request_service"))
            consent_fields = ["accepted_privacy", "accepted_contact", "accepted_e_signature", "confirmed_accuracy"]
            if not all(checkbox_value(field) for field in consent_fields):
                flash("Debes aceptar las condiciones y consentimientos requeridos para enviar la solicitud.", "danger")
                return redirect(url_for("request_service"))
            estimated_date = parse_date(form_text("estimated_date", 20))
            if form_text("estimated_date", 20) and estimated_date is None:
                return redirect(url_for("request_service"))
            customer = Customer(
                uuid=make_uuid(),
                full_name=required["full_name"],
                identity_document=form_text("identity_document", 80),
                company=form_text("company", 180),
                position=form_text("position", 120),
                email=email,
                phone=required["phone"],
                whatsapp=form_text("whatsapp", 80),
                address=form_text("address", 260),
                city=form_text("city", 120),
                province=form_text("province", 120),
            )
            db.session.add(customer)
            db.session.flush()
            service_request = ServiceRequest(
                uuid=make_uuid(),
                customer_id=customer.id,
                requested_service=required["requested_service"],
                service_type=form_text("service_type", 120),
                need_description=required["need_description"],
                equipment_count=form_text("equipment_count", 80),
                estimated_date=estimated_date,
                modality=form_text("modality", 40) or "Remoto",
                priority=form_text("priority", 40) or "Normal",
                estimated_budget=form_text("estimated_budget", 80),
                initial_scope=form_text("initial_scope", 5000),
                observations=form_text("observations", 5000),
                accepted_privacy=True,
                accepted_contact=True,
                accepted_e_signature=True,
                confirmed_accuracy=True,
                consent_version=CONSENT_VERSION,
                consent_ip_hash=request_ip_hash(),
                status="recibida",
            )
            db.session.add(service_request)
            db.session.flush()
            upload = save_private_upload(request.files.get("attachment"), ALLOWED_ATTACHMENT_FILES, ATTACHMENT_STORAGE)
            if upload:
                db.session.add(Attachment(
                    uuid=make_uuid(),
                    service_request_id=service_request.id,
                    original_name=secure_filename(request.files["attachment"].filename),
                    file_path=upload["relative_path"],
                    file_size=upload["size"],
                    mime_type=mimetypes.guess_type(upload["relative_path"])[0] or "application/octet-stream",
                    sha256=upload["sha256"],
                ))
            document = create_service_document(service_request)
            company_recipient = os.getenv("COMPANY_NOTIFICATION_EMAIL") or get_settings().main_email
            send_configured_email(
                company_recipient,
                f"Nueva solicitud de servicio - {service_request.requested_service}",
                f"Cliente: {customer.full_name}\nCorreo: {customer.email}\nServicio: {service_request.requested_service}\nDocumento: {document.code}",
                "service_request_notification",
            )
            db.session.commit()
            flash("Solicitud recibida. Si el correo está configurado, recibirás el enlace de revisión y firma.", "success")
            return redirect(url_for("request_service"))
        return render_template("public/service_request.html", services=services)

    @app.route("/firmar/<token>", methods=["GET", "POST"])
    def sign_document(token):
        signature_request = SignatureRequest.query.filter_by(token_hash=hash_token(token)).first_or_404()
        document = signature_request.document
        version = DocumentVersion.query.filter_by(document_id=document.id, version_number=signature_request.version_number).first()
        now = utc_now()
        if signature_request.version_number != document.current_version and signature_request.status == "pendiente":
            signature_request.status = "invalidado_por_nueva_version"
            log_signature_event("signature_request_invalidated", document, signature_request, "El documento fue actualizado a una version nueva.")
            db.session.commit()
            return render_template("public/sign_document.html", item=signature_request, document=document, version=version, expired=True)
        if as_utc(signature_request.expires_at) < now or signature_request.used_at:
            signature_request.status = "vencido" if not signature_request.used_at else signature_request.status
            db.session.commit()
            return render_template("public/sign_document.html", item=signature_request, document=document, version=version, expired=True)
        if request.method == "POST":
            action = request.form.get("action", "sign")
            if action == "reject":
                signature_request.status = "rechazado"
                signature_request.reject_reason = form_text("reject_reason", 1000)
                document.status = "rechazado"
                log_signature_event("signature_rejected", document, signature_request, signature_request.reject_reason)
                db.session.commit()
                flash("Documento rechazado correctamente.", "warning")
                return redirect(url_for("sign_document", token=token))
            if not checkbox_value("consent"):
                flash("Debes aceptar el consentimiento de firma electrónica.", "danger")
                return redirect(url_for("sign_document", token=token))
            otp = form_text("otp", 12)
            if signature_request.otp_expires_at and as_utc(signature_request.otp_expires_at) < now:
                flash("El código OTP venció. Solicita un nuevo enlace desde AFCyber Solutions.", "danger")
                return redirect(url_for("sign_document", token=token))
            if signature_request.otp_attempts >= OTP_MAX_ATTEMPTS:
                signature_request.status = "bloqueado"
                db.session.commit()
                flash("Demasiados intentos de OTP. Solicita asistencia.", "danger")
                return redirect(url_for("sign_document", token=token))
            if not hmac.compare_digest(signature_request.otp_hash or "", hash_token(otp)):
                signature_request.otp_attempts += 1
                db.session.commit()
                flash("Código OTP incorrecto.", "danger")
                return redirect(url_for("sign_document", token=token))
            signature_text = form_text("signature_text", 180)
            if not signature_text:
                flash("Escribe tu nombre como evidencia de firma.", "danger")
                return redirect(url_for("sign_document", token=token))
            signed_hash = hash_token("|".join([document.code, version.sha256 or "", signature_request.signer_email, signature_text, now.isoformat()]))
            db.session.add(ElectronicSignature(
                uuid=make_uuid(),
                document_id=document.id,
                signature_request_id=signature_request.id,
                version_number=signature_request.version_number,
                signer_name=signature_request.signer_name,
                signer_email=signature_request.signer_email,
                signer_role=signature_request.signer_role,
                signature_text=signature_text,
                consent_text=f"Consentimiento de firma electrónica versión {CONSENT_VERSION}.",
                ip_hash=request_ip_hash(),
                user_agent_hash=request_user_agent_hash(),
                document_hash=version.sha256 or "",
                signed_hash=signed_hash,
            ))
            signature_request.status = "firmado"
            signature_request.used_at = now
            refresh_document_signature_status(document, signature_request.version_number)
            path, digest = create_document_pdf(document, version)
            document.final_pdf_path = path
            document.final_sha256 = digest
            log_signature_event("signature_completed", document, signature_request, f"Firmado por {signature_request.signer_role}.")
            send_configured_email(signature_request.signer_email, f"Documento firmado - {document.code}", "Tu firma fue registrada correctamente.", "signature_completed", document.final_pdf_path)
            db.session.commit()
            flash("Firma registrada correctamente.", "success")
            return redirect(url_for("sign_document", token=token))
        return render_template("public/sign_document.html", item=signature_request, document=document, version=version, expired=False)

    @app.get("/firmar/<token>/pdf")
    def signed_document_pdf(token):
        signature_request = SignatureRequest.query.filter_by(token_hash=hash_token(token)).first_or_404()
        document = signature_request.document
        path = private_path(document.final_pdf_path)
        if not path.exists():
            abort(404)
        return send_file(path, mimetype="application/pdf", as_attachment=True, download_name=f"{document.code}.pdf", conditional=True)

    @app.get("/verificar-documento/<codigo>")
    def verify_document(codigo):
        document = ServiceDocument.query.filter_by(verification_code=codigo).first_or_404()
        signatures = ElectronicSignature.query.filter_by(document_id=document.id).order_by(ElectronicSignature.created_at).all()
        return render_template("public/verify_document.html", document=document, signatures=signatures)

    @app.post("/contact")
    def contact():
        name = form_text("name", 160)
        phone = form_text("phone", 60)
        message = form_text("message", 5000)
        email = normalize_email(form_text("email", 160))
        if email is None:
            return redirect(url_for("index") + "#contacto")
        if not name or not phone or not message:
            flash("Completa nombre, teléfono y mensaje.", "danger")
            return redirect(url_for("index") + "#contacto")
        db.session.add(ContactMessage(
            name=name,
            company=form_text("company", 160),
            phone=phone,
            email=email,
            requested_service=form_text("requested_service", 160),
            message=message,
        ))
        db.session.commit()
        flash("Mensaje enviado correctamente. Te contactaremos pronto.", "success")
        return redirect(url_for("index") + "#contacto")

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if current_user.is_authenticated:
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            lock_until = float(session.get("_login_lock_until", 0) or 0)
            if lock_until > time():
                flash("Demasiados intentos. Intenta nuevamente en unos minutos.", "danger")
                return render_template("admin/login.html")
            email = normalize_email(form_text("email", 160), required=True)
            if not email:
                return render_template("admin/login.html")
            user = User.query.filter_by(email=email).first()
            if user and user.is_active_admin and user.check_password(request.form.get("password", "")):
                session.pop("_login_attempts", None)
                session.pop("_login_lock_until", None)
                login_user(user)
                return redirect(url_for("admin_dashboard"))
            attempts = int(session.get("_login_attempts", 0) or 0) + 1
            session["_login_attempts"] = attempts
            if attempts >= LOGIN_MAX_ATTEMPTS:
                session["_login_lock_until"] = time() + LOGIN_LOCKOUT_SECONDS
                session["_login_attempts"] = 0
            flash("Credenciales incorrectas.", "danger")
        return render_template("admin/login.html")

    @app.post("/admin/logout")
    @login_required
    def admin_logout():
        logout_user()
        return redirect(url_for("admin_login"))

    @app.get("/admin")
    @login_required
    def admin_dashboard():
        return render_template("admin/dashboard.html", totals={
            "messages": ContactMessage.query.filter_by(is_read=False).count(),
            "services": Service.query.count(),
            "projects": PortfolioProject.query.count(),
            "testimonials": Testimonial.query.count(),
            "plans": Plan.query.count(),
            "faqs": FAQ.query.count(),
            "programs": Program.query.filter_by(deleted_at=None).count(),
            "manuals": Manual.query.filter_by(deleted_at=None).count(),
            "requests": ServiceRequest.query.filter_by(deleted_at=None).count(),
            "documents": ServiceDocument.query.filter_by(deleted_at=None).count(),
        }, messages=ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(6).all())

    register_admin_routes(app)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("public/error.html", code=404, title="Página no encontrada", message="La página que buscas no existe o fue movida."), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("public/error.html", code=500, title="Error interno", message="Ocurrió un problema temporal. Intenta nuevamente o contáctanos por WhatsApp."), 500


def get_public_testimonials():
    generic_names = {"Cliente comercial", "Gerente operativo", "Emprendedor"}
    return [
        item
        for item in Testimonial.query.filter_by(is_active=True).order_by(Testimonial.created_at.desc()).all()
        if item.client_name not in generic_names and item.company and item.comment
    ]


def get_public_projects():
    generic_names = {"BarberShop", "Sistema POS", "Sistema CMMS", "Catálogos digitales", "Catalogos digitales", "Landing pages", "Sistemas empresariales"}
    return [
        item
        for item in PortfolioProject.query.filter_by(is_active=True).order_by(PortfolioProject.created_at.desc()).all()
        if item.name not in generic_names and (item.link or item.image)
    ]


def get_public_social_links():
    return [
        item
        for item in SocialLink.query.filter_by(is_active=True).order_by(SocialLink.position, SocialLink.id).all()
        if item.url and item.url.startswith(("https://", "http://"))
    ]


def register_admin_routes(app):
    @app.route("/admin/settings", methods=["GET", "POST"])
    @login_required
    def admin_settings():
        settings = get_settings()
        if request.method == "POST":
            text_fields = [
                "company_name", "slogan", "short_description", "phone", "whatsapp", "address",
                "business_hours", "meta_title", "meta_description", "meta_keywords", "google_search_console",
                "footer_text", "copyright_text",
            ]
            main_email = normalize_email(form_text("main_email", 160), required=True)
            if not main_email:
                return redirect(url_for("admin_settings"))
            settings.main_email = main_email
            for field in text_fields:
                setattr(settings, field, form_text(field, 500))
            for field in ["facebook", "instagram", "linkedin", "tiktok", "youtube"]:
                setattr(settings, field, clean_url(form_text(field, 255), allow_fragment=True))
            color_fields = ["primary_color", "secondary_color", "background_color", "button_color", "text_color"]
            for field in color_fields:
                setattr(settings, field, clean_color(request.form.get(field), getattr(settings, field)))
            analytics_id = form_text("google_analytics_id", 80)
            settings.google_analytics_id = analytics_id if not analytics_id or GOOGLE_TAG_RE.fullmatch(analytics_id) else ""
            for field in ["logo", "favicon", "og_image"]:
                uploaded = save_upload(request.files.get(field))
                if uploaded:
                    setattr(settings, field, uploaded)
            for field in ["dark_mode", "tech_gradients", "show_about", "show_ceo", "show_services", "show_plans", "show_portfolio", "show_testimonials", "show_faq", "show_contact"]:
                setattr(settings, field, checkbox_value(field))
            db.session.commit()
            flash("Configuración actualizada.", "success")
            return redirect(url_for("admin_settings"))
        return render_template("admin/settings.html", settings=settings)

    @app.route("/admin/hero", methods=["GET", "POST"])
    @login_required
    def admin_hero():
        hero = get_hero()
        if request.method == "POST":
            for field in ["title", "subtitle", "description", "primary_button_text", "secondary_button_text", "secondary_button_message"]:
                setattr(hero, field, form_text(field, 500))
            hero.primary_button_url = clean_url(form_text("primary_button_url", 255), allow_fragment=True, allow_relative=True) or "#contacto"
            hero.animation_enabled = checkbox_value("animation_enabled")
            uploaded = save_upload(request.files.get("image"))
            if uploaded:
                hero.image = uploaded
            db.session.commit()
            flash("Hero actualizado.", "success")
            return redirect(url_for("admin_hero"))
        return render_template("admin/hero.html", item=hero)

    @app.route("/admin/about", methods=["GET", "POST"])
    @login_required
    def admin_about():
        about = get_about()
        if request.method == "POST":
            for field in ["history", "mission", "vision", "values", "experience"]:
                setattr(about, field, form_text(field, 5000))
            uploaded = save_upload(request.files.get("image"))
            if uploaded:
                about.image = uploaded
            db.session.commit()
            flash("Nosotros actualizado.", "success")
            return redirect(url_for("admin_about"))
        return render_template("admin/about.html", item=about)

    @app.route("/admin/ceo", methods=["GET", "POST"])
    @login_required
    def admin_ceo():
        ceo = get_ceo()
        if request.method == "POST":
            for field in ["full_name", "role", "tagline", "bio", "experience", "certifications", "skills", "whatsapp_message"]:
                setattr(ceo, field, form_text(field, 5000))
            ceo.linkedin = clean_url(form_text("linkedin", 255))
            for field, label in [
                ("projects_count", "Proyectos"),
                ("clients_count", "Clientes"),
                ("systems_count", "Sistemas"),
                ("experience_years", "Anios de experiencia"),
            ]:
                value = form_int(field, label, min_value=0, max_value=100000)
                if value is None:
                    return redirect(url_for("admin_ceo"))
                setattr(ceo, field, value)
            photo = save_upload(request.files.get("photo"))
            cv = save_upload(request.files.get("cv_pdf"), allow_pdf=True)
            if photo:
                ceo.photo = photo
            if cv:
                ceo.cv_pdf = cv
            db.session.commit()
            flash("Perfil CEO actualizado.", "success")
            return redirect(url_for("admin_ceo"))
        return render_template("admin/ceo.html", item=ceo)

    crud_routes(app)
    download_admin_routes(app)
    document_admin_routes(app)


def crud_routes(app):
    @app.route("/admin/services", methods=["GET", "POST"])
    @login_required
    def admin_services():
        if request.method == "POST":
            position = form_int("position", "Orden")
            if position is None:
                return redirect(url_for("admin_services"))
            db.session.add(Service(
                name=form_text("name", 160),
                description=form_text("description", 5000),
                icon=form_text("icon", 80) or "fa-solid fa-shield-halved",
                price=form_text("price", 80),
                position=position,
                image=save_upload(request.files.get("image")),
                is_active=checkbox_value("is_active"),
            ))
            db.session.commit()
            flash("Servicio creado.", "success")
            return redirect(url_for("admin_services"))
        return render_template("admin/services.html", items=Service.query.order_by(Service.position, Service.id).all())

    @app.post("/admin/services/<int:item_id>")
    @login_required
    def update_service(item_id):
        item = Service.query.get_or_404(item_id)
        for field in ["name", "description", "icon", "price"]:
            setattr(item, field, form_text(field, 5000 if field == "description" else 160))
        position = form_int("position", "Orden")
        if position is None:
            return redirect(url_for("admin_services"))
        item.position = position
        item.is_active = checkbox_value("is_active")
        uploaded = save_upload(request.files.get("image"))
        if uploaded:
            item.image = uploaded
        db.session.commit()
        flash("Servicio actualizado.", "success")
        return redirect(url_for("admin_services"))

    @app.post("/admin/services/<int:item_id>/delete")
    @login_required
    def delete_service(item_id):
        db.session.delete(Service.query.get_or_404(item_id))
        db.session.commit()
        flash("Servicio eliminado.", "success")
        return redirect(url_for("admin_services"))

    @app.route("/admin/plans", methods=["GET", "POST"])
    @login_required
    def admin_plans():
        if request.method == "POST":
            position = form_int("position", "Orden")
            if position is None:
                return redirect(url_for("admin_plans"))
            db.session.add(Plan(
                name=form_text("name", 120),
                price=form_text("price", 80),
                description=form_text("description", 5000),
                features=form_text("features", 5000),
                button_text=form_text("button_text", 80) or "Solicitar plan",
                position=position,
                is_featured=checkbox_value("is_featured"),
                is_active=checkbox_value("is_active"),
            ))
            db.session.commit()
            flash("Plan creado.", "success")
            return redirect(url_for("admin_plans"))
        return render_template("admin/plans.html", items=Plan.query.order_by(Plan.position, Plan.id).all())

    @app.post("/admin/plans/<int:item_id>")
    @login_required
    def update_plan(item_id):
        item = Plan.query.get_or_404(item_id)
        for field in ["name", "price", "description", "features", "button_text"]:
            setattr(item, field, form_text(field, 5000 if field in {"description", "features"} else 120))
        position = form_int("position", "Orden")
        if position is None:
            return redirect(url_for("admin_plans"))
        item.position = position
        item.is_featured = checkbox_value("is_featured")
        item.is_active = checkbox_value("is_active")
        db.session.commit()
        flash("Plan actualizado.", "success")
        return redirect(url_for("admin_plans"))

    @app.post("/admin/plans/<int:item_id>/delete")
    @login_required
    def delete_plan(item_id):
        db.session.delete(Plan.query.get_or_404(item_id))
        db.session.commit()
        return redirect(url_for("admin_plans"))

    @app.route("/admin/portfolio", methods=["GET", "POST"])
    @login_required
    def admin_portfolio():
        if request.method == "POST":
            db.session.add(PortfolioProject(
                name=form_text("name", 160),
                description=form_text("description", 5000),
                category=form_text("category", 120),
                technologies=form_text("technologies", 5000),
                link=clean_url(form_text("link", 255)),
                image=save_upload(request.files.get("image")),
                is_active=checkbox_value("is_active"),
            ))
            db.session.commit()
            flash("Proyecto creado.", "success")
            return redirect(url_for("admin_portfolio"))
        return render_template("admin/portfolio.html", items=PortfolioProject.query.order_by(PortfolioProject.created_at.desc()).all())

    @app.post("/admin/portfolio/<int:item_id>")
    @login_required
    def update_portfolio(item_id):
        item = PortfolioProject.query.get_or_404(item_id)
        for field in ["name", "description", "category", "technologies", "link"]:
            value = form_text(field, 5000 if field in {"description", "technologies"} else 255)
            setattr(item, field, clean_url(value) if field == "link" else value)
        item.is_active = checkbox_value("is_active")
        uploaded = save_upload(request.files.get("image"))
        if uploaded:
            item.image = uploaded
        db.session.commit()
        flash("Proyecto actualizado.", "success")
        return redirect(url_for("admin_portfolio"))

    @app.post("/admin/portfolio/<int:item_id>/delete")
    @login_required
    def delete_portfolio(item_id):
        db.session.delete(PortfolioProject.query.get_or_404(item_id))
        db.session.commit()
        return redirect(url_for("admin_portfolio"))

    @app.route("/admin/testimonials", methods=["GET", "POST"])
    @login_required
    def admin_testimonials():
        if request.method == "POST":
            stars = form_int("stars", "Estrellas", default=5, min_value=1, max_value=5)
            if stars is None:
                return redirect(url_for("admin_testimonials"))
            db.session.add(Testimonial(
                client_name=form_text("client_name", 160),
                company=form_text("company", 160),
                comment=form_text("comment", 5000),
                stars=stars,
                photo=save_upload(request.files.get("photo")),
                is_active=checkbox_value("is_active"),
            ))
            db.session.commit()
            return redirect(url_for("admin_testimonials"))
        return render_template("admin/testimonials.html", items=Testimonial.query.order_by(Testimonial.created_at.desc()).all())

    @app.post("/admin/testimonials/<int:item_id>")
    @login_required
    def update_testimonial(item_id):
        item = Testimonial.query.get_or_404(item_id)
        for field in ["client_name", "company", "comment"]:
            setattr(item, field, form_text(field, 5000 if field == "comment" else 160))
        stars = form_int("stars", "Estrellas", default=5, min_value=1, max_value=5)
        if stars is None:
            return redirect(url_for("admin_testimonials"))
        item.stars = stars
        item.is_active = checkbox_value("is_active")
        uploaded = save_upload(request.files.get("photo"))
        if uploaded:
            item.photo = uploaded
        db.session.commit()
        return redirect(url_for("admin_testimonials"))

    @app.post("/admin/testimonials/<int:item_id>/delete")
    @login_required
    def delete_testimonial(item_id):
        db.session.delete(Testimonial.query.get_or_404(item_id))
        db.session.commit()
        return redirect(url_for("admin_testimonials"))

    @app.route("/admin/faq", methods=["GET", "POST"])
    @login_required
    def admin_faq():
        if request.method == "POST":
            position = form_int("position", "Orden")
            if position is None:
                return redirect(url_for("admin_faq"))
            db.session.add(FAQ(question=form_text("question", 255), answer=form_text("answer", 5000), position=position, is_active=checkbox_value("is_active")))
            db.session.commit()
            return redirect(url_for("admin_faq"))
        return render_template("admin/faq.html", items=FAQ.query.order_by(FAQ.position, FAQ.id).all())

    @app.post("/admin/faq/<int:item_id>")
    @login_required
    def update_faq(item_id):
        item = FAQ.query.get_or_404(item_id)
        position = form_int("position", "Orden")
        if position is None:
            return redirect(url_for("admin_faq"))
        item.question = form_text("question", 255)
        item.answer = form_text("answer", 5000)
        item.position = position
        item.is_active = checkbox_value("is_active")
        db.session.commit()
        return redirect(url_for("admin_faq"))

    @app.post("/admin/faq/<int:item_id>/delete")
    @login_required
    def delete_faq(item_id):
        db.session.delete(FAQ.query.get_or_404(item_id))
        db.session.commit()
        return redirect(url_for("admin_faq"))

    @app.route("/admin/social", methods=["GET", "POST"])
    @login_required
    def admin_social():
        if request.method == "POST":
            position = form_int("position", "Orden")
            if position is None:
                return redirect(url_for("admin_social"))
            url = clean_url(form_text("url", 255), allow_fragment=True)
            if not url:
                return redirect(url_for("admin_social"))
            db.session.add(SocialLink(name=form_text("name", 80), icon=form_text("icon", 80), url=url, position=position, is_active=checkbox_value("is_active")))
            db.session.commit()
            return redirect(url_for("admin_social"))
        return render_template("admin/social.html", items=SocialLink.query.order_by(SocialLink.position, SocialLink.id).all())

    @app.post("/admin/social/<int:item_id>")
    @login_required
    def update_social(item_id):
        item = SocialLink.query.get_or_404(item_id)
        for field in ["name", "icon", "url"]:
            value = form_text(field, 255)
            setattr(item, field, clean_url(value, allow_fragment=True) if field == "url" else value)
        position = form_int("position", "Orden")
        if position is None:
            return redirect(url_for("admin_social"))
        item.position = position
        item.is_active = checkbox_value("is_active")
        db.session.commit()
        return redirect(url_for("admin_social"))

    @app.post("/admin/social/<int:item_id>/delete")
    @login_required
    def delete_social(item_id):
        db.session.delete(SocialLink.query.get_or_404(item_id))
        db.session.commit()
        return redirect(url_for("admin_social"))

    @app.get("/admin/messages")
    @login_required
    def admin_messages():
        return render_template("admin/messages.html", items=ContactMessage.query.order_by(ContactMessage.created_at.desc()).all())

    @app.post("/admin/messages/<int:item_id>/read")
    @login_required
    def read_message(item_id):
        item = ContactMessage.query.get_or_404(item_id)
        item.is_read = True
        db.session.commit()
        return redirect(url_for("admin_messages"))

    @app.post("/admin/messages/<int:item_id>/delete")
    @login_required
    def delete_message(item_id):
        db.session.delete(ContactMessage.query.get_or_404(item_id))
        db.session.commit()
        return redirect(url_for("admin_messages"))

    @app.route("/admin/users", methods=["GET", "POST"])
    @login_required
    def admin_users():
        if request.method == "POST":
            email = normalize_email(form_text("email", 160), required=True)
            password = request.form.get("password", "")
            if not email:
                return redirect(url_for("admin_users"))
            if User.query.filter_by(email=email).first():
                flash("Ya existe un usuario con ese correo.", "danger")
                return redirect(url_for("admin_users"))
            if not password_is_strong(password):
                flash("La contraseña debe tener al menos 12 caracteres, mayúsculas, minúsculas y números.", "danger")
                return redirect(url_for("admin_users"))
            user = User(email=email, name=form_text("name", 120), is_active_admin=checkbox_value("is_active_admin"))
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Usuario creado.", "success")
            return redirect(url_for("admin_users"))
        return render_template("admin/users.html", items=User.query.order_by(User.created_at.desc()).all())

    @app.post("/admin/users/<int:item_id>")
    @login_required
    def update_user(item_id):
        item = User.query.get_or_404(item_id)
        email = normalize_email(form_text("email", 160), required=True)
        if not email:
            return redirect(url_for("admin_users"))
        existing = User.query.filter(User.email == email, User.id != item.id).first()
        if existing:
            flash("Ya existe otro usuario con ese correo.", "danger")
            return redirect(url_for("admin_users"))
        is_active_admin = checkbox_value("is_active_admin")
        if item.id == current_user.id and not is_active_admin:
            flash("No puedes desactivar tu propio usuario.", "danger")
            return redirect(url_for("admin_users"))
        password = request.form.get("password", "")
        if password and not password_is_strong(password):
            flash("La contraseña debe tener al menos 12 caracteres, mayúsculas, minúsculas y números.", "danger")
            return redirect(url_for("admin_users"))
        item.email = email
        item.name = form_text("name", 120)
        item.is_active_admin = is_active_admin
        if password:
            item.set_password(password)
        db.session.commit()
        flash("Usuario actualizado.", "success")
        return redirect(url_for("admin_users"))


def download_admin_routes(app):
    @app.route("/admin/downloads", methods=["GET", "POST"])
    @login_required
    def admin_downloads():
        if request.method == "POST":
            item_type = request.form.get("item_type")
            if item_type == "program":
                name = form_text("name", 180)
                if not name:
                    flash("El programa necesita nombre.", "danger")
                    return redirect(url_for("admin_downloads"))
                upload = save_private_upload(request.files.get("program_file"), ALLOWED_PROGRAM_FILES, INSTALLER_STORAGE)
                external_url = clean_url(form_text("external_url", 500))
                if not upload and not external_url:
                    flash("Agrega un instalador privado o una URL externa segura.", "danger")
                    return redirect(url_for("admin_downloads"))
                image = save_upload(request.files.get("image"))
                program = Program(
                    uuid=make_uuid(),
                    slug=unique_slug(Program, name),
                    name=name,
                    version=form_text("version", 60) or "1.0",
                    short_description=form_text("short_description", 260),
                    description=form_text("description", 6000),
                    category=form_text("category", 120) or "Programa",
                    target_business=form_text("target_business", 180),
                    operating_system=form_text("operating_system", 120) or "Windows",
                    architecture=form_text("architecture", 40) or "x64",
                    updated_on=parse_date(form_text("updated_on", 20)),
                    status=form_text("status", 40) or "borrador",
                    license_type=form_text("license_type", 120) or "A definir",
                    requirements=form_text("requirements", 5000),
                    image=image,
                    external_url=external_url,
                    is_active=checkbox_value("is_active"),
                    is_featured=checkbox_value("is_featured"),
                )
                if upload:
                    if Program.query.filter_by(sha256=upload["sha256"]).first():
                        flash("Ya existe un programa con el mismo hash SHA-256.", "danger")
                        return redirect(url_for("admin_downloads"))
                    program.file_path = upload["relative_path"]
                    program.file_size = upload["size"]
                    program.sha256 = upload["sha256"]
                manual_id = form_int("manual_id", "Manual relacionado", default=0, min_value=0)
                if manual_id is None:
                    return redirect(url_for("admin_downloads"))
                program.manual_id = manual_id or None
                db.session.add(program)
                db.session.commit()
                flash("Programa creado.", "success")
                return redirect(url_for("admin_downloads"))
            if item_type == "manual":
                title = form_text("title", 180)
                if not title:
                    flash("El manual necesita título.", "danger")
                    return redirect(url_for("admin_downloads"))
                upload = save_private_upload(request.files.get("manual_file"), ALLOWED_MANUAL_FILES, MANUAL_STORAGE)
                external_url = clean_url(form_text("external_url", 500))
                if not upload and not external_url:
                    flash("Agrega un PDF privado o una URL externa segura.", "danger")
                    return redirect(url_for("admin_downloads"))
                manual = Manual(
                    uuid=make_uuid(),
                    slug=unique_slug(Manual, title),
                    title=title,
                    related_item=form_text("related_item", 180),
                    category=form_text("category", 120) or "Documentación",
                    version=form_text("version", 60) or "1.0",
                    description=form_text("description", 6000),
                    external_url=external_url,
                    updated_on=parse_date(form_text("updated_on", 20)),
                    status=form_text("status", 40) or "borrador",
                    is_active=checkbox_value("is_active"),
                )
                if upload:
                    if Manual.query.filter_by(sha256=upload["sha256"]).first():
                        flash("Ya existe un manual con el mismo hash SHA-256.", "danger")
                        return redirect(url_for("admin_downloads"))
                    manual.file_path = upload["relative_path"]
                    manual.file_size = upload["size"]
                    manual.sha256 = upload["sha256"]
                db.session.add(manual)
                db.session.commit()
                flash("Manual creado.", "success")
                return redirect(url_for("admin_downloads"))
        return render_template(
            "admin/downloads.html",
            programs=Program.query.filter_by(deleted_at=None).order_by(Program.updated_at.desc()).all(),
            manuals=Manual.query.filter_by(deleted_at=None).order_by(Manual.updated_at.desc()).all(),
        )

    @app.post("/admin/downloads/programs/<int:item_id>")
    @login_required
    def update_program_download(item_id):
        program = Program.query.get_or_404(item_id)
        program.name = form_text("name", 180)
        program.slug = unique_slug(Program, program.name, current_id=program.id)
        for field, limit in [
            ("version", 60), ("short_description", 260), ("description", 6000), ("category", 120),
            ("target_business", 180), ("operating_system", 120), ("architecture", 40), ("license_type", 120),
            ("requirements", 5000), ("status", 40),
        ]:
            setattr(program, field, form_text(field, limit))
        program.external_url = clean_url(form_text("external_url", 500))
        program.updated_on = parse_date(form_text("updated_on", 20))
        manual_id = form_int("manual_id", "Manual relacionado", default=0, min_value=0)
        if manual_id is None:
            return redirect(url_for("admin_downloads"))
        program.manual_id = manual_id or None
        program.is_active = checkbox_value("is_active")
        program.is_featured = checkbox_value("is_featured")
        image = save_upload(request.files.get("image"))
        if image:
            program.image = image
        upload = save_private_upload(request.files.get("program_file"), ALLOWED_PROGRAM_FILES, INSTALLER_STORAGE)
        if upload:
            duplicate = Program.query.filter(Program.sha256 == upload["sha256"], Program.id != program.id).first()
            if duplicate:
                flash("Ya existe otro programa con el mismo hash SHA-256.", "danger")
                return redirect(url_for("admin_downloads"))
            program.file_path = upload["relative_path"]
            program.file_size = upload["size"]
            program.sha256 = upload["sha256"]
        db.session.commit()
        flash("Programa actualizado.", "success")
        return redirect(url_for("admin_downloads"))

    @app.post("/admin/downloads/manuals/<int:item_id>")
    @login_required
    def update_manual_download(item_id):
        manual = Manual.query.get_or_404(item_id)
        manual.title = form_text("title", 180)
        manual.slug = unique_slug(Manual, manual.title, current_id=manual.id)
        for field, limit in [("related_item", 180), ("category", 120), ("version", 60), ("description", 6000), ("status", 40)]:
            setattr(manual, field, form_text(field, limit))
        manual.external_url = clean_url(form_text("external_url", 500))
        manual.updated_on = parse_date(form_text("updated_on", 20))
        manual.is_active = checkbox_value("is_active")
        upload = save_private_upload(request.files.get("manual_file"), ALLOWED_MANUAL_FILES, MANUAL_STORAGE)
        if upload:
            duplicate = Manual.query.filter(Manual.sha256 == upload["sha256"], Manual.id != manual.id).first()
            if duplicate:
                flash("Ya existe otro manual con el mismo hash SHA-256.", "danger")
                return redirect(url_for("admin_downloads"))
            manual.file_path = upload["relative_path"]
            manual.file_size = upload["size"]
            manual.sha256 = upload["sha256"]
        db.session.commit()
        flash("Manual actualizado.", "success")
        return redirect(url_for("admin_downloads"))

    @app.post("/admin/downloads/<item_type>/<int:item_id>/delete")
    @login_required
    def delete_download_item(item_type, item_id):
        model = Program if item_type == "programs" else Manual
        item = model.query.get_or_404(item_id)
        item.deleted_at = utc_now()
        item.is_active = False
        db.session.commit()
        flash("Elemento desactivado. El archivo físico no fue eliminado.", "warning")
        return redirect(url_for("admin_downloads"))


def document_admin_routes(app):
    @app.get("/admin/service-requests")
    @login_required
    def admin_service_requests():
        return render_template(
            "admin/service_requests.html",
            items=ServiceRequest.query.filter_by(deleted_at=None).order_by(ServiceRequest.created_at.desc()).all(),
        )

    @app.route("/admin/document-templates", methods=["GET", "POST"])
    @login_required
    def admin_document_templates():
        if request.method == "POST":
            db.session.add(DocumentTemplate(
                uuid=make_uuid(),
                name=form_text("name", 180),
                document_type=form_text("document_type", 80),
                version=form_int("version", "Versión", default=1, min_value=1) or 1,
                body=form_text("body", 12000),
                status=form_text("status", 40) or "borrador",
                is_active=checkbox_value("is_active"),
            ))
            db.session.commit()
            flash("Plantilla creada.", "success")
            return redirect(url_for("admin_document_templates"))
        return render_template("admin/document_templates.html", items=DocumentTemplate.query.order_by(DocumentTemplate.updated_at.desc()).all())

    @app.post("/admin/document-templates/<int:item_id>")
    @login_required
    def update_document_template(item_id):
        item = DocumentTemplate.query.get_or_404(item_id)
        item.name = form_text("name", 180)
        item.document_type = form_text("document_type", 80)
        version = form_int("version", "Versión", default=item.version, min_value=1)
        if version is None:
            return redirect(url_for("admin_document_templates"))
        item.version = version
        item.body = form_text("body", 12000)
        item.status = form_text("status", 40) or "borrador"
        item.is_active = checkbox_value("is_active")
        db.session.commit()
        flash("Plantilla actualizada.", "success")
        return redirect(url_for("admin_document_templates"))

    @app.get("/admin/documents")
    @login_required
    def admin_documents():
        documents = ServiceDocument.query.filter_by(deleted_at=None).order_by(ServiceDocument.created_at.desc()).all()
        return render_template(
            "admin/documents.html",
            documents=documents,
            latest_versions={
                document.id: DocumentVersion.query.filter_by(
                    document_id=document.id,
                    version_number=document.current_version,
                ).first()
                for document in documents
            },
            emails=EmailDelivery.query.order_by(EmailDelivery.created_at.desc()).limit(30).all(),
        )

    @app.post("/admin/documents/<int:item_id>/afcyber-otp")
    @login_required
    def admin_request_afcyber_otp(item_id):
        document = ServiceDocument.query.get_or_404(item_id)
        if document.status in {"cancelado", "rechazado"}:
            flash("No se puede solicitar OTP para un documento cancelado o rechazado.", "danger")
            return redirect(url_for("admin_documents"))
        for pending in SignatureRequest.query.filter_by(
            document_id=document.id,
            version_number=document.current_version,
            signer_role="afcyber",
            signer_email=current_user.email,
            status="pendiente",
        ).all():
            pending.status = "reemplazado"
        create_signature_request(
            document,
            "afcyber",
            current_user.name or "Representante AFCyber",
            current_user.email,
            include_sign_link=False,
        )
        db.session.commit()
        flash("OTP enviado al correo del representante administrador.", "success")
        return redirect(url_for("admin_documents"))

    @app.post("/admin/documents/<int:item_id>/versions")
    @login_required
    def admin_create_document_version(item_id):
        document = ServiceDocument.query.get_or_404(item_id)
        if document.status in {"cancelado", "rechazado"}:
            flash("No se puede versionar un documento cancelado o rechazado.", "danger")
            return redirect(url_for("admin_documents"))
        content = form_text("content", 12000)
        reason = form_text("reason", 1000)
        if not content:
            flash("El contenido de la nueva version no puede estar vacio.", "danger")
            return redirect(url_for("admin_documents"))
        _, created = create_new_document_version(document, content, reason)
        if not created:
            flash("No se creo version nueva porque el contenido no cambio.", "warning")
            return redirect(url_for("admin_documents"))
        db.session.commit()
        flash("Nueva version creada. Las firmas pendientes anteriores fueron invalidadas y se requiere firmar nuevamente.", "success")
        return redirect(url_for("admin_documents"))

    @app.post("/admin/documents/<int:item_id>/sign")
    @login_required
    def admin_sign_document(item_id):
        document = ServiceDocument.query.get_or_404(item_id)
        version = DocumentVersion.query.filter_by(document_id=document.id, version_number=document.current_version).first_or_404()
        signature_text = form_text("signature_text", 180)
        if not signature_text or not checkbox_value("consent"):
            flash("Escribe el nombre del representante y acepta el consentimiento.", "danger")
            return redirect(url_for("admin_documents"))
        otp = form_text("otp", 12)
        now = utc_now()
        signature_request = SignatureRequest.query.filter_by(
            document_id=document.id,
            version_number=document.current_version,
            signer_role="afcyber",
            signer_email=current_user.email,
            status="pendiente",
        ).order_by(SignatureRequest.created_at.desc()).first()
        if not signature_request:
            flash("Solicita un OTP antes de firmar como AFCyber.", "danger")
            return redirect(url_for("admin_documents"))
        if as_utc(signature_request.expires_at) < now or not signature_request.otp_expires_at or as_utc(signature_request.otp_expires_at) < now:
            signature_request.status = "vencido"
            db.session.commit()
            flash("El OTP de AFCyber vencio. Solicita uno nuevo.", "danger")
            return redirect(url_for("admin_documents"))
        if signature_request.otp_attempts >= OTP_MAX_ATTEMPTS:
            signature_request.status = "bloqueado"
            db.session.commit()
            flash("Demasiados intentos de OTP. Solicita uno nuevo.", "danger")
            return redirect(url_for("admin_documents"))
        if not hmac.compare_digest(signature_request.otp_hash or "", hash_token(otp)):
            signature_request.otp_attempts += 1
            db.session.commit()
            flash("OTP incorrecto para firma AFCyber.", "danger")
            return redirect(url_for("admin_documents"))
        signature_request.used_at = now
        signature_request.status = "firmado"
        signed_hash = hash_token("|".join([document.code, version.sha256 or "", current_user.email, signature_text, now.isoformat()]))
        db.session.add(ElectronicSignature(
            uuid=make_uuid(),
            document_id=document.id,
            signature_request_id=signature_request.id,
            version_number=signature_request.version_number,
            signer_name=signature_request.signer_name,
            signer_email=current_user.email,
            signer_role="afcyber",
            signature_text=signature_text,
            consent_text=f"Consentimiento de firma electrónica versión {CONSENT_VERSION}.",
            ip_hash=request_ip_hash(),
            user_agent_hash=request_user_agent_hash(),
            document_hash=version.sha256 or "",
            signed_hash=signed_hash,
        ))
        refresh_document_signature_status(document, signature_request.version_number)
        path, digest = create_document_pdf(document, version)
        document.final_pdf_path = path
        document.final_sha256 = digest
        log_signature_event("admin_signature_completed", document, signature_request, "Firma registrada desde panel administrativo.")
        db.session.commit()
        flash("Firma de AFCyber registrada y PDF actualizado.", "success")
        return redirect(url_for("admin_documents"))

    @app.get("/admin/documents/<int:item_id>/pdf")
    @login_required
    def admin_download_document_pdf(item_id):
        document = ServiceDocument.query.get_or_404(item_id)
        if not document.final_pdf_path:
            abort(404)
        path = private_path(document.final_pdf_path)
        if not path.exists():
            abort(404)
        return send_file(path, mimetype="application/pdf", as_attachment=True, download_name=f"{document.code}.pdf", conditional=True)

    @app.post("/admin/documents/<int:item_id>/cancel")
    @login_required
    def admin_cancel_document(item_id):
        document = ServiceDocument.query.get_or_404(item_id)
        document.status = "cancelado"
        log_signature_event("document_cancelled", document, detail="Cancelado desde panel administrativo.")
        db.session.commit()
        flash("Documento cancelado.", "warning")
        return redirect(url_for("admin_documents"))


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
