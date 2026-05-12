import os
import secrets
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from extensions import db, login_manager
from models import (
    AboutSection,
    CEOProfile,
    ContactMessage,
    FAQ,
    HeroSection,
    Plan,
    PortfolioProject,
    Service,
    SiteSettings,
    SocialLink,
    Testimonial,
    User,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
ALLOWED_IMAGES = {"jpg", "jpeg", "png", "webp", "svg"}
ALLOWED_DOCS = {"pdf"}


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'afcyber_platform.db'}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

    (BASE_DIR / "instance").mkdir(exist_ok=True)
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    register_filters(app)
    register_security(app)
    register_routes(app)

    with app.app_context():
        db.create_all()
        seed_database()

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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


def allowed_file(filename, allow_pdf=False):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in (ALLOWED_IMAGES | (ALLOWED_DOCS if allow_pdf else set()))


def save_upload(file, allow_pdf=False):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename, allow_pdf=allow_pdf):
        flash("Archivo no permitido. Usa imagen jpg, jpeg, png, webp, svg o PDF cuando aplique.", "danger")
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    safe_name = secure_filename(file.filename.rsplit(".", 1)[0])[:64] or "archivo"
    filename = f"{safe_name}-{uuid4().hex[:10]}.{ext}"
    file.save(UPLOAD_FOLDER / filename)
    return filename


