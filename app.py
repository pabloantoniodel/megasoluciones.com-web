from flask import Flask, render_template, render_template_string, request, flash, redirect, url_for, Response, abort, session, send_file
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from wtforms import StringField, TextAreaField, EmailField, TelField, SelectField
from wtforms.validators import DataRequired, Email
import os
from datetime import datetime
from time import time

from geo_pages import GEO_HUB, GEO_INDEX_GROUPS, geo_sitemap_entries, get_geo_page

from yt_posts import db as yt_db
from yt_posts import stats as yt_stats
from yt_posts.admin import admin_bp

from spam_protection import (
    HONEYPOT_FIELD,
    check_akismet_spam,
    get_client_ip,
    load_akismet_api_key,
    load_turnstile_secret_key,
    load_turnstile_site_key,
    record_submission,
    should_silently_drop,
    spam_block_reason,
    verify_turnstile,
)

def load_gsc_verification_token() -> str | None:
    """Token de Google Search Console (meta HTML tag)."""
    for name in ('gsc-verification.txt', '.gsc-verification'):
        path = os.path.join(os.path.dirname(__file__), name)
        if os.path.isfile(path):
            token = open(path, encoding='utf-8').read().strip()
            if token and not token.startswith('#'):
                return token
    env = os.environ.get('GSC_VERIFICATION_TOKEN', '').strip()
    return env or None


def load_ga4_id() -> str | None:
    for name in ('ga4-id.txt', '.ga4-id'):
        path = os.path.join(os.path.dirname(__file__), name)
        if os.path.isfile(path):
            gid = open(path, encoding='utf-8').read().strip()
            if gid and not gid.startswith('#'):
                return gid
    return os.environ.get('GA4_MEASUREMENT_ID', '').strip() or None


GSC_VERIFICATION_TOKEN = load_gsc_verification_token()
GA4_MEASUREMENT_ID = load_ga4_id()

LINKEDIN_URL = 'https://www.linkedin.com/showcase/megasolucion'
X_URL = 'https://x.com/Megasolucion'
TURNSTILE_SITE_KEY = load_turnstile_site_key()
TURNSTILE_SECRET_KEY = load_turnstile_secret_key()
AKISMET_API_KEY = load_akismet_api_key()

CANONICAL_BASE_URL = os.environ.get('CANONICAL_BASE_URL', 'https://megasolucion.es').rstrip('/')
PRIMARY_HOST = 'megasolucion.es'
REDIRECT_TO_PRIMARY_HOSTS = frozenset({
    'megasolucion.com',
    'www.megasolucion.com',
    'www.megasolucion.es',
})

HREFLANG_ES = 'https://megasolucion.es'

SITEMAP_PAGES = [
    {'path': '/', 'changefreq': 'weekly', 'priority': '1.0'},
    {'path': '/desarrollo-software', 'changefreq': 'monthly', 'priority': '0.95'},
    {'path': '/automatizaciones', 'changefreq': 'monthly', 'priority': '0.95'},
    {'path': '/servicios', 'changefreq': 'monthly', 'priority': '0.9'},
    {'path': '/sobre', 'changefreq': 'monthly', 'priority': '0.8'},
    {'path': '/portfolio', 'changefreq': 'monthly', 'priority': '0.8'},
    {'path': '/testimonios', 'changefreq': 'monthly', 'priority': '0.7'},
    {'path': '/contacto', 'changefreq': 'monthly', 'priority': '0.8'},
    {'path': '/recursos', 'changefreq': 'monthly', 'priority': '0.7'},
    {'path': '/privacidad', 'changefreq': 'yearly', 'priority': '0.3'},
    {'path': '/aviso-legal', 'changefreq': 'yearly', 'priority': '0.3'},
]

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'megasoluciones-secret-key-2026')

app.register_blueprint(admin_bp)
yt_db.init_db()


@app.after_request
def track_visit(response):
    """Estadísticas propias (tipo WP Statistics). Informado en /privacidad (RGPD)."""
    try:
        ua = request.headers.get('User-Agent', '')
        if yt_stats.should_track(
            request.path, request.method, response.status_code,
            response.content_type or '', ua,
        ):
            client_ip = get_client_ip(
                request.headers.get('X-Forwarded-For'),
                request.remote_addr,
            )
            yt_stats.track(
                path=request.path,
                referrer=request.headers.get('Referer', ''),
                ip=client_ip or '',
                user_agent=ua,
                own_host=(request.host or '').split(':')[0],
            )
    except Exception as e:
        print(f'[stats] after_request error: {e}')
    return response


COM_HOSTS = frozenset({'megasolucion.com', 'www.megasolucion.com'})


@app.before_request
def redirect_to_primary_host():
    """301 megasolucion.com → megasolucion.es (Google Search Console cambio de dominio)."""
    host = (request.host or '').split(':')[0].lower()
    if host in COM_HOSTS and request.path == '/robots.txt':
        return None
    if host in REDIRECT_TO_PRIMARY_HOSTS:
        target = f"{HREFLANG_ES}{request.path or '/'}"
        if request.query_string:
            target = f"{target}?{request.query_string.decode()}"
        return redirect(target, code=301)


LEGACY_REDIRECTS = {
    '/proyectos': '/portfolio',
    '/proyectos/': '/portfolio',
    '/livechat': '/contacto',
    '/livechat/': '/contacto',
    '/blog': '/recursos',
    '/blog/': '/recursos',
}


