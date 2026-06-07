from flask import Flask, render_template, request, flash, redirect, url_for, Response
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from wtforms import StringField, TextAreaField, EmailField, TelField, SelectField
from wtforms.validators import DataRequired, Email
import os
from datetime import datetime

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


GSC_VERIFICATION_TOKEN = load_gsc_verification_token()

CANONICAL_BASE_URL = os.environ.get('CANONICAL_BASE_URL', 'https://megasolucion.com').rstrip('/')

SITEMAP_HOSTS = {
    'megasolucion.com': 'https://megasolucion.com',
    'www.megasolucion.com': 'https://megasolucion.com',
    'megasolucion.es': 'https://megasolucion.es',
    'www.megasolucion.es': 'https://megasolucion.es',
}

HREFLANG_ES = 'https://megasolucion.es'
HREFLANG_COM = 'https://megasolucion.com'

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

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'info@megasolucion.net')
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_ASCII_ATTACHMENTS'] = False

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
        'slug': 'automatizar-procesos-pyme',
        'titulo': 'Cómo automatizar procesos en una pyme española',
        'resumen': 'Guía práctica para identificar qué automatizar primero y calcular el ROI de las automatizaciones empresariales.',
        'fecha': '2026-05-01',
    },
    {
        'slug': 'coste-desarrollo-software-2026',
        'titulo': 'Cuánto cuesta un desarrollo de software a medida en 2026',
        'resumen': 'Desglose de precios por tipo de proyecto: web, API, plataforma SaaS e integraciones con ERP/CRM.',
        'fecha': '2026-04-15',
    },
    {
        'slug': 'rpa-vs-automatizacion-apis',
        'titulo': 'RPA vs automatización con APIs: qué elegir',
        'resumen': 'Comparativa técnica y económica para decidir la mejor estrategia de automatización en tu empresa.',
        'fecha': '2026-03-20',
    },
]

TESTIMONIOS = [
    {
        'nombre': 'María González',
        'cargo': 'CEO, TechCorp España',
        'texto': 'Megasoluciones desarrolló nuestra plataforma de gestión a medida e integró todos nuestros sistemas. El proyecto se entregó a tiempo y el equipo fue excepcional.',
        'rating': 5,
        'servicio': 'desarrollo'
    },
    {
        'nombre': 'Carlos Ramírez',
        'cargo': 'Director IT, Innovatech',
        'texto': 'Automatizaron nuestros procesos de reporting y sincronización entre departamentos. Ahorramos más de 200.000€ en el primer año. Profesionales excepcionales.',
        'rating': 5,
        'servicio': 'automatizacion'
    },
    {
        'nombre': 'Laura Martínez',
        'cargo': 'COO, FinanceGlobal',
        'texto': 'Las automatizaciones de Megasoluciones nos permitieron escalar operaciones sin aumentar plantilla. ROI impresionante en menos de 6 meses.',
        'rating': 5,
        'servicio': 'automatizacion'
    }
]

PORTFOLIO = [
    {
        'titulo': 'Plataforma de Gestión a Medida',
        'cliente': 'Empresa servicios, España',
        'descripcion': 'ERP personalizado con módulos de facturación, inventario e integración bancaria',
        'tecnologias': ['Python', 'React', 'PostgreSQL', 'Docker'],
        'imagen': 'portfolio-ecommerce.png',
        'categoria': 'Desarrollo'
    },
    {
        'titulo': 'Automatización Integración ERP-CRM',
        'cliente': 'Distribuidora industrial',
        'descripcion': 'Workflows automáticos que sincronizan pedidos, stock y facturación entre Odoo y Salesforce',
        'tecnologias': ['Python', 'APIs REST', 'n8n', 'PostgreSQL'],
        'imagen': 'portfolio-industry.png',
        'categoria': 'Automatización'
    },
    {
        'titulo': 'Portal Clientes y API Bancaria',
        'cliente': 'Entidad financiera internacional',
        'descripcion': 'Desarrollo web con integración API bancaria y panel de autogestión para 10.000+ usuarios',
        'tecnologias': ['Node.js', 'React', 'Azure', 'PostgreSQL'],
        'imagen': 'portfolio-banking.png',
        'categoria': 'Desarrollo'
    },
    {
        'titulo': 'RPA Documental y OCR',
        'cliente': 'Sector legal, España',
        'descripcion': 'Automatización de extracción y clasificación de contratos con 98% de precisión',
        'tecnologias': ['Python', 'Computer Vision', 'FastAPI', 'MongoDB'],
        'imagen': 'portfolio-documents.png',
        'categoria': 'Automatización'
    }
]