def seed_database():
    settings = get_settings()
    get_hero()
    get_about()
    get_ceo()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@afcybersolutions.com.do")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin12345!")
    if not User.query.filter_by(email=admin_email).first():
        user = User(email=admin_email, name="Administrador AFCyber")
        user.set_password(admin_password)
        db.session.add(user)

    if Service.query.count() == 0:
        services = [
            ("Desarrollo web", "Paginas corporativas premium, landing pages, sitios rapidos y experiencias digitales responsive.", "fa-solid fa-laptop-code"),
            ("Ciberseguridad basica", "Revision inicial, buenas practicas, proteccion de cuentas, endpoints y orientacion preventiva.", "fa-solid fa-shield-halved"),
            ("Soporte tecnico", "Asistencia remota y presencial para usuarios, equipos, software y continuidad operativa.", "fa-solid fa-headset"),
            ("Camaras de seguridad", "Instalacion y configuracion de camaras IP, analogicas, DVR/NVR y acceso remoto.", "fa-solid fa-video"),
            ("Redes empresariales", "Cableado, configuracion, optimizacion y documentacion de redes para empresas.", "fa-solid fa-network-wired"),
            ("Correos corporativos", "Correos profesionales, dominios, firmas, configuracion y seguridad basica.", "fa-solid fa-envelope-circle-check"),
            ("Sistemas POS", "Sistemas para ventas, inventario, usuarios, reportes y control comercial.", "fa-solid fa-cash-register"),
            ("Sistemas CMMS", "Gestion de activos, mantenimiento, tecnicos, ordenes de trabajo e historial.", "fa-solid fa-screwdriver-wrench"),
            ("Sistemas de citas", "Agenda digital, reservas, confirmaciones y gestion de clientes.", "fa-solid fa-calendar-check"),
            ("Automatizacion de procesos", "Flujos digitales, reportes, herramientas internas y reduccion de tareas repetitivas.", "fa-solid fa-gears"),
        ]
        for index, (name, description, icon) in enumerate(services, 1):
            db.session.add(Service(name=name, description=description, icon=icon, position=index))

    if Plan.query.count() == 0:
        plans = [
            ("Plan Basico", "A cotizar", "Presencia digital inicial para negocios que necesitan una pagina profesional.", "Pagina informativa\nBoton de WhatsApp\nDiseno responsive\nSEO inicial", False, 1),
            ("Plan Profesional", "A cotizar", "Web avanzada para marcas que buscan una presencia premium y mejor captacion.", "Pagina avanzada\nDominio y hosting\nSEO basico\nSecciones corporativas\nIntegracion WhatsApp", True, 2),
            ("Plan Empresarial", "A cotizar", "Soluciones a medida para operaciones que requieren sistemas, paneles o automatizacion.", "Sistema personalizado\nPanel administrativo\nAutomatizacion\nSoporte tecnico\nReportes", False, 3),
        ]
        for name, price, description, features, featured, position in plans:
            db.session.add(Plan(name=name, price=price, description=description, features=features, is_featured=featured, position=position))

    if PortfolioProject.query.count() == 0:
        projects = [
            ("BarberShop", "Landing page moderna para reservas, servicios y contacto directo.", "Landing page", "HTML, CSS, JavaScript"),
            ("Sistema POS", "Control de ventas, inventario, usuarios y reportes.", "Sistema", "Flask, SQLite, Bootstrap"),
            ("Sistema CMMS", "Gestion de mantenimiento, activos y ordenes de trabajo.", "Gestion", "Python, Flask, SQLite"),
            ("Catalogos digitales", "Presentacion digital profesional para servicios y promociones.", "Digital", "HTML, CSS, JS"),
            ("Landing pages", "Paginas enfocadas en conversion y captacion de clientes.", "Marketing", "Bootstrap, SEO"),
            ("Sistemas empresariales", "Herramientas internas para controlar procesos y reportes.", "Empresarial", "Flask, Render, GitHub"),
        ]
        for name, description, category, technologies in projects:
            db.session.add(PortfolioProject(name=name, description=description, category=category, technologies=technologies))

    if Testimonial.query.count() == 0:
        db.session.add(Testimonial(client_name="Cliente comercial", company="Servicios profesionales", comment="La presencia digital quedo moderna, rapida y lista para captar clientes por WhatsApp.", stars=5))
        db.session.add(Testimonial(client_name="Gerente operativo", company="Empresa local", comment="AFCyber SOLUTIONS nos ayudo a organizar procesos y entender que solucion necesitaba el negocio.", stars=5))
        db.session.add(Testimonial(client_name="Emprendedor", company="Marca digital", comment="Excelente trato, diseno muy profesional y soporte claro durante todo el proceso.", stars=5))

    if FAQ.query.count() == 0:
        faqs = [
            ("Que servicios ofrece AFCyber SOLUTIONS?", "Ofrecemos desarrollo web, POS, CMMS, soporte tecnico, redes, camaras, correos, ciberseguridad basica y automatizacion.", 1),
            ("Puedo solicitar un sistema personalizado?", "Si. Evaluamos el proceso, definimos alcance y construimos una solucion ajustada a la operacion.", 2),
            ("La web se puede editar desde admin?", "Si. Esta plataforma permite editar contenido, servicios, planes, portafolio, FAQ, SEO, redes y mensajes.", 3),
            ("Se puede desplegar en Render?", "Si. El proyecto incluye Procfile, render.yaml y gunicorn para despliegue.", 4),
        ]
        for question, answer, position in faqs:
            db.session.add(FAQ(question=question, answer=answer, position=position))

    if SocialLink.query.count() == 0:
        db.session.add(SocialLink(name="LinkedIn", icon="fa-brands fa-linkedin-in", url="#", position=1))
        db.session.add(SocialLink(name="Instagram", icon="fa-brands fa-instagram", url="#", position=2))
        db.session.add(SocialLink(name="Facebook", icon="fa-brands fa-facebook-f", url="#", position=3))

    db.session.commit()
    return settings


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
            projects=PortfolioProject.query.filter_by(is_active=True).order_by(PortfolioProject.created_at.desc()).all(),
            testimonials=Testimonial.query.filter_by(is_active=True).order_by(Testimonial.created_at.desc()).all(),
            faqs=FAQ.query.filter_by(is_active=True).order_by(FAQ.position, FAQ.id).all(),
            social_links=SocialLink.query.filter_by(is_active=True).order_by(SocialLink.position, SocialLink.id).all(),
        )

    @app.post("/contact")
    def contact():
        required = ["name", "phone", "message"]
        if any(not request.form.get(field, "").strip() for field in required):
            flash("Completa nombre, telefono y mensaje.", "danger")
            return redirect(url_for("index") + "#contacto")
        db.session.add(ContactMessage(
            name=request.form["name"].strip(),
            company=request.form.get("company", "").strip(),
            phone=request.form["phone"].strip(),
            email=request.form.get("email", "").strip(),
            requested_service=request.form.get("requested_service", "").strip(),
            message=request.form["message"].strip(),
        ))
        db.session.commit()
        flash("Mensaje enviado correctamente. Te contactaremos pronto.", "success")
        return redirect(url_for("index") + "#contacto")

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if current_user.is_authenticated:
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            user = User.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
            if user and user.is_active_admin and user.check_password(request.form.get("password", "")):
                login_user(user)
                return redirect(url_for("admin_dashboard"))
            flash("Credenciales incorrectas.", "danger")
        return render_template("admin/login.html")

    @app.get("/admin/logout")
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
        }, messages=ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(6).all())

    register_admin_routes(app)


