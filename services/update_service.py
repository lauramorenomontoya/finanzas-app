"""
Servicio de Detección de Actualizaciones para Control Financiero.
Consulta la API pública de GitHub Releases en segundo plano para verificar si existe
una versión más reciente del sistema y proveer el enlace de descarga correspondiente.
"""

import json
import logging
import platform
import re
import sys
import threading
import urllib.request
import urllib.error
from typing import Callable, Dict, Any, Optional, Tuple

logger = logging.getLogger("ControlFinanciero.UpdateService")

GITHUB_REPO = "lauramorenomontoya/finanzas"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class UpdateService:
    @staticmethod
    def parse_version(version_str: str) -> Tuple[int, ...]:
        """
        Convierte una cadena de versión como 'v1.2.0', '1.3', 'v2.0.1-beta'
        en una tupla de enteros comparables (1, 2, 0).
        """
        if not version_str:
            return (0, 0, 0)
        
        # Eliminar 'v' inicial y extraer los bloques de dígitos
        cleaned = version_str.strip().lstrip("vV")
        numbers = re.findall(r"\d+", cleaned)
        if not numbers:
            return (0, 0, 0)
        return tuple(int(n) for n in numbers)

    @classmethod
    def check_for_updates(cls, current_version: str) -> Dict[str, Any]:
        """
        Consulta síncrona a la API de GitHub Releases.
        Retorna un diccionario con el resultado del chequeo.
        """
        result: Dict[str, Any] = {
            "update_available": False,
            "current_version": current_version,
            "latest_version": current_version,
            "release_name": "",
            "release_notes": "",
            "download_url": "",
            "html_url": "",
            "error": None
        }

        req = urllib.request.Request(
            LATEST_RELEASE_URL,
            headers={
                "User-Agent": "ControlFinanciero-DesktopApp",
                "Accept": "application/vnd.github.v3+json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=4.0) as response:
                if response.status != 200:
                    result["error"] = f"HTTP {response.status}"
                    return result

                data = json.loads(response.read().decode("utf-8"))

            tag_name = data.get("tag_name", "")
            current_tuple = cls.parse_version(current_version)
            latest_tuple = cls.parse_version(tag_name)

            html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
            result["html_url"] = html_url
            result["latest_version"] = tag_name.lstrip("vV")
            result["release_name"] = data.get("name") or f"Versión {tag_name}"
            result["release_notes"] = data.get("body", "").strip()

            # Encontrar el enlace de descarga según la plataforma del usuario
            assets = data.get("assets", [])
            download_url = None

            is_mac = sys.platform == "darwin"
            is_win = sys.platform == "win32"

            if is_mac:
                for asset in assets:
                    name = asset.get("name", "").lower()
                    if name.endswith(".dmg") or (name.endswith(".zip") and "mac" in name):
                        download_url = asset.get("browser_download_url")
                        break
            elif is_win:
                for asset in assets:
                    name = asset.get("name", "").lower()
                    if name.endswith(".exe") or (name.endswith(".zip") and "win" in name):
                        download_url = asset.get("browser_download_url")
                        break

            # Fallback a la página de releases si no hay asset específico
            result["download_url"] = download_url or html_url

            if latest_tuple > current_tuple:
                result["update_available"] = True
                logger.info(f"Actualización detectada: {current_version} -> {tag_name}")
            else:
                logger.debug(f"La versión actual ({current_version}) está al día.")

        except urllib.error.HTTPError as e:
            # 404 significa que aún no hay releases creados
            if e.code == 404:
                logger.debug("No se encontraron releases públicos en el repositorio.")
            else:
                logger.warning(f"Error consultando actualizaciones: HTTP {e.code}")
            result["error"] = f"HTTP {e.code}"
        except Exception as e:
            # Errores de red, timeout, etc., no deben interrumpir al usuario
            logger.debug(f"No fue posible verificar actualizaciones: {e}")
            result["error"] = str(e)

        return result

    @classmethod
    def check_for_updates_async(cls, current_version: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Ejecuta el chequeo de actualizaciones en un hilo secundario y entrega el
        resultado al callback en cuanto termine.
        """
        def _worker():
            info = cls.check_for_updates(current_version)
            try:
                callback(info)
            except Exception as e:
                logger.error(f"Error en callback de actualización: {e}")

        thread = threading.Thread(target=_worker, daemon=True, name="UpdateCheckerThread")
        thread.start()
