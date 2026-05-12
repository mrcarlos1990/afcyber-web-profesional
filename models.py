from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), unique=True, nullable=False)
    name = db.Column(db.String(120), default="Administrador")
    password_hash = db.Column(db.String(255), nullable=False)
    is_active_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(160), default="AFCyber SOLUTIONS")
    slogan = db.Column(db.String(255), default="Soluciones tecnologicas modernas para empresas y emprendedores")
    short_description = db.Column(db.Text, default="Servicios premium de desarrollo web, ciberseguridad, soporte, redes, sistemas empresariales y automatizacion.")
    logo = db.Column(db.String(255))
    favicon = db.Column(db.String(255))
    main_email = db.Column(db.String(160), default="info@afcybersolutions.com.do")
    phone = db.Column(db.String(60), default="829-919-8058")
    whatsapp = db.Column(db.String(60), default="18299198058")
    address = db.Column(db.String(255), default="Republica Dominicana")
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
    meta_title = db.Column(db.String(180), default="AFCyber SOLUTIONS | Servicios tecnologicos premium")
    meta_description = db.Column(db.Text, default="AFCyber SOLUTIONS ofrece desarrollo web, sistemas POS, CMMS, soporte tecnico, redes, camaras, ciberseguridad y automatizacion.")
    meta_keywords = db.Column(db.Text, default="AFCyber SOLUTIONS, desarrollo web, ciberseguridad, POS, CMMS, soporte tecnico, redes, camaras")
    og_image = db.Column(db.String(255))
    google_analytics_id = db.Column(db.String(80))
    google_search_console = db.Column(db.String(255))
    footer_text = db.Column(db.String(255), default="Desarrollado por AFCyber SOLUTIONS")
    copyright_text = db.Column(db.String(255), default="Todos los derechos reservados.")
    show_about = db.Column(db.Boolean, default=True)
    show_ceo = db.Column(db.Boolean, default=True)
    show_services = db.Column(db.Boolean, default=True)
    show_plans = db.Column(db.Boolean, default=True)
    show_portfolio = db.Column(db.Boolean, default=True)
    show_testimonials = db.Column(db.Boolean, default=True)
    show_faq = db.Column(db.Boolean, default=True)
    show_contact = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HeroSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), default="AFCyber SOLUTIONS")
    subtitle = db.Column(db.String(255), default="Soluciones tecnologicas modernas para empresas y emprendedores")
    description = db.Column(db.Text, default="Disenamos, implementamos y damos soporte a plataformas digitales, sistemas empresariales, redes, seguridad y automatizacion para negocios que necesitan tecnologia confiable.")
    primary_button_text = db.Column(db.String(80), default="Solicitar servicio")
    primary_button_url = db.Column(db.String(255), default="#contacto")
    secondary_button_text = db.Column(db.String(80), default="Contactar por WhatsApp")
    secondary_button_message = db.Column(db.String(255), default="Hola AFCyber SOLUTIONS, quiero solicitar informacion.")
    image = db.Column(db.String(255))
    animation_enabled = db.Column(db.Boolean, default=True)


class AboutSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    history = db.Column(db.Text, default="AFCyber SOLUTIONS acompana a empresas y emprendedores en su transformacion digital con soluciones modernas, funcionales y seguras.")
    mission = db.Column(db.Text, default="Crear soluciones tecnologicas claras, seguras y profesionales que impulsen la productividad de cada cliente.")
    vision = db.Column(db.Text, default="Ser una marca tecnologica reconocida por diseno premium, soporte confiable e innovacion practica.")
    values = db.Column(db.Text, default="Responsabilidad, innovacion, seguridad, transparencia, atencion personalizada y mejora continua.")
    experience = db.Column(db.Text, default="Experiencia en desarrollo web, sistemas empresariales, redes, soporte tecnico, camaras, automatizacion y ciberseguridad basica.")
    image = db.Column(db.String(255))


class CEOProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.String(255))
    full_name = db.Column(db.String(160), default="Ing. Amauri Feliz")
    role = db.Column(db.String(180), default="CEO & Fundador de AFCyber SOLUTIONS")
    tagline = db.Column(db.String(255), default="Transformando ideas en soluciones tecnologicas modernas y seguras.")
    bio = db.Column(db.Text, default="Ingeniero en Ciberseguridad con experiencia en soporte tecnologico, automatizacion, desarrollo de sistemas empresariales, redes, seguridad informatica y soluciones digitales para empresas y emprendedores.")
    experience = db.Column(db.Text, default="Desarrollo de sistemas POS\nDesarrollo de sistemas CMMS\nDesarrollo web\nRedes, soporte tecnico, camaras IP y analogicas\nAutomatizacion empresarial\nSeguridad informatica\nImplementacion tecnologica")
    certifications = db.Column(db.Text, default="Ciberseguridad\nSoporte tecnologico\nImplementacion de soluciones empresariales")
    skills = db.Column(db.Text, default="Python\nFlask\nSQLite\nRedes\nCiberseguridad\nSoporte empresarial\nHTML/CSS/JS\nRender\nGitHub\nLinux basico/intermedio\nAutomatizacion\nSistemas administrativos")
    linkedin = db.Column(db.String(255))
    whatsapp_message = db.Column(db.String(255), default="Hola Ing. Amauri Feliz, quiero conversar sobre un proyecto tecnologico.")
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
    category = db.Column(db.String(120), default="Tecnologia")
    technologies = db.Column(db.Text, default="HTML, CSS, JavaScript")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(160), nullable=False)
    company = db.Column(db.String(160))
    comment = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(255))
    stars = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SocialLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    icon = db.Column(db.String(80), default="fa-solid fa-link")
    url = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    position = db.Column(db.Integer, default=0)
