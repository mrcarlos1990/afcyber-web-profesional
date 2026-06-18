import os
import json
import secrets
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import text
from werkzeug.utils import secure_filename

from extensions import db, login_manager
from models import (
    AboutSection,
    CEOProfile,
    Certificate,
    ContactMessage,
    FAQ,
    HeroSection,
    Plan,
    PortfolioProject,
    Service,
    SiteSettings,
    Skill,
    SocialLink,
    Testimonial,
    User,
)

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ALLOWED_IMAGES = {"jpg", "jpeg", "png", "webp", "svg"}
ALLOWED_PDF = {"pdf"}


REAL_SERVICES = [
    {
        "slug": "software-empresarial",
        "name": "Desarrollo de Software Empresarial",
        "short_name": "Software a medida",
        "description": "Plataformas personalizadas, CRMs y automatización de flujos de trabajo para optimizar la gestión de su negocio.",
        "icon": "fa-solid fa-gears",
        "image": "img/services/software-dev.jpeg",
        "features": [
            "Desarrollo Web & Mobile",
            "Paneles administrativos",
            "Automatización de procesos",
            "Integración de APIs",
            "Bases de datos escalables",
            "Arquitectura en la nube"
        ],
    },
    {
        "slug": "sistemas-pos-erp",
        "name": "Sistemas POS & ERP",
        "short_name": "Sistemas de Ventas",
        "description": "Soluciones robustas para el control de inventario, facturación y gestión de recursos empresariales.",
        "icon": "fa-solid fa-cash-register",
        "image": "img/services/pos-system.jpeg",
        "features": [
            "Sistemas ERP y CRM",
            "Paneles administrativos",
            "Automatización de procesos",
            "Integración de APIs",
            "Bases de datos escalables",
            "Arquitectura en la nube"
        ],
    },
    {
        "slug": "ciberseguridad",
        "name": "Ciberseguridad Avanzada",
        "short_name": "Ciberseguridad",
        "description": "Protección de activos digitales, auditorías de seguridad y respuesta ante incidentes.",
        "icon": "fa-solid fa-shield-virus",
        "image": "img/services/cybersecurity.jpeg",
        "features": [
            "Auditorías de seguridad",
            "Protección de datos",
            "Pentesting",
            "Seguridad perimetral",
            "Cumplimiento normativo",
            "Recuperación ante desastres"
        ],
    },
    {
        "slug": "inteligencia-artificial",
        "name": "Soluciones de Inteligencia Artificial",
        "short_name": "IA & Automatización",
        "description": "Implementación de modelos de IA para análisis de datos y automatización inteligente.",
        "icon": "fa-solid fa-brain",
        "image": "img/services/ai-solutions.jpeg",
        "features": [
            "Chatbots inteligentes",
            "Análisis predictivo",
            "Procesamiento de lenguaje natural",
            "Automatización con IA",
            "Machine Learning aplicado"
        ],
    },
    {
        "slug": "infraestructura-tecnologica",
        "name": "Infraestructura Tecnológica",
        "short_name": "Infraestructura",
        "description": "Diseño y despliegue de redes, servidores y soluciones de alta disponibilidad.",
        "icon": "fa-solid fa-server",
        "image": "img/services/infrastructure.jpeg",
        "features": [
            "Redes empresariales",
            "Virtualización",
            "Cloud Computing",
            "Soporte de servidores",
            "Monitoreo 24/7"
        ],
    },
    {
        "slug": "cctv-control-acceso",
        "name": "CCTV & Control de Acceso",
        "short_name": "Seguridad Física",
        "description": "Instalación y configuración de sistemas de videovigilancia IP y analógica con monitoreo remoto.",
        "icon": "fa-solid fa-video",
        "image": "img/services/cctv.jpeg",
        "features": [
            "Cámaras IP y Analógicas",
            "Control de acceso biométrico",
            "Monitoreo remoto móvil",
            "Sistemas de alarmas",
            "Mantenimiento preventivo"
        ],
    },
]

