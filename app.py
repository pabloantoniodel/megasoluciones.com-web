from flask import Flask, render_template, render_template_string, request, flash, redirect, url_for, Response, abort, session, send_file, g
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from flask_babel import Babel, _
from wtforms import StringField, TextAreaField, EmailField, TelField, SelectField
from wtforms.validators import DataRequired, Email
import os
from datetime import datetime
from time import time

from geo_pages import GEO_HUB, GEO_INDEX_GROUPS, geo_sitemap_entries, get_geo_page, get_geo_hub

import recursos_seo
from recursos_seo import (
    articulo_canonical_href,
    video_schema_graph,
    mostrar_video_en_articulo,
    build_actualidad_context,
    build_hub_context,
    get_articulos_relacionados,
    include_recurso_in_sitemap,
    redirect_path_for_slug,
    sitemap_priority,
)

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

GA4_LINKER_DOMAINS = (
    'megasolucion.es',
    'www.megasolucion.es',
    'megasolucion.com',
    'www.megasolucion.com',
)

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
    {'path': '/recursos', 'changefreq': 'weekly', 'priority': '0.85'},
    {'path': '/recursos/actualidad', 'changefreq': 'daily', 'priority': '0.65'},
    {'path': '/privacidad', 'changefreq': 'yearly', 'priority': '0.3'},
    {'path': '/aviso-legal', 'changefreq': 'yearly', 'priority': '0.3'},
]

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'megasoluciones-secret-key-2026')
app.config['BABEL_DEFAULT_LOCALE'] = 'es'
app.config['BABEL_SUPPORTED_LOCALES'] = ['es', 'en']

def get_locale():
    return g.get('lang', 'es')

babel = Babel(app, locale_selector=get_locale)

class I18nMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith('/en/') or path == '/en':
            environ['PATH_INFO'] = path[3:] or '/'
            environ['megasoluciones.lang'] = 'en'
        else:
            environ['megasoluciones.lang'] = 'es'
        return self.app(environ, start_response)

app.wsgi_app = I18nMiddleware(app.wsgi_app)

app.register_blueprint(admin_bp)
yt_db.init_db()


@app.after_request
def track_visit(response):
    """Estadísticas propias (tipo WP Statistics). Informado en /privacidad (RGPD)."""
    try:
        ua = request.headers.get('User-Agent', '')
        client_ip = get_client_ip(
            request.headers.get('X-Forwarded-For'),
            request.remote_addr,
        )
        if yt_stats.should_track(
            request.path, request.method, response.status_code,
            response.content_type or '', ua,
            ip=client_ip or '',
            referrer=request.headers.get('Referer', ''),
        ):
            yt_stats.track(
                path=request.path,
                referrer=request.headers.get('Referer', ''),
                ip=client_ip or '',
                user_agent=ua,
                own_host=(request.host or '').split(':')[0],
                landing_query_string=request.query_string.decode('utf-8', errors='replace'),
            )
    except Exception as e:
        print(f'[stats] after_request error: {e}')
    return response


@app.before_request
def set_language_and_redirect():
    """Establece el idioma y redirige a /en/ si es necesario en la raíz."""
    g.lang = request.environ.get('megasoluciones.lang', 'es')
    
    # Si el usuario entra en la raíz (es)
    if request.path == '/' and g.lang == 'es' and not request.args.get('lang'):
        if session.get('lang') == 'en':
            return redirect('/en/')
        elif 'lang' not in session:
            best_match = request.accept_languages.best_match(['es', 'en'])
            if best_match == 'en':
                session['lang'] = 'en'
                return redirect('/en/')
            else:
                session['lang'] = 'es'

    # Guardar preferencia si viene por URL
    if g.lang == 'en' and session.get('lang') != 'en':
        session['lang'] = 'en'
    elif g.lang == 'es' and session.get('lang') != 'es':
        session['lang'] = 'es'

    if request.args.get('lang') == 'es' and g.lang == 'en':
        session['lang'] = 'es'
        path = request.path or '/'
        return redirect(path if path != '/' else '/')

@app.context_processor
def inject_i18n():
    def i18n_url_for(endpoint, **values):
        if g.lang == 'en':
            # Generate normal url
            url = url_for(endpoint, **values)
            # Prepend /en if it's a local absolute path
            if url.startswith('/') and not url.startswith('/en/'):
                if url == '/':
                    return '/en/'
                return f'/en{url}'
            return url
        return url_for(endpoint, **values)
        
    def get_field(item, field):
        if not item:
            return ''
        if g.lang == 'en' and f'{field}_en' in item:
            val = item[f'{field}_en']
            return val if val is not None else item.get(field)
        return item.get(field)
    
    return dict(
        url_for=i18n_url_for,
        current_lang=g.lang,
        get_field=get_field,
        html_lang='en' if g.lang == 'en' else 'es',
    )

COM_HOSTS = frozenset({'megasolucion.com', 'www.megasolucion.com'})


@app.before_request
def redirect_to_primary_host():
    """301 megasolucion.com → megasolucion.es (Google Search Console cambio de dominio)."""
    host = (request.host or '').split(':')[0].lower()
    if request.path in ('/robots.txt', '/llms.txt') and (
        host in COM_HOSTS or host in REDIRECT_TO_PRIMARY_HOSTS
    ):
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
LEGACY_REDIRECTS.update(recursos_seo.RECURSOS_SLUG_REDIRECTS)


@app.before_request
def redirect_legacy_urls():
    """301 de URLs antiguas con enlaces externos para conservar el SEO."""
    path = request.path or ''
    target = LEGACY_REDIRECTS.get(path)
    if target:
        return redirect(f"{HREFLANG_ES}{target}", code=301)
    if path.startswith('/blog/') and path not in ('/blog', '/blog/'):
        slug = path.removeprefix('/blog/').strip('/')
        if slug:
            return redirect(f"{HREFLANG_ES}/recursos/{slug}", code=301)


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


SERVICIO_CHOICES_EN = {'': 'Select a service',
 'desarrollo-software': 'Custom software development',
 'automatizaciones-rpa': 'Automations and RPA',
 'chatbots-ia': 'AI Chatbots',
 'consultoria-ia': 'AI Consulting',
 'machine-learning': 'Machine Learning',
 'otro': 'Other / Not sure'}


class ContactForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    telefono = TelField('Teléfono')
    empresa = StringField('Empresa')
    servicio = SelectField('Servicio de interés', choices=SERVICIO_CHOICES, default='')
    mensaje = TextAreaField('Mensaje', validators=[DataRequired()])