@app.before_request
def redirect_legacy_urls():
    """301 de URLs antiguas con enlaces externos para conservar el SEO."""
    target = LEGACY_REDIRECTS.get(request.path)
    if target:
        return redirect(f"{HREFLANG_ES}{target}", code=301)


app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'info@megasolucion.net')
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_ASCII_ATTACHMENTS'] = False
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'True') == 'True'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

mail = Mail(app)

SERVICIO_CHOICES = [
    ('', 'Selecciona un servicio'),
    ('desarrollo-software', 'Desarrollo de software a medida'),
    ('automatizaciones-rpa', 'Automatizaciones y RPA'),
    ('chatbots-ia', 'Chatbots IA'),
    ('consultoria-ia', 'Consultoría IA'),
    ('machine-learning', 'Machine Learning'),
    ('otro', 'Otro / No estoy seguro'),
]


class ContactForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    telefono = TelField('Teléfono')
    empresa = StringField('Empresa')
    servicio = SelectField('Servicio de interés', choices=SERVICIO_CHOICES, default='')
    mensaje = TextAreaField('Mensaje', validators=[DataRequired()])

SERVICIOS = [
    {
        'id': 1,
        'slug': 'desarrollo-software',
        'pilar': 'desarrollo',
        'titulo': 'Desarrollo de Software a Medida',
        'descripcion': 'Aplicaciones web, APIs e integraciones diseñadas para tu negocio. Stack moderno, escalable y mantenible para empresas en España.',
        'precio_desde': '5.000€',
        'precio_hasta': '50.000€',
        'caracteristicas': ['Desarrollo a medida', 'APIs e integraciones', 'Stack moderno (Python, React, Node)', 'Despliegue cloud y soporte continuo'],
        'icon': '💻'
    },
    {
        'id': 2,
        'slug': 'automatizaciones-rpa',
        'pilar': 'automatizacion',
        'titulo': 'Automatizaciones y RPA para Empresas',
        'descripcion': 'Automatización de procesos repetitivos, workflows inteligentes e integración entre sistemas para reducir costes y errores.',
        'precio_desde': '399€',
        'precio_hasta': '1.499€/mes',
        'caracteristicas': ['RPA empresarial', 'Automatizaciones con APIs', 'Workflows y orquestación', 'Monitorización 24/7'],
        'icon': '⚙️'
    },
    {
        'id': 3,
        'slug': 'chatbots-ia',
        'pilar': 'ia',
        'titulo': 'Chatbots IA Personalizados',
        'descripcion': 'Asistentes virtuales que atienden a tus clientes 24/7 con procesamiento de lenguaje natural avanzado.',
        'precio_desde': '299€',
        'precio_hasta': '999€/mes',
        'caracteristicas': ['Integración multicanal', 'NLP avanzado', 'Aprendizaje continuo', 'Analytics en tiempo real'],
        'icon': '🤖'
    },
    {
        'id': 4,
        'slug': 'consultoria-ia',
        'pilar': 'ia',
        'titulo': 'Consultoría Estratégica IA',
        'descripcion': 'Asesoramiento experto para definir tu hoja de ruta de transformación digital con inteligencia artificial.',
        'precio_desde': '100€',
        'precio_hasta': '250€/hora',
        'caracteristicas': ['Análisis de viabilidad', 'ROI proyectado', 'Roadmap tecnológico', 'Formación equipos'],
        'icon': '📊'
    },
    {
        'id': 5,
        'slug': 'machine-learning',
        'pilar': 'ia',
        'titulo': 'Machine Learning & Modelos Predictivos',
        'descripcion': 'Modelos de ML personalizados para predicción de demanda, detección de anomalías y análisis predictivo.',
        'precio_desde': '10.000€',
        'precio_hasta': '100.000€',
        'caracteristicas': ['Modelos custom', 'Entrenamiento continuo', 'Deploy cloud', 'MLOps incluido'],
        'icon': '🧠'
    },
    {
        'id': 6,
        'slug': 'computer-vision',
        'pilar': 'ia',
        'titulo': 'Computer Vision',
        'descripcion': 'Visión artificial para reconocimiento facial, detección de objetos, OCR y control de calidad automatizado.',
        'precio_desde': '8.000€',
        'precio_hasta': '80.000€',
        'caracteristicas': ['Reconocimiento de imágenes', 'Video analytics', 'OCR avanzado', 'Edge computing'],
        'icon': '👁️'
    },
    {
        'id': 7,
        'slug': 'nlp',
        'pilar': 'ia',
        'titulo': 'Procesamiento Lenguaje Natural',
        'descripcion': 'Análisis de sentimiento, extracción de información, traducción automática y generación de contenido.',
        'precio_desde': '6.000€',
        'precio_hasta': '60.000€',
        'caracteristicas': ['Análisis de sentimiento', 'NER & clasificación', 'Modelos multiidioma', 'API REST'],
        'icon': '📝'
    },
    {
        'id': 8,
        'slug': 'agentes-ia',
        'pilar': 'ia',
        'titulo': 'Agentes IA Generativos',
        'descripcion': 'Agentes inteligentes avanzados con IA generativa para ventas, soporte y asesoramiento personalizado.',
        'precio_desde': '15.000€',
        'precio_hasta': '150.000€',
        'caracteristicas': ['GPT-4 & Claude', 'RAG personalizado', 'Multi-agente', 'Memoria contextual'],
        'icon': '✨'
    }
]

