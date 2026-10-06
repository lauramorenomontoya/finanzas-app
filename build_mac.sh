#!/bin/bash
set -e

# Cambiar al directorio del script
cd "$(dirname "$0")"

echo "============================================="
echo "   Compilando Control Financiero para macOS  "
echo "============================================="

# Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Instalar dependencias necesarias
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt
./venv/bin/pip install -q pyinstaller

# Limpiar compilaciones anteriores
rm -rf build dist

# Compilar la aplicación con PyInstaller
echo "Empaquetando aplicación .app..."
./venv/bin/pyinstaller ControlFinanciero.spec --noconfirm --clean

# Crear el instalador .dmg para compartir
echo "Generando instalador .dmg..."
hdiutil create -volname "Control Financiero" -srcfolder "dist/ControlFinanciero.app" -ov -format UDZO "dist/ControlFinanciero_macOS.dmg"

echo "============================================="
echo "✅ ¡Compilación completada exitosamente!"
echo "📦 Instalador listo para compartir:"
echo "   $(pwd)/dist/ControlFinanciero_macOS.dmg"
echo "============================================="
