"""Legacy Netlify export; never used by Render's Flask build or startup.

The canonical HOME is templates/public/index.html, rendered by app.index.
This exporter preserves the former static deployment, whose root HTML content
is independent of the live Flask database. Do not run it to update Render.

Run with the project's Python environment: python scripts/build_corporate.py.
Jinja2 is already provided by Flask; no new product dependency is required.
"""
import json
import re
from pathlib import Path
from jinja2 import ChoiceLoader, DictLoader, Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
company = json.loads((ROOT / 'static/data/company.json').read_text(encoding='utf-8'))

def static_url(endpoint, **values):
    if endpoint == 'static': return '/static/' + values['filename']
    if endpoint == 'public_catalog': return {'services':'/servicios', 'portfolio':'/portafolio', 'about':'/nosotros'}[values['catalog']]
    if endpoint == 'legal_document': return '/' + values['document']
    return {'index':'/', 'contact_page':'/contacto', 'quality_policy':'/politica-de-calidad', 'contact':'/contact'}[endpoint]

# These settings reproduce the existing static site's public contact and branding.
settings = {
    'company_name':company['name'], 'logo':None, 'phone':'829-919-8058',
    'whatsapp':'18299198058', 'address':'República Dominicana', 'business_hours':'',
    'copyright_text':'Todos los derechos reservados.', 'footer_text':'Desarrollado por AFCyber Solutions',
    'meta_title':'AFCyber Solutions | Soluciones tecnológicas', 'meta_description':company['summary'],
    'show_ceo':True,
}
ceo = {'full_name':'Ing. Amauri Feliz', 'role':'CEO & Fundador', 'photo':None, 'bio':'', 'experience':'', 'skills':'', 'linkedin':None, 'cv_pdf':None, 'whatsapp_message':'Hola Ing. Amauri Feliz, quiero conversar sobre un proyecto tecnológico.'}
home = (ROOT / 'index.html').read_text(encoding='utf-8')
head = home[:home.index('</head>')+len('</head>')]
head = re.sub(r'<title>.*?</title>', '<title>{{ page_title }}</title>', head, flags=re.S)
head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="{{ page_description|default(corporate.summary, true) }}">', head)
head = re.sub(r'<meta property="og:title"[^>]*>', '<meta property="og:title" content="{{ page_title }}">', head)
head = re.sub(r'<meta property="og:description"[^>]*>', '<meta property="og:description" content="{{ page_description|default(corporate.summary, true) }}">', head)
head = re.sub(r'<meta property="og:url"[^>]*>', '<meta property="og:url" content="{{ page_canonical }}">', head)
head = head.replace('</head>', '<link rel="canonical" href="{{ page_canonical }}">\n</head>')
scripts = re.search(r'  <script src="https://cdn.jsdelivr.net/npm/bootstrap.*?</body>',home,re.S).group().replace('</body>','')
layout=head+'\n<body class="compact-site">{% block content %}{% endblock %}\n'+scripts+'\n</body></html>\n'
env=Environment(loader=ChoiceLoader([DictLoader({'public/base.html':layout}),FileSystemLoader(ROOT/'templates')]),autoescape=select_autoescape(['html']))
env.globals['url_for']=static_url
env.filters['asset']=lambda value: value if (value or '').startswith('http') else '/static/uploads/'+value
env.filters['lines']=lambda value:[line.strip() for line in (value or '').splitlines() if line.strip()]
context={'corporate':company,'settings':settings,'ceo':ceo,'static_site':True,'social_links':[]}

components={
    'nav':env.get_template('public/partials/nav.html').render(**context),
    'footer':env.get_template('public/partials/footer.html').render(**context),
    'identity':env.get_template('public/partials/identity.html').render(**context,identity_internal=False),
    'departments':env.get_template('public/partials/departments.html').render(**context,department_compact=True),
}
for filename in ['index.html','servicios.html','portafolio.html']:
    p=ROOT/filename;text=p.read_text(encoding='utf-8')
    for name,content in components.items():
        pattern=r'<!-- corporate:'+name+r':start -->.*?<!-- corporate:'+name+r':end -->'
        text=re.sub(pattern,lambda m:'<!-- corporate:'+name+':start -->\n'+content+'\n<!-- corporate:'+name+':end -->',text,flags=re.S)
    p.write_text(text,encoding='utf-8',newline='\n')

for filename,template,title,extra in [
    ('nosotros','about','Nosotros | AFCyber Solutions',{}),
    ('contacto','contact','Contacto | AFCyber Solutions',{}),
    ('politica-de-calidad','quality','Política de Calidad | AFCyber Solutions',{}),
    ('privacy-policy','legal','Política de Privacidad | AFCyber Solutions',{'legal_document':'privacy-policy'}),
    ('terms-and-conditions','legal','Términos y Condiciones | AFCyber Solutions',{'legal_document':'terms-and-conditions'}),
]:
    output=env.get_template('public/'+template+'.html').render(**context,**extra,page_title=title,page_canonical='https://'+company['domain']+'/'+filename)
    (ROOT/(filename+'.html')).write_text(output,encoding='utf-8',newline='\n')
print('Static corporate pages and shared components regenerated.')
