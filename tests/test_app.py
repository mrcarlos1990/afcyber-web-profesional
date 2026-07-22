import io
import os
import shutil
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path


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
    utc_now,
)


def tearDownModule():
    shutil.rmtree(TEST_STORAGE_ROOT, ignore_errors=True)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = app_module.app
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            app_module.seed_database()

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
        self.assertIn("Sitemap:", self.client.get("/robots.txt").get_data(as_text=True))
        self.assertIn("<urlset", self.client.get("/sitemap.xml").get_data(as_text=True))
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

    def test_admin_permissions_are_required(self):
        self.assertEqual(self.client.get("/admin/downloads").status_code, 302)
        self.assertIn("/admin/login", self.client.get("/admin/documents").headers["Location"])

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
                self.assertIn("CREATE INDEX", str(CreateIndex(index).compile(dialect=dialect)))


if __name__ == "__main__":
    unittest.main()
