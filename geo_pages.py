"""Contenido GEO — Comunidad de Madrid (páginas adicionales, no sustituyen la home)."""

from __future__ import annotations

GEO_HUB = {
    'slug': '',
    'h1': 'Servicios por zona en la Comunidad de Madrid',
    'subtitle': (
        'Automatización, desarrollo de software e inteligencia artificial para empresas '
        'en Madrid capital y municipios del Corredor del Henares.'
    ),
    'meta_title': 'Servicios por zona — Comunidad de Madrid | Megasoluciones',
    'meta_description': (
        'Mapa de servicios de Megasoluciones por municipio: IA en Madrid, automatización '
        'y desarrollo en Alcalá, Torrejón, Coslada, Rivas, Arganda y San Fernando.'
    ),
    'sitemap_priority': '0.75',
}

GEO_PAGES: dict[str, dict] = {
    'madrid': {
        'slug': 'madrid',
        'city_name': 'Madrid',
        'h1': 'Agencia de Inteligencia Artificial en Madrid',
        'subtitle': (
            'Soluciones de IA, automatización y desarrollo a medida para empresas y pymes '
            'en la capital. Proyectos por fases, con equipos que pueden trabajar contigo en '
            'remoto o de forma presencial cuando el proyecto lo requiera.'
        ),
        'meta_title': 'Agencia de Inteligencia Artificial Madrid | Megasoluciones',
        'meta_description': (
            'Chatbots, automatización RPA, integraciones Odoo/CRM y desarrollo a medida '
            'para empresas en Madrid. Primera consulta sin compromiso.'
        ),
        'sitemap_priority': '0.8',
        'intro_title': 'Qué hacemos en Madrid',
        'intro_paragraphs': [
            (
                'Madrid concentra una parte relevante de la actividad empresarial de España: '
                'servicios profesionales, retail, logística, finanzas, hostelería y tecnología. '
                'En ese contexto, la inteligencia artificial deja de ser un experimento y pasa '
                'a resolver problemas concretos: atender consultas fuera de horario, sincronizar '
                'datos entre sistemas que no se hablan o reducir horas de trabajo administrativo.'
            ),
            (
                'En Megasoluciones trabajamos con empresas madrileñas — desde oficinas en el centro '
                'y el norte de la ciudad hasta operaciones en polígonos del Corredor del Henares — '
                'en proyectos de IA aplicada: chatbots, automatización de procesos, integraciones '
                'y software a medida. No vendemos presentaciones: entregamos sistemas en producción, '
                'con soporte posterior.'
            ),
            (
                'Nuestro enfoque empieza por entender qué proceso te cuesta más tiempo o genera '
                'más errores. A partir de ahí definimos un piloto acotado, lo validamos con datos '
                'reales y escalamos solo si el retorno está claro.'
            ),
        ],
        'resources_article_slug': 'agencia-ia-madrid-apuesta-comunidad-pymes',
        'services_title': 'Servicios más demandados en Madrid',
        'services': [
            {
                'title': 'Chatbots IA',
                'description': (
                    'Asistentes para web, WhatsApp o CRM que resuelven consultas frecuentes, '
                    'cualifican leads y derivan a un humano cuando hace falta. Útil para e-commerce, '
                    'clínicas, inmobiliarias, academias y cualquier negocio con alto volumen de '
                    'preguntas repetitivas en Madrid.'
                ),
            },
            {
                'title': 'Automatización RPA + APIs',
                'description': (
                    'Workflows y robots que conectan ERP, CRM, email, hojas de cálculo y herramientas '
                    'SaaS. Eliminan la copia manual de datos entre sistemas — un dolor habitual en '
                    'pymes madrileñas que han crecido acumulando software sin integrar.'
                ),
            },
            {
                'title': 'Integraciones con Odoo / CRM / ERP',
                'description': (
                    'Conectamos Odoo, HubSpot, Salesforce, Holded y otros sistemas con APIs, webhooks '
                    'y agentes de IA. Si tu operativa en Madrid depende de varias herramientas que no '
                    'se sincronizan, aquí está el punto de partida.'
                ),
            },
            {
                'title': 'Desarrollo a medida',
                'description': (
                    'Aplicaciones web, paneles internos, APIs y microservicios con IA embebida. '
                    'Para empresas que necesitan una herramienta propia, no un SaaS genérico que '
                    'no encaja con su forma de trabajar.'
                ),
            },
            {
                'title': 'Modelos predictivos',
                'description': (
                    'Análisis de datos para prever demanda, detectar anomalías o priorizar leads. '
                    'Aplicado a inventario, facturación, operaciones logísticas o carteras comerciales '
                    '— siempre con datos que ya tienes, no con promesas abstractas.'
                ),
            },
        ],
        'use_cases_title': 'Casos de uso reales en Madrid',
        'use_cases_note': 'Ejemplos ilustrativos de procesos habituales. No representan clientes concretos.',
        'use_cases': [
            {
                'context': 'Despacho profesional (Chamberí / Salamanca)',
                'situation': 'Clasificación manual de documentos entrantes por email',
                'solution': 'Pipeline OCR + clasificación con IA y revisión humana',
            },
            {
                'context': 'E-commerce con almacén en Getafe o Leganés',
                'situation': 'Consultas repetitivas sobre envíos, devoluciones y stock',
                'solution': 'Chatbot conectado al ERP con respuestas en tiempo real',
            },
            {
                'context': 'Empresa de servicios B2B (AZCA / Nuevos Ministerios)',
                'situation': 'Informes semanales copiados entre CRM, Excel y email',
                'solution': 'Dashboard automatizado con datos sincronizados',
            },
            {
                'context': 'Distribuidora en polígono sur',
                'situation': 'Pedidos duplicados entre tienda online y ERP',
                'solution': 'Workflow de sincronización con validación automática',
            },
            {
                'context': 'Clínica o centro sanitario privado',
                'situation': 'Cita previa y FAQs fuera de horario de recepción',
                'solution': 'Chatbot multicanal con escalado a personal en horario laboral',
            },
            {
                'context': 'Startup en distrito tecnológico',
                'situation': 'MVP con IA embebida sin equipo interno de ML',
                'solution': 'Desarrollo a medida por fases con modelo preentrenado + fine-tuning',
            },
        ],
        'benefits_title': 'Beneficios claros',
        'benefits': [
            'Menos horas en tareas repetitivas — reporting, altas, conciliaciones y sincronización de datos.',
            'Atención al cliente ampliada — el chatbot cubre lo frecuente; tu equipo se centra en lo que aporta valor.',
            'Sistemas conectados — IA integrada en las herramientas que ya usas, no otro silo más.',
            'Pilotos antes de escalar — inviertes de forma progresiva, con entregas cada dos semanas.',
            'Cumplimiento RGPD — datos en entornos controlados, contratos claros y documentación incluida.',
        ],
        'why_title': 'Por qué trabajar con nosotros si estás en Madrid',
        'why_items': [
            'Base en Madrid, alcance nacional — reuniones presenciales cuando el proyecto lo pide; remoto para el día a día.',
            'ADN de desarrollo — no somos consultores que entregan un informe y se van: implementamos, desplegamos y mantenemos.',
            'Enfoque pyme y mediana empresa — presupuestos adaptados, sin mínimos diseñados solo para corporaciones.',
            'Transparencia en cada fase — sabes qué se entrega, cuándo y cuánto cuesta antes de seguir adelante.',
        ],
        'cta_title': '¿Tienes un proceso en Madrid que quieres automatizar o mejorar con IA?',
        'cta_text': 'Cuéntanos tu caso. Respondemos en menos de 24 horas y la primera consulta es sin compromiso.',
        'contact_servicio': 'consultoria-ia',
        'contact_origen': 'geo-madrid',
        'related_slugs': ['comunidad-de-madrid', 'rivas-vaciamadrid'],
        'parent_slug': 'comunidad-de-madrid',
    },
    'comunidad-de-madrid': {
        'slug': 'comunidad-de-madrid',
        'city_name': 'Comunidad de Madrid',
        'h1': 'Automatización y Desarrollo Tecnológico en la Comunidad de Madrid',
        'subtitle': (
            'Soluciones de software, integraciones e IA aplicada para empresas en toda la región: '
            'desde la capital hasta municipios del Corredor del Henares, la zona sur y el resto de provincia.'
        ),
        'meta_title': 'Automatización y Desarrollo en la Comunidad de Madrid | Megasoluciones',
        'meta_description': (
            'Software, integraciones e IA aplicada para empresas de toda la Comunidad de Madrid. '
            'Corredor del Henares, sur y capital.'
        ),
        'sitemap_priority': '0.75',
        'intro_title': 'Sectores con los que trabajamos',
        'sectors': [
            {
                'title': 'Logística y transporte',
                'description': 'Operadores en Corredor del Henares, plataformas junto a Barajas, distribución última milla.',
            },
            {
                'title': 'Industria y manufactura',
                'description': 'Metal, alimentación, cerámica y componentes en polígonos de Coslada, Arganda, San Fernando.',
            },
            {
                'title': 'Servicios profesionales',
                'description': 'Despachos, consultoras, inmobiliarias y agencias en Madrid capital y municipios del cinturón.',
            },
            {
                'title': 'Retail y hostelería',
                'description': 'Cadenas, franquicias y comercio local con necesidad de digitalización operativa.',
            },
            {
                'title': 'Tecnología y startups',
                'description': 'Empresas en parques tecnológicos (Rivas, Tres Cantos, Madrid) que necesitan desarrollo o integraciones.',
            },
            {
                'title': 'Educación y formación',
                'description': 'Centros con gestión de matrículas, comunicación con familias y administración documental.',
            },
            {
                'title': 'Salud privada',
                'description': 'Clínicas y centros con citas, historiales y atención multicanal.',
            },
        ],
        'services_title': 'Servicios aplicables a toda la región',
        'services': [
            {
                'title': 'Automatización de procesos',
                'description': (
                    'Workflows, RPA y agentes que eliminan tareas manuales entre ERP, CRM, email y hojas de cálculo. '
                    'Aplicable a cualquier empresa de la Comunidad que haya crecido usando herramientas desconectadas.'
                ),
            },
            {
                'title': 'Desarrollo de software a medida',
                'description': (
                    'Aplicaciones web, APIs, paneles internos y conectores. Para empresas que necesitan una solución '
                    'propia, no un producto genérico.'
                ),
            },
            {
                'title': 'Integraciones entre sistemas',
                'description': (
                    'Odoo, HubSpot, Salesforce, Holded, Google Workspace, Microsoft 365 y herramientas sectoriales. '
                    'Unificamos datos sin cambiar toda tu operativa de golpe.'
                ),
            },
            {
                'title': 'Chatbots y asistentes IA',
                'description': (
                    'Atención al cliente, cualificación de leads y FAQs automatizadas. Web, WhatsApp o integrados en tu CRM.'
                ),
            },
            {
                'title': 'Consultoría tecnológica',
                'description': (
                    'Diagnóstico de madurez digital, hoja de ruta, viabilidad de proyectos de IA y selección de herramientas. '
                    'Para decidir bien antes de invertir.'
                ),
            },
        ],
        'use_cases_title': 'Casos de uso por tipo de empresa',
        'use_cases_note': 'Ejemplos genéricos. No representan clientes reales.',
        'use_cases_simple': [
            {
                'title': 'Pyme industrial (polígono, 20–80 empleados)',
                'situation': 'Pedidos, albaranes y facturas se gestionan en Excel y se pasan a mano al ERP.',
                'solution': 'Automatización de flujo documental con validación y sincronización al ERP.',
            },
            {
                'title': 'Empresa de servicios (10–30 empleados, varios municipios)',
                'situation': 'El equipo comercial pierde tiempo en tareas administrativas post-visita.',
                'solution': 'Integración CRM + email + generación automática de propuestas.',
            },
            {
                'title': 'Comercio con varias tiendas en la región',
                'situation': 'Stock desactualizado entre tienda física y web.',
                'solution': 'Sincronización en tiempo real entre TPV, e-commerce y almacén.',
            },
            {
                'title': 'Centro formativo o clínica privada',
                'situation': 'Llamadas y emails repetitivos sobre horarios, precios y disponibilidad.',
                'solution': 'Chatbot con acceso a calendario y base de conocimiento interna.',
            },
            {
                'title': 'Empresa logística del Corredor del Henares',
                'situation': 'Incidencias de entrega gestionadas por email sin trazabilidad.',
                'solution': 'Panel interno con alertas automáticas y comunicación estructurada con clientes.',
            },
        ],
        'cta_title': '¿Tu empresa está en la Comunidad de Madrid y quieres modernizar procesos sin parar la operativa?',
        'cta_text': 'Te ayudamos a identificar por dónde empezar. Primera consulta sin compromiso.',
        'contact_origen': 'geo-comunidad-madrid',
        'related_slugs': ['madrid', 'alcala-de-henares', 'torrejon-de-ardoz', 'coslada', 'rivas-vaciamadrid', 'arganda-del-rey', 'san-fernando-de-henares'],
        'parent_slug': None,
        'is_hub': True,
    },
    'alcala-de-henares': {
        'slug': 'alcala-de-henares',
        'city_name': 'Alcalá de Henares',
        'h1': 'Automatización y Desarrollo de Software en Alcalá de Henares',
        'subtitle': (
            'Soluciones tecnológicas para empresas, comercios y centros de formación en Alcalá: '
            'menos tareas manuales, sistemas conectados y software que encaja con tu operativa.'
        ),
        'meta_title': 'Automatización y Software en Alcalá de Henares | Megasoluciones',
        'meta_description': (
            'Desarrollo a medida, integraciones y automatización para empresas, comercios y '
            'centros formativos en Alcalá de Henares.'
        ),
        'sitemap_priority': '0.7',
        'intro_title': 'Sectores típicos de Alcalá de Henares',
        'intro_paragraphs': [
            (
                'Alcalá combina un tejido universitario y cultural con industria ligera, comercio de '
                'proximidad y servicios. Trabajamos con academias y centros formativos, hostelería, '
                'comercio local, industria ligera y actividades vinculadas al turismo y patrimonio.'
            ),
        ],
        'sectors': [
            {'title': 'Educación y formación', 'description': 'Academias, centros de idiomas y entidades con gestión de alumnos y matrículas.'},
            {'title': 'Hostelería y restauración', 'description': 'Reservas, pedidos y gestión de proveedores sin centralizar.'},
            {'title': 'Comercio y servicios', 'description': 'Tiendas, clínicas y despachos con operativa interna aún manual.'},
            {'title': 'Industria ligera y talleres', 'description': 'Fabricación y subcontratas con administración desconectada de la planta.'},
            {'title': 'Turismo y patrimonio', 'description': 'Reservas, atención y reporting vinculados al flujo de visitantes.'},
        ],
        'services_title': 'Servicios más relevantes',
        'services': [
            {'title': 'Automatización administrativa', 'description': 'Altas de alumnos, contratos, documentación y conciliación de pagos.'},
            {'title': 'Desarrollo web y aplicaciones a medida', 'description': 'Portales internos, gestores de reservas y herramientas conectadas a tu backoffice.'},
            {'title': 'Integraciones CRM / ERP / email', 'description': 'Holded, Odoo, CRM genérico o Google Workspace sincronizados.'},
            {'title': 'Chatbots para atención y reservas', 'description': 'Horarios, precios y plazas con escalado a persona en horario laboral.'},
            {'title': 'Consultoría tecnológica', 'description': 'Diagnóstico y hoja de ruta para modernizar sin parar la operativa.'},
        ],
        'use_cases_title': 'Casos de uso aplicables',
        'use_cases_note': 'Ejemplos ilustrativos. No son clientes reales.',
        'use_cases_simple': [
            {'situation': 'Academia con 200+ alumnos y matrículas en papel/Excel', 'solution': 'Portal de matrícula online + sincronización con contabilidad'},
            {'situation': 'Restaurante con reservas por teléfono, WhatsApp y web sin centralizar', 'solution': 'Sistema unificado de reservas con confirmación automática'},
            {'situation': 'Taller industrial que recibe pedidos por email y los pasa a mano al ERP', 'solution': 'Automatización de entrada de pedidos con validación'},
            {'situation': 'Despacho profesional con documentos entrantes sin clasificar', 'solution': 'Clasificación automática + archivo por cliente'},
            {'situation': 'Comercio con tienda física y online con stock desincronizado', 'solution': 'Integración TPV–e-commerce en tiempo real'},
        ],
        'cta_title': '¿Tienes una empresa en Alcalá de Henares y quieres reducir trabajo manual?',
        'cta_text': 'Cuéntanos qué proceso te quita más tiempo. Respondemos en menos de 24 h.',
        'contact_origen': 'geo-alcala-henares',
        'related_slugs': ['comunidad-de-madrid', 'torrejon-de-ardoz', 'madrid'],
        'parent_slug': 'comunidad-de-madrid',
    },
    'torrejon-de-ardoz': {
        'slug': 'torrejon-de-ardoz',
        'city_name': 'Torrejón de Ardoz',
        'h1': 'Automatización y Desarrollo Tecnológico en Torrejón de Ardoz',
        'subtitle': (
            'Software, integraciones y automatización para empresas de Torrejón: comercio, logística, '
            'servicios y pymes que necesitan conectar sus sistemas y ganar eficiencia operativa.'
        ),
        'meta_title': 'Automatización y Desarrollo en Torrejón de Ardoz | Megasoluciones',
        'meta_description': (
            'Software, integraciones ERP y automatización para pymes de Torrejón: comercio, '
            'logística y servicios del Corredor del Henares.'
        ),
        'sitemap_priority': '0.7',
        'intro_title': 'Sectores típicos de Torrejón de Ardoz',
        'intro_paragraphs': [
            (
                'Torrejón es uno de los municipios más poblados del Corredor del Henares, con comercio '
                'urbano, servicios a empresas y actividad logística vinculada a Barajas y la A-2.'
            ),
        ],
        'sectors': [
            {'title': 'Comercio y retail', 'description': 'Grandes superficies, comercio de barrio y franquicias multicanal.'},
            {'title': 'Logística y transporte', 'description': 'Distribución, mensajería y operadores de última milla.'},
            {'title': 'Servicios a empresas', 'description': 'Mantenimiento, limpieza industrial, seguridad y subcontratas.'},
            {'title': 'Hostelería y ocio', 'description': 'Reservas, proveedores y gestión operativa diaria.'},
            {'title': 'Administración y concesionados', 'description': 'Procesos documentales y reporting periódico.'},
        ],
        'services_title': 'Servicios más relevantes',
        'services': [
            {'title': 'Automatización de procesos operativos', 'description': 'Sincronización de pedidos, albaranes, facturas y datos entre sistemas.'},
            {'title': 'Integraciones ERP / CRM / TPV', 'description': 'Eliminación de la doble entrada de datos en pymes en crecimiento.'},
            {'title': 'Desarrollo de software a medida', 'description': 'Paneles de incidencias, portales de clientes y apps para equipos de campo.'},
            {'title': 'Chatbots para atención al cliente', 'description': 'Consultas sobre envíos, plazos y estado de servicio en web y WhatsApp.'},
            {'title': 'Consultoría y diagnóstico tecnológico', 'description': 'Mapa de procesos y mejora por fases.'},
        ],
        'use_cases_title': 'Casos de uso aplicables',
        'use_cases_note': 'Ejemplos genéricos. No representan clientes concretos.',
        'use_cases_simple': [
            {'situation': 'Operador logístico con incidencias gestionadas por email', 'solution': 'Panel de incidencias con alertas automáticas y comunicación al cliente'},
            {'situation': 'Comercio con pedidos online y gestión en tienda desconectados', 'solution': 'Integración e-commerce + TPV + almacén'},
            {'situation': 'Empresa de servicios con partes de trabajo en papel', 'solution': 'App web para técnicos de campo con sincronización al ERP'},
            {'situation': 'Distribuidora con catálogo en Excel y pedidos por WhatsApp', 'solution': 'Portal de pedidos B2B conectado al sistema de facturación'},
            {'situation': 'Franquicia con reporting semanal manual entre locales', 'solution': 'Dashboard centralizado con datos automáticos de cada punto de venta'},
        ],
        'cta_title': '¿Tu empresa en Torrejón de Ardoz necesita conectar sistemas o automatizar procesos?',
        'cta_text': 'Primera consulta sin compromiso. Trabajamos en remoto y presencial en el Corredor del Henares.',
        'contact_origen': 'geo-torrejon-ardoz',
        'related_slugs': ['comunidad-de-madrid', 'coslada', 'alcala-de-henares'],
        'parent_slug': 'comunidad-de-madrid',
    },
    'coslada': {
        'slug': 'coslada',
        'city_name': 'Coslada',
        'h1': 'Automatización Industrial y Desarrollo de Software en Coslada',
        'subtitle': (
            'Soluciones tecnológicas para empresas del polígono industrial y el tejido empresarial de Coslada: '
            'integraciones, software a medida y automatización administrativa y operativa.'
        ),
        'meta_title': 'Automatización Industrial en Coslada | Megasoluciones',
        'meta_description': (
            'Integraciones ERP, RPA y desarrollo de software para empresas del polígono industrial '
            'y tejido empresarial de Coslada.'
        ),
        'sitemap_priority': '0.7',
        'intro_title': 'Sectores típicos de Coslada',
        'intro_paragraphs': [
            (
                'Coslada tiene un peso industrial relevante en la Comunidad de Madrid: metal, logística, '
                'alimentación y componentes en polígonos consolidados, además de comercio y servicios en el casco urbano.'
            ),
        ],
        'sectors': [
            {'title': 'Industria metalúrgica y mecánica', 'description': 'Talleres y fabricantes con administración manual pese a planta digitalizada.'},
            {'title': 'Logística y almacenaje', 'description': 'Operadores junto a la A-2 con gestión documental intensiva.'},
            {'title': 'Alimentación y distribución', 'description': 'Producción, envasado y trazabilidad con pedidos complejos.'},
            {'title': 'Comercio y servicios', 'description': 'Pymes del casco urbano con backoffice por digitalizar.'},
            {'title': 'Subcontratas industriales', 'description': 'Reporting y documentación exigida por clientes corporativos.'},
        ],
        'services_title': 'Servicios más relevantes',
        'services': [
            {'title': 'Automatización documental', 'description': 'Entrada de pedidos, albaranes, facturas de proveedor y conciliaciones.'},
            {'title': 'Integraciones ERP / MRP / CRM', 'description': 'Producción, almacén y facturación conectados sin intervención manual.'},
            {'title': 'Desarrollo de paneles y herramientas internas', 'description': 'Control de producción, incidencias, portales de proveedores y KPIs.'},
            {'title': 'RPA y workflows', 'description': 'Tareas repetitivas entre aplicaciones: informes, alertas y sincronización.'},
            {'title': 'Consultoría tecnológica industrial', 'description': 'Diagnóstico de backoffice en empresas con planta ya digitalizada.'},
        ],
        'use_cases_title': 'Casos de uso aplicables',
        'use_cases_note': 'Ejemplos ilustrativos. No son clientes reales.',
        'use_cases_simple': [
            {'situation': 'Fabricante con órdenes de producción en Excel y ERP desconectado', 'solution': 'Integración bidireccional entre planificación y ERP'},
            {'situation': 'Operador logístico con albaranes en PDF que se teclean a mano', 'solution': 'Extracción automática de datos + validación + carga al sistema'},
            {'situation': 'Empresa de componentes con reporting semanal exigido por clientes', 'solution': 'Generación automática de informes de calidad y entrega'},
            {'situation': 'Pyme industrial con facturación retrasada por carga administrativa', 'solution': 'Automatización de flujo pedido–albarán–factura'},
            {'situation': 'Taller con gestión de mantenimiento en papel', 'solution': 'App de partes de trabajo con historial de máquinas'},
        ],
        'cta_title': '¿Tu empresa en Coslada quiere reducir carga administrativa sin tocar la producción?',
        'cta_text': 'Empezamos por un diagnóstico de procesos. Sin compromiso.',
        'contact_origen': 'geo-coslada',
        'related_slugs': ['san-fernando-de-henares', 'torrejon-de-ardoz', 'comunidad-de-madrid'],
        'parent_slug': 'comunidad-de-madrid',
    },
    'rivas-vaciamadrid': {
        'slug': 'rivas-vaciamadrid',
        'city_name': 'Rivas-Vaciamadrid',
        'h1': 'Desarrollo de Software y Automatización en Rivas-Vaciamadrid',
        'subtitle': (
            'Soluciones tecnológicas para empresas del Parque Tecnológico, el retail de La Garena '
            'y el tejido empresarial de Rivas: software a medida, integraciones y automatización práctica.'
        ),
        'meta_title': 'Desarrollo de Software en Rivas-Vaciamadrid | Megasoluciones',
        'meta_description': (
            'Software a medida, integraciones y automatización para empresas del Parque Tecnológico, '
            'La Garena y Rivas-Vaciamadrid.'
        ),
        'sitemap_priority': '0.7',
        'intro_title': 'Sectores típicos de Rivas-Vaciamadrid',
        'intro_paragraphs': [
            (
                'Rivas combina parque tecnológico, gran área comercial (La Garena), empresas de servicios '
                'y una población residencial en crecimiento.'
            ),
        ],
        'sectors': [
            {'title': 'Tecnología y servicios digitales', 'description': 'Empresas del Parque Tecnológico con necesidad de desarrollo o integraciones.'},
            {'title': 'Retail y gran distribución', 'description': 'Operaciones multicanal, stock y atención al cliente.'},
            {'title': 'Servicios profesionales', 'description': 'Consultoras, agencias, clínicas y despachos.'},
            {'title': 'Construcción y servicios auxiliares', 'description': 'Proyectos, partes de obra y documentación dispersa.'},
            {'title': 'Educación y ocio familiar', 'description': 'Reservas, matrículas y comunicación con usuarios.'},
        ],
        'services_title': 'Servicios más relevantes',
        'services': [
            {'title': 'Desarrollo de software a medida', 'description': 'Aplicaciones web, APIs, MVPs y herramientas internas por fases.'},
            {'title': 'Integraciones entre plataformas', 'description': 'SaaS, CRM, ERP, pasarelas de pago y marketing conectados.'},
            {'title': 'Automatización de procesos', 'description': 'Reporting, onboarding, sincronización y tareas administrativas recurrentes.'},
            {'title': 'Chatbots y asistentes', 'description': 'Atención automatizada para retail y centros de servicios.'},
            {'title': 'Consultoría tecnológica', 'description': 'Hoja de ruta y viabilidad para escalar sin rehacer todo desde cero.'},
        ],
        'use_cases_title': 'Casos de uso aplicables',
        'use_cases_note': 'Ejemplos genéricos. No representan clientes concretos.',
        'use_cases_simple': [
            {'situation': 'Startup en parque tecnológico con MVP y necesidad de integrar IA', 'solution': 'Desarrollo por fases con API + modelo preentrenado'},
            {'situation': 'Tienda en La Garena con e-commerce y stock de tienda desincronizado', 'solution': 'Integración TPV–web con alertas de rotura de stock'},
            {'situation': 'Agencia de marketing con reporting manual para 15 clientes', 'solution': 'Dashboard automatizado con datos de Analytics, Ads y CRM'},
            {'situation': 'Clínica privada con citas por teléfono y web sin centralizar', 'solution': 'Reservas online + recordatorios automáticos'},
            {'situation': 'Empresa de servicios con contratos generados a mano', 'solution': 'Plantillas automatizadas con datos del CRM'},
        ],
        'cta_title': '¿Tienes una empresa en Rivas-Vaciamadrid y necesitas software o integraciones?',
        'cta_text': 'Cuéntanos tu proyecto. Primera consulta sin compromiso.',
        'contact_origen': 'geo-rivas-vaciamadrid',
        'related_slugs': ['madrid', 'arganda-del-rey', 'comunidad-de-madrid'],
        'parent_slug': 'comunidad-de-madrid',
    },
    'arganda-del-rey': {
        'slug': 'arganda-del-rey',
        'city_name': 'Arganda del Rey',
        'h1': 'Automatización y Desarrollo Tecnológico en Arganda del Rey',
        'subtitle': (
            'Soluciones de software e integraciones para empresas de Arganda: industria alimentaria, '
            'cerámica, logística y pymes del polígono que quieren modernizar procesos sin frenar la producción.'
        ),
        'meta_title': 'Automatización Empresas Arganda del Rey | Megasoluciones',
        'meta_description': (
            'Software e integraciones para industria alimentaria, cerámica y logística en Arganda del Rey. '
            'Piloto acotado, sin compromiso.'
        ),
        'sitemap_priority': '0.7',
        'intro_title': 'Sectores típicos de Arganda del Rey',
        'intro_paragraphs': [
            (
                'Arganda combina tradición industrial con polígonos activos en alimentación, cerámica, '
                'logística y servicios, además de comercio y hostelería en el casco urbano.'
            ),
        ],
        'sectors': [
            {'title': 'Industria alimentaria y bebidas', 'description': 'Bodegas, procesado, envasado y distribución con trazabilidad regulada.'},
            {'title': 'Cerámica y materiales de construcción', 'description': 'Pedidos B2B, materias primas y logística de entrega.'},
            {'title': 'Logística y transporte', 'description': 'Rutas, albaranes e incidencias en polígonos.'},
            {'title': 'Comercio y hostelería', 'description': 'Reservas, pedidos y proveedores aún manuales.'},
            {'title': 'Servicios auxiliares industriales', 'description': 'Mantenimiento, calidad y subcontratas con reporting exigido.'},
        ],
        'services_title': 'Servicios más relevantes',
        'services': [
            {'title': 'Automatización de flujos documentales', 'description': 'Pedidos, albaranes, certificados de calidad y facturas.'},
            {'title': 'Integraciones ERP / almacén / facturación', 'description': 'Un solo flujo desde el pedido hasta la factura.'},
            {'title': 'Desarrollo de herramientas a medida', 'description': 'Portales B2B, trazabilidad e incidencias en planta.'},
            {'title': 'Consultoría tecnológica', 'description': 'Salto digital en administración sin tocar la línea de producción.'},
            {'title': 'Chatbots B2B y B2C', 'description': 'Consultas sobre pedidos, plazos y catálogo conectadas al ERP.'},
        ],
        'use_cases_title': 'Casos de uso aplicables',
        'use_cases_note': 'Ejemplos ilustrativos. No son clientes reales.',
        'use_cases_simple': [
            {'situation': 'Bodega con pedidos por email y stock en Excel', 'solution': 'Portal B2B con pedidos online conectado al almacén'},
            {'situation': 'Fabricante cerámico con albaranes en papel', 'solution': 'Digitalización de albaranes + sincronización con facturación'},
            {'situation': 'Planta alimentaria con trazabilidad manual por lote', 'solution': 'Panel de trazabilidad con datos de producción y expedición'},
            {'situation': 'Distribuidor con rutas planificadas en hoja de cálculo', 'solution': 'Planificación con alertas de incidencias'},
            {'situation': 'Restaurante con proveedores gestionados por WhatsApp', 'solution': 'Pedidos a proveedores con historial y conciliación'},
        ],
        'cta_title': '¿Tu empresa en Arganda del Rey quiere automatizar administración o conectar sistemas?',
        'cta_text': 'Te proponemos un piloto acotado. Sin compromiso en la primera consulta.',
        'contact_origen': 'geo-arganda-del-rey',
        'related_slugs': ['comunidad-de-madrid', 'rivas-vaciamadrid'],
        'parent_slug': 'comunidad-de-madrid',
    },
    'san-fernando-de-henares': {
        'slug': 'san-fernando-de-henares',
        'city_name': 'San Fernando de Henares',
        'h1': 'Automatización y Desarrollo de Software en San Fernando de Henares',
        'subtitle': (
            'Soluciones tecnológicas para empresas de San Fernando: logística, comercio mayorista, '
            'industria ligera y servicios del Corredor del Henares que necesitan eficiencia operativa.'
        ),
        'meta_title': 'Automatización San Fernando de Henares | Megasoluciones',
        'meta_description': (
            'Desarrollo de software, portales B2B e integraciones logísticas para empresas de '
            'San Fernando de Henares y el Corredor.'
        ),
        'sitemap_priority': '0.7',
        'intro_title': 'Sectores típicos de San Fernando de Henares',
        'intro_paragraphs': [
            (
                'San Fernando ocupa una posición estratégica en el Corredor del Henares, con polígonos '
                'industriales, actividad logística y comercio mayorista.'
            ),
        ],
        'sectors': [
            {'title': 'Logística y almacenaje', 'description': 'Albaranes, incidencias y comunicación con clientes.'},
            {'title': 'Comercio mayorista y distribución', 'description': 'Catálogos amplios, pedidos B2B y rutas.'},
            {'title': 'Industria ligera y transformación', 'description': 'Administración manual pese a planta semi-automatizada.'},
            {'title': 'Servicios a empresas', 'description': 'Mantenimiento, mensajería y subcontratas del Corredor.'},
            {'title': 'Retail y comercio local', 'description': 'Venta y backoffice desconectados.'},
        ],
        'services_title': 'Servicios más relevantes',
        'services': [
            {'title': 'Automatización de procesos logísticos', 'description': 'Pedidos, albaranes, incidencias y sincronización con clientes.'},
            {'title': 'Integraciones ERP / WMS / CRM', 'description': 'Almacén, facturación y relación con clientes unificados.'},
            {'title': 'Desarrollo de portales B2B', 'description': 'Catálogo, pedidos recurrentes y estado de envío para mayoristas.'},
            {'title': 'RPA y workflows administrativos', 'description': 'Conciliaciones, reporting y altas de proveedores.'},
            {'title': 'Consultoría tecnológica', 'description': 'Diagnóstico en empresas que han crecido más rápido que su infraestructura digital.'},
        ],
        'use_cases_title': 'Casos de uso aplicables',
        'use_cases_note': 'Ejemplos genéricos. No representan clientes concretos.',
        'use_cases_simple': [
            {'situation': 'Mayorista con pedidos por fax, email y teléfono sin centralizar', 'solution': 'Portal B2B unificado conectado al ERP'},
            {'situation': 'Operador logístico con incidencias sin trazabilidad', 'solution': 'Panel de incidencias con historial y alertas automáticas'},
            {'situation': 'Empresa industrial con facturación retrasada por carga admin', 'solution': 'Automatización pedido–albarán–factura'},
            {'situation': 'Distribuidor con rutas asignadas manualmente cada mañana', 'solution': 'Asignación con datos de pedidos del día anterior'},
            {'situation': 'Comercio local con TPV y contabilidad desconectados', 'solution': 'Integración diaria de ventas con conciliación automática'},
        ],
        'cta_title': '¿Tu empresa en San Fernando de Henares quiere modernizar procesos?',
        'cta_text': 'Cuéntanos tu caso. Respondemos en menos de 24 horas.',
        'contact_origen': 'geo-san-fernando-henares',
        'related_slugs': ['coslada', 'comunidad-de-madrid', 'torrejon-de-ardoz'],
        'parent_slug': 'comunidad-de-madrid',
    },
}

# Municipios mostrados en el índice /geo/ (orden de navegación)
GEO_INDEX_GROUPS = [
    {
        'title': 'Región',
        'pages': ['comunidad-de-madrid', 'madrid'],
    },
    {
        'title': 'Corredor del Henares',
        'pages': [
            'alcala-de-henares',
            'torrejon-de-ardoz',
            'coslada',
            'san-fernando-de-henares',
        ],
    },
    {
        'title': 'Sur y este de la Comunidad',
        'pages': ['rivas-vaciamadrid', 'arganda-del-rey'],
    },
]


def get_geo_page(slug: str) -> dict | None:
    return GEO_PAGES.get(slug)


def iter_geo_pages() -> list[dict]:
    return list(GEO_PAGES.values())


def geo_sitemap_entries() -> list[dict]:
    entries = [{'path': '/geo/', 'changefreq': 'monthly', 'priority': GEO_HUB['sitemap_priority']}]
    for page in GEO_PAGES.values():
        entries.append({
            'path': f"/geo/{page['slug']}",
            'changefreq': 'monthly',
            'priority': page['sitemap_priority'],
        })
    return entries
