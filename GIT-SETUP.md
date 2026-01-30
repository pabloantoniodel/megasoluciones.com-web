# 🚀 Git Repository - Megasoluciones

## ✅ Repositorio Git Inicializado

```
✅ Git inicializado
✅ Rama: main
✅ Commit inicial: 27 archivos
✅ .gitignore configurado
```

---

## 📤 SUBIR A GITHUB

### Opción 1: Crear Repositorio en GitHub (Web)

1. **Ve a GitHub**: https://github.com/new

2. **Configuración del repositorio**:
   - **Repository name**: `megasoluciones-web`
   - **Description**: `Web de servicios de IA y desarrollo con Flask, Traefik y SSL`
   - **Visibility**: Private (recomendado) o Public
   - ⚠️ **NO** marques "Initialize with README" (ya lo tenemos)

3. **Crear repositorio**

4. **Conectar y subir**:
```bash
cd /home/administrator/megasoluciones

# Añadir remote (reemplaza TU_USUARIO con tu usuario de GitHub)
git remote add origin https://github.com/TU_USUARIO/megasoluciones-web.git

# Push inicial
git push -u origin main
```

### Opción 2: GitHub CLI (si está instalado)

```bash
cd /home/administrator/megasoluciones

# Login (solo primera vez)
gh auth login

# Crear repo y push automático
gh repo create megasoluciones-web --private --source=. --push

# O si quieres público:
gh repo create megasoluciones-web --public --source=. --push
```

---

## 📤 SUBIR A GITLAB

### Crear Repositorio en GitLab

1. **Ve a GitLab**: https://gitlab.com/projects/new

2. **Configuración**:
   - **Project name**: `megasoluciones-web`
   - **Visibility**: Private o Public
   - **Initialize repository**: NO

3. **Conectar y subir**:
```bash
cd /home/administrator/megasoluciones

# Añadir remote
git remote add origin https://gitlab.com/TU_USUARIO/megasoluciones-web.git

# Push inicial
git push -u origin main
```

---

## 🎮 COMANDOS GIT ÚTILES

### Ver Estado
```bash
git status
```

### Ver Historial
```bash
git log --oneline --graph --all
```

### Añadir Cambios
```bash
# Añadir archivo específico
git add archivo.py

# Añadir todos los cambios
git add .

# Añadir solo archivos modificados (no nuevos)
git add -u
```

### Hacer Commit
```bash
git commit -m "Descripción del cambio"
```

### Push a Remoto
```bash
git push
```

### Pull (traer cambios)
```bash
git pull
```

### Ver Diferencias
```bash
# Ver cambios no commiteados
git diff

# Ver cambios en staging
git diff --staged
```

### Crear Rama
```bash
# Crear y cambiar a nueva rama
git checkout -b feature/nueva-funcionalidad

# Listar ramas
git branch

# Cambiar de rama
git checkout main
```

### Merge
```bash
# Desde main, mergear otra rama
git checkout main
git merge feature/nueva-funcionalidad
```

---

## 📋 WORKFLOW RECOMENDADO

### 1. Desarrollo Diario
```bash
# Ver estado
git status

# Añadir cambios
git add .

# Commit
git commit -m "feat: descripción del cambio"

# Push
git push
```

### 2. Trabajar con Ramas
```bash
# Crear rama para nueva feature
git checkout -b feature/chatbot-mejorado

# Hacer cambios y commits
git add .
git commit -m "feat: mejorar chatbot"

# Volver a main y mergear
git checkout main
git merge feature/chatbot-mejorado

# Push
git push
```

### 3. Desplegar Cambios
```bash
# Hacer cambios en código
vim app.py

# Commit
git add app.py
git commit -m "fix: corregir formulario contacto"

# Push a GitHub/GitLab
git push

# Actualizar en servidor
docker compose -f docker-compose.yml -f docker-compose.traefik.yml up --build -d
```

---

## 🏷️ CONVENCIONES DE COMMITS

Usa prefijos para organizar tus commits:

- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bugs
- `docs:` - Cambios en documentación
- `style:` - Cambios de estilo (CSS, formato)
- `refactor:` - Refactorización de código
- `test:` - Añadir tests
- `chore:` - Tareas de mantenimiento

