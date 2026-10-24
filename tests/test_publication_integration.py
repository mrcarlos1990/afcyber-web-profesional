"""Focused tests for the corporate functionality integrated from publication.

The shared fixture uses SQLite in memory and a temporary private-storage root.
No local instance database or persistent storage is opened by these tests.
"""

import re
import json
import os
import unittest
from io import BytesIO
from urllib.error import HTTPError, URLError
from unittest.mock import patch

try:
    import test_app
except ModuleNotFoundError:  # Direct module execution from the repository root.
    from tests import test_app
import app as app_module
from extensions import db
from models import ContactMessage, EmailDelivery, QuoteRequest, ServiceRequest


class FakeResendResponse:
    def __init__(self, payload=None, status=200):
        self.status = status
        self._payload = json.dumps(payload or {}).encode("utf-8")

    def read(self, limit=-1):
        return self._payload[:limit]

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


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
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        home_html = home.get_data(as_text=True)
        self.assertIn('id="assistant-toggle"', home_html)
        self.assertIn("/static/js/assistant.js", home_html)
        self.assertIn("No compartas contraseñas ni datos sensibles", home_html)
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

    def test_home_contact_routes_to_info_with_html_and_reply_to(self):
        self.client.get("/")
        with self.client.session_transaction() as session:
            csrf = session["_csrf_token"]
            nonce = session["quote_nonce"]
        with patch.dict(
            os.environ,
            {
                "MAIL_SERVER": "smtp.example.invalid",
                "MAIL_PORT": "587",
                "MAIL_USE_TLS": "0",
                "MAIL_DEFAULT_SENDER": "no-reply@afcybersolutions.com.do",
                "MAIL_USERNAME": "smtp-user",
                "MAIL_PASSWORD": "smtp-password",
                "MAIL_MAX_RETRIES": "0",
                "CONTACT_RECIPIENT": "info@afcybersolutions.com.do",
                "SUPPORT_RECIPIENT": "soporte@afcybersolutions.com.do",
            },
        ), patch.object(app_module.smtplib, "SMTP") as smtp:
            response = self.client.post(
                "/contact",
                data={
                    "_csrf_token": csrf,
                    "quote_nonce": nonce,
                    "name": "Cliente de contacto",
                    "company": "Empresa de contacto",
                    "phone": "8090000000",
                    "email": "cliente@example.com",
                    "requested_service": "Desarrollo web",
                    "message": "Consulta general de prueba.",
                    "accepted_privacy": "on",
                },
            )
        self.assertEqual(response.status_code, 302)
        messages = [call.args[0] for call in smtp.return_value.__enter__.return_value.send_message.call_args_list]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["To"], "info@afcybersolutions.com.do")
        self.assertEqual(messages[0]["From"], "no-reply@afcybersolutions.com.do")
        self.assertEqual(messages[0]["Reply-To"], "cliente@example.com")
        self.assertTrue(any(part.get_content_type() == "text/html" for part in messages[0].walk()))
        with self.app.app_context():
            self.assertEqual(ContactMessage.query.count(), 1)
            self.assertEqual(QuoteRequest.query.count(), 1)
            self.assertEqual(EmailDelivery.query.filter_by(email_type="quotation_administrador", status="enviado").count(), 1)

    def test_support_requests_use_support_recipient_and_service_html(self):
        token = self.csrf_token("/solicitar-servicio")
        with patch.dict(
            os.environ,
            {
                "MAIL_SERVER": "smtp.example.invalid",
                "MAIL_PORT": "587",
                "MAIL_USE_TLS": "0",
                "MAIL_DEFAULT_SENDER": "no-reply@afcybersolutions.com.do",
                "MAIL_USERNAME": "smtp-user",
                "MAIL_PASSWORD": "smtp-password",
                "MAIL_MAX_RETRIES": "0",
                "CONTACT_RECIPIENT": "info@afcybersolutions.com.do",
                "SUPPORT_RECIPIENT": "soporte@afcybersolutions.com.do",
            },
        ), patch.object(app_module.smtplib, "SMTP") as smtp:
            response = self.client.post(
                "/solicitar-servicio",
                data={
                    "_csrf_token": token,
                    "full_name": "Cliente de soporte",
                    "email": "cliente@example.com",
                    "phone": "8090000000",
                    "requested_service": "Soporte técnico",
                    "service_type": "Incidente de soporte",
                    "need_description": "Necesito asistencia con un equipo.",
                    "modality": "Remoto",
                    "priority": "Alta",
                    "accepted_privacy": "on",
                    "accepted_contact": "on",
                    "accepted_e_signature": "on",
                    "confirmed_accuracy": "on",
                },
            )
        self.assertEqual(response.status_code, 302)
        message = smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        self.assertEqual(message["To"], "soporte@afcybersolutions.com.do")
        self.assertEqual(message["Reply-To"], "cliente@example.com")
        self.assertTrue(any(part.get_content_type() == "text/html" for part in message.walk()))
        html_part = next(part for part in message.walk() if part.get_content_type() == "text/html")
        self.assertIn("Cliente de soporte", html_part.get_content())
        with self.app.app_context():
            self.assertEqual(ServiceRequest.query.count(), 1)
            self.assertEqual(EmailDelivery.query.filter_by(email_type="service_request_notification", status="enviado").count(), 1)

    def test_smtp_failure_preserves_service_request_and_records_error(self):
        token = self.csrf_token("/solicitar-servicio")
        with patch.dict(
            os.environ,
            {
                "MAIL_SERVER": "smtp.example.invalid",
                "MAIL_PORT": "587",
                "MAIL_USE_TLS": "0",
                "MAIL_DEFAULT_SENDER": "no-reply@afcybersolutions.com.do",
                "MAIL_MAX_RETRIES": "0",
                "SUPPORT_RECIPIENT": "soporte@afcybersolutions.com.do",
            },
        ), patch.object(app_module.smtplib, "SMTP", side_effect=OSError("SMTP offline")):
            response = self.client.post(
                "/solicitar-servicio",
                data={
                    "_csrf_token": token,
                    "full_name": "Cliente sin SMTP",
                    "email": "cliente@example.com",
                    "phone": "8090000000",
                    "requested_service": "Soporte técnico",
                    "need_description": "La solicitud debe conservarse aunque no haya SMTP.",
                    "accepted_privacy": "on",
                    "accepted_contact": "on",
                    "accepted_e_signature": "on",
                    "confirmed_accuracy": "on",
                },
            )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(ServiceRequest.query.count(), 1)
            delivery = EmailDelivery.query.filter_by(email_type="service_request_notification").one()
            self.assertEqual(delivery.status, "error")
            self.assertNotIn("smtp-password", delivery.error or "")

    def test_service_request_honeypot_and_rate_limit_block_abuse(self):
        token = self.csrf_token("/solicitar-servicio")
        honeypot_response = self.client.post(
            "/solicitar-servicio",
            data={"_csrf_token": token, "website": "automated-value"},
        )
        self.assertEqual(honeypot_response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(ServiceRequest.query.count(), 0)

        with patch("quotations.rate_limit", return_value=False):
            limited_response = self.client.post(
                "/solicitar-servicio",
                data={"_csrf_token": token},
            )
        self.assertEqual(limited_response.status_code, 429)
        self.assertEqual(limited_response.headers["Retry-After"], "600")

    def test_notification_recipient_falls_back_to_official_addresses(self):
        with patch.dict(os.environ, {"CONTACT_RECIPIENT": "invalid", "SUPPORT_RECIPIENT": "invalid"}, clear=False):
            self.assertEqual(app_module.notification_recipient("Desarrollo web"), "info@afcybersolutions.com.do")
            self.assertEqual(app_module.notification_recipient("Soporte técnico"), "soporte@afcybersolutions.com.do")

    def test_resend_contact_uses_https_bearer_reply_to_and_records_acceptance(self):
        self.client.get("/")
        with self.client.session_transaction() as session:
            csrf = session["_csrf_token"]
            nonce = session["quote_nonce"]
        requests = []

        def fake_urlopen(request, timeout):
            requests.append((request, timeout))
            return FakeResendResponse({"id": "resend-message-contact"})

        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "resend",
                "RESEND_API_KEY": "re_test_only",
                "RESEND_FROM_EMAIL": "notificaciones@afcybersolutions.com.do",
                "RESEND_MAX_RETRIES": "0",
                "RESEND_TIMEOUT_SECONDS": "10",
                "REQUIRE_EMAIL_DELIVERY": "1",
                "CONTACT_RECIPIENT": "contact@afcybersolutions.com.do",
                "QUOTATION_RECIPIENT": "info@afcybersolutions.com.do",
            },
        ), patch("resend_client.urlopen", side_effect=fake_urlopen):
            response = self.client.post(
                "/contact",
                data={
                    "_csrf_token": csrf,
                    "quote_nonce": nonce,
                    "name": "Cliente Resend",
                    "phone": "8090000000",
                    "email": "cliente@example.com",
                    "requested_service": "Desarrollo web",
                    "message": "Solicitud simulada sin envío real.",
                    "accepted_privacy": "on",
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(requests), 2)  # administrador y confirmación al cliente
        request, timeout = requests[0]
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertEqual(request.get_header("Authorization"), "Bearer re_test_only")
        self.assertEqual(request.get_header("User-agent"), "AFCyber-Solutions/1.0")
        self.assertEqual(timeout, 10)
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["to"], ["info@afcybersolutions.com.do"])
        self.assertEqual(payload["reply_to"], ["cliente@example.com"])
        self.assertIn("html", payload)
        with self.app.app_context():
            deliveries = EmailDelivery.query.filter_by(provider="resend").all()
            self.assertEqual(len(deliveries), 2)
            self.assertTrue(all(item.status == "aceptado" for item in deliveries))
            self.assertTrue(all(item.provider_message_id == "resend-message-contact" for item in deliveries))
            self.assertTrue(all(item.idempotency_key for item in deliveries))
            self.assertNotIn("re_test_only", " ".join(item.error or "" for item in deliveries))

    def test_resend_retries_429_with_same_idempotency_key(self):
        responses = [
            HTTPError(
                "https://api.resend.com/emails",
                429,
                "rate limited",
                {"Retry-After": "0"},
                BytesIO(b'{"name":"rate_limit_exceeded"}'),
            ),
            FakeResendResponse({"id": "resend-message-retried"}),
        ]
        requests = []

        def fake_urlopen(request, timeout):
            requests.append(request)
            response = responses.pop(0)
            if isinstance(response, HTTPError):
                raise response
            return response

        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "resend",
                "RESEND_API_KEY": "re_test_only",
                "RESEND_FROM_EMAIL": "notificaciones@afcybersolutions.com.do",
                "RESEND_MAX_RETRIES": "1",
                "REQUIRE_EMAIL_DELIVERY": "1",
            },
        ), patch("resend_client.urlopen", side_effect=fake_urlopen), patch("resend_client.time.sleep") as sleeper:
            with self.app.app_context():
                delivery = app_module.send_configured_email(
                    "info@afcybersolutions.com.do",
                    "Prueba Resend",
                    "Contenido de prueba",
                    "test_resend",
                    html_body="<p>Contenido de prueba</p>",
                    reply_to="cliente@example.com",
                )
        self.assertEqual(delivery.status, "aceptado")
        self.assertEqual(delivery.retries, 1)
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].get_header("Idempotency-key"), requests[1].get_header("Idempotency-key"))
        sleeper.assert_called_once()

    def test_resend_non_transient_401_does_not_fallback_or_retry(self):
        error = HTTPError(
            "https://api.resend.com/emails",
            401,
            "unauthorized",
            {},
            BytesIO(b'{"name":"missing_api_key"}'),
        )
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "resend",
                "RESEND_API_KEY": "re_test_only",
                "RESEND_FROM_EMAIL": "notificaciones@afcybersolutions.com.do",
                "RESEND_MAX_RETRIES": "3",
                "REQUIRE_EMAIL_DELIVERY": "1",
            },
        ), patch("resend_client.urlopen", side_effect=error) as urlopen_mock, patch.object(app_module.smtplib, "SMTP") as smtp:
            with self.app.app_context():
                delivery = app_module.send_configured_email(
                    "info@afcybersolutions.com.do", "No enviar", "Prueba", "test_resend_401"
                )
        self.assertEqual(delivery.status, "error")
        self.assertEqual(delivery.retries, 0)
        self.assertEqual(urlopen_mock.call_count, 1)
        smtp.assert_not_called()

    def test_resend_400_is_recorded_without_retry(self):
        error = HTTPError(
            "https://api.resend.com/emails",
            400,
            "bad request",
            {},
            BytesIO(b'{"name":"validation_error"}'),
        )
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "resend",
                "RESEND_API_KEY": "re_test_only",
                "RESEND_FROM_EMAIL": "notificaciones@afcybersolutions.com.do",
                "RESEND_MAX_RETRIES": "3",
                "REQUIRE_EMAIL_DELIVERY": "1",
            },
        ), patch("resend_client.urlopen", side_effect=error) as urlopen_mock:
            with self.app.app_context():
                delivery = app_module.send_configured_email(
                    "info@afcybersolutions.com.do", "Solicitud inválida", "Prueba", "test_resend_400"
                )
        self.assertEqual(delivery.status, "error")
        self.assertEqual(delivery.retries, 0)
        self.assertEqual(urlopen_mock.call_count, 1)

    def test_resend_500_retries_and_timeout_is_bounded(self):
        responses = [
            FakeResendResponse({"name": "internal_server_error"}, status=500),
            FakeResendResponse({"id": "resend-message-500-retry"}),
        ]

        def fake_urlopen(request, timeout):
            return responses.pop(0)

        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "resend",
                "RESEND_API_KEY": "re_test_only",
                "RESEND_FROM_EMAIL": "notificaciones@afcybersolutions.com.do",
                "RESEND_MAX_RETRIES": "1",
                "RESEND_TIMEOUT_SECONDS": "10",
                "REQUIRE_EMAIL_DELIVERY": "1",
            },
        ), patch("resend_client.urlopen", side_effect=fake_urlopen), patch("resend_client.time.sleep"):
            with self.app.app_context():
                delivery = app_module.send_configured_email(
                    "info@afcybersolutions.com.do", "Reintento 500", "Prueba", "test_resend_500"
                )
        self.assertEqual(delivery.status, "aceptado")
        self.assertEqual(delivery.retries, 1)

    def test_resend_timeout_retries_are_bounded_and_do_not_use_smtp(self):
        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "resend",
                "RESEND_API_KEY": "re_test_only",
                "RESEND_FROM_EMAIL": "notificaciones@afcybersolutions.com.do",
                "RESEND_MAX_RETRIES": "1",
                "REQUIRE_EMAIL_DELIVERY": "1",
            },
        ), patch("resend_client.urlopen", side_effect=URLError("timeout")) as urlopen_mock, patch(
            "resend_client.time.sleep"
        ), patch.object(app_module.smtplib, "SMTP") as smtp:
            with self.app.app_context():
                delivery = app_module.send_configured_email(
                    "info@afcybersolutions.com.do", "Timeout", "Prueba", "test_resend_timeout"
                )
        self.assertEqual(delivery.status, "error")
        self.assertEqual(delivery.retries, 1)
        self.assertEqual(urlopen_mock.call_count, 2)
        smtp.assert_not_called()

    def test_resend_application_retry_reuses_delivery_idempotency_key(self):
        responses = [
            FakeResendResponse({"name": "internal_server_error"}, status=500),
            FakeResendResponse({"id": "resend-message-application-retry"}),
        ]
        requests = []

        def fake_urlopen(request, timeout):
            requests.append(request)
            return responses.pop(0)

        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "resend",
                "RESEND_API_KEY": "re_test_only",
                "RESEND_FROM_EMAIL": "notificaciones@afcybersolutions.com.do",
                "RESEND_MAX_RETRIES": "0",
                "REQUIRE_EMAIL_DELIVERY": "1",
            },
        ), patch("resend_client.urlopen", side_effect=fake_urlopen):
            with self.app.app_context():
                first = app_module.send_configured_email(
                    "info@afcybersolutions.com.do", "Reintento de aplicación", "Prueba", "test_resend_reuse"
                )
                second = app_module.send_configured_email(
                    "info@afcybersolutions.com.do",
                    "Reintento de aplicación",
                    "Prueba",
                    "test_resend_reuse",
                    existing_delivery=first,
                )
                db.session.flush()
                self.assertEqual(EmailDelivery.query.filter_by(email_type="test_resend_reuse").count(), 1)
        self.assertEqual(first.uuid, second.uuid)
        self.assertEqual(first.idempotency_key, second.idempotency_key)
        self.assertEqual(second.status, "aceptado")
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].get_header("Idempotency-key"), requests[1].get_header("Idempotency-key"))

    def test_resend_service_request_routes_support_to_support_recipient(self):
        token = self.csrf_token("/solicitar-servicio")
        requests = []

        def fake_urlopen(request, timeout):
            requests.append(request)
            return FakeResendResponse({"id": "resend-message-support"})

        with patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "resend",
                "RESEND_API_KEY": "re_test_only",
                "RESEND_FROM_EMAIL": "notificaciones@afcybersolutions.com.do",
                "RESEND_MAX_RETRIES": "0",
                "REQUIRE_EMAIL_DELIVERY": "1",
                "CONTACT_RECIPIENT": "info@afcybersolutions.com.do",
                "SUPPORT_RECIPIENT": "soporte@afcybersolutions.com.do",
            },
        ), patch("resend_client.urlopen", side_effect=fake_urlopen):
            response = self.client.post(
                "/solicitar-servicio",
                data={
                    "_csrf_token": token,
                    "full_name": "Cliente soporte Resend",
                    "email": "cliente@example.com",
                    "phone": "8090000000",
                    "requested_service": "Soporte técnico",
                    "service_type": "Incidente de soporte",
                    "need_description": "Solicitud simulada para soporte.",
                    "modality": "Remoto",
                    "priority": "Alta",
                    "accepted_privacy": "on",
                    "accepted_contact": "on",
                    "accepted_e_signature": "on",
                    "confirmed_accuracy": "on",
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(requests), 2)  # OTP de firma y notificación de soporte
        payloads = [json.loads(item.data.decode("utf-8")) for item in requests]
        self.assertIn(["soporte@afcybersolutions.com.do"], [payload["to"] for payload in payloads])
        with self.app.app_context():
            delivery = EmailDelivery.query.filter_by(email_type="service_request_notification").one()
            self.assertEqual(delivery.status, "aceptado")


if __name__ == "__main__":
    unittest.main()