DESARROLLO_FAQS = [
    {
        'question': '¿Cuánto cuesta un desarrollo de software a medida en España?',
        'answer': 'Depende del alcance. Proyectos web o integraciones sencillas suelen partir de 5.000€. Plataformas complejas con múltiples módulos pueden superar los 50.000€. Tras una consulta inicial te entregamos presupuesto cerrado por fases.'
    },
    {
        'question': '¿Qué tecnologías utilizáis para el desarrollo?',
        'answer': 'Trabajamos con Python (Flask, FastAPI, Django), JavaScript/TypeScript (React, Vue, Node.js), bases de datos PostgreSQL y MongoDB, y despliegue en Docker, AWS o Azure según las necesidades del proyecto.'
    },
    {
        'question': '¿Cuánto tarda un proyecto de desarrollo a medida?',
        'answer': 'Un MVP puede estar listo en 6–10 semanas. Proyectos enterprise completos suelen requerir 3–6 meses. Usamos metodología ágil con entregas parciales cada 2 semanas.'
    },
    {
        'question': '¿Ofrecéis mantenimiento tras la entrega?',
        'answer': 'Sí. Todos los proyectos incluyen periodo de garantía post-lanzamiento. Además ofrecemos planes de mantenimiento mensual con SLA, actualizaciones de seguridad y evolutivos.'
    },
    {
        'question': '¿Podéis integrar el software con nuestros sistemas actuales?',
        'answer': 'Sí. Es uno de nuestros focos: conectamos ERPs (Odoo, SAP), CRMs, pasarelas de pago, APIs de terceros y bases de datos legacy mediante integraciones robustas y documentadas.'
    },
]

AUTOMATIZACIONES_FAQS = [
    {
        'question': '¿Qué procesos se pueden automatizar en una empresa?',
        'answer': 'Facturación y contabilidad, gestión documental, sincronización entre CRM y ERP, informes periódicos, onboarding de clientes, extracción de datos de emails o PDFs, y cualquier tarea repetitiva con reglas claras.'
    },
    {
        'question': '¿Qué diferencia hay entre RPA y automatización con APIs?',
        'answer': 'RPA simula acciones humanas en interfaces gráficas (ideal cuando no hay API). La automatización con APIs es más rápida, estable y barata de mantener cuando los sistemas lo permiten. Evaluamos ambas opciones en la consulta inicial.'
    },
    {
        'question': '¿Cuánto se ahorra con automatizaciones empresariales?',
        'answer': 'Nuestros clientes suelen recuperar la inversión en 3–6 meses. Automatizar un proceso que consume 20 h/semana puede suponer un ahorro superior a 30.000€/año en costes operativos.'
    },
    {
        'question': '¿Cuánto tarda implementar una automatización?',
        'answer': 'Automatizaciones sencillas (2–3 procesos) en 3–4 semanas. Proyectos RPA multi-departamento entre 6 y 12 semanas. Siempre con piloto inicial antes del despliegue completo.'
    },
    {
        'question': '¿Las automatizaciones requieren cambiar nuestro software actual?',
        'answer': 'No necesariamente. Diseñamos automatizaciones que conviven con tus herramientas actuales: Excel, Google Workspace, Odoo, Salesforce, y cualquier aplicación con API o interfaz web.'
    },
]

HOME_FAQS = [
    {
        'question': '¿Cómo integrar IA en mi empresa sin cambiar todo el software?',
        'answer': 'Empezamos por un piloto acotado: un chatbot, una automatización o una integración. Se conecta con tus herramientas actuales (ERP, CRM, email). Si funciona, escalamos por fases.'
    },
    {
        'question': '¿Qué procesos se pueden automatizar con IA en una pyme?',
        'answer': 'Facturación, reporting, sincronización entre sistemas, clasificación documental, respuestas a clientes frecuentes y extracción de datos de emails o PDFs. Cualquier tarea repetitiva con reglas claras es candidata.'
    },
    {
        'question': '¿Cuánto cuesta implementar IA en una empresa en España?',
        'answer': 'Un chatbot desde ~299€/mes. Automatizaciones desde ~399€/mes. Desarrollo a medida desde ~5.000€. Consultoría desde 100€/hora. El coste exacto depende del alcance; damos presupuesto cerrado tras la consulta inicial.'
    },
    {
        'question': '¿Qué es la GEO (Generative Engine Optimization)?',
        'answer': 'Es optimizar tu contenido y datos para que motores generativos (ChatGPT, Gemini, Perplexity, AI Overviews) te citen como referente. Complementa al SEO clásico: estructura clara, FAQs, schema markup y contenido verificable.',
        'link_slug': 'seo-geo-inteligencia-artificial-2026',
        'link_text': 'Leer la guía completa de SEO para IA y GEO en 2026',
    },
    {
        'question': '¿Megasoluciones trabaja solo en Madrid?',
        'answer': 'Tenemos base en Madrid y trabajamos con empresas en toda España y LATAM. Proyectos 100% remotos o híbridos según necesidad.'
    },
    {
        'question': '¿Ofrecéis mantenimiento tras el proyecto?',
        'answer': 'Sí. Todos los proyectos incluyen garantía post-lanzamiento. Planes mensuales con SLA, monitorización de automatizaciones y evolutivos.'
    },
    {
        'question': '¿Qué diferencia hay entre un chatbot genérico y uno a medida?',
        'answer': 'Un chatbot a medida conoce tus productos, procesos y tono. Se integra con tu CRM, escala a humanos y mejora con feedback real. Los genéricos suelen dar respuestas vagas y frustrar al cliente.'
    },
    {
        'question': '¿Cuánto tarda un proyecto de IA?',
        'answer': 'Piloto de automatización: 3–4 semanas. Chatbot en producción: 4–8 semanas. Plataforma a medida: 3–6 meses con entregas parciales cada 2 semanas.'
    },
]

