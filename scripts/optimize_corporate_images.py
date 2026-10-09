"""Create optimized derivatives; originals are opened read-only and never changed."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageOps

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Imagenes wed'
OUTPUT=ROOT/'static/images/corporativas'
ASSIGNMENTS={
 'hero-afcyber':('Centro de ciberseguridad futurista nocturno.png',1672),
 'servicio-cloud':('Infraestructura global en la nube.png',1200),
 'ceo-amauri-tecnologia':('WhatsApp Image 2026-10-08 at 20.41.33 (1).jpeg',1000),
 'ceo-amauri-institucional':('WhatsApp Image 2026-10-08 at 20.41.33.jpeg',1000),
 'servicio-ciberseguridad':('WhatsApp Image 2026-10-08 at 20.41.33 (2).jpeg',1200),
 'servicio-software':('WhatsApp Image 2026-10-08 at 20.41.33 (3).jpeg',1200),
 'servicio-redes':('WhatsApp Image 2026-10-08 at 20.41.33 (4).jpeg',1200),
 'servicio-soporte':('WhatsApp Image 2026-10-08 at 20.41.34 (1).jpeg',1200),
 'servicio-control-acceso':('WhatsApp Image 2026-10-08 at 20.41.34 (2).jpeg',1200),
 'nosotros-valores':('WhatsApp Image 2026-10-08 at 20.41.34 (3).jpeg',1600),
 'politica-calidad':('WhatsApp Image 2026-10-08 at 20.41.34 (4).jpeg',1200),
 'contacto-afcyber':('WhatsApp Image 2026-10-08 at 20.41.34 (5).jpeg',1200),
 'servicio-cctv':('WhatsApp Image 2026-10-08 at 20.41.34.jpeg',1200),
 'productos-software-afcyber':('WhatsApp Image 2026-10-08 at 20.41.35.jpeg',1600),
}

def main():
 OUTPUT.mkdir(parents=True,exist_ok=True);records=[]
 for name,(filename,max_width) in ASSIGNMENTS.items():
  source=SOURCE/filename;digest=hashlib.sha256(source.read_bytes()).hexdigest()
  with Image.open(source) as raw:
   image=ImageOps.exif_transpose(raw).convert('RGB');original_size=image.size
   widths=[320,640,max_width] if name.startswith('ceo-') else [640,960,max_width]
   variants=[]
   for width in sorted(set(min(w,image.width) for w in widths)):
    height=round(image.height*width/image.width)
    variant=image.resize((width,height),Image.Resampling.LANCZOS)
    output=OUTPUT/(name+('' if width==min(max_width,image.width) else '-'+str(width))+'.webp')
    variant.save(output,'WEBP',quality=84,method=6)
    with Image.open(output) as check:check.verify()
    variants.append({'file':str(output.relative_to(ROOT)).replace('\\','/'),'width':width,'height':height,'bytes':output.stat().st_size})
  assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
  records.append({'name':name,'source':'Imagenes wed/'+filename,'source_width':original_size[0],'source_height':original_size[1],'source_bytes':source.stat().st_size,'source_sha256':digest,'variants':variants})
 (ROOT/'docs/IMAGENES-CORPORATIVAS.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'images':len(records),'original_bytes':sum(r['source_bytes'] for r in records),'primary_webp_bytes':sum(r['variants'][-1]['bytes'] for r in records),'derivative_files':sum(len(r['variants']) for r in records)},indent=2))

if __name__=='__main__':main()
