"""Canonical Flask presentation and deployment checks; no production database."""
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import test_app  # Uses memory-only SQLite and isolated private storage.
from app import app, get_initial_admin_password

ROOT = Path(__file__).resolve().parents[1]


class PublicArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_uses_flask_layout_and_shared_components(self):
        html = self.client.get('/').get_data(as_text=True)
        for file in ['platform.css', 'home.css', 'corporate.css', 'platform.js']:
            self.assertIn(file, html)
        self.assertNotIn('js/main.js', html)
        self.assertNotIn('min-vh-100', html)
        self.assertNotIn('networkCanvas', html)
        self.assertEqual(html.count('id="identidad"'), 1)
        self.assertEqual(html.count('id="confianza"'), 1)
        self.assertIn('href="/politica-de-calidad"', html)

    def test_public_navigation_assets_and_fragments(self):
        routes = ['/', '/nosotros', '/contacto', '/politica-de-calidad',
                  '/privacy-policy', '/terms-and-conditions', '/servicios',
                  '/portafolio', '/preguntas-frecuentes', '/descargas',
                  '/descargas/programas', '/descargas/manuales', '/solicitar-servicio']
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, route)
            html = response.get_data(as_text=True)
            for target in re.findall(r'(?:href|src)="(/[^"]*)"', html):
                if target.startswith('//'):
                    continue
                path, _, fragment = target.partition('#')
                with self.client.get(path or route) as destination:
                    self.assertEqual(destination.status_code, 200, (route, target))
                    if fragment:
                        self.assertIn('id="' + fragment + '"', destination.get_data(as_text=True), target)

    def test_home_faq_is_limited_and_full_data_remains_public(self):
        home = self.client.get('/').get_data(as_text=True)
        full = self.client.get('/preguntas-frecuentes').get_data(as_text=True)
        self.assertLessEqual(home.count('class="accordion-item"'), 3)
        self.assertGreaterEqual(full.count('class="accordion-item"'), home.count('class="accordion-item"'))

    def test_render_runs_migrations_before_gunicorn(self):
        for file in ['render.yaml', 'Procfile']:
            self.assertIn('flask db upgrade && gunicorn app:app', (ROOT/file).read_text(encoding='utf-8'))

    def test_production_password_guard_is_preserved(self):
        with patch.dict('os.environ', {'FLASK_DEBUG':'0', 'ADMIN_PASSWORD':''}):
            with self.assertRaises(RuntimeError):
                get_initial_admin_password()
        with patch.dict('os.environ', {'FLASK_DEBUG':'0', 'ADMIN_PASSWORD':'weak'}):
            with self.assertRaises(RuntimeError):
                get_initial_admin_password()