HOME_SERVICIOS = [
    {
        'slug': 'chatbots-ia',
        'icon': '🤖',
        'titulo': 'Chatbots IA',
        'descripcion': 'Asistentes virtuales para web, WhatsApp o CRM. Atienden consultas frecuentes, cualifican leads y escalan a una persona cuando hace falta.',
        'para_quien': 'E-commerce, servicios profesionales, soporte con alto volumen de preguntas repetitivas.',
        'precio_desde': '299€/mes',
        'caracteristicas': ['Integración multicanal', 'NLP y respuestas contextuales', 'Traspaso a agente humano'],
        'cta_url': 'servicios',
        'cta_anchor': 'chatbots-ia',
        'cta_text': 'Ver chatbots IA',
    },
    {
        'slug': 'automatizaciones-rpa',
        'icon': '⚙️',
        'titulo': 'Automatización de procesos',
        'descripcion': 'Workflows, RPA y agentes de IA que conectan ERP, CRM, email y hojas de cálculo. Elimina copiar datos a mano y reduce errores operativos.',
        'para_quien': 'Operaciones, administración, finanzas, logística.',
        'precio_desde': '399€/mes',
        'caracteristicas': ['Workflows inteligentes', 'Integración ERP/CRM', 'Monitorización continua'],
        'cta_url': 'automatizaciones',
        'cta_anchor': None,
        'cta_text': 'Ver automatizaciones',
    },
    {
        'slug': 'desarrollo-software',
        'icon': '💻',
        'titulo': 'Desarrollo a medida',
        'descripcion': 'Aplicaciones web, APIs e integraciones con IA embebida. Conectamos modelos y agentes con tus sistemas existentes.',
        'para_quien': 'Empresas que necesitan una herramienta propia, no un SaaS genérico.',
        'precio_desde': '5.000€',
        'caracteristicas': ['Integración de IA en sistemas existentes', 'APIs e integraciones ERP/CRM', 'Código mantenible y escalable'],
        'cta_url': 'desarrollo_software',
        'cta_anchor': None,
        'cta_text': 'Ver desarrollo',
    },
    {
        'slug': 'consultoria-ia',
        'icon': '📊',
        'titulo': 'Consultoría IA',
        'descripcion': 'Hoja de ruta, viabilidad, selección de herramientas y formación de equipos. Para decidir bien antes de invertir.',
        'para_quien': 'Dirección, IT y responsables de transformación digital.',
        'precio_desde': '100€/hora',
        'caracteristicas': ['Análisis de viabilidad', 'Roadmap tecnológico', 'Formación de equipos'],
        'cta_url': 'contacto',
        'cta_query': 'servicio=consultoria-ia',
        'cta_anchor': None,
        'cta_text': 'Reservar consultoría',
    },
]

HOME_CASOS_USO = [
    {'sector': 'Distribución', 'problema': 'Pedidos duplicados entre CRM y ERP', 'solucion': 'Sincronización automática con workflows'},
    {'sector': 'Servicios profesionales', 'problema': 'Clasificación manual de documentos entrantes', 'solucion': 'OCR + clasificación con IA'},
    {'sector': 'Retail / e-commerce', 'problema': 'Consultas repetitivas sobre envíos y stock', 'solucion': 'Chatbot multicanal con acceso a inventario'},
    {'sector': 'Finanzas / seguros', 'problema': 'Extracción de datos de formularios PDF', 'solucion': 'Pipeline NLP + validación humana'},
    {'sector': 'RRHH / administración', 'problema': 'Onboarding manual de empleados', 'solucion': 'Automatización de altas y documentación'},
    {'sector': 'Marketing', 'problema': 'Informes semanales copiados entre herramientas', 'solucion': 'Dashboards y reporting automatizado'},
]

CONTACTO_FAQS = [
    {
        'question': '¿Cuánto tarda un proyecto de desarrollo de software?',
        'answer': 'Una web o integración sencilla puede estar lista en 4–8 semanas. Plataformas a medida con varios módulos suelen requerir 3–6 meses. Trabajamos con entregas parciales cada sprint.'
    },
    {
        'question': '¿Cómo funciona un proyecto de automatización/RPA?',
        'answer': 'Analizamos tus procesos actuales, identificamos candidatos a automatizar, diseñamos el workflow, implementamos un piloto y escalamos. Todo con documentación y formación para tu equipo.'
    },
    {
        'question': '¿Trabajáis con pymes y empresas medianas en España?',
        'answer': 'Sí. Adaptamos alcance y presupuesto al tamaño de la empresa. Tenemos experiencia con pymes, scale-ups y corporaciones en España y LATAM.'
    },
    {
        'question': '¿Ofrecéis mantenimiento y soporte post-implementación?',
        'answer': 'Sí, todos nuestros proyectos incluyen soporte continuo. Ofrecemos planes mensuales de mantenimiento, monitorización de automatizaciones y evolutivos de software.'
    },
]

