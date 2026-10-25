"""Public, deterministic knowledge retrieval. No remote AI or private records."""

import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, session, url_for

from models import FAQ, Plan, Program, Service, SiteSettings


ROOT = Path(__file__).resolve().parent
FALLBACK = (
    "No tengo información suficiente para responder con precisión. "
    "Puedo ayudarte a solicitar una cotización o comunicarte con un asesor de AFCyber Solutions."
)
STATUSES = {"DISPONIBLE", "EN_DESARROLLO", "PROXIMAMENTE", "NO_CONFIRMADO"}


def normalize(value):
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        "".join(
            char
            for char in unicodedata.normalize("NFKD", value.lower())
            if not unicodedata.combining(char)
        ),
    ).strip()


def products():
    """Return only the public product catalogue and eligible published programs."""
    data = json.loads((ROOT / "static/data/products.json").read_text(encoding="utf-8"))
    result = []
    for raw in data["products"]:
        product = dict(raw)
        if product["commercial_status"] not in STATUSES:
            product["commercial_status"] = "NO_CONFIRMADO"
        if product.get("image") and not (
            product["image"].startswith("/static/")
            and ".." not in product["image"]
            and (ROOT / product["image"].lstrip("/")).is_file()
        ):
            product["image"] = ""
        result.append(product)

    known = {normalize(product["name"]) for product in result}
    from flask import current_app

    storage = Path(current_app.config["PRIVATE_STORAGE_ROOT"])
    for program in (
        Program.query.filter_by(is_active=True, status="publicado", deleted_at=None)
        .order_by(Program.id)
        .all()
    ):
        target = (storage / (program.file_path or "")).resolve()
        external = (program.external_url or "").startswith("https://")
        if not external and (
            not program.file_path
            or not target.is_relative_to(storage)
            or not target.is_file()
        ):
            continue
        if normalize(program.name) in known:
            continue
        result.append(
            dict(
                id="programa-" + program.slug,
                name=program.name,
                description=program.short_description,
                category=program.category,
                main_function=program.short_description,
                features=[],
                modules=[],
                benefits=[],
                recommended_business=program.target_business or "",
                platform=program.operating_system or "",
                requirements=program.requirements or "",
                commercial_status="NO_CONFIRMADO",
                license=program.license_type
                if program.license_type not in {"A definir", "Por definir"}
                else "",
                support_email="soporte@afcybersolutions.com.do",
                url=url_for("program_detail", slug=program.slug),
                image=url_for("public_media", filename=program.image)
                if program.image
                else "",
                quote_available=True,
                icon="fa-box",
                keywords=[program.name, program.category],
                sources=["Catálogo público de descargas"],
            )
        )
    return result


def service_groups():
    return json.loads((ROOT / "static/data/service-groups.json").read_text(encoding="utf-8"))


def knowledge():
    company = json.loads((ROOT / "static/data/company.json").read_text(encoding="utf-8"))
    settings = SiteSettings.query.first()
    services = [
        dict(
            id=service.id,
            name=service.name,
            description=service.description,
            url="/servicios",
            sources=["Catálogo público de servicios"],
        )
        for service in Service.query.filter_by(is_active=True).order_by(Service.position, Service.id)
    ]
    services += [
        dict(
            id=group["id"],
            name=group["name"],
            description=group["description"],
            url=group["source"],
            sources=[group["source"]],
        )
        for group in service_groups()
    ]
    faqs = [
        dict(question=faq.question, answer=faq.answer, url="/preguntas-frecuentes")
        for faq in FAQ.query.filter_by(is_active=True).order_by(FAQ.position, FAQ.id)
    ]
    plans = [
        dict(
            name=plan.name,
            description=plan.description,
            features=plan.features.splitlines(),
            price=plan.price,
        )
        for plan in Plan.query.filter_by(is_active=True).order_by(Plan.position)
    ]
    public_facts = company.get("public_facts", {})
    return dict(
        company=dict(
            name=company["name"],
            description=company["summary"],
            who=company["who"],
            mission=company["mission"],
            vision=company["vision"],
            values=[value["name"] for value in company["values"]],
            quality=company["quality"],
            location=settings.address if settings else "San Cristóbal, República Dominicana",
            history=public_facts.get("history"),
            published_hours=public_facts.get("published_hours"),
            contacts=company["contacts"],
            founder=public_facts.get("founder"),
            phone=public_facts.get("phone"),
            website="https://" + company["domain"] + "/",
            source="/nosotros",
        ),
        products=products(),
        services=services,
        faqs=faqs,
        plans=plans,
    )


