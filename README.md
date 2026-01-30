# Megasoluciones - Web de Servicios de IA y Desarrollo

🚀 Web profesional completa desarrollada con Flask para Megasoluciones, líder en servicios de inteligencia artificial y desarrollo de software.

## 🎯 Características

- ✅ **Diseño Moderno**: UI/UX 2026 con gradientes azul brillante a verde brillante
- ✅ **Responsive**: Mobile-first, optimizado para todos los dispositivos
- ✅ **8 Servicios IA**: Chatbots, Automatización, ML, Computer Vision, NLP, etc.
- ✅ **Precios del Sector**: Basados en investigación de mercado real
- ✅ **SEO Optimizado**: Schema markup, meta tags, URLs amigables
- ✅ **Animaciones**: Scroll parallax, hover effects, fade-in animations
- ✅ **Formulario Contacto**: Flask-WTF con validación
- ✅ **WhatsApp Float**: Botón flotante para contacto directo

## 📁 Estructura del Proyecto

```
megasoluciones/
├── app.py                 # Aplicación Flask principal
├── requirements.txt       # Dependencias Python
├── README.md             # Este archivo
├── static/
│   ├── css/
│   │   └── style.css     # Estilos con gradientes custom
│   ├── js/
│   │   └── app.js        # JavaScript para animaciones
│   └── images/
│       ├── logo.png      # Logo principal (red neuronal)
│       └── logo_alt.png  # Logo alternativo (hexágono M)
└── templates/
    ├── base.html         # Template base
    ├── index.html        # Homepage
    ├── sobre.html        # Sobre nosotros
    ├── servicios.html    # 8 servicios con precios
    ├── portfolio.html    # Proyectos realizados
    ├── testimonios.html  # Testimonios clientes
    └── contacto.html     # Formulario contacto
```

## 🚀 Instalación Local

### Requisitos Previos
- Python 3.8+
- pip

### Pasos

1. **Clonar/Descargar el proyecto**
```bash
cd megasoluciones
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Ejecutar la aplicación**
```bash
python app.py
```

5. **Abrir en navegador**
```
http://localhost:5000
```

## 🌐 Despliegue en Producción

### Opción 1: Render (RECOMENDADO - Gratis)

1. Crear cuenta en [Render](https://render.com)
2. Nuevo Web Service → conectar repositorio Git
3. Configuración:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3
4. Variables de entorno:
   - `SECRET_KEY`: tu-clave-secreta-segura
5. Deploy automático

### Opción 2: Heroku

```bash
# Instalar Heroku CLI
heroku login
heroku create megasoluciones-web

# Crear Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
git init
git add .
git commit -m "Deploy Megasoluciones"
git push heroku main

# Configurar variable de entorno
heroku config:set SECRET_KEY=tu-clave-secreta
```

### Opción 3: PythonAnywhere

1. Subir archivos a PythonAnywhere
2. Crear Web App → Flask
3. Configurar WSGI file apuntando a `app.py`
4. Reload web app

## 🎨 Personalización

### Colores
Los colores están definidos en `static/css/style.css`:
```css
:root {
    --color-primary: #3b82f6;      /* Azul brillante */
    --color-secondary: #10b981;     /* Verde brillante */
    --gradient-main: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
}
```

### Datos de Contacto
Editar en `templates/base.html` (footer) y `templates/contacto.html`:
- Email: info@megasoluciones.com
- Teléfono: +34 XXX XXX XXX
- WhatsApp: Actualizar href en botón flotante

### Servicios y Precios
Modificar en `app.py` la variable `SERVICIOS`:
```python
SERVICIOS = [
    {
        'titulo': 'Nombre del Servicio',
        'precio_desde': '€XXX',
        # ...
    }
]
```

## 📊 Servicios Incluidos (Investigación Mercado)

| Servicio | Precio Desde | Precio Hasta |
|----------|--------------|--------------|
| Chatbots IA | €299/mes | €999/mes |
| Automatización | €399/mes | €1.499/mes |
| Desarrollo Software | €5.000 | €50.000 |
| Consultoría IA | €100/hora | €250/hora |
| Machine Learning | €10.000 | €100.000 |
| Computer Vision | €8.000 | €80.000 |
| NLP | €6.000 | €60.000 |
| Agentes IA Generativos | €15.000 | €150.000 |

## 🔧 Funcionalidades Implementadas

✅ Navegación responsive con menú móvil
✅ Hero section con estadísticas animadas
✅ 8 servicios con precios reales del mercado
✅ Tabla comparativa de servicios
✅ Portfolio con proyectos ejemplo
✅ Testimonios de clientes
✅ Formulario de contacto con Flask-WTF
✅ Footer completo con enlaces
✅ Botón WhatsApp flotante
✅ Animaciones smooth scroll y fade-in
✅ Schema markup JSON-LD para SEO
✅ Meta tags OpenGraph
✅ Google Analytics ready

## 📈 Mejoras vs Competencia

1. **Precios Transparentes**: Tabla comparativa clara (competencia oculta precios)
2. **Gradientes Modernos 2026**: Diseño actualizado con tendencias actuales
3. **Mobile-First Total**: Experiencia perfecta en móvil (competencia descuida móvil)
4. **Velocidad**: Flask ultrarrápido vs WordPress pesado
5. **SEO Avanzado**: Schema markup completo desde día 1

## 🔐 Seguridad

- Flask-WTF con CSRF protection
- Validación de formularios server-side
- Environment variables para secrets
- HTTPS obligatorio en producción

## 📝 Próximos Pasos (Opcional)

- [ ] Configurar dominio personalizado
- [ ] Añadir Google Analytics
- [ ] Implementar envío real de emails (SMTP)
- [ ] Blog con artículos sobre IA
- [ ] Chat en vivo
- [ ] Sistema de cotizaciones online

## 📞 Soporte

Para cualquier consulta sobre el proyecto, contactar a través de:
- Email: info@megasoluciones.com
- WhatsApp: +34 XXX XXX XXX

---

**Desarrollado con ❤️ para Megasoluciones**

Tecnologías: Python, Flask, HTML5, CSS3, JavaScript
Diseño: Tendencias 2026 - Gradientes azul-verde, minimalismo inteligente