SERVICIOS = [   {   'id': 1,
        'slug': 'desarrollo-software',
        'pilar': 'desarrollo',
        'titulo': 'Desarrollo de Software a Medida',
        'titulo_en': 'Custom Software Development',
        'descripcion': 'Aplicaciones web, APIs e integraciones diseñadas para tu negocio. Stack moderno, escalable y '
                       'mantenible para empresas en España.',
        'descripcion_en': 'Web applications, APIs, and integrations designed for your business. Modern, scalable, and '
                          'maintainable stack for companies in Spain.',
        'precio_desde': '5.000€',
        'caracteristicas': [   'Desarrollo a medida',
                               'APIs e integraciones',
                               'Stack moderno (Python, React, Node)',
                               'Despliegue cloud y soporte continuo'],
        'caracteristicas_en': [   'Custom development',
                                  'APIs and integrations',
                                  'Modern stack (Python, React, Node)',
                                  'Cloud deployment and continuous support'],
        'icon': '💻'},
    {   'id': 2,
        'slug': 'automatizaciones-rpa',
        'pilar': 'automatizacion',
        'titulo': 'Automatizaciones y RPA para Empresas',
        'titulo_en': 'Automations and RPA for Businesses',
        'descripcion': 'Automatización de procesos repetitivos, workflows inteligentes e integración entre sistemas '
                       'para reducir costes y errores.',
        'descripcion_en': 'Automation of repetitive processes, intelligent workflows, and system integration to reduce '
                          'costs and errors.',
        'precio_desde': '399€',
        'caracteristicas': [   'RPA empresarial',
                               'Automatizaciones con APIs',
                               'Workflows y orquestación',
                               'Monitorización 24/7'],
        'caracteristicas_en': [   'Enterprise RPA',
                                  'Automations with APIs',
                                  'Workflows and orchestration',
                                  '24/7 monitoring'],
        'icon': '⚙️'},
    {   'id': 3,
        'slug': 'chatbots-ia',
        'pilar': 'ia',
        'titulo': 'Chatbots IA Personalizados',
        'titulo_en': 'Custom AI Chatbots',
        'descripcion': 'Asistentes virtuales que atienden a tus clientes 24/7 con procesamiento de lenguaje natural '
                       'avanzado.',
        'descripcion_en': 'Virtual assistants that serve your customers 24/7 with advanced natural language '
                          'processing.',
        'precio_desde': '299€',
        'caracteristicas': [   'Integración multicanal',
                               'NLP avanzado',
                               'Aprendizaje continuo',
                               'Analytics en tiempo real'],
        'caracteristicas_en': [   'Multichannel integration',
                                  'Advanced NLP',
                                  'Continuous learning',
                                  'Real-time analytics'],
        'icon': '🤖'},
    {   'id': 4,
        'slug': 'consultoria-ia',
        'pilar': 'ia',
        'titulo': 'Consultoría Estratégica IA',
        'titulo_en': 'Strategic AI Consulting',
        'descripcion': 'Asesoramiento experto para definir tu hoja de ruta de transformación digital con inteligencia '
                       'artificial.',
        'descripcion_en': 'Expert advice to define your digital transformation roadmap with artificial intelligence.',
        'precio_desde': '100€',
        'caracteristicas': ['Análisis de viabilidad', 'ROI proyectado', 'Roadmap tecnológico', 'Formación equipos'],
        'caracteristicas_en': ['Feasibility analysis', 'Projected ROI', 'Technological roadmap', 'Team training'],
        'icon': '📊'},
    {   'id': 5,
        'slug': 'machine-learning',
        'pilar': 'ia',
        'titulo': 'Machine Learning & Modelos Predictivos',
        'titulo_en': 'Machine Learning & Predictive Models',
        'descripcion': 'Modelos de ML personalizados para predicción de demanda, detección de anomalías y análisis '
                       'predictivo.',
        'descripcion_en': 'Custom ML models for demand prediction, anomaly detection, and predictive analysis.',
        'precio_desde': '10.000€',
        'caracteristicas': ['Modelos custom', 'Entrenamiento continuo', 'Deploy cloud', 'MLOps incluido'],
        'caracteristicas_en': ['Custom models', 'Continuous training', 'Cloud deployment', 'MLOps included'],
        'icon': '🧠'},
    {   'id': 6,
        'slug': 'computer-vision',
        'pilar': 'ia',
        'titulo': 'Computer Vision',
        'titulo_en': 'Computer Vision',
        'descripcion': 'Visión artificial para reconocimiento facial, detección de objetos, OCR y control de calidad '
                       'automatizado.',
        'descripcion_en': 'Artificial vision for facial recognition, object detection, OCR, and automated quality '
                          'control.',
        'precio_desde': '8.000€',
        'caracteristicas': ['Reconocimiento de imágenes', 'Video analytics', 'OCR avanzado', 'Edge computing'],
        'caracteristicas_en': ['Image recognition', 'Video analytics', 'Advanced OCR', 'Edge computing'],
        'icon': '👁️'},
    {   'id': 7,
        'slug': 'nlp',
        'pilar': 'ia',
        'titulo': 'Procesamiento Lenguaje Natural',
        'titulo_en': 'Natural Language Processing',
        'descripcion': 'Análisis de sentimiento, extracción de información, traducción automática y generación de '
                       'contenido.',
        'descripcion_en': 'Sentiment analysis, information extraction, automatic translation, and content generation.',
        'precio_desde': '6.000€',
        'caracteristicas': ['Análisis de sentimiento', 'NER & clasificación', 'Modelos multiidioma', 'API REST'],
        'caracteristicas_en': ['Sentiment analysis', 'NER & classification', 'Multilingual models', 'REST API'],
        'icon': '📝'},
    {   'id': 8,
        'slug': 'agentes-ia',
        'pilar': 'ia',
        'titulo': 'Agentes IA Generativos',
        'titulo_en': 'Generative AI Agents',
        'descripcion': 'Agentes inteligentes avanzados con IA generativa para ventas, soporte y asesoramiento '
                       'personalizado.',
        'descripcion_en': 'Advanced intelligent agents with generative AI for sales, support, and personalized advice.',
        'precio_desde': '15.000€',
        'caracteristicas': ['GPT-4 & Claude', 'RAG personalizado', 'Multi-agente', 'Memoria contextual'],
        'caracteristicas_en': ['GPT-4 & Claude', 'Custom RAG', 'Multi-agent', 'Contextual memory'],
        'icon': '✨'}]

DESARROLLO_FAQS = [{'question': '¿Cuánto cuesta un desarrollo de software a medida en España?',
  'question_en': 'How much does custom software development cost in Spain?',
  'answer': 'Depende del alcance. Proyectos web o integraciones sencillas suelen partir de 5.000€. Plataformas '
            'complejas con múltiples módulos parten desde importes superiores según funcionalidad. Tras una consulta '
            'inicial te entregamos presupuesto cerrado por fases.',
  'answer_en': 'It depends on the scope. Web projects or simple integrations usually start at €5,000. Complex '
               'platforms with multiple modules start from higher amounts depending on functionality. After an initial '
               'consultation, we provide a fixed budget by phases.'},
 {'question': '¿Qué tecnologías utilizáis para el desarrollo?',
  'question_en': 'What technologies do you use for development?',
  'answer': 'Trabajamos con Python (Flask, FastAPI, Django), JavaScript/TypeScript (React, Vue, Node.js), bases de '
            'datos PostgreSQL y MongoDB, y despliegue en Docker, AWS o Azure según las necesidades del proyecto.',
  'answer_en': 'We work with Python (Flask, FastAPI, Django), JavaScript/TypeScript (React, Vue, Node.js), PostgreSQL '
               "and MongoDB databases, and deployment on Docker, AWS, or Azure depending on the project's needs."},
 {'question': '¿Cuánto tarda un proyecto de desarrollo a medida?',
  'question_en': 'How long does a custom development project take?',
  'answer': 'Un MVP puede estar listo en 6–10 semanas. Proyectos enterprise completos suelen requerir 3–6 meses. '
            'Usamos metodología ágil con entregas parciales cada 2 semanas.',
  'answer_en': 'An MVP can be ready in 6–10 weeks. Complete enterprise projects usually require 3–6 months. We use '
               'agile methodology with partial deliveries every 2 weeks.'},
 {'question': '¿Ofrecéis mantenimiento tras la entrega?',
  'question_en': 'Do you offer maintenance after delivery?',
  'answer': 'Sí. Todos los proyectos incluyen periodo de garantía post-lanzamiento. Además ofrecemos planes de '
            'mantenimiento mensual con SLA, actualizaciones de seguridad y evolutivos.',
  'answer_en': 'Yes. All projects include a post-launch warranty period. We also offer monthly maintenance plans with '
               'SLA, security updates, and evolutive maintenance.'},
 {'question': '¿Podéis integrar el software con nuestros sistemas actuales?',
  'question_en': 'Can you integrate the software with our current systems?',
  'answer': 'Sí. Es uno de nuestros focos: conectamos ERPs (Odoo, SAP), CRMs, pasarelas de pago, APIs de terceros y '
            'bases de datos legacy mediante integraciones robustas y documentadas.',
  'answer_en': 'Yes. It is one of our focuses: we connect ERPs (Odoo, SAP), CRMs, payment gateways, third-party APIs, '
               'and legacy databases through robust and documented integrations.'}]

AUTOMATIZACIONES_FAQS = [{'question': '¿Qué procesos se pueden automatizar en una empresa?',
  'question_en': 'What processes can be automated in a company?',
  'answer': 'Facturación y contabilidad, gestión documental, sincronización entre CRM y ERP, informes periódicos, '
            'onboarding de clientes, extracción de datos de emails o PDFs, y cualquier tarea repetitiva con reglas '
            'claras.',
  'answer_en': 'Billing and accounting, document management, synchronization between CRM and ERP, periodic reports, '
               'customer onboarding, data extraction from emails or PDFs, and any repetitive task with clear rules.'},
 {'question': '¿Qué diferencia hay entre RPA y automatización con APIs?',
  'question_en': 'What is the difference between RPA and automation with APIs?',
  'answer': 'RPA simula acciones humanas en interfaces gráficas (ideal cuando no hay API). La automatización con APIs '
            'es más rápida, estable y barata de mantener cuando los sistemas lo permiten. Evaluamos ambas opciones en '
            'la consulta inicial.',
  'answer_en': 'RPA simulates human actions in graphical interfaces (ideal when there is no API). Automation with APIs '
               'is faster, more stable, and cheaper to maintain when systems allow it. We evaluate both options in the '
               'initial consultation.'},
 {'question': '¿Cuánto se ahorra con automatizaciones empresariales?',
  'question_en': 'How much can be saved with business automations?',
  'answer': 'Nuestros clientes suelen recuperar la inversión en 3–6 meses. Automatizar un proceso que consume 20 '
            'h/semana puede suponer un ahorro superior a 30.000€/año en costes operativos.',
  'answer_en': 'Our clients usually recover their investment in 3–6 months. Automating a process that consumes 20 '
               'hours/week can result in savings of over €30,000/year in operating costs.'},
 {'question': '¿Cuánto tarda implementar una automatización?',
  'question_en': 'How long does it take to implement an automation?',
  'answer': 'Automatizaciones sencillas (2–3 procesos) en 3–4 semanas. Proyectos RPA multi-departamento entre 6 y 12 '
            'semanas. Siempre con piloto inicial antes del despliegue completo.',
  'answer_en': 'Simple automations (2–3 processes) in 3–4 weeks. Multi-department RPA projects between 6 and 12 weeks. '
               'Always with an initial pilot before full deployment.'},
 {'question': '¿Las automatizaciones requieren cambiar nuestro software actual?',
  'question_en': 'Do automations require changing our current software?',
  'answer': 'No necesariamente. Diseñamos automatizaciones que conviven con tus herramientas actuales: Excel, Google '
            'Workspace, Odoo, Salesforce, y cualquier aplicación con API o interfaz web.',
  'answer_en': 'Not necessarily. We design automations that coexist with your current tools: Excel, Google Workspace, '
               'Odoo, Salesforce, and any application with an API or web interface.'}]