CONTACT_CHANNELS = {
    "cotizacion": {
        "label": "Cotizaciones",
        "email": "cotizaciones@afcybersolutions.com.do",
        "subject": "Nueva Solicitud de Cotización",
        "icon": "fa-solid fa-file-invoice-dollar",
    },
    "ventas": {
        "label": "Ventas",
        "email": "ventas@afcybersolutions.com.do",
        "subject": "Consulta de Ventas",
        "icon": "fa-solid fa-cart-shopping",
    },
    "contacto": {
        "label": "Contacto General",
        "email": "info@afcybersolutions.com.do",
        "subject": "Consulta desde sitio web AFCyber Solutions",
        "icon": "fa-solid fa-envelope-open-text",
    },
    "ingeniero": {
        "label": "Contactar al Ingeniero",
        "email": "a.felizv@afcybersolutions.com.do",
        "subject": "Contacto para Ing. Amauri Feliz",
        "icon": "fa-solid fa-user-tie",
    },
    "soporte": {
        "label": "Soporte Técnico",
        "email": "soporte@afcybersolutions.com.do",
        "subject": "Solicitud de Soporte Técnico",
        "icon": "fa-solid fa-headset",
    },
    "licencias": {
        "label": "Licencias",
        "email": "licencias@afcybersolutions.com.do",
        "subject": "Consulta sobre Licencias",
        "icon": "fa-solid fa-key",
    },
}


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-this-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'afcyber.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        ensure_database_schema()
        seed_database()

    register_routes(app)
    register_template_helpers(app)
    register_error_handlers(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def register_template_helpers(app):
    @app.context_processor
    def inject_settings():
        settings = get_settings()
        
        # Datos estructurados de la empresa (Schema.org)
        company_schema = {
            "@context": "https://schema.org",
            "@type": "ProfessionalService",
            "name": settings.company_name if settings else "AFCyber SOLUTIONS",
            "description": settings.meta_description if settings else "",
            "url": request.url_root,
            "logo": url_for('static', filename=settings.logo) if settings and settings.logo else "",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Santo Domingo",
                "addressCountry": "DO",
                "streetAddress": settings.address if settings else ""
            },
            "telephone": settings.phone if settings else "",
            "email": settings.primary_email if settings else "",
            "sameAs": [
                settings.facebook,
                settings.instagram,
                settings.linkedin,
                settings.tiktok,
                settings.youtube
            ]
        }

        return {
            "settings": settings,
            "visual_assets": get_visual_assets(settings),
            "company_schema": json.dumps(company_schema),
            "meta": {
                "title": settings.meta_title if settings else "AFCyber SOLUTIONS",
                "description": settings.meta_description if settings else "",
                "og_image": url_for('static', filename=settings.og_image) if settings and settings.og_image else ""
            }
        }

    @app.template_filter("lines")
    def lines(value):
        return [line.strip() for line in (value or "").splitlines() if line.strip()]

    @app.template_filter("split_cards")
    def split_cards(value):
        cards = []
        for line in (value or "").splitlines():
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 2:
                cards.append({
                    "title": parts[0],
                    "text": parts[1],
                    "icon": parts[2] if len(parts) > 2 else "fa-solid fa-gem",
                })
        return cards

    @app.template_filter("asset")
    def asset(path):
        if not path:
            return ""
        return url_for("static", filename=path)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_error):
        return render_template("public/error.html", code=404, title="Página no encontrada"), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template("public/error.html", code=500, title="Error interno"), 500


