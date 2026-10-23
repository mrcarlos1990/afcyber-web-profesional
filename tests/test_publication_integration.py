"""Focused tests for the corporate functionality integrated from publication.

The shared fixture uses SQLite in memory and a temporary private-storage root.
No local instance database or persistent storage is opened by these tests.
"""

import re
import os
import unittest
from unittest.mock import patch

try:
    import test_app
except ModuleNotFoundError:  # Direct module execution from the repository root.
    from tests import test_app
import app as app_module
from extensions import db
from models import ContactMessage, QuoteRequest


class PublicationIntegrationTests(unittest.TestCase):
    setUpBase = test_app.AppTests.setUp
    tearDownBase = test_app.AppTests.tearDown

    def setUp(self):
        self.setUpBase()

    def tearDown(self):
        self.tearDownBase()

    def csrf_token(self, path="/"):
        self.client.get(path)
        with self.client.session_transaction() as session:
            return session["_csrf_token"]

    def test_corporate_pages_and_legal_links_are_public(self):
        for path in (
            "/nosotros",
            "/servicios",
            "/portafolio",
            "/contacto",
            "/preguntas-frecuentes",
            "/politica-de-calidad",
            "/privacy-policy",
            "/terms-and-conditions",
            "/productos/afcyber-prestamos",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("AFCyber Solutions", response.get_data(as_text=True))

    def test_assistant_is_deterministic_public_and_csrf_protected(self):
        self.assertEqual(self.client.post("/asistente/responder", data={"message": "hola"}).status_code, 400)
        token = self.csrf_token("/")
        response = self.client.post(
            "/asistente/responder",
            data={"_csrf_token": token, "message": "Necesito información sobre desarrollo web"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("text", payload)
        self.assertNotIn("password_hash", response.get_data(as_text=True))
        self.assertNotIn("SECRET_KEY", response.get_data(as_text=True))

    def test_quote_form_persists_one_request_and_keeps_admin_private(self):
        html = self.client.get("/cotizacion").get_data(as_text=True)
        csrf = re.search(r'name="_csrf_token" value="([^"]+)"', html).group(1)
        nonce = re.search(r'name="quote_nonce" value="([^"]+)"', html).group(1)
        payload = {
            "_csrf_token": csrf,
            "quote_nonce": nonce,
            "name": "Cliente de prueba",
            "company": "Empresa de prueba",
            "phone": "8090000000",
            "email": "cliente@example.com",
            "requested_service": "Software empresarial",
            "message": "Solicitud aislada de prueba.",
            "budget": "",
            "accepted_privacy": "on",
        }
        response = self.client.post("/cotizacion", data=payload)
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(QuoteRequest.query.count(), 1)
            self.assertEqual(ContactMessage.query.count(), 1)
            number = QuoteRequest.query.one().number
        self.assertIn(number, self.client.get("/cotizacion").get_data(as_text=True))
        self.assertEqual(self.client.get("/admin/cotizaciones").status_code, 302)

    def test_quote_admin_requires_authentication_and_csrf_for_state_changes(self):
        html = self.client.get("/cotizacion").get_data(as_text=True)
        csrf = re.search(r'name="_csrf_token" value="([^"]+)"', html).group(1)
        nonce = re.search(r'name="quote_nonce" value="([^"]+)"', html).group(1)
        self.client.post(
            "/cotizacion",
            data={
                "_csrf_token": csrf,
                "quote_nonce": nonce,
                "name": "Cliente",
                "phone": "8090000000",
                "email": "cliente@example.com",
                "requested_service": "Soporte",
                "message": "Prueba administrativa.",
                "accepted_privacy": "on",
            },
        )
        self.assertEqual(self.client.get("/admin/cotizaciones").status_code, 302)
        self.assertEqual(self.client.post("/admin/login", data={}).status_code, 400)
        login_token = self.csrf_token("/admin/login")
        self.client.post(
            "/admin/login",
            data={"_csrf_token": login_token, "email": "admin@example.com", "password": "StrongAdmin123"},
        )
        self.assertEqual(self.client.get("/admin/cotizaciones").status_code, 200)
        with self.app.app_context():
            quote_id = QuoteRequest.query.one().id
        self.assertEqual(self.client.post(f"/admin/cotizaciones/{quote_id}/estado", data={"status": "CERRADA"}).status_code, 400)

    def test_quote_email_uses_existing_delivery_log_and_html_headers(self):
        html = self.client.get("/cotizacion").get_data(as_text=True)
        csrf = re.search(r'name="_csrf_token" value="([^"]+)"', html).group(1)
        nonce = re.search(r'name="quote_nonce" value="([^"]+)"', html).group(1)
        with patch.dict(
            os.environ,
            {
                "MAIL_SERVER": "smtp.example.invalid",
                "MAIL_DEFAULT_SENDER": "system@example.org",
                "MAIL_USERNAME": "",
                "MAIL_PASSWORD": "",
                "MAIL_MAX_RETRIES": "0",
            },
        ), patch.object(app_module.smtplib, "SMTP") as smtp:
            response = self.client.post(
                "/cotizacion",
                data={
                    "_csrf_token": csrf,
                    "quote_nonce": nonce,
                    "name": "Cliente de correo",
                    "phone": "8090000000",
                    "email": "cliente@example.com",
                    "requested_service": "Software empresarial",
                    "message": "Prueba de entrega HTML.",
                    "accepted_privacy": "on",
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(smtp.return_value.__enter__.return_value.send_message.call_count, 2)
        administrator = smtp.return_value.__enter__.return_value.send_message.call_args_list[0].args[0]
        self.assertEqual(administrator["Reply-To"], "cliente@example.com")
        self.assertTrue(any(part.get_content_type() == "text/html" for part in administrator.walk()))
        with self.app.app_context():
            self.assertEqual(QuoteRequest.query.one().mail_jobs[0].delivery.status, "enviado")


if __name__ == "__main__":
    unittest.main()
