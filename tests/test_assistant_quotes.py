"""Integration checks for the deterministic assistant and quotation outbox."""

import json
import os
import re
import unittest
from unittest.mock import patch

import app as module
import test_app
from assistant import knowledge, respond
from extensions import db
from models import ContactMessage, QuoteMail, QuoteRequest


class AssistantQuoteTests(unittest.TestCase):
    setUpBase = test_app.AppTests.setUp
    login = test_app.AppTests.login
    csrf_token = test_app.AppTests.csrf_token

    def setUp(self):
        self.setUpBase()
        self.smtp_patch = patch.object(module.smtplib, "SMTP")
        self.smtp = self.smtp_patch.start()
        self.addCleanup(self.smtp_patch.stop)
        self.env = patch.dict(
            os.environ,
            {
                "EMAIL_PROVIDER": "smtp",
                "MAIL_SERVER": "smtp.example.invalid",
                "MAIL_DEFAULT_SENDER": "system@example.org",
                "MAIL_USERNAME": "",
                "MAIL_PASSWORD": "",
                "MAIL_MAX_RETRIES": "0",
                "QUOTATION_RECIPIENT": "info@afcybersolutions.com.do",
                "REQUIRE_EMAIL_DELIVERY": "1",
            },
            clear=False,
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def payload(self, strict=True):
        html = self.client.get("/cotizacion" if strict else "/contacto").get_data(as_text=True)
        return {
            "_csrf_token": re.search(r'name="_csrf_token" value="([^"]+)"', html).group(1),
            "quote_nonce": re.search(r'name="quote_nonce" value="([^"]+)"', html).group(1),
            "name": "Cliente de prueba",
            "company": "Empresa de prueba",
            "phone": "8090000000",
            "email": "client@example.org",
            "requested_service": "MultiNegocios",
            "message": "Necesito controlar ventas.",
            "budget": "RD$ 10000",
            "accepted_privacy": "on",
        }

    def ask(self, text):
        token = self.csrf_token("/")
        return self.client.post("/asistente/responder", data={"_csrf_token": token, "message": text})

    def test_assistant_is_deterministic_public_and_does_not_expose_secrets(self):
        with self.app.test_request_context("/"):
            facts = knowledge()
            self.assertIn("mission", facts["company"])
            serialized = json.dumps(facts)
            self.assertNotIn("SECRET_KEY", serialized)
            self.assertNotIn("password_hash", serialized)
            self.assertIn("No tengo información suficiente", respond("precio de una solución")["text"])

        response = self.ask("¿Qué hace AFCyber Préstamos Enterprise?")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["products"][0]["id"], "prestamos-enterprise")
        self.assertIn("Android", response.get_data(as_text=True))

    def test_assistant_routes_and_unknown_question(self):
        self.assertEqual(self.client.get("/asistente/catalogo").status_code, 200)
        self.assertEqual(self.client.get("/productos/prestamos-enterprise").status_code, 200)
        unknown = self.ask("neutrinos galaxias orbitales")
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(unknown.json["products"], [])
        self.assertIn("No tengo información suficiente", unknown.json["text"])

    def test_assistant_requires_csrf_limits_payload_and_rate(self):
        self.assertEqual(self.client.post("/asistente/responder", data={"message": "hola"}).status_code, 400)
        self.assertEqual(self.ask("x" * 601).status_code, 422)
        self.assertEqual(self.client.post("/asistente/responder", data={"_csrf_token": self.csrf_token("/"), "message": "x" * 5000}).status_code, 413)
        for _ in range(29):
            self.assertEqual(self.ask("hola").status_code, 200)
        self.assertEqual(self.ask("hola").status_code, 429)

    def test_dedicated_quote_persists_both_mail_jobs_and_uses_reply_to(self):
        response = self.client.post("/cotizacion", data=self.payload(), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            quote = QuoteRequest.query.one()
            self.assertRegex(quote.number, r"^AFC-\d{4}-\d{6}$")
            self.assertEqual(ContactMessage.query.count(), 1)
            self.assertEqual(QuoteMail.query.count(), 2)
            self.assertEqual({job.status for job in quote.mail_jobs}, {"ENVIADO"})
        sent = self.smtp.return_value.__enter__.return_value.send_message.call_args_list
        self.assertEqual(len(sent), 2)
        administrator = sent[0].args[0]
        self.assertEqual(administrator["To"], "info@afcybersolutions.com.do")
        self.assertEqual(administrator["Reply-To"], "client@example.org")
        self.assertTrue(any(part.get_content_type() == "text/html" for part in administrator.walk()))

    def test_quote_duplicate_honeypot_and_validation_are_safe(self):
        payload = self.payload()
        self.assertEqual(self.client.post("/cotizacion", data=payload).status_code, 302)
        self.assertEqual(self.client.post("/cotizacion", data=payload).status_code, 302)
        with self.app.app_context():
            self.assertEqual(QuoteRequest.query.count(), 1)
            self.assertEqual(QuoteMail.query.count(), 2)
        invalid = self.payload()
        invalid["website"] = "automated"
        self.assertEqual(self.client.post("/cotizacion", data=invalid).status_code, 422)
        invalid = self.payload()
        invalid["email"] = ""
        self.assertEqual(self.client.post("/cotizacion", data=invalid).status_code, 422)

    def test_quote_failure_keeps_request_and_admin_is_protected(self):
        self.smtp.return_value.__enter__.return_value.send_message.side_effect = module.smtplib.SMTPException("synthetic failure")
        self.client.post("/cotizacion", data=self.payload())
        self.assertEqual(self.client.get("/admin/cotizaciones").status_code, 302)
        with self.app.app_context():
            quote = QuoteRequest.query.one()
            self.assertEqual({job.status for job in quote.mail_jobs}, {"FALLIDO"})
            quote_id = quote.id
        self.login()
        self.assertEqual(self.client.get("/admin/cotizaciones").status_code, 200)
        csrf = self.csrf_token("/admin/cotizaciones")
        response = self.client.post(
            f"/admin/cotizaciones/{quote_id}/estado",
            data={"_csrf_token": csrf, "status": "CERRADA"},
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.get(QuoteRequest, quote_id).status, "CERRADA")


if __name__ == "__main__":
    unittest.main()