RECURSOS = [
    {
        'slug': 'seo-geo-inteligencia-artificial-2026',
        'titulo': 'SEO para IA y GEO en 2026: guía de Generative Engine Optimization',
        'resumen': 'Qué es el SEO con inteligencia artificial y la GEO, cómo posicionarte en ChatGPT, Gemini y AI Overviews, y 7 acciones prácticas para empresas en España.',
        'fecha': '2026-06-07',
        'cluster': 'ia',
        'cta_servicio': 'consultoria-ia',
    },
    {
        'slug': 'automatizar-procesos-pyme',
        'titulo': 'Cómo automatizar procesos en una pyme española',
        'resumen': 'Guía práctica para identificar qué automatizar primero y calcular el ROI de las automatizaciones empresariales.',
        'fecha': '2026-05-01',
        'cluster': 'automatizaciones',
        'cta_servicio': 'automatizaciones-rpa',
    },
    {
        'slug': 'coste-desarrollo-software-2026',
        'titulo': 'Cuánto cuesta un desarrollo de software a medida en 2026',
        'resumen': 'Desglose de precios por tipo de proyecto: web, API, plataforma SaaS e integraciones con ERP/CRM.',
        'fecha': '2026-04-15',
        'cluster': 'desarrollo',
        'cta_servicio': 'desarrollo-software',
    },
    {
        'slug': 'rpa-vs-automatizacion-apis',
        'titulo': 'RPA vs automatización con APIs: qué elegir',
        'resumen': 'Comparativa técnica y económica para decidir la mejor estrategia de automatización en tu empresa.',
        'fecha': '2026-03-20',
        'cluster': 'automatizaciones',
        'cta_servicio': 'automatizaciones-rpa',
    },
    {
        'slug': 'integrar-odoo-web-crm',
        'titulo': 'Integrar Odoo con tu web y CRM: guía práctica',
        'resumen': 'Cómo conectar Odoo con ecommerce, CRM y banca sin duplicar datos ni errores manuales.',
        'fecha': '2026-02-10',
        'cluster': 'desarrollo',
        'cta_servicio': 'desarrollo-software',
    },
    {
        'slug': 'procesos-automatizar-empresa',
        'titulo': '5 procesos que toda empresa debería automatizar ya',
        'resumen': 'Los procesos con mayor retorno rápido en pymes y medianas empresas en España.',
        'fecha': '2026-01-15',
        'cluster': 'automatizaciones',
        'cta_servicio': 'automatizaciones-rpa',
    },
    {
        'slug': 'elegir-empresa-desarrollo-software',
        'titulo': 'Checklist para elegir empresa de desarrollo software en España',
        'resumen': '8 criterios clave antes de contratar desarrollo a medida o integraciones.',
        'fecha': '2025-12-01',
        'cluster': 'desarrollo',
        'cta_servicio': 'desarrollo-software',
    },
]

TESTIMONIOS = [
    {
        'nombre': 'Ana R.',
        'cargo': 'Responsable de Operaciones · Empresa de distribución (España)',
        'texto': 'Necesitábamos conectar nuestro CRM con el ERP sin contratar a dos personas más. En pocas semanas teníamos los pedidos sincronizados y el equipo dejó de duplicar trabajo.',
        'rating': 5,
        'servicio': 'automatizacion',
        'ilustrativo': True,
    },
    {
        'nombre': 'Miguel S.',
        'cargo': 'Director Comercial · Servicios B2B (Madrid)',
        'texto': 'El chatbot resuelve gran parte de las consultas de soporte sin intervención humana. Nos permitió ampliar horario de atención sin ampliar plantilla.',
        'rating': 5,
        'servicio': 'ia',
        'ilustrativo': True,
    },
    {
        'nombre': 'Elena V.',
        'cargo': 'CEO · Pyme tecnológica (España)',
        'texto': 'Lo que más valoramos es que no nos vendieron un producto cerrado. Desarrollaron una herramienta a medida que encaja con cómo trabajamos.',
        'rating': 5,
        'servicio': 'desarrollo',
        'ilustrativo': True,
    },
]

PORTFOLIO = [
    {
        'slug': 'plataforma-gestion-medida',
        'titulo': 'Plataforma de Gestión a Medida',
        'cliente': 'Empresa de servicios, España',
        'descripcion': 'ERP personalizado con módulos de facturación, inventario e integración bancaria',
        'problema': 'La empresa gestionaba pedidos, stock y facturación en hojas de cálculo desconectadas. Errores de stock y retrasos en facturación afectaban al cash-flow.',
        'solucion': 'Desarrollamos un ERP a medida con Python y React, integrado con la API bancaria y módulos de facturación automática.',
        'resultados': ['-60% tiempo en gestión administrativa', 'Facturación en 24h vs 5 días', 'Stock sincronizado en tiempo real'],
        'tecnologias': ['Python', 'React', 'PostgreSQL', 'Docker'],
        'imagen': 'portfolio-ecommerce',
        'categoria': 'Desarrollo',
        'real': False,
        'testimonial': None,
    },
    {
        'slug': 'automatizacion-erp-crm',
        'titulo': 'Automatización Integración ERP-CRM',
        'cliente': 'Distribuidora industrial, España',
        'descripcion': 'Workflows automáticos que sincronizan pedidos, stock y facturación entre Odoo y Salesforce',
        'problema': 'Dos equipos introducían los mismos pedidos en Odoo y Salesforce manualmente. Duplicidad de datos y 15 h/semana de trabajo repetitivo.',
        'solucion': 'Automatizaciones con Python y n8n: cada pedido en Salesforce crea/actualiza registros en Odoo, genera albarán y notifica al almacén.',
        'resultados': ['-40% horas manuales semanales', 'ROI en 4 meses', 'Cero duplicados de pedidos en 6 meses'],
        'tecnologias': ['Python', 'APIs REST', 'n8n', 'PostgreSQL'],
        'imagen': 'portfolio-industry',
        'categoria': 'Automatización',
        'real': True,
        'testimonial': 'Automatizaron nuestros procesos de reporting y sincronización entre departamentos. Ahorramos más de 200.000€ en el primer año.',
    },
    {
        'slug': 'portal-clientes-api-bancaria',
        'titulo': 'Portal Clientes y API Bancaria',
        'cliente': 'Entidad financiera internacional',
        'descripcion': 'Desarrollo web con integración API bancaria y panel de autogestión para 10.000+ usuarios',
        'problema': 'Los clientes no podían consultar movimientos ni gestionar productos online. Alta carga en call center.',
        'solucion': 'Portal web con autenticación segura, integración API bancaria PSD2 y panel de autogestión escalable en Azure.',
        'resultados': ['-70% consultas al call center', '10.000+ usuarios activos', 'LCP < 2s en mobile'],
        'tecnologias': ['Node.js', 'React', 'Azure', 'PostgreSQL'],
        'imagen': 'portfolio-banking',
        'categoria': 'Desarrollo',
        'real': False,
        'testimonial': None,
    },
    {
        'slug': 'rpa-documental-ocr',
        'titulo': 'RPA Documental y OCR',
        'cliente': 'Sector legal, España',
        'descripcion': 'Automatización de extracción y clasificación de contratos con 98% de precisión',
        'problema': 'Abogados dedicaban horas a clasificar y extraer datos de contratos PDF entrantes por email.',
        'solucion': 'Pipeline OCR + clasificación automática con Computer Vision y FastAPI, integrado al DMS del despacho.',
        'resultados': ['98% precisión extracción', '-80% tiempo clasificación documental', 'Integración con email entrante'],
        'tecnologias': ['Python', 'Computer Vision', 'FastAPI', 'MongoDB'],
        'imagen': 'portfolio-documents',
        'categoria': 'Automatización',
        'real': False,
        'testimonial': None,
    }
]