HOME_FAQS = [{'question': '¿Cómo integrar IA en mi empresa sin cambiar todo el software?',
  'question_en': 'How to integrate AI into my company without changing all the software?',
  'answer': 'Empezamos por un piloto acotado: un chatbot, una automatización o una integración. Se conecta con tus '
            'herramientas actuales (ERP, CRM, email). Si funciona, escalamos por fases.',
  'answer_en': 'We start with a limited pilot: a chatbot, an automation, or an integration. It connects with your '
               'current tools (ERP, CRM, email). If it works, we scale in phases.'},
 {'question': '¿Qué procesos se pueden automatizar con IA en una pyme?',
  'question_en': 'What processes can be automated with AI in an SME?',
  'answer': 'Facturación, reporting, sincronización entre sistemas, clasificación documental, respuestas a clientes '
            'frecuentes y extracción de datos de emails o PDFs. Cualquier tarea repetitiva con reglas claras es '
            'candidata.',
  'answer_en': 'Invoicing, reporting, synchronization between systems, document classification, responses to frequent '
               'customer inquiries, and data extraction from emails or PDFs. Any repetitive task with clear rules is a '
               'candidate.'},
 {'question': '¿Cuánto cuesta implementar IA en una empresa en España?',
  'question_en': 'How much does it cost to implement AI in a company in Spain?',
  'answer': 'Un chatbot desde ~299€/mes. Automatizaciones desde ~399€/mes. Desarrollo a medida desde ~5.000€. '
            'Consultoría desde 100€/hora. El coste exacto depende del alcance; damos presupuesto cerrado tras la '
            'consulta inicial.',
  'answer_en': 'A chatbot from ~299€/month. Automations from ~399€/month. Custom development from ~5,000€. Consulting '
               'from 100€/hour. The exact cost depends on the scope; we provide a fixed quote after the initial '
               'consultation.'},
 {'question': '¿Qué es la GEO (Generative Engine Optimization)?',
  'question_en': 'What is GEO (Generative Engine Optimization)?',
  'answer': 'Es optimizar tu contenido y datos para que motores generativos (ChatGPT, Gemini, Perplexity, AI '
            'Overviews) te citen como referente. Complementa al SEO clásico: estructura clara, FAQs, schema markup y '
            'contenido verificable.',
  'answer_en': 'It is optimizing your content and data so that generative engines (ChatGPT, Gemini, Perplexity, AI '
               'Overviews) cite you as a reference. It complements classic SEO: clear structure, FAQs, schema markup, '
               'and verifiable content.',
  'link_slug': 'seo-geo-inteligencia-artificial-2026',
  'link_text': 'Leer la guía completa de SEO para IA y GEO en 2026',
  'link_text_en': 'Read the complete SEO guide for AI and GEO in 2026'},
 {'question': '¿Megasoluciones trabaja solo en Madrid?',
  'question_en': 'Does Megasoluciones only work in Madrid?',
  'answer': 'Tenemos base en Madrid y trabajamos con empresas en toda España y LATAM. Proyectos 100% remotos o '
            'híbridos según necesidad.',
  'answer_en': 'We are based in Madrid and work with companies throughout Spain and LATAM. Projects are 100% remote or '
               'hybrid as needed.'},
 {'question': '¿Ofrecéis mantenimiento tras el proyecto?',
  'question_en': 'Do you offer maintenance after the project?',
  'answer': 'Sí. Todos los proyectos incluyen garantía post-lanzamiento. Planes mensuales con SLA, monitorización de '
            'automatizaciones y evolutivos.',
  'answer_en': 'Yes. All projects include post-launch warranty. Monthly plans with SLA, automation monitoring, and '
               'evolutive updates.'},
 {'question': '¿Qué diferencia hay entre un chatbot genérico y uno a medida?',
  'question_en': 'What is the difference between a generic chatbot and a custom one?',
  'answer': 'Un chatbot a medida conoce tus productos, procesos y tono. Se integra con tu CRM, escala a humanos y '
            'mejora con feedback real. Los genéricos suelen dar respuestas vagas y frustrar al cliente.',
  'answer_en': 'A custom chatbot knows your products, processes, and tone. It integrates with your CRM, escalates to '
               'humans, and improves with real feedback. Generic ones often give vague answers and frustrate the '
               'customer.'},
 {'question': '¿Cuánto tarda un proyecto de IA?',
  'question_en': 'How long does an AI project take?',
  'answer': 'Piloto de automatización: 3–4 semanas. Chatbot en producción: 4–8 semanas. Plataforma a medida: 3–6 meses '
            'con entregas parciales cada 2 semanas.',
  'answer_en': 'Automation pilot: 3–4 weeks. Chatbot in production: 4–8 weeks. Custom platform: 3–6 months with '
               'partial deliveries every 2 weeks.'}]

HOME_SERVICIOS = [{'slug': 'chatbots-ia',
  'icon': '🤖',
  'titulo': 'Chatbots IA',
  'titulo_en': 'AI Chatbots',
  'descripcion': 'Asistentes virtuales para web, WhatsApp o CRM. Atienden consultas frecuentes, cualifican leads y '
                 'escalan a una persona cuando hace falta.',
  'descripcion_en': 'Virtual assistants for web, WhatsApp, or CRM. They handle frequent inquiries, qualify leads, and '
                    'escalate to a person when necessary.',
  'para_quien': 'E-commerce, servicios profesionales, soporte con alto volumen de preguntas repetitivas.',
  'para_quien_en': 'E-commerce, professional services, support with a high volume of repetitive questions.',
  'precio_desde': '299€/mes',
  'caracteristicas': ['Integración multicanal', 'NLP y respuestas contextuales', 'Traspaso a agente humano'],
  'caracteristicas_en': ['Multichannel integration', 'NLP and contextual responses', 'Transfer to human agent'],
  'cta_url': 'servicios',
  'cta_anchor': 'chatbots-ia',
  'cta_text': 'Ver chatbots IA',
  'cta_text_en': 'See AI chatbots'},
 {'slug': 'automatizaciones-rpa',
  'icon': '⚙️',
  'titulo': 'Automatización de procesos',
  'titulo_en': 'Process Automation',
  'descripcion': 'Workflows, RPA y agentes de IA que conectan ERP, CRM, email y hojas de cálculo. Elimina copiar datos '
                 'a mano y reduce errores operativos.',
  'descripcion_en': 'Workflows, RPA, and AI agents that connect ERP, CRM, email, and spreadsheets. Eliminates manual '
                    'data copying and reduces operational errors.',
  'para_quien': 'Operaciones, administración, finanzas, logística.',
  'para_quien_en': 'Operations, administration, finance, logistics.',
  'precio_desde': '399€/mes',
  'caracteristicas': ['Workflows inteligentes', 'Integración ERP/CRM', 'Monitorización continua'],
  'caracteristicas_en': ['Intelligent workflows', 'ERP/CRM integration', 'Continuous monitoring'],
  'cta_url': 'automatizaciones',
  'cta_anchor': None,
  'cta_text': 'Ver automatizaciones',
  'cta_text_en': 'See automations'},
 {'slug': 'desarrollo-software',
  'icon': '💻',
  'titulo': 'Desarrollo a medida',
  'titulo_en': 'Custom Development',
  'descripcion': 'Aplicaciones web, APIs e integraciones con IA embebida. Conectamos modelos y agentes con tus '
                 'sistemas existentes.',
  'descripcion_en': 'Web applications, APIs, and integrations with embedded AI. We connect models and agents with your '
                    'existing systems.',
  'para_quien': 'Empresas que necesitan una herramienta propia, no un SaaS genérico.',
  'para_quien_en': 'Companies that need their own tool, not a generic SaaS.',
  'precio_desde': '5.000€',
  'caracteristicas': ['Integración de IA en sistemas existentes',
                      'APIs e integraciones ERP/CRM',
                      'Código mantenible y escalable'],
  'caracteristicas_en': ['AI integration in existing systems',
                         'APIs and ERP/CRM integrations',
                         'Maintainable and scalable code'],
  'cta_url': 'desarrollo_software',
  'cta_anchor': None,
  'cta_text': 'Ver desarrollo',
  'cta_text_en': 'See development'},
 {'slug': 'consultoria-ia',
  'icon': '📊',
  'titulo': 'Consultoría IA',
  'titulo_en': 'AI Consulting',
  'descripcion': 'Hoja de ruta, viabilidad, selección de herramientas y formación de equipos. Para decidir bien antes '
                 'de invertir.',
  'descripcion_en': 'Roadmap, feasibility, tool selection, and team training. To make informed decisions before '
                    'investing.',
  'para_quien': 'Dirección, IT y responsables de transformación digital.',
  'para_quien_en': 'Management, IT, and digital transformation leaders.',
  'precio_desde': '100€/hora',
  'caracteristicas': ['Análisis de viabilidad', 'Roadmap tecnológico', 'Formación de equipos'],
  'caracteristicas_en': ['Feasibility analysis', 'Technological roadmap', 'Team training'],
  'cta_url': 'contacto',
  'cta_query': 'servicio=consultoria-ia',
  'cta_anchor': None,
  'cta_text': 'Reservar consultoría',
  'cta_text_en': 'Book consulting'}]

HOME_CASOS_USO = [{'sector': 'Distribución',
  'sector_en': 'Distribution',
  'problema': 'Pedidos duplicados entre CRM y ERP',
  'problema_en': 'Duplicate orders between CRM and ERP',
  'solucion': 'Sincronización automática con workflows',
  'solucion_en': 'Automatic synchronization with workflows'},
 {'sector': 'Servicios profesionales',
  'sector_en': 'Professional services',
  'problema': 'Clasificación manual de documentos entrantes',
  'problema_en': 'Manual classification of incoming documents',
  'solucion': 'OCR + clasificación con IA',
  'solucion_en': 'OCR + AI classification'},
 {'sector': 'Retail / e-commerce',
  'sector_en': 'Retail / e-commerce',
  'problema': 'Consultas repetitivas sobre envíos y stock',
  'problema_en': 'Repetitive inquiries about shipments and stock',
  'solucion': 'Chatbot multicanal con acceso a inventario',
  'solucion_en': 'Multichannel chatbot with inventory access'},
 {'sector': 'Finanzas / seguros',
  'sector_en': 'Finance / insurance',
  'problema': 'Extracción de datos de formularios PDF',
  'problema_en': 'Data extraction from PDF forms',
  'solucion': 'Pipeline NLP + validación humana',
  'solucion_en': 'NLP pipeline + human validation'},
 {'sector': 'RRHH / administración',
  'sector_en': 'HR / administration',
  'problema': 'Onboarding manual de empleados',
  'problema_en': 'Manual employee onboarding',
  'solucion': 'Automatización de altas y documentación',
  'solucion_en': 'Automation of registrations and documentation'},
 {'sector': 'Marketing',
  'sector_en': 'Marketing',
  'problema': 'Informes semanales copiados entre herramientas',
  'problema_en': 'Weekly reports copied between tools',
  'solucion': 'Dashboards y reporting automatizado',
  'solucion_en': 'Automated dashboards and reporting'}]

