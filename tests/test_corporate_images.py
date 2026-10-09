"""Image delivery, original integrity and layout metadata on isolated Flask."""
import hashlib,json,unittest
from html.parser import HTMLParser
from pathlib import Path
import test_app
from app import app
from PIL import Image
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]

class Images(HTMLParser):
    def __init__(self):super().__init__();self.items=[]
    def handle_starttag(self,tag,attrs):
        if tag=='img':self.items.append(dict(attrs))

class CorporateImageTests(unittest.TestCase):
    def test_originals_and_derivatives_preserve_integrity_and_dimensions(self):
        records=json.loads((ROOT/'docs/IMAGENES-CORPORATIVAS.json').read_text(encoding='utf-8'))
        for record in records:
            source=ROOT/record['source']
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),record['source_sha256'])
            for variant in record['variants']:
                with Image.open(ROOT/variant['file']) as image:
                    self.assertEqual(image.format,'WEBP')
                    self.assertEqual(image.size,(variant['width'],variant['height']))
                    self.assertLessEqual(image.width,record['source_width'])
                    self.assertLessEqual(image.height,record['source_height'])
                    self.assertAlmostEqual(image.width/image.height,record['source_width']/record['source_height'],delta=.002)
                    image.verify()

    def test_all_corporate_image_urls_and_candidates_are_served(self):
        client=app.test_client();checked=set()
        for route in ['/','/nosotros','/servicios','/contacto','/politica-de-calidad']:
            html=client.get(route).get_data(as_text=True)
            self.assertNotIn('C:\\',html)
            parser=Images();parser.feed(html)
            for image in parser.items:
                if '/images/corporativas/' not in image.get('src',''):continue
                for field in ['width','height','alt','sizes','srcset']:
                    self.assertTrue(image.get(field), (route,field))
                self.assertEqual(image.get('decoding'),'async')
                candidates=[image['src']]+[value.strip().split()[0] for value in image['srcset'].split(',')]
                for target in candidates:
                    if target in checked:continue
                    with client.get(target) as response:
                        self.assertEqual(response.status_code,200,target)
                        self.assertEqual(response.mimetype,'image/webp')
                    checked.add(target)
        self.assertGreaterEqual(len(checked),27)

    def test_approved_hero_is_eager_and_founder_is_portrait(self):
        client=app.test_client();parser=Images();parser.feed(client.get('/').get_data(as_text=True))
        self.assertTrue(any('hero-afcyber' in image.get('src','') for image in parser.items))
        hero=next(image for image in parser.items if image.get('fetchpriority')=='high')
        self.assertNotEqual(hero.get('loading'),'lazy')
        self.assertEqual(hero.get('fetchpriority'),'high')
        for route in ['/','/nosotros']:
            parser=Images();html=client.get(route).get_data(as_text=True);parser.feed(html)
            founder=next(image for image in parser.items if 'ceo-amauri-institucional.webp' in image.get('src',''))
            self.assertEqual((founder['width'],founder['height']),('1000','1250'))
            self.assertEqual(founder.get('loading'),'lazy')
            self.assertIn('Amauri Feliz Valenzuela',html)

    def test_no_new_services_or_duplicate_sections_added(self):
        html=app.test_client().get('/').get_data(as_text=True)
        self.assertEqual(html.count('class="service-card'),6)
        self.assertEqual(html.count('id="servicios"'),1)
        self.assertEqual(html.count('id="identidad"'),1)
        self.assertEqual(html.count('id="contacto"'),1)

    def test_service_assignment_prefers_corporate_assets_without_altering_records(self):
        with app.test_request_context('/'):
            macro=app.jinja_env.get_template('public/partials/corporate-images.html').module.service_image
            configured=SimpleNamespace(name='Ciberseguridad',image='existing-image.jpg',icon='fa-solid fa-shield')
            self.assertIn('servicio-ciberseguridad.webp',str(macro(configured)))
            self.assertEqual(configured.image,'existing-image.jpg')
            custom=SimpleNamespace(name='Servicio personalizado',image='existing-image.jpg',icon='fa-solid fa-code')
            self.assertIn('existing-image.jpg',str(macro(custom)))
            for name in ['Computación en la nube', 'Software Cloud', 'Servidores cloud']:
                cloud=SimpleNamespace(name=name,image='existing-cloud.jpg',icon='fa-solid fa-cloud')
                rendered=str(macro(cloud))
                self.assertIn('servicio-cloud.webp',rendered)
                self.assertIn('loading="lazy"',rendered)
                self.assertNotIn('existing-cloud.jpg',rendered)
                self.assertEqual(cloud.image,'existing-cloud.jpg')
                cloud.image=''
                self.assertIn('servicio-cloud.webp',str(macro(cloud)))
