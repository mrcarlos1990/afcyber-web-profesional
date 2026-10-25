"""Resend integration tests: isolated SQLite and mocked HTTPS only."""

import io
import json
import os
import unittest
from urllib.error import HTTPError
from unittest.mock import patch

import test_app
import app as app_module
from extensions import db
from models import ContactMessage, EmailDelivery


class FakeResendResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self._payload = payload

    def read(self, _size=-1):
        return json.dumps(self._payload).encode("utf-8")

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class ResendIntegrationTests(unittest.TestCase):
    setUp = test_app.AppTests.setUp

    def contact_tokens(self):
        self.client.get("/contacto")
        with self.client.session_transaction() as session:
            return session["_csrf_token"], session["quote_nonce"]

    def resend_environment(self):
        return {
            "EMAIL_PROVIDER": "resend",
            "RESEND_API_KEY": "re_test_only",
            "RESEND_FROM_EMAIL": "notificaciones@afcybersolutions.com.do",
            "RESEND_TIMEOUT_SECONDS": "10",
            "RESEND_MAX_RETRIES": "0",
            "REQUIRE_EMAIL_DELIVERY": "1",
            "CONTACT_RECIPIENT": "info@afcybersolutions.com.do",
            "SUPPORT_RECIPIENT": "soporte@afcybersolutions.com.do",
            "QUOTATION_RECIPIENT": "info@afcybersolutions.com.do",
        }

    def test_contact_uses_mocked_resend_and_records_acceptance(self):
        csrf, nonce = self.contact_tokens()
        requests = []

        def fake_urlopen(request, timeout):
            requests.append((request, timeout))
            return FakeResendResponse({"id": "resend-main-contact"})

        with patch.dict(os.environ, self.resend_environment(), clear=False), \
                patch("resend_client.urlopen", side_effect=fake_urlopen), \
                patch.object(app_module.smtplib, "SMTP") as smtp:
            response = self.client.post("/contact", data={
                "_csrf_token": csrf,
                "quote_nonce": nonce,
                "name": "Consulta aislada",
                "email": "cliente@example.com",
                "phone": "8090000000",
                "requested_service": "Desarrollo web",
                "message": "Solicitud de prueba sin envío real.",
                "accepted_privacy": "on",
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(requests), 1)
        request, timeout = requests[0]
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertEqual(request.get_header("Authorization"), "Bearer re_test_only")
        self.assertEqual(timeout, 10)
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["to"], ["info@afcybersolutions.com.do"])
        self.assertEqual(payload["reply_to"], ["cliente@example.com"])
        self.assertIn("html", payload)
        smtp.assert_not_called()
        with self.app.app_context():
            self.assertEqual(ContactMessage.query.count(), 1)
            delivery = EmailDelivery.query.one()
            self.assertEqual(delivery.provider, "resend")
            self.assertEqual(delivery.status, "aceptado")
            self.assertEqual(delivery.provider_message_id, "resend-main-contact")
            self.assertTrue(delivery.idempotency_key)

    def test_resend_unauthorized_does_not_fallback_to_smtp(self):
        error = HTTPError(
            "https://api.resend.com/emails",
            401,
            "unauthorized",
            {},
            io.BytesIO(b'{"name":"unauthorized"}'),
        )
        environment = self.resend_environment()
        environment["RESEND_MAX_RETRIES"] = "3"
        with patch.dict(os.environ, environment, clear=False), \
                patch("resend_client.urlopen", side_effect=error) as urlopen_mock, \
                patch.object(app_module.smtplib, "SMTP") as smtp:
            with self.app.app_context():
                delivery = app_module.send_configured_email(
                    "info@afcybersolutions.com.do", "No enviar", "Prueba", "resend_401"
                )
                db.session.commit()
                status = delivery.status
                retries = delivery.retries
                error_message = delivery.error or ""
        self.assertEqual(status, "error")
        self.assertEqual(retries, 0)
        self.assertEqual(urlopen_mock.call_count, 1)
        self.assertNotIn("re_test_only", error_message)
        smtp.assert_not_called()

    def test_require_email_delivery_controls_missing_resend_configuration(self):
        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "resend",
            "RESEND_API_KEY": "",
            "RESEND_FROM_EMAIL": "",
            "REQUIRE_EMAIL_DELIVERY": "1",
        }, clear=False):
            with self.app.app_context():
                required = app_module.send_configured_email(
                    "info@afcybersolutions.com.do", "Configuración requerida", "Prueba", "required_config"
                )
                db.session.commit()
                required_status = required.status
        self.assertEqual(required_status, "error")

        with patch.dict(os.environ, {
            "EMAIL_PROVIDER": "resend",
            "RESEND_API_KEY": "",
            "RESEND_FROM_EMAIL": "",
            "REQUIRE_EMAIL_DELIVERY": "0",
        }, clear=False):
            with self.app.app_context():
                optional = app_module.send_configured_email(
                    "info@afcybersolutions.com.do", "Configuración opcional", "Prueba", "optional_config"
                )
                db.session.commit()
                optional_status = optional.status
        self.assertEqual(optional_status, "omitido")


if __name__ == "__main__":
    unittest.main()