def sitemap_base_url() -> str:
    host = (request.host or '').split(':')[0].lower()
    return SITEMAP_HOSTS.get(host, CANONICAL_BASE_URL)


def canonical_url() -> str:
    base = sitemap_base_url()
    path = request.path or '/'
    return f"{base}{path}" if path != '/' else f"{base}/"


def hreflang_urls() -> list[tuple[str, str]]:
    path = request.path or '/'
    suffix = path if path != '/' else '/'
    return [
        ('es-ES', f"{HREFLANG_ES}{suffix}"),
        ('x-default', f"{HREFLANG_COM}{suffix}"),
    ]


def servicios_por_pilar(pilar: str) -> list:
    return [s for s in SERVICIOS if s['pilar'] == pilar]


def get_servicio(slug: str) -> dict | None:
    return next((s for s in SERVICIOS if s['slug'] == slug), None)


@app.route('/')
def index():
    servicios_destacados = servicios_por_pilar('desarrollo') + servicios_por_pilar('automatizacion')
    return render_template(
        'index.html',
        servicios=servicios_destacados,
        testimonios=TESTIMONIOS[:2],
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


@app.route('/sobre')
def sobre():
    return render_template('sobre.html')


@app.route('/servicios')
def servicios():
    return render_template(
        'servicios.html',
        servicios=SERVICIOS,
        servicios_desarrollo=servicios_por_pilar('desarrollo'),
        servicios_automatizacion=servicios_por_pilar('automatizacion'),
        servicios_ia=servicios_por_pilar('ia'),
    )


@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html', proyectos=PORTFOLIO)


@app.route('/testimonios')
def testimonios():
    return render_template('testimonios.html', testimonios=TESTIMONIOS)


@app.route('/recursos')
def recursos():
    return render_template('recursos.html', articulos=RECURSOS)


@app.route('/privacidad')
def privacidad():
    return render_template('privacidad.html')


@app.route('/aviso-legal')
def aviso_legal():
    return render_template('aviso-legal.html')


@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    form = ContactForm()
    servicio_param = request.args.get('servicio', '')
    if servicio_param in dict(SERVICIO_CHOICES):
        form.servicio.data = servicio_param
    if form.validate_on_submit():
        try:
            servicio_label = dict(SERVICIO_CHOICES).get(form.servicio.data, 'No especificado')
            msg = Message(
                subject=f'Nuevo contacto de {form.nombre.data} - Megasoluciones',
                recipients=['info@megasolucion.net'],
                reply_to=form.email.data
            )
            msg.body = f"""
Nuevo mensaje de contacto desde megasolucion.com

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
            flash(f'¡Gracias {form.nombre.data}! Tu mensaje ha sido enviado. Te contactaremos pronto.', 'success')
        except Exception as e:
            print(f"Error enviando email: {str(e)}")
            flash(f'¡Gracias {form.nombre.data}! Hemos recibido tu mensaje y te contactaremos pronto.', 'success')
        return redirect(url_for('contacto'))
    return render_template('contacto.html', form=form, faqs=CONTACTO_FAQS)


@app.route('/health')
def health():
    return {'status': 'ok', 'service': 'megasoluciones'}, 200


@app.route('/robots.txt')
def robots_txt():
    base = sitemap_base_url()
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /health\n"
        f"\nSitemap: {base}/sitemap.xml\n"
    )
    return Response(body, mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    base = sitemap_base_url()
    lastmod = datetime.now().strftime('%Y-%m-%d')
    urls = []
    for page in SITEMAP_PAGES:
        loc = f"{base}{page['path']}"
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
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
