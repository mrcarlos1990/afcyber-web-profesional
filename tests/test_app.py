import io
import os
import shutil
import tempfile
import unittest
import zipfile
from datetime import timedelta
from pathlib import Path

from sqlalchemy.exc import IntegrityError


TEST_STORAGE_ROOT = tempfile.mkdtemp(prefix="afcyber-test-storage-")

os.environ["SECRET_KEY"] = "test-secret-key-with-more-than-32-characters"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "StrongAdmin123"
os.environ["FLASK_DEBUG"] = "1"
os.environ["AUTO_CREATE_DB"] = "1"
os.environ["PRIVATE_STORAGE_ROOT"] = TEST_STORAGE_ROOT
os.environ["BASE_URL"] = "http://localhost"

import app as app_module
from extensions import db
from models import (
    AdminAuditEvent,
    AndroidAppVersion,
    Attachment,
    ContactMessage,
    DocumentVersion,
    DownloadEvent,
    ElectronicSignature,
    EmailDelivery,
    Manual,
    Program,
    ServiceDocument,
    ServiceRequest,
    SignatureRequest,
    User,
    utc_now,
)


def tearDownModule():
    shutil.rmtree(TEST_STORAGE_ROOT, ignore_errors=True)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = app_module.app
        self.app.config.update(TESTING=True)
        self.original_apksigner = app_module.shutil.which
        app_module.shutil.which = lambda name: None if name == "apksigner" else self.original_apksigner(name)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            app_module.seed_database()

    def tearDown(self):
        app_module.shutil.which = self.original_apksigner

    def csrf_token(self, path="/"):
        self.client.get(path)
        with self.client.session_transaction() as sess:
            return sess["_csrf_token"]

    def login(self):
        token = self.csrf_token("/admin/login")
        return self.client.post(
            "/admin/login",
            data={
                "_csrf_token": token,
                "email": "admin@example.com",
                "password": "StrongAdmin123",
            },
        )

    def submit_service_request(self):
        token = self.csrf_token("/solicitar-servicio")
        return self.client.post(
            "/solicitar-servicio",
            data={
                "_csrf_token": token,
                "full_name": "Cliente Prueba",
                "email": "cliente@example.com",
                "phone": "8090000000",
                "requested_service": "Soporte tecnico",
                "need_description": "Necesito revisar varios equipos.",
                "modality": "Remoto",
                "priority": "Normal",
                "accepted_privacy": "on",
                "accepted_contact": "on",
                "accepted_e_signature": "on",
                "confirmed_accuracy": "on",
            },
        )

    def apk_bytes(self, package_name="do.afcyber.prestamos"):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w") as archive:
            archive.writestr("AndroidManifest.xml", f"<manifest package='{package_name}' />")
            archive.writestr("classes.dex", b"dex\n035\0")
        payload.seek(0)
        return payload.getvalue()

    def upload_android_apk(self, version="1.0.0", publish=True, content=None, filename="app-release.apk"):
        self.login()
        token = self.csrf_token("/admin/applications/afcyber-prestamos")
        return self.client.post(
            "/admin/applications/afcyber-prestamos",
            data={
                "_csrf_token": token,
                "version": version,
                "published_on": "2026-10-23",
                "min_sdk": "26",
                "description": "Versión administrativa para operaciones de crédito.",
                "release_notes": "Versión release verificada antes de cargar.",
                "is_public": "on" if publish else "",
                "apk_file": (io.BytesIO(content if content is not None else self.apk_bytes()), filename),
            },
            content_type="multipart/form-data",
        )

    def prepare_signature_token(self, token_value="test-token", otp_value="123456"):
        self.submit_service_request()
        with self.app.app_context():
            signature = SignatureRequest.query.filter_by(signer_role="cliente").first()
            signature.token_hash = app_module.hash_token(token_value)
            signature.otp_hash = app_module.hash_token(otp_value)
            signature.otp_expires_at = utc_now() + timedelta(minutes=10)
            db.session.commit()
        return token_value, otp_value

    def sign_client(self, token_value="test-token", otp_value="123456"):
        token = self.csrf_token(f"/firmar/{token_value}")
        return self.client.post(
            f"/firmar/{token_value}",
            data={
                "_csrf_token": token,
                "signature_text": "Cliente Prueba",
                "otp": otp_value,
                "consent": "on",
            },
        )

    def test_runtime_is_isolated_from_real_database_and_private_storage(self):
        self.assertEqual(self.app.config["SQLALCHEMY_DATABASE_URI"], "sqlite:///:memory:")
        self.assertEqual(Path(app_module.PRIVATE_STORAGE), Path(TEST_STORAGE_ROOT).resolve())
        with self.app.app_context():
            self.assertEqual(ServiceRequest.query.count(), 0)

    def test_public_admin_contact_and_seo_routes(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/descargas").status_code, 200)
        self.assertEqual(self.client.get("/solicitar-servicio").status_code, 200)
        self.assertEqual(self.client.get("/productos/afcyber-prestamos").status_code, 200)
        self.assertEqual(self.client.get("/privacidad/afcyber-prestamos").status_code, 200)
        self.assertEqual(self.client.get("/eliminar-datos/afcyber-prestamos").status_code, 200)
        self.assertIn("Sitemap:", self.client.get("/robots.txt").get_data(as_text=True))
        sitemap = self.client.get("/sitemap.xml").get_data(as_text=True)
        self.assertIn("<urlset", sitemap)
        self.assertIn("/productos/afcyber-prestamos", sitemap)
        self.assertIn("/privacidad/afcyber-prestamos", sitemap)
        self.assertIn("/eliminar-datos/afcyber-prestamos", sitemap)
        self.assertEqual(self.client.get("/no-existe").status_code, 404)

        response = self.client.post("/contact", data={"name": "Ana", "phone": "8090000000", "message": "Hola"})
        self.assertEqual(response.status_code, 400)
        token = self.csrf_token("/")
        response = self.client.post(
            "/contact",
            data={
                "_csrf_token": token,
                "name": "Ana",
                "phone": "8090000000",
                "email": "ana@example.com",
                "message": "Hola",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(ContactMessage.query.count(), 1)

    def test_afcyber_prestamos_legal_pages_content_seo_and_links(self):
        privacy = self.client.get("/privacidad/afcyber-prestamos")
        deletion = self.client.get("/eliminar-datos/afcyber-prestamos")
        self.assertEqual(privacy.status_code, 200)
        self.assertEqual(deletion.status_code, 200)
        privacy_html = privacy.get_data(as_text=True)
        deletion_html = deletion.get_data(as_text=True)

        self.assertIn("<title>Política de Privacidad | AFCyber Préstamos Enterprise</title>", privacy_html)
        self.assertIn(
            '<meta name="description" content="Política de privacidad de AFCyber Préstamos Enterprise. Información sobre almacenamiento local, seguridad, licenciamiento, cámara QR, Bluetooth, respaldos y eliminación de datos.">',
            privacy_html,
        )
        self.assertIn(
            '<link rel="canonical" href="https://afcybersolutions.com.do/privacidad/afcyber-prestamos">',
            privacy_html,
        )
        self.assertIn("Política de Privacidad — AFCyber Préstamos Enterprise", privacy_html)
        self.assertIn("La base de datos comercial local no cuenta actualmente con cifrado integral propio de la base de datos.", privacy_html)
        self.assertIn("Consultar instrucciones para eliminar los datos de AFCyber Préstamos Enterprise", privacy_html)
        self.assertIn('mailto:soporte@afcybersolutions.com.do', privacy_html)
        self.assertIn('mailto:info@afcybersolutions.com.do', privacy_html)
        self.assertIn("https://afcybersolutions.com.do/", privacy_html)

        self.assertIn("<title>Eliminación de Datos | AFCyber Préstamos Enterprise</title>", deletion_html)
        self.assertIn(
            '<meta name="description" content="Información e instrucciones para eliminar los datos almacenados localmente por AFCyber Préstamos Enterprise.">',
            deletion_html,
        )
        self.assertIn(
            '<link rel="canonical" href="https://afcybersolutions.com.do/eliminar-datos/afcyber-prestamos">',
            deletion_html,
        )
        self.assertIn("Eliminación de Datos — AFCyber Préstamos Enterprise", deletion_html)
        self.assertIn("La eliminación es irreversible respecto de los datos locales afectados.", deletion_html)
        self.assertIn("Ver Política de Privacidad de AFCyber Préstamos Enterprise", deletion_html)
        self.assertIn('mailto:soporte@afcybersolutions.com.do', deletion_html)
        self.assertIn('mailto:info@afcybersolutions.com.do', deletion_html)
        self.assertIn("https://afcybersolutions.com.do/", deletion_html)

        combined = privacy_html + deletion_html
        self.assertNotRegex(combined, r"soporte@afcybersolutions\.com(?!\.do)")
        self.assertNotRegex(combined, r"https?://(?:www\.)?afcybersolutions\.com(?!\.do)")
        self.assertNotIn("www.afcybersolutions.com.do", combined)

    def test_product_page_without_public_apk_has_no_broken_download(self):
        response = self.client.get("/productos/afcyber-prestamos")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("<title>AFCyber Préstamos Enterprise para Android | AFCyber Solutions</title>", html)
        self.assertIn("Descarga no publicada", html)
        self.assertNotIn('/descargar/afcyber-prestamos/android"', html)
        self.assertIn("/privacidad/afcyber-prestamos", html)
        self.assertIn("/eliminar-datos/afcyber-prestamos", html)
        self.assertIn("mailto:soporte@afcybersolutions.com.do", html)
        self.assertIn("mailto:info@afcybersolutions.com.do", html)
        self.assertIn("https://afcybersolutions.com.do/", html)

    def test_android_admin_requires_auth_and_rejects_invalid_files(self):
        self.assertIn("/admin/login", self.client.get("/admin/applications/afcyber-prestamos").headers["Location"])
        self.login()
        token = self.csrf_token("/admin/applications/afcyber-prestamos")
        for filename, content in [("not-apk.txt", b"not an apk"), ("empty.apk", b""), ("invalid.apk", b"not a zip")]:
            response = self.client.post(
                "/admin/applications/afcyber-prestamos",
                data={"_csrf_token": token, "version": "1.0.0", "apk_file": (io.BytesIO(content), filename)},
                content_type="multipart/form-data",
            )
            self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(AndroidAppVersion.query.count(), 0)

    def test_android_apk_upload_publishes_sha256_and_downloads_private_file(self):
        content = self.apk_bytes("do.afcyber.v100")
        response = self.upload_android_apk(version="1.0.0", content=content)
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            item = AndroidAppVersion.query.one()
            self.assertTrue(item.is_public)
            self.assertEqual(item.status, "publicado")
            self.assertEqual(item.file_size, len(content))
            self.assertEqual(item.sha256, app_module.sha256_bytes(content))
            self.assertTrue(item.file_path.startswith("android-apks/afcyber-prestamos/"))
            self.assertNotIn("static", item.file_path)
            self.assertTrue(app_module.private_path(item.file_path).is_file())
            self.assertEqual(AdminAuditEvent.query.filter_by(action="android_apk_uploaded").count(), 1)

        product = self.client.get("/productos/afcyber-prestamos").get_data(as_text=True)
        self.assertIn("v1.0.0", product)
        self.assertIn("Android 8.0 o superior", product)
        self.assertIn(app_module.sha256_bytes(content), product)
        self.assertIn("Descripción de la versión", product)

        download = self.client.get("/descargar/afcyber-prestamos/android")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.data, content)
        self.assertEqual(download.mimetype, "application/vnd.android.package-archive")
        self.assertIn("AFCyber-Prestamos-Enterprise-v1.0.0.apk", download.headers["Content-Disposition"])
        self.assertNotIn("..", download.headers["Content-Disposition"])
        self.assertNotIn("/", download.headers["Content-Disposition"])
        download.close()
        with self.app.app_context():
            self.assertEqual(DownloadEvent.query.filter_by(item_type="android_apk").count(), 1)

    def test_android_private_version_is_not_downloadable_and_only_one_is_public(self):
        first = self.upload_android_apk(version="1.0.0", publish=False, content=self.apk_bytes("do.afcyber.v100"))
        self.assertEqual(first.status_code, 302)
        self.assertEqual(self.client.get("/descargar/afcyber-prestamos/android").status_code, 404)
        second = self.upload_android_apk(version="1.0.1", publish=True, content=self.apk_bytes("do.afcyber.v101"))
        self.assertEqual(second.status_code, 302)
        with self.app.app_context():
            versions = AndroidAppVersion.query.order_by(AndroidAppVersion.version).all()
            self.assertEqual(len(versions), 2)
            self.assertFalse(versions[0].is_public)
            self.assertEqual(versions[0].status, "anterior")
            self.assertTrue(versions[1].is_public)
            versions[1].file_path = "../outside.apk"
            db.session.commit()
        self.assertEqual(self.client.get("/descargar/afcyber-prestamos/android").status_code, 404)

    def test_android_admin_can_update_and_unpublish_without_deleting_file(self):
        self.assertEqual(self.upload_android_apk(content=self.apk_bytes("do.afcyber.edit")).status_code, 302)
        with self.app.app_context():
            item = AndroidAppVersion.query.one()
            item_id = item.id
            stored_path = item.file_path
            original_hash = item.sha256
        token = self.csrf_token("/admin/applications/afcyber-prestamos")
        response = self.client.post(
            f"/admin/applications/afcyber-prestamos/{item_id}",
            data={
                "_csrf_token": token,
                "version": "1.0.1",
                "published_on": "2026-10-23",
                "min_sdk": "26",
                "status": "publicado",
                "description": "Descripción actualizada.",
                "release_notes": "Correcciones de estabilidad.",
                "is_public": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            item = AndroidAppVersion.query.get(item_id)
            self.assertEqual(item.version, "1.0.1")
            self.assertEqual(item.sha256, original_hash)
            self.assertTrue(app_module.private_path(stored_path).is_file())
            self.assertEqual(item.description, "Descripción actualizada.")
        token = self.csrf_token("/admin/applications/afcyber-prestamos")
        response = self.client.post(
            f"/admin/applications/afcyber-prestamos/{item_id}/unpublish",
            data={"_csrf_token": token},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/descargar/afcyber-prestamos/android").status_code, 404)
        with self.app.app_context():
            item = AndroidAppVersion.query.get(item_id)
            self.assertFalse(item.is_public)
            self.assertEqual(item.status, "borrador")
            self.assertTrue(app_module.private_path(item.file_path).is_file())
            self.assertEqual(AdminAuditEvent.query.filter_by(action="android_apk_unpublished").count(), 1)

    def test_android_cannot_publish_missing_file_or_unverified_signature_when_required(self):
        self.assertEqual(self.upload_android_apk(publish=False).status_code, 302)
        with self.app.app_context():
            item = AndroidAppVersion.query.one()
            item.file_path = "android-apks/afcyber-prestamos/missing.apk"
            db.session.commit()
            item_id = item.id
        token = self.csrf_token("/admin/applications/afcyber-prestamos")
        response = self.client.post(
            f"/admin/applications/afcyber-prestamos/{item_id}",
            data={
                "_csrf_token": token,
                "version": "1.0.0",
                "min_sdk": "26",
                "status": "publicado",
                "is_public": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            item = AndroidAppVersion.query.get(item_id)
            self.assertFalse(item.is_public)
            self.assertEqual(item.status, "borrador")

        with self.app.app_context():
            item.file_path = "android-apks/afcyber-prestamos/available.apk"
            Path(app_module.PRIVATE_STORAGE / item.file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(app_module.PRIVATE_STORAGE / item.file_path).write_bytes(self.apk_bytes())
            db.session.commit()
        previous_requirement = app_module.REQUIRE_APK_SIGNATURE
        app_module.REQUIRE_APK_SIGNATURE = True
        try:
            token = self.csrf_token("/admin/applications/afcyber-prestamos")
            response = self.client.post(
                f"/admin/applications/afcyber-prestamos/{item_id}",
                data={
                    "_csrf_token": token,
                    "version": "1.0.0",
                    "min_sdk": "26",
                    "status": "publicado",
                    "is_public": "on",
                },
            )
            self.assertEqual(response.status_code, 302)
            with self.app.app_context():
                item = AndroidAppVersion.query.get(item_id)
                self.assertFalse(item.is_public)
                self.assertEqual(item.status, "borrador")
        finally:
            app_module.REQUIRE_APK_SIGNATURE = previous_requirement

    def test_android_public_version_constraint_prevents_concurrent_duplicate_publication(self):
        with self.app.app_context():
            db.session.add_all([
                AndroidAppVersion(
                    uuid=app_module.make_uuid(),
                    app_slug="same-app",
                    version="1.0.0",
                    file_path="android-apks/one.apk",
                    sha256="a" * 64,
                    is_public=True,
                    status="publicado",
                ),
                AndroidAppVersion(
                    uuid=app_module.make_uuid(),
                    app_slug="same-app",
                    version="1.0.1",
                    file_path="android-apks/two.apk",
                    sha256="b" * 64,
                    is_public=True,
                    status="publicado",
                ),
            ])
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_admin_permissions_are_required(self):
        self.assertEqual(self.client.get("/admin/downloads").status_code, 302)
        self.assertIn("/admin/login", self.client.get("/admin/documents").headers["Location"])
        self.assertIn("/admin/login", self.client.get("/admin/applications/afcyber-prestamos").headers["Location"])
        self.login()
        with self.app.app_context():
            admin = User.query.filter_by(email="admin@example.com").first()
            admin.is_active_admin = False
            db.session.commit()
        self.assertEqual(self.client.get("/admin/applications/afcyber-prestamos").status_code, 403)

    def test_program_and_manual_downloads_use_private_storage_and_log_events(self):
        self.login()
        token = self.csrf_token("/admin/downloads")
        response = self.client.post(
            "/admin/downloads",
            data={
                "_csrf_token": token,
                "item_type": "program",
                "name": "Programa de prueba",
                "version": "1.0",
                "short_description": "Instalador temporal",
                "description": "Elemento temporal de prueba.",
                "status": "publicado",
                "is_active": "on",
                "program_file": (io.BytesIO(b"PK\x03\x04programa"), "programa.zip"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)
        token = self.csrf_token("/admin/downloads")
        response = self.client.post(
            "/admin/downloads",
            data={
                "_csrf_token": token,
                "item_type": "manual",
                "title": "Manual de prueba",
                "description": "Manual temporal de prueba.",
                "status": "publicado",
                "is_active": "on",
                "manual_file": (io.BytesIO(b"%PDF-1.4\nmanual"), "manual.pdf"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)
        program_response = self.client.get("/descargar/programa/programa-de-prueba")
        manual_response = self.client.get("/descargar/manual/manual-de-prueba")
        self.assertEqual(program_response.status_code, 200)
        self.assertEqual(manual_response.status_code, 200)
        program_response.close()
        manual_response.close()
        with self.app.app_context():
            program = Program.query.first()
            manual = Manual.query.first()
            self.assertTrue(program.file_path.startswith("installers/"))
            self.assertTrue(manual.file_path.startswith("manuals/"))
            self.assertNotIn("static", program.file_path)
            self.assertEqual(DownloadEvent.query.count(), 2)

    def test_service_request_generates_document_pdf_attachment_and_email_log(self):
        token = self.csrf_token("/solicitar-servicio")
        response = self.client.post(
            "/solicitar-servicio",
            data={
                "_csrf_token": token,
                "full_name": "Cliente Prueba",
                "email": "cliente@example.com",
                "phone": "8090000000",
                "requested_service": "Soporte tecnico",
                "need_description": "Necesito revisar varios equipos.",
                "modality": "Remoto",
                "priority": "Normal",
                "accepted_privacy": "on",
                "accepted_contact": "on",
                "accepted_e_signature": "on",
                "confirmed_accuracy": "on",
                "attachment": (io.BytesIO(b"%PDF-1.4\nadjunto"), "diagnostico.pdf"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            document = ServiceDocument.query.first()
            self.assertEqual(ServiceRequest.query.count(), 1)
            self.assertEqual(Attachment.query.count(), 1)
            self.assertEqual(SignatureRequest.query.count(), 1)
            self.assertGreaterEqual(EmailDelivery.query.count(), 1)
            self.assertTrue(document.final_pdf_path.startswith("signed-pdfs/"))
            self.assertTrue(app_module.private_path(document.final_pdf_path).exists())

    def test_client_signature_otp_expiration_and_token_reuse(self):
        token_value, otp_value = self.prepare_signature_token()
        self.assertEqual(self.sign_client(token_value, otp_value).status_code, 302)
        self.assertEqual(self.sign_client(token_value, otp_value).status_code, 200)
        with self.app.app_context():
            self.assertEqual(ElectronicSignature.query.count(), 1)
            self.assertEqual(ServiceDocument.query.first().status, "firmado_cliente")

    def test_expired_signature_request_cannot_sign(self):
        token_value, otp_value = self.prepare_signature_token("expired-token", "111111")
        with self.app.app_context():
            signature = SignatureRequest.query.first()
            signature.expires_at = utc_now() - timedelta(minutes=1)
            signature.otp_expires_at = utc_now() - timedelta(minutes=1)
            db.session.commit()
        response = self.sign_client(token_value, otp_value)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertEqual(ElectronicSignature.query.count(), 0)
            self.assertEqual(SignatureRequest.query.first().status, "vencido")

    def test_admin_afcyber_signature_requires_otp(self):
        self.submit_service_request()
        self.login()
        with self.app.app_context():
            document_id = ServiceDocument.query.first().id
        token = self.csrf_token("/admin/documents")
        response = self.client.post(
            f"/admin/documents/{document_id}/sign",
            data={"_csrf_token": token, "signature_text": "Admin", "consent": "on", "otp": "654321"},
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(ElectronicSignature.query.count(), 0)

        token = self.csrf_token("/admin/documents")
        self.assertEqual(self.client.post(f"/admin/documents/{document_id}/afcyber-otp", data={"_csrf_token": token}).status_code, 302)
        with self.app.app_context():
            request_item = SignatureRequest.query.filter_by(signer_role="afcyber").first()
            request_item.otp_hash = app_module.hash_token("654321")
            request_item.otp_expires_at = utc_now() + timedelta(minutes=10)
            db.session.commit()
        token = self.csrf_token("/admin/documents")
        response = self.client.post(
            f"/admin/documents/{document_id}/sign",
            data={"_csrf_token": token, "signature_text": "Admin", "consent": "on", "otp": "654321"},
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(ElectronicSignature.query.filter_by(signer_role="afcyber").count(), 1)
            self.assertEqual(ServiceDocument.query.first().status, "firmado_afcyber")

    def test_signed_document_change_creates_new_version_and_requires_signatures(self):
        token_value, otp_value = self.prepare_signature_token()
        self.sign_client(token_value, otp_value)
        self.login()
        with self.app.app_context():
            document_id = ServiceDocument.query.first().id
            self.assertEqual(DocumentVersion.query.count(), 1)
        token = self.csrf_token("/admin/documents")
        response = self.client.post(
            f"/admin/documents/{document_id}/versions",
            data={
                "_csrf_token": token,
                "content": "Contenido modificado que requiere nuevas firmas.",
                "reason": "Cambio de alcance",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            document = ServiceDocument.query.first()
            self.assertEqual(document.current_version, 2)
            self.assertEqual(document.status, "pendiente_firma_cliente")
            self.assertEqual(DocumentVersion.query.count(), 2)
            self.assertEqual(ElectronicSignature.query.first().version_number, 1)
            self.assertTrue(SignatureRequest.query.filter_by(version_number=2, signer_role="cliente", status="pendiente").first())

    def test_pdf_generation_has_hash_and_private_path(self):
        self.submit_service_request()
        with self.app.app_context():
            document = ServiceDocument.query.first()
            path = app_module.private_path(document.final_pdf_path)
            data = path.read_bytes()
            self.assertTrue(data.startswith(b"%PDF"))
            self.assertGreater(len(data), 2000)
            self.assertEqual(document.final_sha256, app_module.sha256_bytes(data))

    def test_mail_delivery_retries_and_logs_status(self):
        class FakeSMTP:
            calls = 0

            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def starttls(self, context=None):
                return None

            def login(self, username, password):
                return None

            def send_message(self, message):
                FakeSMTP.calls += 1
                if FakeSMTP.calls == 1:
                    raise RuntimeError("temporary failure")

        original_smtp = app_module.smtplib.SMTP
        app_module.smtplib.SMTP = FakeSMTP
        os.environ["MAIL_SERVER"] = "smtp.example.com"
        os.environ["MAIL_DEFAULT_SENDER"] = "no-reply@example.com"
        os.environ["MAIL_USERNAME"] = "user"
        os.environ["MAIL_PASSWORD"] = "secret"
        os.environ["MAIL_MAX_RETRIES"] = "2"
        try:
            with self.app.app_context():
                delivery = app_module.send_configured_email("cliente@example.com", "Asunto", "Cuerpo", "test")
                self.assertEqual(delivery.status, "enviado")
                self.assertEqual(delivery.retries, 1)
        finally:
            app_module.smtplib.SMTP = original_smtp
            for key in ["MAIL_SERVER", "MAIL_DEFAULT_SENDER", "MAIL_USERNAME", "MAIL_PASSWORD"]:
                os.environ.pop(key, None)

    def test_private_path_blocks_traversal(self):
        with self.app.test_request_context("/"):
            with self.assertRaises(Exception):
                app_module.private_path("../secret.pdf")

    def test_postgresql_ddl_compiles_without_vendor_specific_breakage(self):
        from sqlalchemy.dialects import postgresql
        from sqlalchemy.schema import CreateIndex, CreateTable

        dialect = postgresql.dialect()
        for table in db.metadata.sorted_tables:
            self.assertIn("CREATE TABLE", str(CreateTable(table).compile(dialect=dialect)))
            for index in table.indexes:
                self.assertRegex(str(CreateIndex(index).compile(dialect=dialect)), r"CREATE (UNIQUE )?INDEX")


if __name__ == "__main__":
    unittest.main()
