# 🚀 Guía de Despliegue en Render (GRATIS)

## Paso 1: Preparar el Repositorio Git

```bash
cd megasoluciones
git init
git add .
git commit -m "Initial commit - Megasoluciones Web"
```

## Paso 2: Subir a GitHub

1. Crear repositorio en GitHub: https://github.com/new
2. Nombre: `megasoluciones-web`
3. Ejecutar:

```bash
git remote add origin https://github.com/TU_USUARIO/megasoluciones-web.git
git branch -M main
git push -u origin main
```

## Paso 3: Desplegar en Render

1. **Crear cuenta gratis**: https://render.com/
2. **New → Web Service**
3. **Connect GitHub repository**: Autorizar y seleccionar `megasoluciones-web`
4. **Configuración**:
   - **Name**: `megasoluciones`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: `Free`

5. **Environment Variables** (Add):
   ```
   SECRET_KEY = genera-una-clave-segura-aqui-123456
   ```

6. **Click "Create Web Service"**

## Paso 4: ¡Listo!

Tu web estará disponible en:
```
https://megasoluciones.onrender.com
```

⏱️ Primer deploy: 5-10 minutos
🔄 Deploys automáticos: Cada git push

## Opciones Adicionales

### Dominio Personalizado
1. En Render Dashboard → Settings → Custom Domain
2. Añadir: `www.megasoluciones.com`
3. Configurar DNS según instrucciones

### SSL/HTTPS
✅ Incluido automáticamente (Let's Encrypt)

### Escalado
- Plan Free: OK para 10.000 visitas/mes
- Plan Starter ($7/mes): 100.000 visitas/mes
- Auto-scale disponible

## Troubleshooting

**Error "Module not found"**
→ Verificar requirements.txt está completo

**Error 500**
→ Ver logs en Render Dashboard → Logs

**Aplicación lenta al inicio**
→ Normal en plan Free (duerme tras 15min inactividad)

---

**Tiempo total de despliegue: 10-15 minutos** ⚡