CONTACTO_FAQS = [{'question': '¿Cuánto tarda un proyecto de desarrollo de software?',
  'question_en': 'How long does a software development project take?',
  'answer': 'Una web o integración sencilla puede estar lista en 4–8 semanas. Plataformas a medida con varios módulos '
            'suelen requerir 3–6 meses. Trabajamos con entregas parciales cada sprint.',
  'answer_en': 'A simple website or integration can be ready in 4–8 weeks. Custom platforms with multiple modules '
               'usually require 3–6 months. We work with partial deliveries each sprint.'},
 {'question': '¿Cómo funciona un proyecto de automatización/RPA?',
  'question_en': 'How does an automation/RPA project work?',
  'answer': 'Analizamos tus procesos actuales, identificamos candidatos a automatizar, diseñamos el workflow, '
            'implementamos un piloto y escalamos. Todo con documentación y formación para tu equipo.',
  'answer_en': 'We analyze your current processes, identify candidates for automation, design the workflow, implement '
               'a pilot, and scale up. All with documentation and training for your team.'},
 {'question': '¿Trabajáis con pymes y empresas medianas en España?',
  'question_en': 'Do you work with SMEs and medium-sized companies in Spain?',
  'answer': 'Sí. Adaptamos alcance y presupuesto al tamaño de la empresa. Tenemos experiencia con pymes, scale-ups y '
            'corporaciones en España y LATAM.',
  'answer_en': 'Yes. We adapt scope and budget to the size of the company. We have experience with SMEs, scale-ups, '
               'and corporations in Spain and LATAM.'},
 {'question': '¿Ofrecéis mantenimiento y soporte post-implementación?',
  'question_en': 'Do you offer post-implementation maintenance and support?',
  'answer': 'Sí, todos nuestros proyectos incluyen soporte continuo. Ofrecemos planes mensuales de mantenimiento, '
            'monitorización de automatizaciones y evolutivos de software.',
  'answer_en': 'Yes, all our projects include continuous support. We offer monthly maintenance plans, automation '
               'monitoring, and software evolution.'},
 {'question': '¿Qué incluye la primera consulta?',
  'question_en': 'What does the first consultation include?',
  'answer': 'Auditoría de procesos con diagrama BPMN, análisis de oportunidades (automatización, desarrollo o IA), '
            'estudio de vulnerabilidades técnicas y un roadmap por fases. Sin compromiso; con entregables claros antes '
            'de presupuestar.',
  'answer_en': 'Process audit with BPMN diagram, opportunity analysis (automation, development, or AI), technical '
               'vulnerability study, and a phased roadmap. No obligation; with clear deliverables before budgeting.'}]

PRIMERA_CONSULTA_PASOS_META = [{'num': 1,
  'titulo': 'Auditoría de procesos',
  'titulo_en': 'Process Audit',
  'badge': 'Dibujo BPMN',
  'badge_en': 'BPMN Drawing',
  'desc': 'Taller con tu equipo, entrevistas y diagrama BPMN del flujo real (no del PowerPoint).',
  'desc_en': 'Workshop with your team, interviews, and BPMN diagram of the real flow (not the PowerPoint).',
  'anchor': 'paso-1-auditoria-bpmn',
  'entregables': ['Diagrama BPMN 2.0 (PDF + editable)',
                  'Inventario de actores y sistemas',
                  'Cuellos de botella y tiempos por etapa'],
  'entregables_en': ['BPMN 2.0 Diagram (PDF + editable)',
                     'Inventory of actors and systems',
                     'Bottlenecks and stage times'],
  'ejemplos': [{'slug': 'automatizar-pyme-sin-direccion-error-estrategia',
                'label': 'Por qué mapear antes de automatizar',
                'label_en': 'Why map before automating'},
               {'slug': 'automatizar-procesos-pyme',
                'label': 'Procesos típicos en pymes',
                'label_en': 'Typical processes in SMEs'}],
  'pagina_label': 'Ver metodología y entregables',
  'pagina_label_en': 'View methodology and deliverables'},
 {'num': 2,
  'titulo': 'Análisis de oportunidades',
  'titulo_en': 'Opportunity Analysis',
  'badge': 'Impacto · coste · viabilidad',
  'badge_en': 'Impact · cost · feasibility',
  'desc': 'Matriz de priorización: qué automatizar, desarrollar o potenciar con IA y por qué.',
  'desc_en': 'Prioritization matrix: what to automate, develop, or enhance with AI and why.',
  'anchor': 'paso-2-oportunidades',
  'entregables': ['Matriz impacto / esfuerzo / riesgo',
                  'Estimación orientativa de ROI',
                  'Recomendación RPA, API, desarrollo o IA'],
  'entregables_en': ['Impact / effort / risk matrix',
                     'Indicative ROI estimation',
                     'RPA, API, development or AI recommendation'],
  'ejemplos': [{'slug': 'rpa-vs-automatizacion-apis', 'label': 'RPA vs APIs', 'label_en': 'RPA vs APIs'},
               {'slug': 'procesos-automatizar-empresa',
                'label': 'Procesos con más ROI',
                'label_en': 'Processes with the most ROI'}],
  'pagina_label': 'Ver metodología y entregables',
  'pagina_label_en': 'View methodology and deliverables'},
 {'num': 3,
  'titulo': 'Estudio de vulnerabilidades',
  'titulo_en': 'Vulnerability Study',
  'badge': 'Datos · integraciones · cumplimiento',
  'badge_en': 'Data · integrations · compliance',
  'desc': 'Checklist técnico y legal antes de invertir: datos, APIs, continuidad y RGPD.',
  'desc_en': 'Technical and legal checklist before investing: data, APIs, continuity, and GDPR.',
  'anchor': 'paso-3-vulnerabilidades',
  'entregables': ['Informe de riesgos técnicos y de datos',
                  'Mapa de integraciones y dependencias',
                  'Medidas de mitigación priorizadas'],
  'entregables_en': ['Technical and data risk report',
                     'Map of integrations and dependencies',
                     'Prioritized mitigation measures'],
  'ejemplos': [{'slug': 'integrar-datos-ia-metodos-estrategias',
                'label': 'Integrar datos en IA con seguridad',
                'label_en': 'Integrate data into AI securely'},
               {'endpoint': 'privacidad',
                'label': 'Tratamiento de datos (RGPD)',
                'label_en': 'Data processing (GDPR)'}],
  'pagina_label': 'Ver metodología y entregables',
  'pagina_label_en': 'View methodology and deliverables'},
 {'num': 4,
  'titulo': 'Roadmap técnico',
  'titulo_en': 'Technical Roadmap',
  'badge': 'Piloto · integración · escala',
  'badge_en': 'Pilot · integration · scale',
  'desc': 'Plan por fases con plazos, dependencias, criterios de éxito y presupuesto orientativo.',
  'desc_en': 'Phase plan with timelines, dependencies, success criteria, and indicative budget.',
  'anchor': 'paso-4-roadmap',
  'entregables': ['Roadmap fase 0 (piloto) · fase 1 · fase 2',
                  'Cronograma y responsables internos',
                  'Propuesta económica por fases (si procede)'],
  'entregables_en': ['Roadmap phase 0 (pilot) · phase 1 · phase 2',
                     'Timeline and internal responsibilities',
                     'Economic proposal by phases (if applicable)'],
  'ejemplos': [{'slug': 'coste-desarrollo-software-2026',
                'label': 'Cómo presupuestamos desarrollo',
                'label_en': 'How we budget development'},
               {'endpoint': 'portfolio_caso',
                'slug': 'automatizacion-erp-crm',
                'label': 'Caso piloto ERP-CRM',
                'label_en': 'ERP-CRM pilot case'}],
  'pagina_label': 'Ver metodología y entregables',
  'pagina_label_en': 'View methodology and deliverables'}]


def primera_consulta_pasos() -> list[dict]:
    """Pasos del roadmap con URLs resueltas para plantillas."""
    articulo_url = url_for('recurso_articulo', slug='primera-consulta-roadmap-auditoria-bpmn')
    pasos = []
    lang = getattr(g, 'lang', 'es')
    for meta in PRIMERA_CONSULTA_PASOS_META:
        def lf(field):
            if lang == 'en' and f'{field}_en' in meta:
                return meta[f'{field}_en']
            return meta.get(field)

        paso = {
            'num': meta['num'],
            'titulo': lf('titulo'),
            'badge': lf('badge'),
            'desc': lf('desc'),
            'anchor': meta['anchor'],
            'url': f"{articulo_url}#{meta['anchor']}",
            'pagina_label': lf('pagina_label') or ('View methodology and deliverables' if lang == 'en' else 'Ver metodología y entregables'),
            'entregables': lf('entregables') or meta.get('entregables', []),
        }
        ejemplos = []
        for ex in meta['ejemplos']:
            label = ex.get('label_en') if lang == 'en' and ex.get('label_en') else ex['label']
            item = {'label': label}
            if ex.get('endpoint') == 'portfolio_caso':
                item['url'] = url_for('portfolio_caso', slug=ex['slug'])
            elif ex.get('endpoint'):
                item['url'] = url_for(ex['endpoint'])
            else:
                item['url'] = url_for('recurso_articulo', slug=ex['slug'])
            ejemplos.append(item)
        paso['ejemplos'] = ejemplos
        pasos.append(paso)
    return pasos


