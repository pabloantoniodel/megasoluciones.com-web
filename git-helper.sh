#!/bin/bash

# Git Helper Script para Megasoluciones
# Simplifica operaciones Git comunes

echo "📦 Megasoluciones - Git Helper"
echo "=============================="
echo ""

case "$1" in
    status|s)
        echo "📊 Estado del repositorio:"
        git status
        ;;
    
    log|l)
        echo "📋 Últimos commits:"
        git log --oneline --graph --all -10
        ;;
    
    commit|c)
        if [ -z "$2" ]; then
            echo "❌ Error: Falta mensaje de commit"
            echo "Uso: ./git-helper.sh commit \"mensaje del commit\""
            exit 1
        fi
        echo "➕ Añadiendo cambios..."
        git add .
        echo "💾 Haciendo commit..."
        git commit -m "$2"
        echo "✅ Commit realizado!"
        ;;
    
    push|p)
        echo "📤 Subiendo cambios al remoto..."
        git push
        echo "✅ Push completado!"
        ;;
    
    pull)
        echo "📥 Descargando cambios del remoto..."
        git pull
        echo "✅ Pull completado!"
        ;;
    
    quick|q)
        if [ -z "$2" ]; then
            echo "❌ Error: Falta mensaje de commit"
            echo "Uso: ./git-helper.sh quick \"mensaje\""
            exit 1
        fi
        echo "⚡ Quick commit & push..."
        git add .
        git commit -m "$2"
        git push
        echo "✅ Cambios subidos!"
        ;;
    
    deploy|d)
        if [ -z "$2" ]; then
            MENSAJE="deploy: actualizar aplicación"
        else
            MENSAJE="$2"
        fi
        echo "🚀 Deploy completo (commit + push + rebuild Docker)..."
        git add .
        git commit -m "$MENSAJE"
        git push
        echo "🐳 Reconstruyendo Docker..."
        docker compose -f docker-compose.yml -f docker-compose.traefik.yml up --build -d
        echo "✅ Deploy completado!"
        ;;
    
    remote|r)
        echo "🌐 Repositorio remoto:"
        git remote -v
        ;;
    
    branch|b)
        echo "🌿 Ramas disponibles:"
        git branch -a
        ;;
    
    diff)
        echo "📝 Cambios no commiteados:"
        git diff
        ;;
    
    setup-github)
        if [ -z "$2" ]; then
            echo "❌ Error: Falta usuario de GitHub"
            echo "Uso: ./git-helper.sh setup-github TU_USUARIO"
            exit 1
        fi
        echo "🔧 Configurando remote de GitHub..."
        git remote add origin "https://github.com/$2/megasoluciones-web.git"
        echo "✅ Remote configurado!"
        echo "📤 Para subir: ./git-helper.sh push"
        ;;
    
    setup-gitlab)
        if [ -z "$2" ]; then
            echo "❌ Error: Falta usuario de GitLab"
            echo "Uso: ./git-helper.sh setup-gitlab TU_USUARIO"
            exit 1
        fi
        echo "🔧 Configurando remote de GitLab..."
        git remote add origin "https://gitlab.com/$2/megasoluciones-web.git"
        echo "✅ Remote configurado!"
        echo "📤 Para subir: ./git-helper.sh push"
        ;;
    
    *)
        echo "Uso: ./git-helper.sh [comando] [opciones]"
        echo ""
        echo "📋 Comandos disponibles:"
        echo ""
        echo "  status, s            - Ver estado del repositorio"
        echo "  log, l               - Ver últimos 10 commits"
        echo "  commit, c \"mensaje\"  - Add + commit con mensaje"
        echo "  push, p              - Push al remoto"
        echo "  pull                 - Pull del remoto"
        echo "  quick, q \"mensaje\"   - Add + commit + push (todo en uno)"
        echo "  deploy, d [mensaje]  - Commit + push + rebuild Docker"
        echo "  remote, r            - Ver repositorio remoto"
        echo "  branch, b            - Ver ramas"
        echo "  diff                 - Ver cambios no commiteados"
        echo "  setup-github USER    - Configurar GitHub remote"
        echo "  setup-gitlab USER    - Configurar GitLab remote"
        echo ""
        echo "💡 Ejemplos:"
        echo "  ./git-helper.sh commit \"feat: añadir blog\""
        echo "  ./git-helper.sh quick \"fix: corregir formulario\""
        echo "  ./git-helper.sh deploy \"deploy: v1.1.0\""
        echo "  ./git-helper.sh setup-github miusuario"
        echo ""
        exit 1
        ;;
esac
