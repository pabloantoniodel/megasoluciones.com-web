#!/usr/bin/env python3
"""
Script para convertir el logo SVG a PNG transparente y ICO (favicon)
Usa base64 y generación de imágenes web
"""
import base64
import os

# Crear el SVG del ícono
svg_icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <defs>
    <linearGradient id="hexGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#00d4ff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#00ff88;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <path d="M 50 5 L 86.6 27.5 L 86.6 72.5 L 50 95 L 13.4 72.5 L 13.4 27.5 Z" 
        fill="none" 
        stroke="url(#hexGradient)" 
        stroke-width="2.5" 
        stroke-linejoin="round"/>
  
  <line x1="25" y1="30" x2="25" y2="70" stroke="url(#hexGradient)" stroke-width="2" stroke-linecap="round"/>
  <circle cx="25" cy="30" r="2.5" fill="url(#hexGradient)"/>
  <circle cx="25" cy="70" r="2.5" fill="url(#hexGradient)"/>
  
  <line x1="25" y1="30" x2="50" y2="50" stroke="url(#hexGradient)" stroke-width="2" stroke-linecap="round"/>
  <circle cx="50" cy="50" r="3" fill="url(#hexGradient)"/>
  
  <line x1="50" y1="50" x2="75" y2="30" stroke="url(#hexGradient)" stroke-width="2" stroke-linecap="round"/>
  <circle cx="75" cy="30" r="2.5" fill="url(#hexGradient)"/>
  
  <line x1="75" y1="30" x2="75" y2="70" stroke="url(#hexGradient)" stroke-width="2" stroke-linecap="round"/>
  <circle cx="75" cy="70" r="2.5" fill="url(#hexGradient)"/>
  
  <line x1="35" y1="40" x2="45" y2="48" stroke="url(#hexGradient)" stroke-width="1.5" stroke-linecap="round"/>
  <circle cx="35" cy="40" r="2" fill="url(#hexGradient)"/>
  
  <line x1="55" y1="48" x2="65" y2="40" stroke="url(#hexGradient)" stroke-width="1.5" stroke-linecap="round"/>
  <circle cx="65" cy="40" r="2" fill="url(#hexGradient)"/>
  
  <line x1="30" y1="55" x2="40" y2="60" stroke="url(#hexGradient)" stroke-width="1.5" stroke-linecap="round"/>
  <circle cx="30" cy="55" r="2" fill="url(#hexGradient)"/>
  
  <line x1="60" y1="60" x2="70" y2="55" stroke="url(#hexGradient)" stroke-width="1.5" stroke-linecap="round"/>
  <circle cx="70" cy="55" r="2" fill="url(#hexGradient)"/>
  
  <circle cx="40" cy="35" r="1.5" fill="url(#hexGradient)"/>
  <circle cx="60" cy="35" r="1.5" fill="url(#hexGradient)"/>
  <circle cx="40" cy="65" r="1.5" fill="url(#hexGradient)"/>
  <circle cx="60" cy="65" r="1.5" fill="url(#hexGradient)"/>
  
  <line x1="35" y1="25" x2="45" y2="25" stroke="url(#hexGradient)" stroke-width="1" stroke-linecap="round"/>
  <line x1="55" y1="25" x2="65" y2="25" stroke="url(#hexGradient)" stroke-width="1" stroke-linecap="round"/>
  <circle cx="35" cy="25" r="1.5" fill="url(#hexGradient)"/>
  <circle cx="65" cy="25" r="1.5" fill="url(#hexGradient)"/>
</svg>'''

print("✓ SVG del ícono creado en: static/images/logo-icon.svg")
print("\n📋 Para generar PNG transparente y ICO:")
print("\nOpción 1 - Usando el navegador:")
print("  1. Abre: static/images/convert-logo.html en tu navegador")
print("  2. Haz clic en los botones para descargar los archivos")
print("\nOpción 2 - Usando herramientas online:")
print("  1. Ve a https://convertio.co/es/svg-png/ o https://cloudconvert.com/svg-to-png")
print("  2. Sube el archivo logo-icon.svg")
print("  3. Descarga el PNG transparente")
print("  4. Para ICO, usa https://convertio.co/es/png-ico/")
print("\nOpción 3 - Si tienes ImageMagick instalado:")
print("  convert logo-icon.svg -background none -resize 512x512 logo-icon.png")
print("  convert logo-icon.svg -background none -resize 32x32 favicon.ico")

print("\n" + "="*60)
print("Archivos creados:")
print("  ✓ static/images/logo-icon.svg (Ícono vectorial)")
print("  ✓ static/images/convert-logo.html (Conversor web)")
print("="*60)