def localize_contact_form(form: ContactForm) -> None:
    """Etiquetas y opciones del formulario según idioma."""
    labels_es = {
        'nombre': 'Nombre',
        'email': 'Email',
        'telefono': 'Teléfono',
        'empresa': 'Empresa',
        'servicio': 'Servicio de interés',
        'mensaje': 'Mensaje',
    }
    labels_en = {
        'nombre': 'Name',
        'email': 'Email',
        'telefono': 'Phone',
        'empresa': 'Company',
        'servicio': 'Service of interest',
        'mensaje': 'Message',
    }
    labels = labels_en if g.lang == 'en' else labels_es
    for field_name, text in labels.items():
        getattr(form, field_name).label.text = text
    if g.lang == 'en':
        form.servicio.choices = [(v, SERVICIO_CHOICES_EN.get(v, l)) for v, l in SERVICIO_CHOICES]
    else:
        form.servicio.choices = SERVICIO_CHOICES


RECURSOS = [   {   'slug': 'itinerarios-turisticos-ia-web-demo-publica',
        'titulo': 'Itinerarios turísticos con IA: de la hoja de cálculo a una web lista para demo pública',
        'titulo_en': 'Tourist itineraries with AI: from spreadsheet to a web ready for public demo',
        'resumen': 'Cómo convertir un catálogo de lugares de interés en una plataforma que genera rutas '
                   'personalizadas, gestiona varias ciudades desde un panel admin y se expone en internet en un solo '
                   'paso — sin reescribir datos ni perder trazabilidad.',
        'resumen_en': 'How to turn a catalog of points of interest into a platform that generates personalized routes, '
                      'manages multiple cities from an admin panel, and is exposed on the internet in one step — '
                      'without rewriting data or losing traceability.',
        'fecha': '2026-06-27',
        'fecha_modificacion': '2026-06-27',
        'cluster': 'desarrollo',
        'tipo': 'noticia',
        'intencion': 'noticia',
        'keyword_principal': 'itinerarios turisticos ia plataforma web',
        'relacionados': [   'elegir-empresa-desarrollo-software',
                            'coste-desarrollo-software-2026',
                            'desarrolladores-ia-gestion-automatizacion-empresas'],
        'cta_servicio': 'desarrollo-software',
        'imagen': 'images/recursos/itinerarios-turisticos-ia-web-demo-publica.png'},
    {   'slug': 'primera-consulta-roadmap-auditoria-bpmn',
        'titulo': 'Primera consulta: roadmap de auditoría BPMN, oportunidades y roadmap técnico',
        'titulo_en': 'First consultation: BPMN audit roadmap, opportunities, and technical roadmap',
        'resumen': 'Metodología completa de la primera consulta: taller BPMN con diagrama entregable, matriz de '
                   'oportunidades, informe de vulnerabilidades y roadmap técnico por fases.',
        'resumen_en': 'Complete methodology of the first consultation: BPMN workshop with deliverable diagram, '
                      'opportunity matrix, vulnerability report, and phased technical roadmap.',
        'fecha': '2026-06-25',
        'fecha_modificacion': '2026-06-25',
        'cluster': 'automatizaciones',
        'tipo': 'soporte',
        'intencion': 'comercial',
        'keyword_principal': 'primera consulta auditoria procesos bpmn roadmap',
        'relacionados': [   'automatizar-procesos-pyme',
                            'automatizar-pyme-sin-direccion-error-estrategia',
                            'elegir-empresa-desarrollo-software'],
        'cta_servicio': 'consultoria-ia',
        'imagen': 'images/primera-consulta-roadmap.png'},
    {   'slug': 'automatizar-pyme-sin-direccion-error-estrategia',
        'titulo': 'Automatizar una pyme sin procesos claros: por qué la tecnología no arregla el desorden',
        'titulo_en': "Automating an SME without clear processes: why technology doesn't fix the mess",
        'resumen': 'Muchas pymes quieren automatizar antes de definir procesos, roles y datos. Megasoluciones explica '
                   'cómo evitar proyectos de IA y RPA que solo aceleran el caos operativo.',
        'resumen_en': 'Many SMEs want to automate before defining processes, roles, and data. Megasoluciones explains '
                      'how to avoid AI and RPA projects that only accelerate operational chaos.',
        'fecha': '2026-06-22',
        'fecha_modificacion': '2026-06-22',
        'cluster': 'automatizaciones',
        'tipo': 'soporte',
        'intencion': 'informacional',
        'keyword_principal': 'automatizacion pyme procesos claros estrategia',
        'relacionados': [   'automatizar-procesos-pyme',
                            'desarrolladores-ia-gestion-automatizacion-empresas',
                            'rpa-vs-automatizacion-apis'],
        'cta_servicio': 'automatizaciones-rpa'},
    {   'slug': 'claude-fable-5-ia-local-estrategia-empresas',
        'titulo': 'Claude Fable 5 y la estrategia híbrida de IA para empresas',
        'titulo_en': 'Claude Fable 5 and the hybrid AI strategy for companies',
        'resumen': 'La retirada de Claude Fable 5 expone la dependencia de la IA en la nube. Megasoluciones explica '
                   'cómo combinar modelos locales y cloud con integración real para pymes.',
        'resumen_en': 'The withdrawal of Claude Fable 5 exposes the dependence on cloud AI. Megasoluciones explains '
                      'how to combine local and cloud models with real integration for SMEs.',
        'fecha': '2026-06-22',
        'fecha_modificacion': '2026-06-22',
        'cluster': 'ia',
        'tipo': 'soporte',
        'intencion': 'informacional',
        'keyword_principal': 'ia local estrategia empresas claude fable',
        'relacionados': [   'desarrolladores-ia-gestion-automatizacion-empresas',
                            'integrar-datos-ia-metodos-estrategias',
                            'seo-geo-inteligencia-artificial-2026'],
        'cta_servicio': 'consultoria-ia'},
    {   'slug': 'agencia-ia-madrid-apuesta-comunidad-pymes',
        'titulo': 'Agencia de IA en Madrid: la apuesta de la Comunidad de Madrid y qué significa para tu pyme',
        'titulo_en': 'AI Agency in Madrid: the bet of the Community of Madrid and what it means for your SME',
        'resumen': 'Estrategia IA 2030, LADIA, Centro de Excelencia y EDIH Madrid Region: qué impulsa la Comunidad de '
                   'Madrid en inteligencia artificial y cómo una pyme puede aprovecharlo.',
        'resumen_en': 'AI Strategy 2030, LADIA, Center of Excellence, and EDIH Madrid Region: what drives the '
                      'Community of Madrid in artificial intelligence and how an SME can benefit from it.',
        'fecha': '2026-06-19',
        'fecha_modificacion': '2026-06-19',
        'cluster': 'ia',
        'tipo': 'soporte',
        'intencion': 'comercial',
        'keyword_principal': 'agencia ia madrid pymes',
        'relacionados': ['seo-geo-inteligencia-artificial-2026', 'desarrolladores-ia-gestion-automatizacion-empresas'],
        'cta_servicio': 'consultoria-ia',
        'imagen': 'images/recursos/agencia-ia-madrid-apuesta-comunidad-pymes.jpg'},
    {   'slug': 'desarrolladores-ia-gestion-automatizacion-empresas',
        'titulo': 'Desarrolladores e IA en empresas: por qué un modelo doméstico no sustituye la producción',
        'titulo_en': "Developers and AI in companies: why a home model doesn't replace production",
        'resumen': 'La IA casera sirve para probar ideas, pero gestionar y automatizar una empresa exige '
                   'integraciones, seguridad y software en producción.',
        'resumen_en': 'Home AI is useful for testing ideas, but managing and automating a company requires '
                      'integrations, security, and production software.',
        'fecha': '2026-06-13',
        'fecha_modificacion': '2026-06-13',
        'cluster': 'ia',
        'tipo': 'soporte',
        'intencion': 'informacional',
        'keyword_principal': 'ia empresas produccion desarrolladores',
        'relacionados': ['seo-geo-inteligencia-artificial-2026', 'elegir-empresa-desarrollo-software'],
        'cta_servicio': 'desarrollo-software',
        'imagen': 'images/recursos/desarrolladores-ia-gestion-automatizacion-empresas.jpg'},
    {   'slug': 'seo-geo-inteligencia-artificial-2026',
        'titulo': 'SEO para IA y GEO en 2026: guía de Generative Engine Optimization',
        'titulo_en': 'SEO for AI and GEO in 2026: Generative Engine Optimization guide',
        'resumen': 'Qué es el SEO con inteligencia artificial y la GEO, cómo posicionarte en ChatGPT, Gemini y AI '
                   'Overviews, y 7 acciones prácticas para empresas en España.',
        'resumen_en': 'What is SEO with artificial intelligence and GEO, how to position yourself in ChatGPT, Gemini, '
                      'and AI Overviews, and 7 practical actions for companies in Spain.',
        'fecha': '2026-06-07',
        'fecha_modificacion': '2026-06-07',
        'cluster': 'ia',
        'tipo': 'pilar',
        'intencion': 'informacional',
        'keyword_principal': 'seo geo inteligencia artificial',
        'relacionados': [   'agencia-ia-madrid-apuesta-comunidad-pymes',
                            'desarrolladores-ia-gestion-automatizacion-empresas'],
        'cta_servicio': 'consultoria-ia'},
    {   'slug': 'memoria-persistente-agentes-ia-desarrollo',
        'titulo': 'Memoria persistente en agentes de IA: capturar conocimiento técnico sin documentación manual',
        'titulo_en': 'Persistent memory in AI agents: capturing technical knowledge without manual documentation',
        'resumen': 'Por qué los agentes sin memoria repiten errores y cómo diseñar memoria persistente en desarrollo y '
                   'automatización empresarial.',
        'resumen_en': 'Why agents without memory repeat errors and how to design persistent memory in business '
                      'development and automation.',
        'fecha': '2026-06-20',
        'fecha_modificacion': '2026-06-20',
        'cluster': 'automatizaciones',
        'tipo': 'soporte',
        'intencion': 'informacional',
        'keyword_principal': 'memoria persistente agentes ia desarrollo',
        'relacionados': [   'integrar-datos-ia-metodos-estrategias',
                            'automatizar-procesos-pyme',
                            'desarrolladores-ia-gestion-automatizacion-empresas'],
        'cta_servicio': 'automatizaciones-rpa',
        'imagen': 'images/recursos/memoria-persistente-agentes-ia-desarrollo.jpg'},
    {   'slug': 'integrar-datos-ia-metodos-estrategias',
        'titulo': 'Cómo integrar tus datos en una IA: métodos y estrategias',
        'titulo_en': 'How to integrate your data into an AI: methods and strategies',
        'resumen': 'Context stuffing, MCP, CLI y RAG explicados con criterio de producción. Cómo elegir el método '
                   'según desarrollo y automatización empresarial.',
        'resumen_en': 'Context stuffing, MCP, CLI, and RAG explained with production criteria. How to choose the '
                      'method according to business development and automation.',
        'fecha': '2026-06-21',
        'fecha_modificacion': '2026-06-21',
        'cluster': 'desarrollo',
        'tipo': 'soporte',
        'intencion': 'informacional',
        'keyword_principal': 'integrar datos ia metodos rag mcp',
        'relacionados': [   'integrar-odoo-web-crm',
                            'memoria-persistente-agentes-ia-desarrollo',
                            'rpa-vs-automatizacion-apis'],
        'cta_servicio': 'desarrollo-software'},
    {   'slug': 'automatizar-procesos-pyme',
        'titulo': 'Cómo automatizar procesos en una pyme española',
        'titulo_en': 'How to automate processes in a Spanish SME',
        'resumen': 'Guía práctica para identificar qué automatizar primero y calcular el ROI de las automatizaciones '
                   'empresariales.',
        'resumen_en': 'Practical guide to identify what to automate first and calculate the ROI of business '
                      'automations.',
        'fecha': '2026-05-01',
        'fecha_modificacion': '2026-05-01',
        'cluster': 'automatizaciones',
        'tipo': 'pilar',
        'intencion': 'informacional',
        'keyword_principal': 'automatizar procesos pyme',
        'relacionados': [   'memoria-persistente-agentes-ia-desarrollo',
                            'rpa-vs-automatizacion-apis',
                            'procesos-automatizar-empresa'],
        'cta_servicio': 'automatizaciones-rpa'},
    {   'slug': 'coste-desarrollo-software-2026',
        'titulo': 'Cuánto cuesta un desarrollo de software a medida en 2026',
        'titulo_en': 'How much does custom software development cost in 2026',
        'resumen': 'Desglose de precios por tipo de proyecto: web, API, plataforma SaaS e integraciones con ERP/CRM.',
        'resumen_en': 'Price breakdown by project type: web, API, SaaS platform, and integrations with ERP/CRM.',
        'fecha': '2026-04-15',
        'fecha_modificacion': '2026-04-15',
        'cluster': 'desarrollo',
        'tipo': 'soporte',
        'intencion': 'comercial',
        'keyword_principal': 'coste desarrollo software a medida',
        'relacionados': ['elegir-empresa-desarrollo-software', 'integrar-odoo-web-crm'],
        'cta_servicio': 'desarrollo-software'},
    {   'slug': 'rpa-vs-automatizacion-apis',
        'titulo': 'RPA vs automatización con APIs: qué elegir',
        'titulo_en': 'RPA vs automation with APIs: what to choose',
        'resumen': 'Comparativa técnica y económica para decidir la mejor estrategia de automatización en tu empresa.',
        'resumen_en': 'Technical and economic comparison to decide the best automation strategy for your company.',
        'fecha': '2026-03-20',
        'fecha_modificacion': '2026-03-20',
        'cluster': 'automatizaciones',
        'tipo': 'soporte',
        'intencion': 'informacional',
        'keyword_principal': 'rpa vs automatizacion apis',
        'relacionados': ['automatizar-procesos-pyme', 'procesos-automatizar-empresa'],
        'cta_servicio': 'automatizaciones-rpa'},
    {   'slug': 'integrar-odoo-web-crm',
        'titulo': 'Integrar Odoo con tu web y CRM: guía práctica',
        'titulo_en': 'Integrate Odoo with your web and CRM: practical guide',
        'resumen': 'Cómo conectar Odoo con ecommerce, CRM y banca sin duplicar datos ni errores manuales.',
        'resumen_en': 'How to connect Odoo with ecommerce, CRM, and banking without duplicating data or manual errors.',
        'fecha': '2026-02-10',
        'fecha_modificacion': '2026-02-10',
        'cluster': 'desarrollo',
        'tipo': 'soporte',
        'intencion': 'informacional',
        'keyword_principal': 'integrar odoo web crm',
        'relacionados': ['elegir-empresa-desarrollo-software', 'integrar-datos-ia-metodos-estrategias'],
        'cta_servicio': 'desarrollo-software'},
    {   'slug': 'procesos-automatizar-empresa',
        'titulo': '5 procesos que toda empresa debería automatizar ya',
        'titulo_en': '5 processes every company should automate now',
        'resumen': 'Los procesos con mayor retorno rápido en pymes y medianas empresas en España.',
        'resumen_en': 'The processes with the fastest return in SMEs and medium-sized companies in Spain.',
        'fecha': '2026-01-15',
        'fecha_modificacion': '2026-01-15',
        'cluster': 'automatizaciones',
        'tipo': 'soporte',
        'intencion': 'informacional',
        'keyword_principal': 'procesos automatizar empresa',
        'relacionados': ['automatizar-procesos-pyme', 'rpa-vs-automatizacion-apis'],
        'cta_servicio': 'automatizaciones-rpa'},
    {   'slug': 'elegir-empresa-desarrollo-software',
        'titulo': 'Checklist para elegir empresa de desarrollo software en España',
        'titulo_en': 'Checklist to choose a software development company in Spain',
        'resumen': '8 criterios clave antes de contratar desarrollo a medida o integraciones.',
        'resumen_en': '8 key criteria before hiring custom development or integrations.',
        'fecha': '2025-12-01',
        'fecha_modificacion': '2025-12-01',
        'cluster': 'desarrollo',
        'tipo': 'pilar',
        'intencion': 'comercial',
        'keyword_principal': 'elegir empresa desarrollo software',
        'relacionados': ['coste-desarrollo-software-2026', 'integrar-odoo-web-crm'],
        'cta_servicio': 'desarrollo-software'}]