def product_score(query, product):
    tokens = query.split()
    aliases = [normalize(product["name"])] + [normalize(keyword) for keyword in product["keywords"]]
    score = 0.0
    for alias in aliases:
        if alias in query:
            score = max(score, 1.0 if len(alias) > 5 else 0.82)
        for word in tokens:
            if len(word) >= 5 and " " not in alias:
                score = max(
                    score,
                    max(
                        (
                            SequenceMatcher(None, word, candidate).ratio()
                            for candidate in alias.split()
                            if len(candidate) >= 5
                        ),
                        default=0,
                    )
                    * 0.85,
                )
    return score


def respond(message, context=None):
    kb = knowledge()
    query = normalize(message)
    answer = dict(
        text=FALLBACK,
        products=[],
        services=[],
        categories=[],
        comparison=[],
        links=[
            dict(label="Solicitar cotización", url="/cotizacion"),
            dict(label="Contactar con un asesor", url="/contacto"),
        ],
        sources=[],
    )
    product_list = kb["products"]
    context = [product for product in product_list if product["id"] in (context or [])][:2]
    if any(word in query.split() for word in ["secretos", "password", "contrasena", "credenciales", "administrativa"]):
        return answer
    if query.startswith("categoria "):
        category = query.removeprefix("categoria ")
        answer.update(
            text="Información publicada de esta categoría.",
            products=[product for product in product_list if normalize(product["category"]) == category],
            sources=["Catálogo público compartido"],
        )
        return answer
    if query in {"productos", "nuestros productos", "explorar productos", "catalogo", "catalogo de productos"}:
        answer.update(
            text="Explora las categorías publicadas. La disponibilidad comercial se confirma con un asesor.",
            categories=sorted({product["category"] for product in product_list}),
            products=product_list,
            sources=["Catálogo público compartido"],
        )
        return answer
    if query in {"planes", "planes y precios", "paquetes", "precios de planes"}:
        answer.update(
            text="Planes publicados: "
            + "\n".join(
                product["name"] + ": " + product["price"] + ". " + product["description"]
                for product in kb["plans"]
            ),
            sources=["/servicios#planes"],
        )
        return answer

    matches = sorted(
        [(product_score(query, product), product) for product in product_list],
        key=lambda pair: pair[0],
        reverse=True,
    )
    relevant = [product for score, product in matches if score >= 0.74][:2]
    comparing = any(word in query for word in ["compar", "diferencia", "versus"]) or " vs " in " " + query + " "
    if comparing:
        selected = relevant if len(relevant) == 2 else context if len(context) == 2 else []
        if len(selected) != 2:
            answer["text"] = "Indica los nombres de dos productos para comparar su información publicada."
            return answer
        rows = [
            ("Finalidad", "main_function"),
            ("Tipo de negocio", "recommended_business"),
            ("Plataforma", "platform"),
            ("Características verificadas", "features"),
            ("Licencia publicada", "license"),
            ("Estado comercial", "commercial_status"),
        ]
        answer.update(
            text="Comparación de información publicada. Los campos sin confirmar se indican expresamente.",
            products=selected,
            comparison=[
                dict(
                    label=label,
                    values=[
                        (" · ".join(product[key]) if isinstance(product[key], list) else product[key])
                        or "No publicado / no confirmado"
                        for product in selected
                    ],
                )
                for label, key in rows
            ],
            sources=["Catálogo público compartido"],
        )
        return answer
    if not relevant and context and any(
        word in query
        for word in ["caracteristica", "funcion", "plataforma", "precio", "licencia", "requisito", "soporte", "disponib"]
    ):
        relevant = context
    if relevant:
        text = "Encontré información publicada sobre estas soluciones. Confirma alcance y disponibilidad con un asesor."
        if any(word in query for word in ["precio", "cuesta", "licencia", "disponib", "requisito"]):
            text = "La ficha muestra únicamente los datos publicados. Si el precio, licencia, requisitos o disponibilidad no aparecen, requieren confirmación con un asesor."
        if any(word in query for word in ["negocio", "ferreteria", "tienda", "necesito", "busco", "quiero"]):
            text = "Estas funciones publicadas se relacionan con tu necesidad: " + "; ".join(
                product["main_function"] for product in relevant
            )
            if "inventario" in query and any(product["id"] == "multinegocios" for product in relevant):
                text += " El control de inventario de MultiNegocios no está confirmado en su ficha; podemos evaluar un sistema POS/ERP o software a medida."
        answer.update(text=text, products=relevant, sources=["Catálogo público compartido"])
        return answer

    company = kb["company"]
    topics = [
        ("mision", company["mission"]),
        ("vision", company["vision"]),
        ("valores", ", ".join(company["values"])),
        ("calidad", "\n".join(company["quality"])),
        ("historia", company["history"] or "No hay una historia cronológica publicada en las fuentes consultadas."),
        ("horario", company["published_hours"] or "No hay un horario publicado confirmado en las páginas consultadas. Contacta con un asesor."),
        ("fundador", (company["founder"] or "No confirmado") + ", fundador y CEO de AFCyber Solutions."),
        ("ubicacion", company["location"]),
        ("direccion", company["location"]),
        ("donde", company["location"]),
    ]
    for term, text in topics:
        if term in query:
            answer.update(text=text, sources=[company["source"]])
            return answer
    if any(term in query for term in ["contacto", "asesor", "telefono", "correo", "whatsapp", "licencias"]):
        answer.update(
            text="Contactos públicos: "
            + "; ".join(contact["name"] + ": " + contact["email"] for contact in company["contacts"])
            + ". WhatsApp: "
            + (company["phone"] or "Consulta la página de contacto"),
            sources=["/contacto"],
        )
        return answer
    if any(term in query for term in ["cotizacion", "presupuesto", "cotizar"]):
        answer.update(
            text="Puedes registrar tu necesidad en el formulario de cotización. El equipo revisará el alcance; no se calcula un precio sin información verificada.",
            sources=["/cotizacion"],
        )
        return answer
    if query in {"empresa", "afcyber", "afcyber solutions"} or any(
        term in query for term in ["conocer afcyber", "sobre la empresa", "acerca de la empresa", "quienes son", "quienes somos"]
    ):
        answer.update(text="\n".join(company["who"]), sources=[company["source"]])
        return answer

    aliases = {
        "camaras": "cctv",
        "videovigilancia": "cctv",
        "seguridad": "ciberseguridad",
        "reparacion": "mantenimiento",
        "soporte": "mantenimiento",
        "programacion": "software",
        "paginas": "web",
    }
    terms = set(query.split())
    terms |= {value for key, value in aliases.items() if key in terms}
    ignored = {"de", "la", "el", "los", "las", "un", "una", "que", "para", "y", "con", "necesito", "servicio", "servicios"}
    ranked = []
    for service in kb["services"]:
        words = set(normalize(service["name"] + " " + service["description"]).split()) - ignored
        score = len((terms - ignored) & words)
        fuzzy = max(
            (
                SequenceMatcher(None, term, word).ratio()
                for term in terms
                for word in words
                if len(term) > 5 and len(word) > 5
            ),
            default=0,
        )
        if score >= 1 or fuzzy >= 0.88:
            ranked.append((score + fuzzy, service))
    if ranked or query in {"servicios", "nuestros servicios"}:
        services = (
            [service for _, service in sorted(ranked, key=lambda item: item[0], reverse=True)[:3]]
            if ranked
            else kb["services"]
        )
        answer.update(
            text="Servicios publicados relacionados con tu consulta. Podemos evaluar tu alcance mediante una cotización.",
            services=services,
            sources=["/servicios"],
        )
        return answer
    for faq in kb["faqs"]:
        faq_question = normalize(faq["question"])
        overlap = len(set(query.split()) & (set(faq_question.split()) - ignored))
        if SequenceMatcher(None, query, faq_question).ratio() >= 0.75 or overlap >= 3:
            answer.update(text=faq["answer"], sources=[faq["url"]])
            return answer
    return answer


