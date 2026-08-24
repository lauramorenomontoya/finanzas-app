#!/usr/bin/env python3
"""
Control Financiero - Gestor Financiero Multimoneda (USD / COP)
Punto de entrada principal de la aplicación.
"""

import sys
import os

# Asegurar que el directorio raíz esté en sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Auto-relanzar usando el entorno virtual si se ejecutó con el Python del sistema
venv_python = os.path.join(BASE_DIR, "venv", "bin", "python3")
if sys.prefix == sys.base_prefix and os.path.exists(venv_python) and sys.executable != venv_python:
    os.execv(venv_python, [venv_python] + sys.argv)

try:
    import customtkinter as ctk
except ImportError:
    print("\n" + "="*70)
    print("❌ ERROR: La librería 'customtkinter' no está instalada.")
    print("Por favor instala las dependencias ejecutando en tu terminal:")
    print("    pip install -r requirements.txt")
    print("="*70 + "\n")
    sys.exit(1)

from ui.app import FinancialApp


def main():
    try:
        app = FinancialApp()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nAplicación cerrada por el usuario.")
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado al ejecutar la aplicación: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