**Ejemplos**:
```bash
git commit -m "feat: añadir sección blog"
git commit -m "fix: corregir validación email"
git commit -m "style: mejorar diseño mobile"
git commit -m "docs: actualizar README"
```

---

## 🔐 CONFIGURAR SSH (Recomendado)

Para no escribir contraseña cada vez:

### 1. Generar SSH Key
```bash
ssh-keygen -t ed25519 -C "info@megasolucion.net"
# Press Enter para todo (dejar por defecto)
```

### 2. Copiar Key Pública
```bash
cat ~/.ssh/id_ed25519.pub
```

### 3. Añadir a GitHub/GitLab
- **GitHub**: Settings → SSH and GPG keys → New SSH key
- **GitLab**: Preferences → SSH Keys

### 4. Cambiar URL a SSH
```bash
# En vez de HTTPS, usar SSH
git remote set-url origin git@github.com:TU_USUARIO/megasoluciones-web.git

# O para GitLab
git remote set-url origin git@gitlab.com:TU_USUARIO/megasoluciones-web.git
```

---

## 📊 INFORMACIÓN DEL REPOSITORIO

### Archivos Commiteados
```
27 archivos, 3244 líneas de código

Principales:
- app.py (200 líneas) - Aplicación Flask
- style.css (900 líneas) - Estilos personalizados
- 7 templates HTML - Páginas web
- Docker configs - Deployment
- Documentación completa
```

### .gitignore Configurado
```
✅ venv/ - Entorno virtual
✅ __pycache__/ - Cache Python
✅ *.pyc, *.pyo - Bytecode
✅ .env - Secrets
✅ *.db - Base de datos
✅ .DS_Store - Mac files
✅ *.log - Logs
```

---

## 🌿 ESTRUCTURA DE RAMAS RECOMENDADA

```
main
├── develop (rama de desarrollo)
├── feature/chatbot (nuevas features)
├── feature/blog
├── hotfix/bug-formulario (fixes urgentes)
└── release/v1.0 (releases)
```

### Crear Ramas
```bash
# Rama de desarrollo
git checkout -b develop

# Rama de feature
git checkout -b feature/blog

# Rama de hotfix
git checkout -b hotfix/ssl-error
```

---

## 🔄 ACTUALIZAR SERVIDOR DESPUÉS DE GIT PUSH

### Script Automático
Crea este script para actualizar fácilmente:

```bash
#!/bin/bash
# deploy.sh

cd /home/administrator/megasoluciones

echo "📥 Pulling latest changes..."
git pull

echo "🔨 Rebuilding Docker..."
docker compose -f docker-compose.yml -f docker-compose.traefik.yml up --build -d

echo "✅ Deployed!"
```

Hacer ejecutable:
```bash
chmod +x deploy.sh
```

Usar:
```bash
./deploy.sh
```

---

## 📝 COMANDOS RÁPIDOS DE REFERENCIA

```bash
# Estado actual
git status

# Log resumido
git log --oneline -10

# Ver remote
git remote -v

# Añadir todo y commit
git add . && git commit -m "mensaje"

# Add + Commit + Push (en uno)
git add . && git commit -m "mensaje" && git push

# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Ver archivos en último commit
git show --name-only

# Ver tamaño del repo
git count-objects -vH
```

---

## 🎯 NEXT STEPS

1. ✅ **Crear repositorio en GitHub/GitLab**
2. ✅ **Conectar remote**
3. ✅ **Push inicial**
4. 📝 **Crear README.md atractivo con badges**
5. 🏷️ **Crear release v1.0.0**
6. 🔄 **Configurar GitHub Actions / GitLab CI** (opcional - deploy automático)

---

## 🆘 PROBLEMAS COMUNES

### Error: "remote origin already exists"
```bash
git remote remove origin
git remote add origin URL_DEL_REPO
```

### Error: "failed to push - non-fast-forward"
```bash
git pull --rebase
git push
```

### Olvidé hacer commit antes de pull
```bash
git stash
git pull
git stash pop
```

---

**¡Repositorio Git listo para subir a GitHub/GitLab!** 🚀

**Commit inicial**: `0477f7c`
**Archivos**: 27
**Líneas de código**: 3.244
