from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), unique=True, nullable=False)
    name = db.Column(db.String(120), default="Administrador")
    password_hash = db.Column(db.String(255), nullable=False)
    is_active_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(160), default="AFCyber Solutions")
    slogan = db.Column(db.String(255), default="Tecnología, seguridad y soporte para negocios que quieren crecer")
    short_description = db.Column(db.Text, default="Desarrollo web, sistemas POS/ERP, CCTV, soporte técnico, automatización y ciberseguridad básica para empresas y hogares.")
    logo = db.Column(db.String(255))
    favicon = db.Column(db.String(255))
    main_email = db.Column(db.String(160), default="info@afcybersolutions.com.do")
    phone = db.Column(db.String(60), default="829-919-8058")
    whatsapp = db.Column(db.String(60), default="18299198058")
    address = db.Column(db.String(255), default="San Cristóbal, República Dominicana")
    business_hours = db.Column(db.String(160), default="Lunes a viernes, 8:00 AM - 6:00 PM")
    facebook = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    tiktok = db.Column(db.String(255))
    youtube = db.Column(db.String(255))
    primary_color = db.Column(db.String(20), default="#1777ff")
    secondary_color = db.Column(db.String(20), default="#00d4ff")
    background_color = db.Column(db.String(20), default="#050b18")
    button_color = db.Column(db.String(20), default="#1777ff")
    text_color = db.Column(db.String(20), default="#e9f3ff")
    dark_mode = db.Column(db.Boolean, default=True)
    tech_gradients = db.Column(db.Boolean, default=True)
    meta_title = db.Column(db.String(180), default="AFCyber Solutions | Desarrollo Web, Sistema POS, CCTV y Soporte Técnico")
    meta_description = db.Column(db.Text, default="AFCyber Solutions ofrece desarrollo web, sistemas POS/ERP, CCTV, soporte técnico, automatización y ciberseguridad básica en República Dominicana.")
    meta_keywords = db.Column(db.Text, default="AFCyber Solutions, desarrollo web, sistemas POS, ERP, CCTV, soporte técnico, ciberseguridad, automatización, República Dominicana")
    og_image = db.Column(db.String(255))
    google_analytics_id = db.Column(db.String(80))
    google_search_console = db.Column(db.String(255))
    footer_text = db.Column(db.String(255), default="Desarrollado por AFCyber Solutions")
    copyright_text = db.Column(db.String(255), default="Todos los derechos reservados.")
    show_about = db.Column(db.Boolean, default=True)
    show_ceo = db.Column(db.Boolean, default=True)
    show_services = db.Column(db.Boolean, default=True)
    show_plans = db.Column(db.Boolean, default=True)
    show_portfolio = db.Column(db.Boolean, default=True)
    show_testimonials = db.Column(db.Boolean, default=True)
    show_faq = db.Column(db.Boolean, default=True)
    show_contact = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)


class HeroSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), default="Soluciones tecnológicas para negocios que quieren crecer")
    subtitle = db.Column(db.String(255), default="Software, web, CCTV, soporte técnico y ciberseguridad básica")
    description = db.Column(db.Text, default="Desarrollo web, sistemas POS/ERP, ciberseguridad, CCTV, soporte técnico, automatización y servicios tecnológicos para empresas y hogares.")
    primary_button_text = db.Column(db.String(80), default="Solicitar cotización")
    primary_button_url = db.Column(db.String(255), default="#contacto")
    secondary_button_text = db.Column(db.String(80), default="Escribir por WhatsApp")
    secondary_button_message = db.Column(db.String(255), default="Hola AFCyber Solutions, quiero solicitar información sobre sus servicios.")
    image = db.Column(db.String(255))
    animation_enabled = db.Column(db.Boolean, default=True)


class AboutSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    history = db.Column(db.Text, default="AFCyber Solutions acompaña a empresas y emprendedores en su transformación digital con soluciones modernas, funcionales y seguras.")
    mission = db.Column(db.Text, default="Crear soluciones tecnológicas claras, seguras y profesionales que impulsen la productividad de cada cliente.")
    vision = db.Column(db.Text, default="Ser una marca tecnológica reconocida por diseño profesional, soporte confiable e innovación práctica.")
    values = db.Column(db.Text, default="Responsabilidad, innovación, seguridad, transparencia, atención personalizada y mejora continua.")
    experience = db.Column(db.Text, default="Experiencia en desarrollo web, sistemas empresariales, redes, soporte técnico, cámaras, automatización y ciberseguridad básica.")
    image = db.Column(db.String(255))


class CEOProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.String(255))
    full_name = db.Column(db.String(160), default="Ing. Amauri Feliz")
    role = db.Column(db.String(180), default="CEO & Fundador de AFCyber Solutions")
    tagline = db.Column(db.String(255), default="Transformando ideas en soluciones tecnológicas modernas y seguras.")
    bio = db.Column(db.Text, default="Ingeniero en Ciberseguridad con experiencia en soporte tecnológico, automatización, desarrollo de sistemas empresariales, redes, seguridad informática y soluciones digitales para empresas y emprendedores.")
    experience = db.Column(db.Text, default="Desarrollo de sistemas POS\nDesarrollo de sistemas CMMS\nDesarrollo web\nRedes, soporte técnico, cámaras IP y analógicas\nAutomatización empresarial\nSeguridad informática\nImplementación tecnológica")
    certifications = db.Column(db.Text, default="Ciberseguridad\nSoporte tecnológico\nImplementación de soluciones empresariales")
    skills = db.Column(db.Text, default="Python\nFlask\nSQLite\nRedes\nCiberseguridad\nSoporte empresarial\nHTML/CSS/JS\nRender\nGitHub\nLinux básico/intermedio\nAutomatización\nSistemas administrativos")
    linkedin = db.Column(db.String(255))
    whatsapp_message = db.Column(db.String(255), default="Hola Ing. Amauri Feliz, quiero conversar sobre un proyecto tecnológico.")
    cv_pdf = db.Column(db.String(255))
    projects_count = db.Column(db.Integer, default=45)
    clients_count = db.Column(db.Integer, default=30)
    systems_count = db.Column(db.Integer, default=12)
    experience_years = db.Column(db.Integer, default=5)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(80), default="fa-solid fa-shield-halved")
    image = db.Column(db.String(255))
    price = db.Column(db.String(80))
    is_active = db.Column(db.Boolean, default=True)
    position = db.Column(db.Integer, default=0)


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.String(80), default="A cotizar")
    description = db.Column(db.Text, nullable=False)
    features = db.Column(db.Text, nullable=False)
    button_text = db.Column(db.String(80), default="Solicitar plan")
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    position = db.Column(db.Integer, default=0)


class PortfolioProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    link = db.Column(db.String(255))
    category = db.Column(db.String(120), default="Tecnología")
    technologies = db.Column(db.Text, default="HTML, CSS, JavaScript")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(160), nullable=False)
    company = db.Column(db.String(160))
    comment = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(255))
    stars = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)


class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    company = db.Column(db.String(160))
    phone = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(160))
    requested_service = db.Column(db.String(160))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)


class SocialLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    icon = db.Column(db.String(80), default="fa-solid fa-link")
    url = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    position = db.Column(db.Integer, default=0)


class Manual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)
    title = db.Column(db.String(180), nullable=False)
    related_item = db.Column(db.String(180))
    category = db.Column(db.String(120), default="Documentación")
    version = db.Column(db.String(60), default="1.0")
    description = db.Column(db.Text, nullable=False)
    file_format = db.Column(db.String(20), default="PDF")
    file_size = db.Column(db.Integer, default=0)
    file_path = db.Column(db.String(255))
    external_url = db.Column(db.String(500))
    sha256 = db.Column(db.String(64))
    updated_on = db.Column(db.Date)
    download_count = db.Column(db.Integer, default=0)
    last_downloaded_at = db.Column(db.DateTime)
    status = db.Column(db.String(40), default="borrador")
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = db.Column(db.DateTime)

    __table_args__ = (
        db.Index("ix_manual_status_active", "status", "is_active"),
    )


class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)
    name = db.Column(db.String(180), nullable=False)
    version = db.Column(db.String(60), default="1.0")
    short_description = db.Column(db.String(260), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(120), default="Programa")
    target_business = db.Column(db.String(180))
    operating_system = db.Column(db.String(120), default="Windows")
    architecture = db.Column(db.String(40), default="x64")
    file_size = db.Column(db.Integer, default=0)
    updated_on = db.Column(db.Date)
    status = db.Column(db.String(40), default="borrador")
    license_type = db.Column(db.String(120), default="A definir")
    requirements = db.Column(db.Text)
    image = db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    external_url = db.Column(db.String(500))
    sha256 = db.Column(db.String(64))
    manual_id = db.Column(db.Integer, db.ForeignKey("manual.id"))
    is_active = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    last_downloaded_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = db.Column(db.DateTime)

    manual = db.relationship("Manual", backref="programs")

    __table_args__ = (
        db.Index("ix_program_status_active", "status", "is_active"),
    )


class DownloadEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    item_type = db.Column(db.String(20), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    item_slug = db.Column(db.String(180), nullable=False)
    ip_hash = db.Column(db.String(64))
    user_agent_hash = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=utc_now)

    __table_args__ = (
        db.Index("ix_download_event_item", "item_type", "item_id"),
    )


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    full_name = db.Column(db.String(180), nullable=False)
    identity_document = db.Column(db.String(80))
    company = db.Column(db.String(180))
    position = db.Column(db.String(120))
    email = db.Column(db.String(180), nullable=False)
    phone = db.Column(db.String(80), nullable=False)
    whatsapp = db.Column(db.String(80))
    address = db.Column(db.String(260))
    city = db.Column(db.String(120))
    province = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = db.Column(db.DateTime)

    __table_args__ = (
        db.Index("ix_customer_email", "email"),
    )


