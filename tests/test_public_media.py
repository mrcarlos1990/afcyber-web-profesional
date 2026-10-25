"""Public upload durability, conversion and private-file isolation."""
import io
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
from werkzeug.datastructures import FileStorage
from PIL import Image
import test_app
import app as module

class PublicMediaTests(unittest.TestCase):
    def setUp(self):
        # test_app's module cleanup removes its storage before this module runs.
        # Give these durability tests their own storage and restore all globals.
        (module.BASE_DIR / '.verification').mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='public-media-test-', dir=module.BASE_DIR / '.verification')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name, value in [('PRIVATE_STORAGE', root), ('UPLOAD_FOLDER', root / 'public-media'),
                            ('LEGACY_UPLOAD_FOLDER', root / 'legacy-public')]:
            value.mkdir(parents=True, exist_ok=True)
            replacement = patch.object(module, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)

    def test_optimized_upload_survives_new_application_and_legacy_url(self):
        data=io.BytesIO()
        Image.new('RGBA',(2400,1200),(20,80,150,120)).save(data,'PNG')
        data.seek(0)
        with module.app.test_request_context('/'):
            filename=module.save_upload(FileStorage(stream=data,filename='logo.png'))
            self.assertIsNotNone(filename)
            asset=module.app.jinja_env.filters['asset'](filename)
        target=module.UPLOAD_FOLDER/filename
        try:
            self.assertTrue(target.is_relative_to(module.PRIVATE_STORAGE))
            self.assertEqual(target.suffix,'.webp')
            with Image.open(target) as image:
                self.assertEqual(image.size,(1920,960))
                self.assertIn('A',image.getbands())
            restarted=module.create_app().test_client()
            for url in [asset,'/static/uploads/'+filename]:
                with restarted.get(url) as response:
                    self.assertEqual(response.status_code,200)
                    self.assertEqual(response.mimetype,'image/webp')
                    self.assertEqual(response.data,target.read_bytes())
            self.assertEqual(restarted.get('/media/../documents/private.pdf').status_code,404)
            self.assertEqual(restarted.get('/media/anything.exe').status_code,404)
        finally:
            target.unlink(missing_ok=True)

    def test_legacy_files_remain_available(self):
        # Create an isolated public fixture, never use real uploaded records.
        filename='verification-public-legacy.webp'
        target=module.LEGACY_UPLOAD_FOLDER/filename
        Image.new('RGB',(4,4),'blue').save(target,'WEBP')
        try:
            with module.app.test_client().get('/media/'+filename) as response:
                self.assertEqual(response.status_code,200)
        finally:
            target.unlink(missing_ok=True)
