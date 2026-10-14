#!/usr/bin/env python3
"""
Montu - Gestor Financiero Multimoneda (USD / COP)
Punto de entrada principal de la aplicación.
"""

import sys
import os
import logging

# Configuración de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("montu")

# Asegurar que el directorio raíz esté en sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Asegurar certificados CA en macOS/Linux para entornos congelados (PyInstaller)
if "SSL_CERT_FILE" not in os.environ:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        for ca_rel in ["certifi/cacert.pem", "cacert.pem"]:
            ca_cand = os.path.join(meipass, ca_rel)
            if os.path.exists(ca_cand):
                os.environ["SSL_CERT_FILE"] = ca_cand
                break
    if "SSL_CERT_FILE" not in os.environ and os.path.exists("/etc/ssl/cert.pem"):
        os.environ["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"

# Auto-relanzar usando el entorno virtual si se ejecutó con el Python del sistema (solo en modo desarrollo)
if not getattr(sys, "frozen", False):
    venv_python = os.path.join(BASE_DIR, "venv", "bin", "python3")
    if sys.prefix == sys.base_prefix and os.path.exists(venv_python) and sys.executable != venv_python:
        os.execv(venv_python, [venv_python] + sys.argv)

try:
    import customtkinter as ctk
except ImportError:
    logger.error("La librería 'customtkinter' no está instalada.")
    print("\n" + "="*70)
    print("❌ ERROR: La librería 'customtkinter' no está instalada.")
    print("Por favor instala las dependencias ejecutando en tu terminal:")
    print("    pip install -r requirements.txt")
    print("="*70 + "\n")
    sys.exit(1)

from ui.app import FinancialApp
from ui.utils.scroll_helper import ScrollHelper


def main():
    try:
        logger.info("Iniciando Montu...")
        ScrollHelper.enable_smooth_scrolling()
        app = FinancialApp()
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("Aplicación cerrada por el usuario.")
    except Exception as e:
        logger.exception("Ocurrió un error inesperado al ejecutar la aplicación: %s", e)


if __name__ == "__main__":
    main()
