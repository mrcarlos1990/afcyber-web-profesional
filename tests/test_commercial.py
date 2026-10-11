"""Commercial enquiry contracts: isolated SQLite, no external email or services."""
import re
import unittest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
import test_app
from extensions import db
from models import ContactMessage

class CommercialTests(unittest.TestCase):
    setUp = test_app.AppTests.setUp
    csrf_token = test_app.AppTests.csrf_token
    # Reuse isolated setup without inheriting the entire parent test suite.
    def payload(self):
        html = self.client.get('/contacto').get_data(as_text=True)
        return {'_csrf_token': re.search(r'name="_csrf_token" value="([^"]+)"', html).group(1),
                'quote_nonce': re.search(r'name="quote_nonce" value="([^"]+)"', html).group(1),
                'name':'Consulta local', 'email':'local@example.org', 'phone':'',
                'requested_service':'Software', 'message':'Necesidad de prueba', 'accepted_privacy':'on'}

    def test_email_only_and_duplicate(self):
        data=self.payload()
        self.assertEqual(self.client.post('/contact',data=data).status_code,302)
        response=self.client.post('/contact',data=data,follow_redirects=True)
        self.assertIn('ya está guardada',response.get_data(as_text=True))
        with self.app.app_context(): self.assertEqual(ContactMessage.query.count(),1)

    def test_missing_contact_and_consent(self):
        data=self.payload();data['email']='';data['accepted_privacy']=''
        response=self.client.post('/contact',data=data)
        self.assertEqual(response.status_code,422)
        self.assertIn('value="Consulta local"',response.get_data(as_text=True))
        with self.app.app_context(): self.assertEqual(ContactMessage.query.count(),0)

    def test_failed_save_has_no_success(self):
        data=self.payload()
        with patch.object(db.session,'commit',side_effect=SQLAlchemyError('synthetic local failure')):
            response=self.client.post('/contact',data=data)
        self.assertEqual(response.status_code,503)
        self.assertNotIn('Solicitud guardada para revisión',response.get_data(as_text=True))
        with self.app.app_context(): self.assertEqual(ContactMessage.query.count(),0)

    def test_download_categories_and_empty_navigation(self):
        html=self.client.get('/descargas').get_data(as_text=True)
        for path in ['/descargas','/descargas/programas','/descargas/manuales']:
            self.assertIn('href="'+path+'"',html)
            self.assertEqual(self.client.get(path).status_code,200)
        home=self.client.get('/').get_data(as_text=True)
        self.assertNotIn('>Portafolio</a>',home)
        self.assertIn('Software y tecnología para impulsar tu negocio',home)
        self.assertIn('CMMS Empresarial',home)

    def test_authorized_product_functions(self):
        home = self.client.get('/').get_data(as_text=True)
        for text in ['Clientes y préstamos; cobros y pagos', 'Intereses y mora; caja', 'Recibos PDF para compartir', 'Reportes y auditoría', 'Importación/exportación', 'POS, créditos y servicios', 'Reportes y dashboard', 'Configuración y licencias', 'Roles y permisos; auditoría', 'Copias de seguridad', 'Impresión de comprobantes', '>Android</span>', '>Windows</span>']:
            self.assertIn(text, home)
        self.assertEqual(home.count('>Solicitar información</a>'), 3)