def sitemap_base_url() -> str:
    return HREFLANG_ES


def canonical_url() -> str:
    path = request.path or '/'
    return f"{HREFLANG_ES}{path}" if path != '/' else f"{HREFLANG_ES}/"


def hreflang_urls() -> list[tuple[str, str]]:
    path = request.path or '/'
    suffix = path if path != '/' else '/'
    return [
        ('es-ES', f"{HREFLANG_ES}{suffix}"),
        ('x-default', f"{HREFLANG_ES}{suffix}"),
    ]


def servicios_por_pilar(pilar: str) -> list:
    return [s for s in SERVICIOS if s['pilar'] == pilar]


def get_servicio(slug: str) -> dict | None:
    return next((s for s in SERVICIOS if s['slug'] == slug), None)


def todos_los_recursos() -> list[dict]:
    """Artículos estáticos + posts de vídeo publicados, ordenados por fecha desc."""
    try:
        posts = yt_db.posts_publicados()
    except Exception as e:
        print(f'[yt_posts] Error leyendo posts publicados: {e}')
        posts = []
    return sorted(RECURSOS + posts, key=lambda r: r.get('fecha', ''), reverse=True)


def get_recurso(slug: str) -> dict | None:
    articulo = next((r for r in RECURSOS if r['slug'] == slug), None)
    if articulo:
        return articulo
    try:
        return yt_db.get_post_publicado(slug)
    except Exception as e:
        print(f'[yt_posts] Error leyendo post {slug}: {e}')
        return None


def get_caso(slug: str) -> dict | None:
    return next((p for p in PORTFOLIO if p['slug'] == slug), None)


def render_recurso_body(slug: str) -> str:
    path = os.path.join(os.path.dirname(__file__), 'content', 'recursos', f'{slug}.html')
    if not os.path.isfile(path):
        return ''
    with open(path, encoding='utf-8') as f:
        return render_template_string(f.read())


def all_sitemap_paths() -> list[dict]:
    today = datetime.now().strftime('%Y-%m-%d')
    pages = [{**p, 'lastmod': today} for p in SITEMAP_PAGES]
    for r in todos_los_recursos():
        pages.append({
            'path': f"/recursos/{r['slug']}",
            'changefreq': 'monthly',
            'priority': '0.75',
            'lastmod': r.get('fecha') or today,
        })
    for p in PORTFOLIO:
        pages.append({
            'path': f"/portfolio/{p['slug']}",
            'changefreq': 'monthly',
            'priority': '0.8',
            'lastmod': today,
        })
    for entry in geo_sitemap_entries():
        pages.append({**entry, 'lastmod': today})
    return pages


def geo_index_groups() -> list[dict]:
    groups = []
    for group in GEO_INDEX_GROUPS:
        pages = []
        for slug in group['pages']:
            page = get_geo_page(slug)
            if page:
                pages.append(page)
        if pages:
            groups.append({'title': group['title'], 'pages': pages})
    return groups


@app.route('/')
def index():
    return render_template(
        'index.html',
        servicios=HOME_SERVICIOS,
        casos_uso=HOME_CASOS_USO,
        testimonios=TESTIMONIOS,
        faqs=HOME_FAQS,
    )


@app.route('/desarrollo-software')
def desarrollo_software():
    return render_template(
        'desarrollo-software.html',
        faqs=DESARROLLO_FAQS,
        servicio=get_servicio('desarrollo-software'),
    )


@app.route('/automatizaciones')
def automatizaciones():
    return render_template(
        'automatizaciones.html',
        faqs=AUTOMATIZACIONES_FAQS,
        servicio=get_servicio('automatizaciones-rpa'),
    )


