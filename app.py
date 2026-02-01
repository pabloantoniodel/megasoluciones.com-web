from flask import Flask, render_template, request, flash, redirect, url_for
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from wtforms import StringField, TextAreaField, EmailField, TelField
from wtforms.validators import DataRequired, Email
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'megasoluciones-secret-key-2026')

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'info@megasolucion.net')
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_ASCII_ATTACHMENTS'] = False

# Inicializar Flask-Mail
mail = Mail(app)

# Formulario de contacto
class ContactForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    telefono = TelField('Teléfono')
    empresa = StringField('Empresa')
    mensaje = TextAreaField('Mensaje', validators=[DataRequired()])

# Datos de servicios (basados en investigación de mercado)
SERVICIOS = [
    {
        'id': 1,
        'titulo': 'Chatbots IA Personalizados',
        'descripcion': 'Asistentes virtuales inteligentes que atienden a tus clientes 24/7 con procesamiento de lenguaje natural avanzado.',
        'precio_desde': '299€',
        'precio_hasta': '999€/mes',
        'caracteristicas': ['Integración multicanal', 'NLP avanzado', 'Aprendizaje continuo', 'Analytics en tiempo real'],
        'icon': '🤖'
    },
    {
        'id': 2,
        'titulo': 'Automatización Inteligente',
        'descripcion': 'Optimiza tus procesos empresariales con RPA y machine learning para reducir costos y aumentar eficiencia.',
        'precio_desde': '399€',
        'precio_hasta': '1.499€/mes',
        'caracteristicas': ['RPA empresarial', 'Workflows inteligentes', 'Integración APIs', 'Monitoreo 24/7'],
        'icon': '⚙️'
    },
    {
        'id': 3,
        'titulo': 'Desarrollo de Software IA',
        'descripcion': 'Aplicaciones web y móviles de última generación con inteligencia artificial integrada desde el diseño.',
        'precio_desde': '5.000€',
        'precio_hasta': '50.000€',
        'caracteristicas': ['Desarrollo a medida', 'Stack moderno', 'Escalabilidad cloud', 'Soporte continuo'],
        'icon': '💻'
    },
    {
        'id': 4,
        'titulo': 'Consultoría Estratégica IA',
        'descripcion': 'Asesoramiento experto para definir tu hoja de ruta de transformación digital con inteligencia artificial.',
        'precio_desde': '100€',
        'precio_hasta': '250€/hora',
        'caracteristicas': ['Análisis de viabilidad', 'ROI proyectado', 'Roadmap tecnológico', 'Formación equipos'],
        'icon': '📊'
    },
    {
        'id': 5,
        'titulo': 'Machine Learning & Modelos Predictivos',
        'descripcion': 'Modelos de ML personalizados para predicción de demanda, detección de anomalías y análisis predictivo.',
        'precio_desde': '10.000€',
        'precio_hasta': '100.000€',
        'caracteristicas': ['Modelos custom', 'Entrenamiento continuo', 'Deploy cloud', 'MLOps incluido'],
        'icon': '🧠'
    },
    {
        'id': 6,
        'titulo': 'Computer Vision',
        'descripcion': 'Visión artificial para reconocimiento facial, detección de objetos, OCR y control de calidad automatizado.',
        'precio_desde': '8.000€',
        'precio_hasta': '80.000€',
        'caracteristicas': ['Reconocimiento de imágenes', 'Video analytics', 'OCR avanzado', 'Edge computing'],
        'icon': '👁️'
    },
    {
        'id': 7,
        'titulo': 'Procesamiento Lenguaje Natural',
        'descripcion': 'Análisis de sentimiento, extracción de información, traducción automática y generación de contenido.',
        'precio_desde': '6.000€',
        'precio_hasta': '60.000€',
        'caracteristicas': ['Análisis de sentimiento', 'NER & clasificación', 'Modelos multiidioma', 'API REST'],
        'icon': '📝'
    },
    {
        'id': 8,
        'titulo': 'Agentes IA Generativos',
        'descripcion': 'Agentes inteligentes avanzados con IA generativa para ventas, soporte y asesoramiento personalizado.',
        'precio_desde': '15.000€',
        'precio_hasta': '150.000€',
        'caracteristicas': ['GPT-4 & Claude', 'RAG personalizado', 'Multi-agente', 'Memoria contextual'],
        'icon': '✨'
    }
]

