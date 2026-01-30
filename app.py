from flask import Flask, render_template, request, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, EmailField, TelField
from wtforms.validators import DataRequired, Email
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'megasoluciones-secret-key-2026')

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
        'precio_desde': '€299',
        'precio_hasta': '€999/mes',
        'caracteristicas': ['Integración multicanal', 'NLP avanzado', 'Aprendizaje continuo', 'Analytics en tiempo real'],
        'icon': '🤖'
    },
    {
        'id': 2,
        'titulo': 'Automatización Inteligente',
        'descripcion': 'Optimiza tus procesos empresariales con RPA y machine learning para reducir costos y aumentar eficiencia.',
        'precio_desde': '€399',
        'precio_hasta': '€1.499/mes',
        'caracteristicas': ['RPA empresarial', 'Workflows inteligentes', 'Integración APIs', 'Monitoreo 24/7'],
        'icon': '⚙️'
    },
    {
        'id': 3,
        'titulo': 'Desarrollo de Software IA',
        'descripcion': 'Aplicaciones web y móviles de última generación con inteligencia artificial integrada desde el diseño.',
        'precio_desde': '€5.000',
        'precio_hasta': '€50.000',
        'caracteristicas': ['Desarrollo a medida', 'Stack moderno', 'Escalabilidad cloud', 'Soporte continuo'],
        'icon': '💻'
    },
    {
        'id': 4,
        'titulo': 'Consultoría Estratégica IA',
        'descripcion': 'Asesoramiento experto para definir tu hoja de ruta de transformación digital con inteligencia artificial.',
        'precio_desde': '€100',
        'precio_hasta': '€250/hora',
        'caracteristicas': ['Análisis de viabilidad', 'ROI proyectado', 'Roadmap tecnológico', 'Formación equipos'],
        'icon': '📊'
    },
    {
        'id': 5,
        'titulo': 'Machine Learning & Modelos Predictivos',
        'descripcion': 'Modelos de ML personalizados para predicción de demanda, detección de anomalías y análisis predictivo.',
        'precio_desde': '€10.000',
        'precio_hasta': '€100.000',
        'caracteristicas': ['Modelos custom', 'Entrenamiento continuo', 'Deploy cloud', 'MLOps incluido'],
        'icon': '🧠'
    },
    {
        'id': 6,
        'titulo': 'Computer Vision',
        'descripcion': 'Visión artificial para reconocimiento facial, detección de objetos, OCR y control de calidad automatizado.',
        'precio_desde': '€8.000',
        'precio_hasta': '€80.000',
        'caracteristicas': ['Reconocimiento de imágenes', 'Video analytics', 'OCR avanzado', 'Edge computing'],
        'icon': '👁️'
    },
    {
        'id': 7,
        'titulo': 'Procesamiento Lenguaje Natural',
        'descripcion': 'Análisis de sentimiento, extracción de información, traducción automática y generación de contenido.',
        'precio_desde': '€6.000',
        'precio_hasta': '€60.000',
        'caracteristicas': ['Análisis de sentimiento', 'NER & clasificación', 'Modelos multiidioma', 'API REST'],
        'icon': '📝'
    },
    {
        'id': 8,
        'titulo': 'Agentes IA Generativos',
        'descripcion': 'Agentes inteligentes avanzados con IA generativa para ventas, soporte y asesoramiento personalizado.',
        'precio_desde': '€15.000',
        'precio_hasta': '€150.000',
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
        'texto': 'El equipo de Megasoluciones desarrolló un sistema de predicción de demanda que nos ahorró más de €200.000 en el primer año. Profesionales excepcionales.',
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
        'tecnologias': ['Python', 'TensorFlow', 'AWS', 'PostgreSQL']
    },
    {
        'titulo': 'Chatbot Bancario Multicanal',
        'cliente': 'Entidad financiera internacional',
        'descripcion': 'Asistente virtual con NLP que atiende 10.000+ consultas/día',
        'tecnologias': ['GPT-4', 'Azure', 'React', 'Node.js']
    },
    {
        'titulo': 'Plataforma Análisis Predictivo',
        'cliente': 'Industria manufacturera',
        'descripcion': 'Predicción de fallos en maquinaria con 92% precisión',
        'tecnologias': ['Python', 'Scikit-learn', 'Docker', 'Grafana']
    },
    {
        'titulo': 'OCR Inteligente Documentos',
        'cliente': 'Sector legal',
        'descripcion': 'Extracción automática de datos de contratos con 98% accuracy',
        'tecnologias': ['Computer Vision', 'Azure AI', 'FastAPI', 'MongoDB']
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
        # Aquí iría la lógica de envío de email
        # Por ahora solo mostramos mensaje de éxito
        flash(f'¡Gracias {form.nombre.data}! Hemos recibido tu mensaje y te contactaremos pronto.', 'success')
        return redirect(url_for('contacto'))
    return render_template('contacto.html', form=form)

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