@app.route('/servicios')
def servicios():
    return render_template(
        'servicios.html',
        servicios=SERVICIOS,
        servicios_desarrollo=servicios_por_pilar('desarrollo'),
        servicios_automatizacion=servicios_por_pilar('automatizacion'),
        servicios_ia=servicios_por_pilar('ia'),
        breadcrumbs=[{'name': 'Servicios', 'url': canonical_url()}],
    )


@app.route('/sobre')
def sobre():
    return render_template(
        'sobre.html',
        breadcrumbs=[{'name': 'Sobre Nosotros', 'url': canonical_url()}],
    )


@app.route('/portfolio')
def portfolio():
    return render_template(
        'portfolio.html',
        proyectos=PORTFOLIO,
        breadcrumbs=[{'name': 'Portfolio', 'url': canonical_url()}],
    )


@app.route('/portfolio/<slug>')
def portfolio_caso(slug):
    caso = get_caso(slug)
    if not caso:
        abort(404)
    servicio = 'desarrollo-software' if caso['categoria'] == 'Desarrollo' else 'automatizaciones-rpa'
    return render_template(
        'caso-exito.html',
        caso=caso,
        servicio=servicio,
        breadcrumbs=[
            {'name': 'Portfolio', 'url': url_for('portfolio', _external=True)},
            {'name': caso['titulo'], 'url': canonical_url()},
        ],
    )


@app.route('/testimonios')
def testimonios():
    return render_template(
        'testimonios.html',
        testimonios=TESTIMONIOS,
        breadcrumbs=[{'name': 'Testimonios', 'url': canonical_url()}],
    )


@app.route('/recursos')
def recursos():
    return render_template(
        'recursos.html',
        articulos=todos_los_recursos(),
        breadcrumbs=[{'name': 'Recursos', 'url': canonical_url()}],
    )


@app.route('/recursos/<slug>')
def recurso_articulo(slug):
    articulo = get_recurso(slug)
    if not articulo:
        abort(404)
    # Posts de vídeo llevan el cuerpo en BD; los artículos estáticos, en content/recursos/
    cuerpo = articulo.get('cuerpo') or render_recurso_body(slug)
    return render_template(
        'recurso-articulo.html',
        articulo=articulo,
        cuerpo=cuerpo,
        breadcrumbs=[
            {'name': 'Recursos', 'url': url_for('recursos', _external=True)},
            {'name': articulo['titulo'], 'url': canonical_url()},
        ],
    )


@app.route('/privacidad')
def privacidad():
    return render_template(
        'privacidad.html',
        breadcrumbs=[{'name': 'Privacidad', 'url': canonical_url()}],
    )


@app.route('/aviso-legal')
def aviso_legal():
    return render_template(
        'aviso-legal.html',
        breadcrumbs=[{'name': 'Aviso Legal', 'url': canonical_url()}],
    )


@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    form = ContactForm()
    servicio_param = request.args.get('servicio', '')
    if servicio_param in dict(SERVICIO_CHOICES):
        form.servicio.data = servicio_param

    if request.method == 'GET':
        session['contact_form_loaded_at'] = time()

    if form.validate_on_submit():
        client_ip = get_client_ip(
            request.headers.get('X-Forwarded-For'),
            request.remote_addr,
        )
        blog_url = canonical_url()
        akismet_spam = check_akismet_spam(
            AKISMET_API_KEY,
            blog_url=blog_url,
            client_ip=client_ip,
            user_agent=request.headers.get('User-Agent', ''),
            author=form.nombre.data,
            email=form.email.data,
            content=form.mensaje.data,
        )
        if should_silently_drop(
            request.form.get(HONEYPOT_FIELD),
            session.get('contact_form_loaded_at'),
            client_ip,
            akismet_spam=akismet_spam,
        ):
            reason = spam_block_reason(
                request.form.get(HONEYPOT_FIELD),
                session.get('contact_form_loaded_at'),
                client_ip,
                akismet_spam=akismet_spam,
            )
            print(f"Contacto bloqueado (anti-spam): {reason} ip={client_ip}")
            flash(f'¡Gracias {form.nombre.data}! Tu mensaje ha sido enviado. Te contactaremos pronto.', 'success')
            return redirect(url_for('contacto'))

        turnstile_result = verify_turnstile(
            request.form.get('cf-turnstile-response'),
            client_ip,
            TURNSTILE_SECRET_KEY,
        )
        if turnstile_result is False:
            print(f"Contacto: Turnstile inválido ip={client_ip}")
            flash('No pudimos verificar el envío. Inténtalo de nuevo.', 'error')
            session['contact_form_loaded_at'] = time()
            return render_template(
                'contacto.html',
                form=form,
                faqs=CONTACTO_FAQS,
                breadcrumbs=[{'name': 'Contacto', 'url': canonical_url()}],
                turnstile_site_key=TURNSTILE_SITE_KEY,
            )

        try:
            servicio_label = dict(SERVICIO_CHOICES).get(form.servicio.data, 'No especificado')
            source_url = canonical_url()
            msg = Message(
                subject=f'Nuevo contacto de {form.nombre.data} - Megasoluciones',
                recipients=['info@megasolucion.net'],
                reply_to=form.email.data
            )
            msg.body = f"""
Nuevo mensaje de contacto desde {source_url}

Nombre: {form.nombre.data}
Email: {form.email.data}
Teléfono: {form.telefono.data or 'No proporcionado'}
Empresa: {form.empresa.data or 'No proporcionada'}
Servicio: {servicio_label}

Mensaje:
{form.mensaje.data}

---
Enviado desde el formulario de contacto de Megasoluciones
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            msg.html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%); border-radius: 10px;">
        <h2 style="color: white; text-align: center;">Nuevo Contacto - Megasoluciones</h2>
    </div>
    <div style="max-width: 600px; margin: 20px auto; padding: 20px; background: #f9fafb; border-radius: 10px;">
        <h3 style="color: #1e3a8a;">Datos del contacto:</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Nombre:</strong></td><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{form.nombre.data}</td></tr>
            <tr><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><a href="mailto:{form.email.data}">{form.email.data}</a></td></tr>
            <tr><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Teléfono:</strong></td><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{form.telefono.data or 'No proporcionado'}</td></tr>
            <tr><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Empresa:</strong></td><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{form.empresa.data or 'No proporcionada'}</td></tr>
            <tr><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Servicio:</strong></td><td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{servicio_label}</td></tr>
        </table>
        <h3 style="color: #1e3a8a; margin-top: 20px;">Mensaje:</h3>
        <div style="background: white; padding: 15px; border-left: 4px solid #3b82f6; border-radius: 5px;">
            <p style="white-space: pre-wrap;">{form.mensaje.data}</p>
        </div>
    </div>
</body>
</html>
            """
            if app.config['MAIL_USERNAME']:
                mail.send(msg)
                print(f"Contacto: email enviado a info@megasolucion.net desde {form.email.data}")
            else:
                print('Contacto: MAIL_USERNAME no configurado, email no enviado')
            record_submission(client_ip)
            flash(f'¡Gracias {form.nombre.data}! Tu mensaje ha sido enviado. Te contactaremos pronto.', 'success')
        except Exception as e:
            print(f"Error enviando email: {str(e)}")
            flash(f'¡Gracias {form.nombre.data}! Hemos recibido tu mensaje y te contactaremos pronto.', 'success')
        return redirect(url_for('contacto'))
    return render_template(
        'contacto.html',
        form=form,
        faqs=CONTACTO_FAQS,
        breadcrumbs=[{'name': 'Contacto', 'url': canonical_url()}],
        turnstile_site_key=TURNSTILE_SITE_KEY,
    )