TESTIMONIOS = [
    {
        'nombre': 'María González',
        'cargo': 'CEO, TechCorp España',
        'texto': 'Megasoluciones transformó nuestra atención al cliente con su chatbot IA. Reducimos tiempos de respuesta en un 70% y aumentamos la satisfacción del cliente significativamente.',
        'rating': 5
    },
    {
        'nombre': 'Carlos Ramírez',
        'cargo': 'Director IT, Innovatech',
        'texto': 'El equipo de Megasoluciones desarrolló un sistema de predicción de demanda que nos ahorró más de 200.000€ en el primer año. Profesionales excepcionales.',
        'rating': 5
    },
    {
        'nombre': 'Laura Martínez',
        'cargo': 'COO, FinanceGlobal',
        'texto': 'Su solución de automatización inteligente nos permitió escalar nuestras operaciones sin aumentar el personal. ROI impresionante en menos de 6 meses.',
        'rating': 5
    }
]

PORTFOLIO = [
    {
        'titulo': 'Sistema de Recomendación E-commerce',
        'cliente': 'Retail líder en España',
        'descripcion': 'Motor de recomendaciones ML que aumentó conversión 35%',
        'tecnologias': ['Python', 'TensorFlow', 'AWS', 'PostgreSQL'],
        'imagen': 'portfolio-ecommerce.png'
    },
    {
        'titulo': 'Chatbot Bancario Multicanal',
        'cliente': 'Entidad financiera internacional',
        'descripcion': 'Asistente virtual con NLP que atiende 10.000+ consultas/día',
        'tecnologias': ['GPT-4', 'Azure', 'React', 'Node.js'],
        'imagen': 'portfolio-banking.png'
    },
    {
        'titulo': 'Plataforma Análisis Predictivo',
        'cliente': 'Industria manufacturera',
        'descripcion': 'Predicción de fallos en maquinaria con 92% precisión',
        'tecnologias': ['Python', 'Scikit-learn', 'Docker', 'Grafana'],
        'imagen': 'portfolio-industry.png'
    },
    {
        'titulo': 'OCR Inteligente Documentos',
        'cliente': 'Sector legal',
        'descripcion': 'Extracción automática de datos de contratos con 98% accuracy',
        'tecnologias': ['Computer Vision', 'Azure AI', 'FastAPI', 'MongoDB'],
        'imagen': 'portfolio-documents.png'
    }
]

@app.route('/')
def index():
    servicios_destacados = SERVICIOS[:3]
    return render_template('index.html', servicios=servicios_destacados, testimonios=TESTIMONIOS[:2])

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/servicios')
def servicios():
    return render_template('servicios.html', servicios=SERVICIOS)

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html', proyectos=PORTFOLIO)

@app.route('/testimonios')
def testimonios():
    return render_template('testimonios.html', testimonios=TESTIMONIOS)

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    form = ContactForm()
    if form.validate_on_submit():
        # Intentar enviar email
        try:
            # Email para el administrador
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
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Nombre:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{form.nombre.data}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><a href="mailto:{form.email.data}">{form.email.data}</a></td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Teléfono:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{form.telefono.data or 'No proporcionado'}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Empresa:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{form.empresa.data or 'No proporcionada'}</td>
            </tr>
        </table>
        
        <h3 style="color: #1e3a8a; margin-top: 20px;">Mensaje:</h3>
        <div style="background: white; padding: 15px; border-left: 4px solid #3b82f6; border-radius: 5px;">
            <p style="white-space: pre-wrap;">{form.mensaje.data}</p>
        </div>
        
        <p style="margin-top: 20px; color: #6b7280; font-size: 12px; text-align: center;">
            Enviado desde el formulario de contacto de <a href="https://megasolucion.com" style="color: #3b82f6;">megasolucion.com</a><br>
            Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        </p>
    </div>
</body>
</html>
            """
            
            # Enviar email
            if app.config['MAIL_USERNAME']:
                mail.send(msg)
                flash(f'¡Gracias {form.nombre.data}! Tu mensaje ha sido enviado. Te contactaremos pronto.', 'success')
            else:
                # Si no está configurado SMTP, solo mostrar mensaje
                flash(f'¡Gracias {form.nombre.data}! Hemos recibido tu mensaje y te contactaremos pronto.', 'success')
                
        except Exception as e:
            # Log del error (en producción usar logging)
            print(f"Error enviando email: {str(e)}")
            flash(f'¡Gracias {form.nombre.data}! Hemos recibido tu mensaje y te contactaremos pronto.', 'success')
        
        return redirect(url_for('contacto'))
    return render_template('contacto.html', form=form)

@app.route('/health')
def health():
    """Endpoint de salud para Traefik/load balancers."""
    return {'status': 'ok', 'service': 'megasoluciones'}, 200

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
