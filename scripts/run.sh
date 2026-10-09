#!/bin/bash
# Lanzador Inteligente de Control Financiero (macOS/Linux)

# Cambiar al directorio raíz del proyecto
cd "$(dirname "$0")/.."

if [ -f "venv/bin/python3" ]; then
    ./venv/bin/python3 main.py
elif command -v python3 &> /dev/null; then
    python3 main.py
elif command -v python &> /dev/null; then
    python main.py
else
    echo "❌ ERROR: No se encontró Python en el sistema."
    echo "Por favor instala Python 3 para continuar."
    exit 1
fi