TESTIMONIOS = [{'nombre': 'Ana R.',
  'cargo': 'Responsable de Operaciones · Empresa de distribución (España)',
  'texto': 'Necesitábamos conectar nuestro CRM con el ERP sin contratar a dos personas más. En pocas semanas teníamos '
           'los pedidos sincronizados y el equipo dejó de duplicar trabajo.',
  'texto_en': 'We needed to connect our CRM with the ERP without hiring two more people. Within a few weeks, we had '
              'the orders synchronized, and the team stopped duplicating work.',
  'rating': 5,
  'servicio': 'automatizacion',
  'ilustrativo': True},
 {'nombre': 'Miguel S.',
  'cargo': 'Director Comercial · Servicios B2B (Madrid)',
  'texto': 'El chatbot resuelve gran parte de las consultas de soporte sin intervención humana. Nos permitió ampliar '
           'horario de atención sin ampliar plantilla.',
  'texto_en': 'The chatbot resolves a large part of the support queries without human intervention. It allowed us to '
              'extend service hours without increasing staff.',
  'rating': 5,
  'servicio': 'ia',
  'ilustrativo': True},
 {'nombre': 'Elena V.',
  'cargo': 'CEO · Pyme tecnológica (España)',
  'texto': 'Lo que más valoramos es que no nos vendieron un producto cerrado. Desarrollaron una herramienta a medida '
           'que encaja con cómo trabajamos.',
  'texto_en': "What we value most is that they didn't sell us a closed product. They developed a custom tool that fits "
              'how we work.',
  'rating': 5,
  'servicio': 'desarrollo',
  'ilustrativo': True}]