def register_admin_routes(app):
    @app.route("/admin/settings", methods=["GET", "POST"])
    @login_required
    def admin_settings():
        settings = get_settings()
        if request.method == "POST":
            text_fields = [
                "company_name", "slogan", "short_description", "main_email", "phone", "whatsapp", "address",
                "business_hours", "facebook", "instagram", "linkedin", "tiktok", "youtube", "primary_color",
                "secondary_color", "background_color", "button_color", "text_color", "meta_title",
                "meta_description", "meta_keywords", "google_analytics_id", "google_search_console",
                "footer_text", "copyright_text",
            ]
            for field in text_fields:
                setattr(settings, field, request.form.get(field, "").strip())
            for field in ["logo", "favicon", "og_image"]:
                uploaded = save_upload(request.files.get(field))
                if uploaded:
                    setattr(settings, field, uploaded)
            for field in ["dark_mode", "tech_gradients", "show_about", "show_ceo", "show_services", "show_plans", "show_portfolio", "show_testimonials", "show_faq", "show_contact"]:
                setattr(settings, field, checkbox_value(field))
            db.session.commit()
            flash("Configuracion actualizada.", "success")
            return redirect(url_for("admin_settings"))
        return render_template("admin/settings.html", settings=settings)

    @app.route("/admin/hero", methods=["GET", "POST"])
    @login_required
    def admin_hero():
        hero = get_hero()
        if request.method == "POST":
            for field in ["title", "subtitle", "description", "primary_button_text", "primary_button_url", "secondary_button_text", "secondary_button_message"]:
                setattr(hero, field, request.form.get(field, "").strip())
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
                setattr(about, field, request.form.get(field, "").strip())
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
            for field in ["full_name", "role", "tagline", "bio", "experience", "certifications", "skills", "linkedin", "whatsapp_message"]:
                setattr(ceo, field, request.form.get(field, "").strip())
            for field in ["projects_count", "clients_count", "systems_count", "experience_years"]:
                setattr(ceo, field, int(request.form.get(field) or 0))
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


def crud_routes(app):
    @app.route("/admin/services", methods=["GET", "POST"])
    @login_required
    def admin_services():
        if request.method == "POST":
            db.session.add(Service(
                name=request.form["name"].strip(),
                description=request.form["description"].strip(),
                icon=request.form.get("icon", "").strip() or "fa-solid fa-shield-halved",
                price=request.form.get("price", "").strip(),
                position=int(request.form.get("position") or 0),
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
            setattr(item, field, request.form.get(field, "").strip())
        item.position = int(request.form.get("position") or 0)
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
            db.session.add(Plan(
                name=request.form["name"].strip(),
                price=request.form.get("price", "").strip(),
                description=request.form["description"].strip(),
                features=request.form["features"].strip(),
                button_text=request.form.get("button_text", "Solicitar plan").strip(),
                position=int(request.form.get("position") or 0),
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
            setattr(item, field, request.form.get(field, "").strip())
        item.position = int(request.form.get("position") or 0)
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
                name=request.form["name"].strip(),
                description=request.form["description"].strip(),
                category=request.form.get("category", "").strip(),
                technologies=request.form.get("technologies", "").strip(),
                link=request.form.get("link", "").strip(),
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
            setattr(item, field, request.form.get(field, "").strip())
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
            db.session.add(Testimonial(
                client_name=request.form["client_name"].strip(),
                company=request.form.get("company", "").strip(),
                comment=request.form["comment"].strip(),
                stars=int(request.form.get("stars") or 5),
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
            setattr(item, field, request.form.get(field, "").strip())
        item.stars = int(request.form.get("stars") or 5)
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
            db.session.add(FAQ(question=request.form["question"].strip(), answer=request.form["answer"].strip(), position=int(request.form.get("position") or 0), is_active=checkbox_value("is_active")))
            db.session.commit()
            return redirect(url_for("admin_faq"))
        return render_template("admin/faq.html", items=FAQ.query.order_by(FAQ.position, FAQ.id).all())

    @app.post("/admin/faq/<int:item_id>")
    @login_required
    def update_faq(item_id):
        item = FAQ.query.get_or_404(item_id)
        item.question = request.form["question"].strip()
        item.answer = request.form["answer"].strip()
        item.position = int(request.form.get("position") or 0)
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
            db.session.add(SocialLink(name=request.form["name"].strip(), icon=request.form.get("icon", "").strip(), url=request.form["url"].strip(), position=int(request.form.get("position") or 0), is_active=checkbox_value("is_active")))
            db.session.commit()
            return redirect(url_for("admin_social"))
        return render_template("admin/social.html", items=SocialLink.query.order_by(SocialLink.position, SocialLink.id).all())

    @app.post("/admin/social/<int:item_id>")
    @login_required
    def update_social(item_id):
        item = SocialLink.query.get_or_404(item_id)
        for field in ["name", "icon", "url"]:
            setattr(item, field, request.form.get(field, "").strip())
        item.position = int(request.form.get("position") or 0)
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
            user = User(email=request.form["email"].strip().lower(), name=request.form.get("name", "").strip(), is_active_admin=checkbox_value("is_active_admin"))
            if request.form.get("password"):
                user.set_password(request.form["password"])
            else:
                user.set_password(secrets.token_urlsafe(12))
            db.session.add(user)
            db.session.commit()
            flash("Usuario creado.", "success")
            return redirect(url_for("admin_users"))
        return render_template("admin/users.html", items=User.query.order_by(User.created_at.desc()).all())

    @app.post("/admin/users/<int:item_id>")
    @login_required
    def update_user(item_id):
        item = User.query.get_or_404(item_id)
        item.email = request.form["email"].strip().lower()
        item.name = request.form.get("name", "").strip()
        item.is_active_admin = checkbox_value("is_active_admin")
        if request.form.get("password"):
            item.set_password(request.form["password"])
        db.session.commit()
        flash("Usuario actualizado.", "success")
        return redirect(url_for("admin_users"))


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