def register_routes(app):
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            inquiry_type = request.form.get("inquiry_type", "cotizacion").strip().lower()
            channel = CONTACT_CHANNELS.get(inquiry_type, CONTACT_CHANNELS["contacto"])
            subject = request.form.get("subject", channel["subject"]).strip() or channel["subject"]
            message = ContactMessage(
                inquiry_type=inquiry_type if inquiry_type in CONTACT_CHANNELS else "contacto",
                subject=subject,
                name=request.form.get("name", "").strip(),
                company=request.form.get("company", "").strip(),
                phone=request.form.get("phone", "").strip(),
                email=request.form.get("email", "").strip(),
                requested_service=request.form.get("requested_service", "").strip(),
                message=request.form.get("message", "").strip(),
            )
            if not message.name or not (message.phone or message.email) or not message.message:
                flash("Completa nombre, teléfono o correo, y descripción.", "danger")
            else:
                db.session.add(message)
                db.session.commit()
                send_contact_notification(message, channel)
                flash("Solicitud enviada correctamente. Nuestro equipo se comunicará con usted.", "success")
                return redirect(url_for("index", _anchor="contacto"))

        return render_template(
            "public/index.html",
            hero=first_or_404(HeroSection),
            about=first_or_404(AboutSection),
            ceo=first_or_404(CEOProfile),
            real_services=REAL_SERVICES,
            contact_channels=CONTACT_CHANNELS,
            skills=Skill.query.filter_by(is_active=True).order_by(Skill.order.asc(), Skill.id.asc()).all(),
            certificates=Certificate.query.filter_by(is_active=True).order_by(Certificate.order.asc(), Certificate.id.asc()).all(),
            services=Service.query.filter_by(is_active=True).order_by(Service.id.asc()).all(),
            plans=Plan.query.order_by(Plan.id.asc()).all(),
            projects=PortfolioProject.query.order_by(PortfolioProject.id.desc()).all(),
            testimonials=Testimonial.query.order_by(Testimonial.id.desc()).all(),
            faqs=FAQ.query.filter_by(is_active=True).order_by(FAQ.order.asc(), FAQ.id.asc()).all(),
            socials=SocialLink.query.filter_by(is_active=True).all(),
        )

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if current_user.is_authenticated:
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            password = request.form.get("password", "")
            master_password = os.getenv("ADMIN_MASTER_PASSWORD")
            if master_password and password == master_password:
                user = User.query.filter_by(is_active_admin=True).order_by(User.id.asc()).first()
                if not user:
                    user = User(email=os.environ.get("ADMIN_EMAIL", "admin@afcybersolutions.com.do"), name="Administrador AFCyber")
                    user.set_password(secrets.token_urlsafe(48))
                    db.session.add(user)
                    db.session.commit()
                login_user(user)
                return redirect(url_for("admin_dashboard"))
            flash("Contraseña maestra incorrecta.", "danger")
        return render_template("admin/login.html")

    @app.route("/admin/logout")
    @login_required
    def admin_logout():
        logout_user()
        flash("Sesion cerrada correctamente.", "success")
        return redirect(url_for("admin_login"))

    @app.route("/admin")
    @login_required
    def admin_dashboard():
        stats = {
            "messages": ContactMessage.query.count(),
            "unread": ContactMessage.query.filter_by(is_read=False).count(),
            "services": Service.query.count(),
            "projects": PortfolioProject.query.count(),
            "testimonials": Testimonial.query.count(),
            "by_type": {
                key: ContactMessage.query.filter_by(inquiry_type=key).count()
                for key in CONTACT_CHANNELS
            },
        }
        recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(6).all()
        return render_template("admin/dashboard.html", stats=stats, recent_messages=recent_messages, contact_channels=CONTACT_CHANNELS)

    @app.route("/admin/settings", methods=["GET", "POST"])
    @login_required
    def admin_settings():
        item = get_settings()
        fields = admin_fields()["settings"]
        if request.method == "POST":
            update_model_from_form(item, fields)
            db.session.commit()
            flash("Configuración actualizada.", "success")
            return redirect(url_for("admin_settings"))
        return render_template("admin/edit_single.html", title="Configuración general", item=item, fields=fields)

    @app.route("/admin/<module>", methods=["GET", "POST"])
    @login_required
    def admin_module(module):
        configs = admin_modules()
        if module not in configs:
            abort(404)
        config = configs[module]
        model = config["model"]
        fields = config["fields"]
        if config.get("single"):
            item = model.query.first()
            if request.method == "POST":
                update_model_from_form(item, fields)
                db.session.commit()
                flash(f"{config['title']} actualizado.", "success")
                return redirect(url_for("admin_module", module=module))
            return render_template("admin/edit_single.html", title=config["title"], item=item, fields=fields)

        if request.method == "POST":
            item = model()
            update_model_from_form(item, fields)
            db.session.add(item)
            db.session.commit()
            flash("Registro creado correctamente.", "success")
            return redirect(url_for("admin_module", module=module))

        items = model.query.order_by(model.id.desc()).all()
        return render_template("admin/list.html", module=module, config=config, fields=fields, items=items)

    @app.route("/admin/<module>/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    def admin_edit_item(module, item_id):
        config = admin_modules().get(module)
        if not config or config.get("single"):
            abort(404)
        item = config["model"].query.get_or_404(item_id)
        if request.method == "POST":
            update_model_from_form(item, config["fields"])
            db.session.commit()
            flash("Registro actualizado.", "success")
            return redirect(url_for("admin_module", module=module))
        return render_template("admin/edit_single.html", title=f"Editar {config['singular']}", item=item, fields=config["fields"])

    @app.route("/admin/<module>/<int:item_id>/delete", methods=["POST"])
    @login_required
    def admin_delete_item(module, item_id):
        config = admin_modules().get(module)
        if not config or config.get("single") or not config.get("delete", True):
            abort(404)
        item = config["model"].query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash("Registro eliminado.", "success")
        return redirect(url_for("admin_module", module=module))

    @app.route("/admin/messages")
    @login_required
    def admin_messages():
        selected_type = request.args.get("type", "").strip().lower()
        query = ContactMessage.query
        if selected_type in CONTACT_CHANNELS:
            query = query.filter_by(inquiry_type=selected_type)
        messages = query.order_by(ContactMessage.created_at.desc()).all()
        return render_template("admin/messages.html", messages=messages, contact_channels=CONTACT_CHANNELS, selected_type=selected_type)

    @app.route("/admin/messages/<int:message_id>")
    @login_required
    def admin_message_detail(message_id):
        message = ContactMessage.query.get_or_404(message_id)
        message.is_read = True
        db.session.commit()
        return render_template("admin/message_detail.html", message=message)

    @app.route("/admin/messages/<int:message_id>/delete", methods=["POST"])
    @login_required
    def admin_message_delete(message_id):
        message = ContactMessage.query.get_or_404(message_id)
        db.session.delete(message)
        db.session.commit()
        flash("Mensaje eliminado.", "success")
        return redirect(url_for("admin_messages"))

    @app.route("/admin/users", methods=["GET", "POST"])
    @login_required
    def admin_users():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            name = request.form.get("name", "").strip() or "Administrador"
            password = request.form.get("password", "")
            if not email or len(password) < 8:
                flash("Indica correo y una contrasena de al menos 8 caracteres.", "danger")
            elif User.query.filter_by(email=email).first():
                flash("Ese usuario ya existe.", "danger")
            else:
                user = User(email=email, name=name)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Usuario admin creado.", "success")
            return redirect(url_for("admin_users"))
        return render_template("admin/users.html", users=User.query.order_by(User.id.asc()).all())

    @app.route("/admin/users/<int:user_id>/password", methods=["POST"])
    @login_required
    def admin_user_password(user_id):
        user = User.query.get_or_404(user_id)
        password = request.form.get("password", "")
        if len(password) < 8:
            flash("La contrasena debe tener al menos 8 caracteres.", "danger")
        else:
            user.set_password(password)
            db.session.commit()
            flash("Contrasena actualizada.", "success")
        return redirect(url_for("admin_users"))


def admin_fields():
    return {
        "settings": [
            ("company_name", "Nombre empresa", "text"), ("slogan", "Slogan", "text"),
            ("short_description", "Descripcion corta", "textarea"), ("logo", "Logo", "image"),
            ("favicon", "Favicon", "image"), ("primary_email", "Correo principal", "email"),
            ("phone", "Telefono", "text"), ("whatsapp", "WhatsApp internacional", "text"),
            ("address", "Direccion", "text"), ("business_hours", "Horario", "text"),
            ("facebook", "Facebook", "url"), ("instagram", "Instagram", "url"),
            ("linkedin", "LinkedIn", "url"), ("tiktok", "TikTok", "url"), ("youtube", "YouTube", "url"),
            ("primary_color", "Color primario", "color"), ("secondary_color", "Color secundario", "color"),
            ("background_color", "Color fondo", "color"), ("button_color", "Color botones", "color"),
            ("theme_mode", "Modo oscuro/claro", "text"), ("tech_gradients", "Gradientes tecnológicos", "textarea"),
            ("meta_title", "Meta title", "text"), ("meta_description", "Meta description", "textarea"),
            ("keywords", "Keywords", "textarea"), ("og_image", "Imagen Open Graph", "image"),
            ("google_analytics_id", "Google Analytics ID", "text"), ("google_search_console", "Google Search Console", "text"),
            ("copyright_text", "Copyright", "text"), ("developer_text", "Texto desarrollado por", "text"),
        ]
    }


def admin_modules():
    return {
        "hero": {"title": "Hero principal", "singular": "hero", "model": HeroSection, "single": True, "fields": [
            ("eyebrow", "Etiqueta", "text"), ("company_name", "Nombre visible", "text"), ("title", "Titulo principal", "text"),
            ("subtitle", "Subtítulo", "textarea"), ("primary_button_text", "Botón principal", "text"), ("primary_button_url", "URL botón principal", "text"),
            ("secondary_button_text", "Botón secundario", "text"), ("secondary_button_url", "URL botón secundario", "text"),
            ("hero_image", "Imagen/animacion", "image"), ("trust_items", "Puntos de confianza, uno por linea", "textarea"),
        ]},
        "about": {"title": "Nosotros", "singular": "nosotros", "model": AboutSection, "single": True, "fields": [
            ("history", "Historia", "textarea"), ("mission", "Misión", "textarea"), ("vision", "Visión", "textarea"),
            ("values", "Valores", "textarea"), ("experience", "Experiencia", "textarea"),
            ("cards", "Tarjetas: titulo|texto|icono, una por linea", "textarea"),
        ]},
        "ceo": {"title": "CEO & Founder", "singular": "CEO", "model": CEOProfile, "single": True, "fields": [
            ("photo", "Foto CEO", "image"), ("full_name", "Nombre completo", "text"), ("role", "Cargo", "text"),
            ("headline", "Linea premium", "text"), ("profile", "Descripcion profesional", "textarea"),
            ("experience", "Experiencia, una por linea", "textarea"), ("linkedin", "LinkedIn", "url"), ("whatsapp", "WhatsApp", "text"),
            ("cv_pdf", "CV PDF", "pdf"), ("projects_count", "Proyectos realizados", "number"),
            ("clients_count", "Clientes atendidos", "number"), ("systems_count", "Sistemas desarrollados", "number"), ("experience_years", "Experiencia tecnológica", "number"),
        ]},
        "skills": {"title": "Habilidades CEO", "singular": "habilidad", "model": Skill, "fields": [
            ("name", "Nombre", "text"), ("icon", "Icono Font Awesome", "text"), ("order", "Orden", "number"), ("is_active", "Activo", "checkbox"),
        ]},
        "certificates": {"title": "Certificaciones CEO", "singular": "certificado", "model": Certificate, "fields": [
            ("name", "Nombre", "text"), ("issuer", "Emisor", "text"), ("year", "Ano", "text"),
            ("description", "Descripcion", "textarea"), ("order", "Orden", "number"), ("is_active", "Activo", "checkbox"),
        ]},
        "services": {"title": "Servicios", "singular": "servicio", "model": Service, "fields": [
            ("name", "Nombre", "text"), ("description", "Descripcion", "textarea"), ("icon", "Icono Font Awesome", "text"),
            ("image", "Imagen", "image"), ("price", "Precio opcional", "text"), ("whatsapp_button", "Botón WhatsApp", "text"), ("is_active", "Activo", "checkbox"),
        ]},
        "plans": {"title": "Planes", "singular": "plan", "model": Plan, "fields": [
            ("name", "Nombre", "text"), ("price", "Precio", "text"), ("description", "Descripcion", "textarea"),
            ("features", "Características, una por línea", "textarea"), ("contact_button", "Botón de contacto", "text"), ("is_featured", "Destacado", "checkbox"),
        ]},
        "portfolio": {"title": "Portafolio", "singular": "proyecto", "model": PortfolioProject, "fields": [
            ("name", "Nombre", "text"), ("description", "Descripcion", "textarea"), ("image", "Imagen", "image"),
            ("link", "Enlace", "url"), ("category", "Categoria", "text"), ("technologies", "Tecnologias usadas", "textarea"),
        ]},
        "testimonials": {"title": "Testimonios", "singular": "testimonio", "model": Testimonial, "fields": [
            ("client_name", "Cliente", "text"), ("company", "Empresa", "text"), ("comment", "Comentario", "textarea"),
            ("photo", "Foto opcional", "image"), ("stars", "Estrellas", "number"),
        ]},
        "faq": {"title": "FAQ", "singular": "pregunta", "model": FAQ, "fields": [
            ("question", "Pregunta", "text"), ("answer", "Respuesta", "textarea"), ("order", "Orden", "number"), ("is_active", "Activo", "checkbox"),
        ]},
        "socials": {"title": "Redes sociales", "singular": "red social", "model": SocialLink, "fields": [
            ("name", "Nombre", "text"), ("icon", "Icono", "text"), ("url", "URL", "url"), ("is_active", "Activo", "checkbox"),
        ]},
    }


def update_model_from_form(item, fields):
    for name, _label, field_type in fields:
        if field_type in {"image", "pdf"}:
            uploaded = request.files.get(name)
            if uploaded and uploaded.filename:
                uploaded_path = save_upload(uploaded, pdf=field_type == "pdf")
                if uploaded_path:
                    setattr(item, name, uploaded_path)
            continue
        if field_type == "checkbox":
            setattr(item, name, name in request.form)
        elif field_type == "number":
            setattr(item, name, int(request.form.get(name) or 0))
        else:
            setattr(item, name, request.form.get(name, "").strip())


def save_upload(file, pdf=False):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed = ALLOWED_PDF if pdf else ALLOWED_IMAGES
    if ext not in allowed:
        flash("Archivo no permitido.", "danger")
        return None
    filename = secure_filename(file.filename)
    stem, extension = os.path.splitext(filename)
    filename = f"{stem[:60]}-{os.urandom(4).hex()}{extension.lower()}"
    path = os.path.join("uploads", filename)
    file.save(os.path.join(BASE_DIR, "static", path))
    return path.replace("\\", "/")


def ensure_database_schema():
    # Migración para ContactMessage
    inspector_sql = text("PRAGMA table_info(contact_message)")
    existing_columns = {row[1] for row in db.session.execute(inspector_sql).fetchall()}
    if "inquiry_type" not in existing_columns:
        db.session.execute(text("ALTER TABLE contact_message ADD COLUMN inquiry_type VARCHAR(60) DEFAULT 'cotizacion'"))
    if "subject" not in existing_columns:
        db.session.execute(text("ALTER TABLE contact_message ADD COLUMN subject VARCHAR(180) DEFAULT 'Nueva Solicitud de Cotización'"))
    
    # Migración para PortfolioProject
    portfolio_inspector = text("PRAGMA table_info(portfolio_project)")
    portfolio_columns = {row[1] for row in db.session.execute(portfolio_inspector).fetchall()}
    if "is_case_study" not in portfolio_columns:
        db.session.execute(text("ALTER TABLE portfolio_project ADD COLUMN is_case_study BOOLEAN DEFAULT 0"))
    if "challenge_solution" not in portfolio_columns:
        db.session.execute(text("ALTER TABLE portfolio_project ADD COLUMN challenge_solution TEXT DEFAULT ''"))
    if "technologies" not in portfolio_columns:
        db.session.execute(text("ALTER TABLE portfolio_project ADD COLUMN technologies TEXT DEFAULT ''"))
        
    db.session.commit()
def send_contact_notification(message, channel):
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    if not smtp_host or not smtp_user or not smtp_password:
        return False

    smtp_port = int(os.environ.get("SMTP_PORT", "587") or 587)
    smtp_from = os.environ.get("SMTP_FROM", smtp_user).strip()
    use_tls = os.environ.get("SMTP_USE_TLS", "1").strip() != "0"

    email = EmailMessage()
    email["From"] = smtp_from
    email["To"] = channel["email"]
    email["Subject"] = message.subject or channel["subject"]
    if message.email:
        email["Reply-To"] = message.email
    email.set_content(build_contact_email_body(message, channel))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(email)
        return True
    except Exception:
        return False


def build_contact_email_body(message, channel):
    return "\n".join([
        f"Tipo: {channel['label']}",
        f"Asunto: {message.subject or channel['subject']}",
        f"Nombre: {message.name}",
        f"Empresa: {message.company or 'No indicada'}",
        f"Telefono: {message.phone or 'No indicado'}",
        f"Correo: {message.email or 'No indicado'}",
        f"Servicio: {message.requested_service or 'No indicado'}",
        "",
        "Descripcion:",
        message.message,
    ])


def get_settings():
    return SiteSettings.query.first()


def get_visual_assets(settings=None):
    def first_existing(candidates):
        for candidate in candidates:
            if candidate and static_asset_exists(candidate):
                return candidate
        return ""

    settings = settings or get_settings()
    logo_candidates = [
        settings.logo if settings else "",
        "img/afcyber-logo-main.png",
        "img/afcyber-logo-reference.png",
        "img/favicon.svg",
    ]
    hero_logo_candidates = [
        "img/afcyber-logo-hero.png",
        *logo_candidates,
    ]
    hero_candidates = [
        "img/afcyber-soc-reference.png",
        "img/hero-futurista.png",
        "img/hero-futuristic.png",
        "uploads/hero-futurista.png",
        settings.og_image if settings else "",
    ]

    return {
        "logo": first_existing(logo_candidates),
        "hero_logo": first_existing(hero_logo_candidates),
        "hero_image": first_existing(hero_candidates),
    }


def static_asset_exists(path):
    return os.path.exists(os.path.join(BASE_DIR, "static", path.replace("/", os.sep)))


def first_or_404(model):
    item = model.query.first()
    if not item:
        abort(404)
    return item


def seed_database():
    if not User.query.first():
        admin = User(email=os.environ.get("ADMIN_EMAIL", "admin@afcybersolutions.com.do"), name="Administrador AFCyber")
        admin.set_password(secrets.token_urlsafe(48))
        db.session.add(admin)

    for model in (SiteSettings, HeroSection, AboutSection, CEOProfile):
        if not model.query.first():
            db.session.add(model())

    if not Service.query.first():
        for service in REAL_SERVICES:
            db.session.add(Service(
                name=service["name"],
                description=service["description"],
                icon=service["icon"],
                image=service["image"],
                whatsapp_button="Solicitar información",
            ))

    if not Plan.query.first():
        db.session.add_all([
            Plan(name="Plan Básico", price="Desde RD$ 12,000", description="Presencia inicial profesional.", features="Página informativa\nBotón WhatsApp\nDiseño responsive"),
            Plan(name="Plan Profesional", price="Desde RD$ 28,000", description="Web avanzada para marcas en crecimiento.", features="Página avanzada\nDominio y hosting\nSEO básico\nSecciones premium", is_featured=True),
            Plan(name="Plan Empresarial", price="A cotizar", description="Software, paneles e integraciones a medida.", features="Sistema personalizado\nPanel admin\nAutomatización\nSoporte técnico"),
        ])

    if not PortfolioProject.query.first():
        for service in REAL_SERVICES:
            db.session.add(PortfolioProject(
                name=service["name"],
                category=service["short_name"],
                technologies=", ".join(service["features"][:4]),
                description=service["description"],
                image=service.get("alt_image") or service["image"],
            ))

    if not Testimonial.query.first():
        db.session.add_all([
            Testimonial(client_name="Cliente comercial", company="Servicios profesionales", comment="La presencia digital quedó moderna, rápida y lista para captar clientes por WhatsApp.", stars=5),
            Testimonial(client_name="Gerente operativo", company="Empresa local", comment="Nos ayudaron a organizar procesos y entender que solucion necesitaba el negocio.", stars=5),
            Testimonial(client_name="Emprendedor", company="Marca digital", comment="Excelente trato, diseño profesional y soporte claro durante todo el proceso.", stars=5),
        ])

    if not FAQ.query.first():
        db.session.add_all([
            FAQ(question="¿Puedo editar el contenido del sitio?", answer="Sí. El panel admin permite modificar textos, imágenes, servicios, planes, SEO y mensajes.", order=1),
            FAQ(question="Los mensajes del formulario se guardan?", answer="Si. Cada mensaje queda almacenado en SQLite y se consulta desde el panel admin.", order=2),
            FAQ(question="Se puede desplegar en Render?", answer="Si. El proyecto incluye Procfile, requirements.txt y render.yaml.", order=3),
        ])

    if not SocialLink.query.first():
        for name, icon in [("Facebook", "fa-brands fa-facebook-f"), ("Instagram", "fa-brands fa-instagram"), ("LinkedIn", "fa-brands fa-linkedin-in"), ("TikTok", "fa-brands fa-tiktok"), ("YouTube", "fa-brands fa-youtube")]:
            db.session.add(SocialLink(name=name, icon=icon, url="#"))

    if not Skill.query.first():
        skill_names = [
            "Desarrollo de Software", "Ciberseguridad", "Inteligencia Artificial", 
            "Infraestructura Cloud", "Automatización Industrial", "Análisis de Datos",
            "Seguridad de Redes", "DevOps", "Consultoría IT", "Soporte Crítico"
        ]
        for index, name in enumerate(skill_names, start=1):
            db.session.add(Skill(name=name, icon="fa-solid fa-microchip", order=index))

    if not Certificate.query.first():
        certificates = [
            ("Implementación de sistemas empresariales", "AFCyber SOLUTIONS", ""),
            ("Servicios técnicos y digitales", "AFCyber SOLUTIONS", ""),
            ("Soporte e instalacion profesional", "AFCyber SOLUTIONS", ""),
        ]
        for index, (name, issuer, year) in enumerate(certificates, start=1):
            db.session.add(Certificate(name=name, issuer=issuer, year=year, order=index))

    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1")