@app.route('/geo/')
@app.route('/geo')
def geo_index():
    return render_template(
        'geo/index.html',
        hub=GEO_HUB,
        index_groups=geo_index_groups(),
        breadcrumbs=[{'name': 'Zona Madrid', 'url': canonical_url()}],
    )


@app.route('/geo/<slug>')
def geo_page(slug):
    page = get_geo_page(slug)
    if not page:
        abort(404)
    parent_page = get_geo_page(page['parent_slug']) if page.get('parent_slug') else None
    related_pages = [
        p for s in page.get('related_slugs', [])
        if (p := get_geo_page(s)) and p['slug'] != slug
    ]
    crumbs = [{'name': 'Zona Madrid', 'url': url_for('geo_index', _external=True)}]
    if parent_page and parent_page['slug'] != slug:
        crumbs.append({
            'name': parent_page['city_name'],
            'url': url_for('geo_page', slug=parent_page['slug'], _external=True),
        })
    crumbs.append({'name': page['city_name'], 'url': canonical_url()})
    return render_template(
        'geo/page.html',
        page=page,
        parent_page=parent_page if parent_page and parent_page['slug'] != slug else None,
        related_pages=related_pages,
        breadcrumbs=crumbs,
    )


@app.route('/health')
def health():
    return {'status': 'ok', 'service': 'megasoluciones'}, 200


@app.route('/media/social/<filename>')
def social_media_file(filename):
    """Imágenes para posts sociales (Instagram requiere URL pública HTTPS)."""
    from yt_posts import social_queue
    safe = os.path.basename(filename)
    path = social_queue.resolve_image_path(safe)
    if not path:
        abort(404)
    return send_file(path, mimetype='image/jpeg', max_age=86400)


@app.route('/robots.txt')
def robots_txt():
    host = (request.host or '').split(':')[0].lower()
    if host in COM_HOSTS:
        # Permitimos el rastreo para que Google descubra el 301 → megasolucion.es
        # y consolide la señal canónica. Sin Allow, no rastrea y nunca llega a ver
        # la redirección.
        body = (
            "# megasolucion.com — alias 301 → megasolucion.es (dominio principal)\n"
            "User-agent: *\n"
            "Allow: /\n"
            f"\nSitemap: {HREFLANG_ES}/sitemap.xml\n"
        )
    else:
        body = (
            "# megasolucion.es — dominio principal Megasoluciones\n"
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /health\n"
            "Disallow: /admin\n"
            "Disallow: /admin/\n"
            f"\nSitemap: {HREFLANG_ES}/sitemap.xml\n"
        )
    return Response(body, mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    base = sitemap_base_url()
    today = datetime.now().strftime('%Y-%m-%d')
    urls = []
    for page in all_sitemap_paths():
        loc = f"{base}{page['path']}"
        lastmod = page.get('lastmod') or today
        urls.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{page['changefreq']}</changefreq>\n"
            f"    <priority>{page['priority']}</priority>\n"
            "  </url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return Response(xml, mimetype='application/xml')


@app.context_processor
def inject_globals():
    return {
        'current_year': datetime.now().year,
        'gsc_verification_token': GSC_VERIFICATION_TOKEN,
        'canonical_url': canonical_url(),
        'hreflang_urls': hreflang_urls(),
        'site_base_url': sitemap_base_url(),
        'ga4_measurement_id': GA4_MEASUREMENT_ID,
        'linkedin_url': LINKEDIN_URL,
        'x_url': X_URL,
        'servicios': SERVICIOS,
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