PORTFOLIO = [   {   'slug': 'itinerarios-turisticos-ia',
        'titulo': 'Plataforma de itinerarios turísticos con IA',
        'titulo_en': 'Tourist Itinerary Platform with AI',
        'cliente': 'Turismo cultural y patrimonio, España',
        'descripcion': 'Web app a medida que genera rutas personalizadas según preferencias del visitante, con gestión '
                       'multi-ciudad, panel de administración y demo pública segura.',
        'descripcion_en': 'Custom web app that generates personalized routes according to visitor preferences, with '
                          'multi-city management, admin panel, and secure public demo.',
        'problema': 'El catálogo turístico vivía en hojas de cálculo: difícil de mantener, inútil para el visitante y '
                    'sin forma ágil de probar nuevas ciudades o rutas con usuarios reales.',
        'problema_en': 'The tourist catalog was in spreadsheets: difficult to maintain, useless for the visitor, and '
                       'no agile way to test new cities or routes with real users.',
        'solucion': 'Plataforma web a medida que unifica mapas, eventos culturales y comercio local. El visitante '
                    'elige preferencias y recibe rutas optimizadas; el equipo gestiona ciudades, contenidos y usuarios '
                    'desde un panel sin depender de cambios de código.',
        'solucion_en': 'Custom web platform that unifies maps, cultural events, and local commerce. The visitor '
                       'chooses preferences and receives optimized routes; the team manages cities, content, and users '
                       'from a panel without relying on code changes.',
        'resultados': [   'Itinerarios en segundos con cientos de puntos de interés por ciudad',
                          'Multi-destino: misma plataforma, catálogos distintos por ciudad',
                          'Demo pública con URL lista para compartir en minutos',
                          'Trazabilidad: logs, correos y mantenimiento desde el panel admin'],
        'resultados_en': [   'Itineraries in seconds with hundreds of points of interest per city',
                             'Multi-destination: same platform, different catalogs per city',
                             'Public demo with URL ready to share in minutes',
                             'Traceability: logs, emails, and maintenance from the admin panel'],
        'tecnologias': [   'App web a medida',
                           'Mapas interactivos',
                           'IA personalizada',
                           'Panel multi-ciudad',
                           'Demo pública segura'],
        'tecnologias_en': [   'Custom web app',
                              'Interactive maps',
                              'Personalized AI',
                              'Multi-city panel',
                              'Secure public demo'],
        'imagen': 'portfolio-itinerarios-turisticos',
        'categoria': 'Desarrollo',
        'real': True,
        'testimonial': None},
    {   'slug': 'plataforma-gestion-medida',
        'titulo': 'Plataforma de Gestión a Medida',
        'titulo_en': 'Custom Management Platform',
        'cliente': 'Empresa de servicios, España',
        'descripcion': 'ERP personalizado con módulos de facturación, inventario e integración bancaria',
        'descripcion_en': 'Custom ERP with billing, inventory, and banking integration modules',
        'problema': 'La empresa gestionaba pedidos, stock y facturación en hojas de cálculo desconectadas. Errores de '
                    'stock y retrasos en facturación afectaban al cash-flow.',
        'problema_en': 'The company managed orders, stock, and billing in disconnected spreadsheets. Stock errors and '
                       'billing delays affected cash flow.',
        'solucion': 'Desarrollamos un ERP a medida con Python y React, integrado con la API bancaria y módulos de '
                    'facturación automática.',
        'solucion_en': 'We developed a custom ERP with Python and React, integrated with the banking API and automatic '
                       'billing modules.',
        'resultados': [   '-60% tiempo en gestión administrativa',
                          'Facturación en 24h vs 5 días',
                          'Stock sincronizado en tiempo real'],
        'resultados_en': [   '-60% time in administrative management',
                             'Billing in 24h vs 5 days',
                             'Real-time synchronized stock'],
        'tecnologias': ['Python', 'React', 'PostgreSQL', 'Docker'],
        'tecnologias_en': ['Python', 'React', 'PostgreSQL', 'Docker'],
        'imagen': 'portfolio-ecommerce',
        'categoria': 'Desarrollo',
        'real': False,
        'testimonial': None},
    {   'slug': 'automatizacion-erp-crm',
        'titulo': 'Automatización Integración ERP-CRM',
        'titulo_en': 'ERP-CRM Integration Automation',
        'cliente': 'Distribuidora industrial, España',
        'descripcion': 'Workflows automáticos que sincronizan pedidos, stock y facturación entre Odoo y Salesforce',
        'descripcion_en': 'Automatic workflows that synchronize orders, stock, and billing between Odoo and Salesforce',
        'problema': 'Dos equipos introducían los mismos pedidos en Odoo y Salesforce manualmente. Duplicidad de datos '
                    'y 15 h/semana de trabajo repetitivo.',
        'problema_en': 'Two teams manually entered the same orders in Odoo and Salesforce. Data duplication and 15 '
                       'hours/week of repetitive work.',
        'solucion': 'Automatizaciones con Python y n8n: cada pedido en Salesforce crea/actualiza registros en Odoo, '
                    'genera albarán y notifica al almacén.',
        'solucion_en': 'Automations with Python and n8n: each order in Salesforce creates/updates records in Odoo, '
                       'generates a delivery note, and notifies the warehouse.',
        'resultados': ['-40% horas manuales semanales', 'ROI en 4 meses', 'Cero duplicados de pedidos en 6 meses'],
        'resultados_en': ['-40% manual hours weekly', 'ROI in 4 months', 'Zero duplicated orders in 6 months'],
        'tecnologias': ['Python', 'APIs REST', 'n8n', 'PostgreSQL'],
        'tecnologias_en': ['Python', 'REST APIs', 'n8n', 'PostgreSQL'],
        'imagen': 'portfolio-industry',
        'categoria': 'Automatización',
        'real': True,
        'testimonial': 'Automatizaron nuestros procesos de reporting y sincronización entre departamentos. Ahorramos '
                       'más de 200.000€ en el primer año.',
        'testimonial_en': 'They automated our reporting and synchronization processes between departments. We saved '
                          'over €200,000 in the first year.'},
    {   'slug': 'portal-clientes-api-bancaria',
        'titulo': 'Portal Clientes y API Bancaria',
        'titulo_en': 'Client Portal and Banking API',
        'cliente': 'Entidad financiera internacional',
        'descripcion': 'Desarrollo web con integración API bancaria y panel de autogestión para 10.000+ usuarios',
        'descripcion_en': 'Web development with banking API integration and self-management panel for 10,000+ users',
        'problema': 'Los clientes no podían consultar movimientos ni gestionar productos online. Alta carga en call '
                    'center.',
        'problema_en': 'Clients could not check transactions or manage products online. High load on call center.',
        'solucion': 'Portal web con autenticación segura, integración API bancaria PSD2 y panel de autogestión '
                    'escalable en Azure.',
        'solucion_en': 'Web portal with secure authentication, PSD2 banking API integration, and scalable '
                       'self-management panel on Azure.',
        'resultados': ['-70% consultas al call center', '10.000+ usuarios activos', 'LCP < 2s en mobile'],
        'resultados_en': ['-70% inquiries to call center', '10,000+ active users', 'LCP < 2s on mobile'],
        'tecnologias': ['Node.js', 'React', 'Azure', 'PostgreSQL'],
        'tecnologias_en': ['Node.js', 'React', 'Azure', 'PostgreSQL'],
        'imagen': 'portfolio-banking',
        'categoria': 'Desarrollo',
        'real': False,
        'testimonial': None},
    {   'slug': 'rpa-documental-ocr',
        'titulo': 'RPA Documental y OCR',
        'titulo_en': 'Document RPA and OCR',
        'cliente': 'Sector legal, España',
        'descripcion': 'Automatización de extracción y clasificación de contratos con 98% de precisión',
        'descripcion_en': 'Automation of contract extraction and classification with 98% accuracy',
        'problema': 'Abogados dedicaban horas a clasificar y extraer datos de contratos PDF entrantes por email.',
        'problema_en': 'Lawyers spent hours classifying and extracting data from incoming PDF contracts via email.',
        'solucion': 'Pipeline OCR + clasificación automática con Computer Vision y FastAPI, integrado al DMS del '
                    'despacho.',
        'solucion_en': 'OCR pipeline + automatic classification with Computer Vision and FastAPI, integrated into the '
                       "firm's DMS.",
        'resultados': [   '98% precisión extracción',
                          '-80% tiempo clasificación documental',
                          'Integración con email entrante'],
        'resultados_en': [   '98% extraction accuracy',
                             '-80% document classification time',
                             'Integration with incoming email'],
        'tecnologias': ['Python', 'Computer Vision', 'FastAPI', 'MongoDB'],
        'tecnologias_en': ['Python', 'Computer Vision', 'FastAPI', 'MongoDB'],
        'imagen': 'portfolio-documents',
        'categoria': 'Automatización',
        'real': False,
        'testimonial': None}]


def sitemap_base_url() -> str:
    return HREFLANG_ES


def canonical_url() -> str:
    path = request.path or '/'
    return f"{HREFLANG_ES}{path}" if path != '/' else f"{HREFLANG_ES}/"


