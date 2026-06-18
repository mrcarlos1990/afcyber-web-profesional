from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), unique=True, nullable=False)
    name = db.Column(db.String(140), nullable=False, default="Administrador")
    password_hash = db.Column(db.String(255), nullable=False)
    is_active_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(140), default="AFCyber SOLUTIONS")
    slogan = db.Column(db.String(220), default="Soluciones tecnológicas modernas y seguras")
    short_description = db.Column(db.Text, default="Servicios tecnológicos premium para empresas y emprendedores.")
    logo = db.Column(db.String(255), default="")
    favicon = db.Column(db.String(255), default="img/favicon.svg")
    primary_email = db.Column(db.String(160), default="info@afcybersolutions.com.do")
    phone = db.Column(db.String(80), default="829-919-8058")
    whatsapp = db.Column(db.String(80), default="18299198058")
    address = db.Column(db.String(220), default="Republica Dominicana")
    business_hours = db.Column(db.String(180), default="Lunes a viernes, 8:00 AM - 6:00 PM")
    facebook = db.Column(db.String(255), default="#")
    instagram = db.Column(db.String(255), default="#")
    linkedin = db.Column(db.String(255), default="#")
    tiktok = db.Column(db.String(255), default="#")
    youtube = db.Column(db.String(255), default="#")
    primary_color = db.Column(db.String(20), default="#1777ff")
    secondary_color = db.Column(db.String(20), default="#00d4ff")
    background_color = db.Column(db.String(20), default="#050b18")
    button_color = db.Column(db.String(20), default="#1777ff")
    theme_mode = db.Column(db.String(20), default="dark")
    tech_gradients = db.Column(db.Text, default="Azul neon, cyan y fondo oscuro corporativo")
    meta_title = db.Column(db.String(180), default="AFCyber SOLUTIONS | Servicios tecnológicos premium")
    meta_description = db.Column(db.Text, default="Desarrollo web, ciberseguridad, soporte técnico, redes, cámaras, POS y automatización empresarial.")
    keywords = db.Column(db.Text, default="AFCyber SOLUTIONS, tecnologia, ciberseguridad, desarrollo web, POS, CMMS")
    og_image = db.Column(db.String(255), default="img/og-afcyber.svg")
    google_analytics_id = db.Column(db.String(80), default="")
    google_search_console = db.Column(db.String(255), default="")
    copyright_text = db.Column(db.String(220), default="Todos los derechos reservados.")
    developer_text = db.Column(db.String(220), default="Desarrollado por AFCyber SOLUTIONS")


class HeroSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eyebrow = db.Column(db.String(160), default="Servicios tecnológicos premium")
    company_name = db.Column(db.String(140), default="AFCyber SOLUTIONS")
    title = db.Column(db.String(220), default="Soluciones tecnológicas modernas para empresas y emprendedores")
    subtitle = db.Column(db.Text, default="Diseñamos, implementamos y damos soporte a plataformas digitales, sistemas empresariales, redes, seguridad y automatización.")
    primary_button_text = db.Column(db.String(80), default="Solicitar servicio")
    primary_button_url = db.Column(db.String(160), default="#contacto")
    secondary_button_text = db.Column(db.String(80), default="Contactar por WhatsApp")
    secondary_button_url = db.Column(db.String(160), default="#")
    hero_image = db.Column(db.String(255), default="")
    trust_items = db.Column(db.Text, default="Webs rápidas\nSoporte profesional\nSeguridad y confianza")


class AboutSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    history = db.Column(db.Text, default="AFCyber SOLUTIONS acompana a empresas y emprendedores en su transformacion digital con soluciones modernas, funcionales y seguras.")
    mission = db.Column(db.Text, default="Crear soluciones tecnológicas claras, seguras y profesionales que impulsen la productividad de cada cliente.")
    vision = db.Column(db.Text, default="Ser una marca tecnológica reconocida por su diseño premium, soporte confiable e innovación práctica.")
    values = db.Column(db.Text, default="Responsabilidad, innovación, seguridad, transparencia, atención personalizada y mejora continua.")
    experience = db.Column(db.Text, default="Experiencia en tecnología, redes, ciberseguridad, desarrollo web, POS, cámaras, soporte y automatización.")
    cards = db.Column(db.Text, default="Estrategia digital|Soluciones pensadas para resultados reales|fa-solid fa-bullseye\nSeguridad|Buenas prácticas para proteger datos y operaciones|fa-solid fa-shield-halved\nSoporte|Acompañamiento técnico claro y profesional|fa-solid fa-headset")


class CEOProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.String(255), default="")
    full_name = db.Column(db.String(160), default="Ing. Amauri Feliz")
    role = db.Column(db.String(180), default="CEO & Fundador de AFCyber SOLUTIONS")
    headline = db.Column(db.String(220), default="Transformando ideas en soluciones tecnológicas modernas y seguras.")
    profile = db.Column(db.Text, default="Ingeniero en Ciberseguridad con experiencia en soporte tecnológico, automatización, desarrollo de sistemas empresariales, redes, seguridad informática y soluciones digitales para empresas y emprendedores.")
    experience = db.Column(db.Text, default="Desarrollo de sistemas POS\nDesarrollo web\nRedes empresariales\nSoporte técnico\nCámaras IP y analógicas\nAutomatización empresarial\nSeguridad informática\nImplementación tecnológica")
    linkedin = db.Column(db.String(255), default="#")
    whatsapp = db.Column(db.String(80), default="18299198058")
    cv_pdf = db.Column(db.String(255), default="")
    projects_count = db.Column(db.Integer, default=45)
    clients_count = db.Column(db.Integer, default=28)
    systems_count = db.Column(db.Integer, default=12)
    experience_years = db.Column(db.Integer, default=5)


class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    icon = db.Column(db.String(120), default="fa-solid fa-code")
    order = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)


class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    issuer = db.Column(db.String(160), default="")
    year = db.Column(db.String(20), default="")
    description = db.Column(db.Text, default="")
    order = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(120), default="fa-solid fa-microchip")
    image = db.Column(db.String(255), default="")
    price = db.Column(db.String(80), default="")
    whatsapp_button = db.Column(db.String(120), default="Solicitar servicio")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    price = db.Column(db.String(80), default="A cotizar")
    description = db.Column(db.Text, default="")
    features = db.Column(db.Text, default="")
    contact_button = db.Column(db.String(120), default="Cotizar plan")
    is_featured = db.Column(db.Boolean, default=False)


class PortfolioProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), default="")
    link = db.Column(db.String(255), default="#")
    category = db.Column(db.String(120), default="Proyecto")
    is_case_study = db.Column(db.Boolean, default=False)
    challenge_solution = db.Column(db.Text, default="")
    technologies = db.Column(db.Text, default="")


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(140), nullable=False)
    company = db.Column(db.String(140), default="")
    comment = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(255), default="")
    stars = db.Column(db.Integer, default=5)


class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(220), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inquiry_type = db.Column(db.String(60), default="cotizacion")
    subject = db.Column(db.String(180), default="Nueva Solicitud de Cotizacion")
    name = db.Column(db.String(140), nullable=False)
    company = db.Column(db.String(140), default="")
    phone = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(160), default="")
    requested_service = db.Column(db.String(160), default="")
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SocialLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    icon = db.Column(db.String(120), default="fa-solid fa-link")
    url = db.Column(db.String(255), default="#")
    is_active = db.Column(db.Boolean, default=True)