def register_assistant(app, rate_limit):
    blueprint = Blueprint("assistant", __name__)

    @app.context_processor
    def shared_products():
        return {"public_products": products(), "public_service_groups": service_groups()}

    @blueprint.get("/productos/<product_id>")
    def product_detail(product_id):
        from flask import abort

        product = next((item for item in products() if item["id"] == product_id), None)
        if not product:
            abort(404)
        return render_template(
            "public/product-detail.html",
            product=product,
            page_title=product["name"] + " | AFCyber Solutions",
        )

    @blueprint.post("/asistente/responder")
    def reply():
        if not rate_limit("assistant", 30, 60):
            return jsonify(error="Has enviado muchas preguntas. Espera un minuto."), 429, {"Retry-After": "60"}
        message = request.form.get("message", "").strip()
        if not message or len(message) > 600:
            return jsonify(error="Escribe entre 1 y 600 caracteres."), 422
        import time

        context = (
            session.get("assistant_context", [])
            if time.time() - session.get("assistant_context_at", 0) < 600
            else []
        )
        response = respond(message, context)
        if response["products"]:
            session["assistant_context"] = [product["id"] for product in response["products"]][:2]
            session["assistant_context_at"] = time.time()
        return jsonify(response), 200, {"Cache-Control": "no-store"}

    @blueprint.get("/asistente/catalogo")
    def catalog():
        if not rate_limit("assistant-catalog", 30, 60):
            return jsonify(error="Espera un minuto."), 429
        product_list = products()
        return jsonify(products=product_list, categories=sorted({product["category"] for product in product_list}))

    app.register_blueprint(blueprint)