class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    requested_service = db.Column(db.String(180), nullable=False)
    service_type = db.Column(db.String(120))
    need_description = db.Column(db.Text, nullable=False)
    equipment_count = db.Column(db.String(80))
    estimated_date = db.Column(db.Date)
    modality = db.Column(db.String(40), default="Remoto")
    priority = db.Column(db.String(40), default="Normal")
    estimated_budget = db.Column(db.String(80))
    initial_scope = db.Column(db.Text)
    observations = db.Column(db.Text)
    accepted_privacy = db.Column(db.Boolean, default=False)
    accepted_contact = db.Column(db.Boolean, default=False)
    accepted_e_signature = db.Column(db.Boolean, default=False)
    confirmed_accuracy = db.Column(db.Boolean, default=False)
    consent_version = db.Column(db.String(40), default="2026-07")
    consent_ip_hash = db.Column(db.String(64))
    status = db.Column(db.String(40), default="recibida")
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = db.Column(db.DateTime)

    customer = db.relationship("Customer", backref="service_requests")

    __table_args__ = (
        db.Index("ix_service_request_status", "status"),
    )


class DocumentTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(180), nullable=False)
    document_type = db.Column(db.String(80), nullable=False)
    version = db.Column(db.Integer, default=1)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), default="borrador")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = db.Column(db.DateTime)


class ServiceDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    code = db.Column(db.String(40), unique=True, nullable=False)
    service_request_id = db.Column(db.Integer, db.ForeignKey("service_request.id"))
    template_id = db.Column(db.Integer, db.ForeignKey("document_template.id"))
    title = db.Column(db.String(180), nullable=False)
    document_type = db.Column(db.String(80), default="Solicitud de servicio")
    status = db.Column(db.String(60), default="borrador")
    current_version = db.Column(db.Integer, default=1)
    verification_code = db.Column(db.String(80), unique=True, nullable=False)
    final_pdf_path = db.Column(db.String(255))
    final_sha256 = db.Column(db.String(64))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = db.Column(db.DateTime)

    service_request = db.relationship("ServiceRequest", backref="documents")
    template = db.relationship("DocumentTemplate")

    __table_args__ = (
        db.Index("ix_service_document_status", "status"),
    )


class DocumentVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("service_document.id"), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    pdf_path = db.Column(db.String(255))
    sha256 = db.Column(db.String(64))
    status = db.Column(db.String(40), default="vigente")
    created_at = db.Column(db.DateTime, default=utc_now)

    document = db.relationship("ServiceDocument", backref="versions")

    __table_args__ = (
        db.UniqueConstraint("document_id", "version_number", name="uq_document_version_number"),
    )


class SignatureRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("service_document.id"), nullable=False)
    version_number = db.Column(db.Integer, default=1, nullable=False)
    signer_role = db.Column(db.String(40), nullable=False)
    signer_name = db.Column(db.String(180), nullable=False)
    signer_email = db.Column(db.String(180), nullable=False)
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    otp_hash = db.Column(db.String(64))
    otp_expires_at = db.Column(db.DateTime)
    otp_attempts = db.Column(db.Integer, default=0)
    status = db.Column(db.String(60), default="pendiente")
    reject_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    document = db.relationship("ServiceDocument", backref="signature_requests")

    __table_args__ = (
        db.Index("ix_signature_request_status", "status"),
    )


class ElectronicSignature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("service_document.id"), nullable=False)
    signature_request_id = db.Column(db.Integer, db.ForeignKey("signature_request.id"), nullable=False)
    version_number = db.Column(db.Integer, default=1, nullable=False)
    signer_name = db.Column(db.String(180), nullable=False)
    signer_email = db.Column(db.String(180), nullable=False)
    signer_role = db.Column(db.String(40), nullable=False)
    signature_method = db.Column(db.String(40), default="nombre_escrito_otp")
    signature_text = db.Column(db.String(180), nullable=False)
    consent_text = db.Column(db.Text, nullable=False)
    ip_hash = db.Column(db.String(64))
    user_agent_hash = db.Column(db.String(64))
    document_hash = db.Column(db.String(64), nullable=False)
    signed_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    document = db.relationship("ServiceDocument", backref="signatures")
    signature_request = db.relationship("SignatureRequest")


class SignatureAuditEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("service_document.id"))
    signature_request_id = db.Column(db.Integer, db.ForeignKey("signature_request.id"))
    event_type = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.Text)
    ip_hash = db.Column(db.String(64))
    user_agent_hash = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=utc_now)

    document = db.relationship("ServiceDocument", backref="audit_events")


class EmailDelivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    recipient = db.Column(db.String(180), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    email_type = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(40), default="pendiente")
    error = db.Column(db.Text)
    retries = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=utc_now)
    sent_at = db.Column(db.DateTime)


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    service_request_id = db.Column(db.Integer, db.ForeignKey("service_request.id"))
    document_id = db.Column(db.Integer, db.ForeignKey("service_document.id"))
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    mime_type = db.Column(db.String(120))
    sha256 = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=utc_now)
