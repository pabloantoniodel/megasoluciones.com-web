# SEO KPIs y medición — Megasoluciones (Fase 3)

## Google Search Console (.es y .com)

Revisión trimestral en ambas propiedades:

| Métrica | Baseline | Objetivo 6 meses |
|---------|----------|------------------|
| URLs indexadas | 11 → ~21 (sitemap) | 20+ |
| Impresiones/mes (clusters desarrollo + automatización) | Medir mes 0 | +150% |
| Errores de cobertura | 0 | 0 |
| Core Web Vitals | Medir PSI mobile | LCP < 2.5s, CLS < 0.1 |

**Clusters a filtrar en GSC:** desarrollo software, automatización, RPA, software a medida, integración Odoo.

## Google Analytics 4

### Activación

1. Crear propiedad GA4 para megasolucion.es/.com
2. Añadir Measurement ID en `ga4-id.txt` (raíz del proyecto) o variable `GA4_MEASUREMENT_ID` en Docker
3. Verificar en tiempo real tras despliegue

### Eventos implementados (app.v2.js)

| Evento | Parámetro | Cuándo |
|--------|-----------|--------|
| `form_submit` | `servicio` (valor del select) | Envío formulario contacto |
| `click_whatsapp` | `event_label: whatsapp_float` | Clic botón flotante WhatsApp |

### Informes recomendados

- Landing pages: tráfico por `/desarrollo-software`, `/automatizaciones`, `/recursos/*`
- Conversiones: form_submit por servicio
- Adquisición orgánica vs directo

## KPIs de negocio

| KPI | Objetivo 6 meses |
|-----|------------------|
| Leads formulario/mes | +50% vs baseline |
| Posición media 5 keywords piloto | Top 20 |
| CTR en snippets principales | Mejorar con titles/OG optimizados |

**Keywords piloto sugeridas:**

1. desarrollo software a medida españa
2. automatización procesos empresa
3. RPA empresas españa
4. integración odoo crm
5. cuánto cuesta desarrollo software

## SEO local (fase posterior)

No activar GBP hasta definir ciudad/zona. Cuando aplique:

- Schema `LocalBusiness` con `areaServed`
- NAP consistente en directorios
- Reseñas de clientes de casos reales

## PageSpeed Insights

Medir mensualmente:

- Home (mobile)
- `/desarrollo-software`
- `/automatizaciones`
- 1 artículo `/recursos/*`

Registrar LCP, INP, CLS en hoja de seguimiento trimestral.

## Dashboard trimestral (plantilla)

```
Trimestre: Q_
GSC .es: impresiones __ | clics __ | CTR __%
GSC .com: impresiones __ | clics __ | CTR __%
URLs indexadas: __
Leads formulario: __
Eventos WhatsApp: __
PSI mobile LCP home: __s
Notas / acciones:
```