def hreflang_urls() -> list[tuple[str, str]]:
    path = request.path or '/'
    suffix = path if path != '/' else '/'
    en_suffix = f"/en{suffix}" if suffix != '/' else '/en/'
    return [
        ('es', f"{HREFLANG_ES}{suffix}"),
        ('en', f"{HREFLANG_ES}{en_suffix}"),
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
    merged = [recursos_seo.normalize_recurso(r) for r in RECURSOS + posts]
    return sorted(merged, key=lambda r: r.get('fecha', ''), reverse=True)


def get_recurso(slug: str) -> dict | None:
    articulo = next((r for r in RECURSOS if r['slug'] == slug), None)
    if articulo:
        return recursos_seo.normalize_recurso(articulo)
    try:
        post = yt_db.get_post_publicado(slug)
        return recursos_seo.normalize_recurso(post) if post else None
    except Exception as e:
        print(f'[yt_posts] Error leyendo post {slug}: {e}')
        return None


def get_caso(slug: str) -> dict | None:
    return next((p for p in PORTFOLIO if p['slug'] == slug), None)


def render_recurso_body(slug: str) -> str:
    lang_suffix = '-en' if g.lang == 'en' else ''
    path = os.path.join(os.path.dirname(__file__), 'content', 'recursos', f'{slug}{lang_suffix}.html')
    if not os.path.isfile(path) and g.lang == 'en':
        path = os.path.join(os.path.dirname(__file__), 'content', 'recursos', f'{slug}.html')
    if not os.path.isfile(path):
        return ''
    with open(path, encoding='utf-8') as f:
        return render_template_string(f.read())


def render_portfolio_body(slug: str) -> str:
    lang_suffix = '-en' if g.lang == 'en' else ''
    path = os.path.join(os.path.dirname(__file__), 'content', 'portfolio', f'{slug}{lang_suffix}.html')
    if not os.path.isfile(path) and g.lang == 'en':
        path = os.path.join(os.path.dirname(__file__), 'content', 'portfolio', f'{slug}.html')
    if not os.path.isfile(path):
        return ''
    with open(path, encoding='utf-8') as f:
        return render_template_string(f.read())


def all_sitemap_paths() -> list[dict]:
    today = datetime.now().strftime('%Y-%m-%d')
    pages = [{**p, 'lastmod': today} for p in SITEMAP_PAGES]
    for p in pages:
        if p.get('path') == '/recursos':
            p['changefreq'] = 'weekly'
    try:
        db_redirects = yt_db.list_recursos_redirects()
    except Exception:
        db_redirects = {}
    for r in todos_los_recursos():
        if not include_recurso_in_sitemap(r, db_redirects):
            continue
        pages.append({
            'path': f"/recursos/{r['slug']}",
            'changefreq': 'monthly',
            'priority': sitemap_priority(r),
            'lastmod': r.get('fecha_modificacion') or r.get('fecha') or today,
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
    lang = getattr(g, 'lang', 'es')
    groups = []
    for group in GEO_INDEX_GROUPS:
        pages = []
        for slug in group['pages']:
            page = get_geo_page(slug, lang=lang)
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
    portfolio_body = render_portfolio_body(slug)
    return render_template(
        'caso-exito.html',
        caso=caso,
        servicio=servicio,
        portfolio_body=portfolio_body,
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
    hub = build_hub_context(todos_los_recursos())
    return render_template(
        'recursos.html',
        breadcrumbs=[{'name': 'Recursos', 'url': canonical_url()}],
        **hub,
    )


@app.route('/recursos/actualidad')
def recursos_actualidad():
    ctx = build_actualidad_context(todos_los_recursos())
    return render_template(
        'recursos-actualidad.html',
        breadcrumbs=[
            {'name': 'Recursos', 'url': url_for('recursos', _external=True)},
            {'name': 'Actualidad IA', 'url': canonical_url()},
        ],
        **ctx,
    )


@app.route('/recursos/temas/<cluster>')
def recursos_tema(cluster):
    if cluster not in recursos_seo.CLUSTERS:
        abort(404)
    todos = [r for r in todos_los_recursos() if r.get('cluster') == cluster]
    meta = recursos_seo.CLUSTER_META[cluster]
    return render_template(
        'recursos-tema.html',
        cluster=cluster,
        cluster_meta=meta,
        pilar_slug=recursos_seo.CLUSTER_PILARES[cluster],
        articulos=todos,
        breadcrumbs=[
            {'name': 'Recursos', 'url': url_for('recursos', _external=True)},
            {'name': meta['nombre'], 'url': canonical_url()},
        ],
    )


@app.route('/recursos/<slug>')
def recurso_articulo(slug):
    try:
        db_redirects = yt_db.list_recursos_redirects()
    except Exception:
        db_redirects = {}
    target = redirect_path_for_slug(slug, db_redirects)
    if target:
        return redirect(f"{HREFLANG_ES}{target}", code=301)

    articulo = get_recurso(slug)
    if not articulo:
        abort(404)
    todos = todos_los_recursos()
    relacionados = get_articulos_relacionados(articulo, todos)
    # Posts de vídeo llevan el cuerpo en BD; los artículos estáticos, en content/recursos/
    cuerpo = articulo.get('cuerpo') or render_recurso_body(slug)
    page_url = articulo_canonical_href(articulo, HREFLANG_ES) or canonical_url()
    mostrar_video = mostrar_video_en_articulo(articulo)
    return render_template(
        'recurso-articulo.html',
        articulo=articulo,
        articulo_canonical_url=page_url,
        mostrar_video=mostrar_video,
        sin_video_canal=slug in recursos_seo.ARTICULOS_SIN_VIDEO_CANAL,
        video_schema=video_schema_graph(articulo, page_url) if mostrar_video else None,
        cuerpo=cuerpo,
        articulos_relacionados=relacionados,
        cluster_meta=recursos_seo.CLUSTER_META.get(articulo.get('cluster', '')) or {},
        pilar_slug=recursos_seo.CLUSTER_PILARES.get(articulo.get('cluster', '')),
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
    localize_contact_form(form)
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
            flash(_('¡Gracias %(nombre)s! Tu mensaje ha sido enviado. Te contactaremos pronto.', nombre=form.nombre.data), 'success')
            return redirect(url_for('contacto'))

        turnstile_result = verify_turnstile(
            request.form.get('cf-turnstile-response'),
            client_ip,
            TURNSTILE_SECRET_KEY,
        )
        if turnstile_result is False:
            print(f"Contacto: Turnstile inválido ip={client_ip}")
            flash(_('No pudimos verificar el envío. Inténtalo de nuevo.'), 'error')
            session['contact_form_loaded_at'] = time()
            return render_template(
                'contacto.html',
                form=form,
                faqs=CONTACTO_FAQS,
                breadcrumbs=[{'name': 'Contacto', 'url': canonical_url()}],
                turnstile_site_key=TURNSTILE_SITE_KEY,
            )

        try:
            choices_map = SERVICIO_CHOICES_EN if g.lang == 'en' else dict(SERVICIO_CHOICES)
            default_svc = 'Not specified' if g.lang == 'en' else 'No especificado'
            servicio_label = choices_map.get(form.servicio.data, default_svc)
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
            flash(_('¡Gracias %(nombre)s! Tu mensaje ha sido enviado. Te contactaremos pronto.', nombre=form.nombre.data), 'success')
        except Exception as e:
            print(f"Error enviando email: {str(e)}")
            flash(_('¡Gracias %(nombre)s! Hemos recibido tu mensaje y te contactaremos pronto.', nombre=form.nombre.data), 'success')
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
    lang = getattr(g, 'lang', 'es')
    return render_template(
        'geo/index.html',
        hub=get_geo_hub(lang),
        index_groups=geo_index_groups(),
        breadcrumbs=[{'name': 'Zona Madrid', 'url': canonical_url()}],
    )


@app.route('/geo/<slug>')
def geo_page(slug):
    lang = getattr(g, 'lang', 'es')
    page = get_geo_page(slug, lang=lang)
    if not page:
        abort(404)
    parent_page = get_geo_page(page['parent_slug'], lang=lang) if page.get('parent_slug') else None
    related_pages = [
        p for s in page.get('related_slugs', [])
        if (p := get_geo_page(s, lang=lang)) and p['slug'] != slug
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
            f"\n# Guía para modelos de lenguaje: {HREFLANG_ES}/llms.txt\n"
        )
    return Response(body, mimetype='text/plain')


@app.route('/llms.txt')
def llms_txt():
    path = os.path.join(os.path.dirname(__file__), 'llms.txt')
    with open(path, encoding='utf-8') as f:
        body = f.read()
    return Response(body, content_type='text/plain; charset=utf-8')


@app.route('/sitemap.xml')
def sitemap_xml():
    base = sitemap_base_url()
    today = datetime.now().strftime('%Y-%m-%d')
    urls = []
    for page in all_sitemap_paths():
        path = page['path']
        loc_es = f"{base}{path}"
        
        en_path = f"/en{path}" if path != '/' else '/en/'
        loc_en = f"{base}{en_path}"
        
        lastmod = page.get('lastmod') or today
        
        # ES version
        urls.append(
            "  <url>\n"
            f"    <loc>{loc_es}</loc>\n"
            f"    <xhtml:link rel=\"alternate\" hreflang=\"es\" href=\"{loc_es}\"/>\n"
            f"    <xhtml:link rel=\"alternate\" hreflang=\"en\" href=\"{loc_en}\"/>\n"
            f"    <xhtml:link rel=\"alternate\" hreflang=\"x-default\" href=\"{loc_es}\"/>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{page['changefreq']}</changefreq>\n"
            f"    <priority>{page['priority']}</priority>\n"
            "  </url>"
        )
        
        # EN version
        urls.append(
            "  <url>\n"
            f"    <loc>{loc_en}</loc>\n"
            f"    <xhtml:link rel=\"alternate\" hreflang=\"es\" href=\"{loc_es}\"/>\n"
            f"    <xhtml:link rel=\"alternate\" hreflang=\"en\" href=\"{loc_en}\"/>\n"
            f"    <xhtml:link rel=\"alternate\" hreflang=\"x-default\" href=\"{loc_es}\"/>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{page['changefreq']}</changefreq>\n"
            f"    <priority>{page['priority']}</priority>\n"
            "  </url>"
        )
        
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
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
        'ga4_linker_domains': GA4_LINKER_DOMAINS,
        'linkedin_url': LINKEDIN_URL,
        'x_url': X_URL,
        'servicios': SERVICIOS,
        'primera_consulta_pasos': primera_consulta_pasos(),
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
