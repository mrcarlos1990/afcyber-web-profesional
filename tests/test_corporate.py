"""Contract checks for corporate routes, official contacts and approved legal text.

Uses SQLite in memory; never changes the existing instance databases.
Run: python -m unittest discover -s tests
"""
import hashlib
import json
import os
import re
import unittest
from pathlib import Path

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ.setdefault('SECRET_KEY', 'corporate-test-secret-more-than-32-characters')
os.environ['FLASK_DEBUG'] = '1'
os.environ['AUTO_CREATE_DB'] = '1'
os.environ.setdefault('PRIVATE_STORAGE_ROOT', str(Path(__file__).resolve().parents[1]/'.verification/test-storage'))
from app import app
from extensions import db
from models import ContactMessage

ROOT = Path(__file__).resolve().parents[1]
EMAILS = {
    'info@afcybersolutions.com.do', 'ventas@afcybersolutions.com.do',
    'cotizaciones@afcybersolutions.com.do', 'soporte@afcybersolutions.com.do',
    'licencias@afcybersolutions.com.do', 'a.felizv@afcybersolutions.com.do',
}

class CorporateContractTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_corporate_pages_are_public_and_have_one_heading(self):
        for route in ['/', '/nosotros', '/contacto', '/politica-de-calidad', '/privacy-policy', '/terms-and-conditions', '/servicios', '/portafolio']:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(re.findall(r'<h1\b', response.get_data(as_text=True))), 1)

    def test_all_official_departments_are_reachable(self):
        for route in ['/contacto', '/nosotros']:
            html = self.client.get(route).get_data(as_text=True)
            self.assertEqual(set(re.findall(r'href="mailto:([^"]+)"', html)), EMAILS)
        home = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('mailto:a.felizv@afcybersolutions.com.do', home)
        self.assertEqual(set(re.findall(r'href="mailto:([^"]+)"', home)), {
            'info@afcybersolutions.com.do', 'ventas@afcybersolutions.com.do',
            'soporte@afcybersolutions.com.do',
        })

    def test_legal_declarations_match_official_source_fingerprints(self):
        sources = json.loads((ROOT/'templates/public/legal/sources.json').read_text(encoding='utf-8'))
        for slug, reference in sources.items():
            response = self.client.get('/' + slug)
            main = re.search(r'<main\b.*?</main>', response.get_data(as_text=True), re.S).group()
            self.assertEqual(hashlib.sha256(main.encode()).hexdigest(), reference['main_sha256'])
            static = (ROOT/(slug+'.html')).read_text(encoding='utf-8')
            static_main = re.search(r'<main\b.*?</main>', static, re.S).group()
            self.assertEqual(hashlib.sha256(static_main.encode()).hexdigest(), reference['main_sha256'])
            self.assertNotIn('Préstamos Enterprise', main)

    def test_quality_is_separate_from_privacy(self):
        company = json.loads((ROOT/'static/data/company.json').read_text(encoding='utf-8'))
        for route in ['/', '/nosotros', '/politica-de-calidad']:
            html = self.client.get(route).get_data(as_text=True)
            for paragraph in company['quality']:
                self.assertIn(paragraph, html)
        self.assertNotIn(company['quality'][0], self.client.get('/privacy-policy').get_data(as_text=True))

    def test_unverified_seed_content_is_not_published_on_home(self):
        html = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('metrics-strip', html)
        self.assertNotIn('Cliente comercial', html)
        self.assertNotIn('Gerente operativo', html)
        self.assertNotIn('class="testimonial-card"', html)

    def test_quote_preserves_csrf_validation_and_optional_fields(self):
        html = self.client.get('/contacto').get_data(as_text=True)
        token = re.search(r'name="_csrf_token" value="([^"]+)"', html).group(1)
        self.assertEqual(self.client.post('/contact', data={'name':'QA','phone':'000','message':'Local test'}).status_code, 400)
        data = {'_csrf_token':token,'name':'QA','phone':'000','message':'Local test','company':'QA Company','email':'qa@example.org','requested_service':'Software empresarial'}
        with app.app_context(): before = ContactMessage.query.count()
        self.assertEqual(self.client.post('/contact', data=data).status_code, 302)
        with app.app_context():
            item = ContactMessage.query.order_by(ContactMessage.id.desc()).first()
            self.assertEqual(ContactMessage.query.count(), before+1)
            self.assertEqual(item.company, data['company'])
            self.assertEqual(item.email, data['email'])
            self.assertEqual(item.requested_service, data['requested_service'])
        data['name'] = ''
        self.assertEqual(self.client.post('/contact', data=data).status_code, 302)
        with app.app_context(): self.assertEqual(ContactMessage.query.count(), before+1)
        self.assertEqual(self.client.get('/admin').status_code, 302)

    def test_unapproved_application_routes_are_not_created(self):
        for route in ['/apps/afcyber-prestamos-enterprise/privacy-policy', '/apps/afcyber-prestamos-enterprise/terms-and-conditions', '/apps/afcyber-prestamos-enterprise/support', '/apps/afcyber-prestamos-enterprise/data-deletion']:
            self.assertEqual(self.client.get(route).status_code, 404)

if __name__ == '__main__': unittest.main()
