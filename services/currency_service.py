"""
Servicio para consulta de la Tasa Representativa del Mercado (TRM) oficial de Colombia (USD -> COP).
Consume prioritariamente la API de la Superintendencia Financiera de Colombia en Datos Abiertos (datos.gov.co).
Incluye fuentes de respaldo internacionales gratuitas (open.er-api.com y exchangerate-api.com).
Cuenta con timeout estricto, headers de cliente de datos y ejecución asíncrona no bloqueante.
"""

import json
import threading
import ssl
import urllib.request
import urllib.error
from typing import Callable, Optional


class CurrencyService:
    DEFAULT_RATE = 3350.0

    # Fuente Primaria Oficial: Superintendencia Financiera de Colombia (Datos Abiertos)
    SUPERFINANCIERA_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC"

    # Fuentes de Respaldo Internacionales
    FALLBACK_URLS = [
        "https://open.er-api.com/v6/latest/USD",
        "https://api.exchangerate-api.com/v4/latest/USD"
    ]

    @staticmethod
    def get_live_usd_to_cop_rate(timeout: float = 4.0) -> Optional[float]:
        """
        Obtiene la TRM oficial de Colombia (USD -> COP).
        Intenta primero la API oficial de la Superintendencia Financiera (datos.gov.co).
        Si no responde en el tiempo límite, recurre a APIs internacionales de respaldo.
        """
        headers = {
            "User-Agent": "Montu/1.0 (Macintosh; Intel)",
            "Accept": "application/json"
        }

        try:
            ctx = ssl.create_default_context()
        except Exception:
            ctx = None

        # 1. Intentar Superintendencia Financiera de Colombia (TRM Oficial)
        try:
            req = urllib.request.Request(CurrencyService.SUPERFINANCIERA_URL, headers=headers)
            kwargs = {"timeout": timeout}
            if ctx is not None:
                kwargs["context"] = ctx

            with urllib.request.urlopen(req, **kwargs) as response:
                if response.status == 200:
                    content = response.read().decode("utf-8")
                    data = json.loads(content)
                    if isinstance(data, list) and len(data) > 0:
                        first = data[0]
                        if "valor" in first:
                            val = float(first["valor"])
                            if val > 0:
                                return round(val, 2)
        except Exception:
            pass

        # 2. Fuentes de respaldo internacionales
        for url in CurrencyService.FALLBACK_URLS:
            try:
                req = urllib.request.Request(url, headers=headers)
                kwargs = {"timeout": timeout}
                if ctx is not None:
                    kwargs["context"] = ctx

                with urllib.request.urlopen(req, **kwargs) as response:
                    if response.status != 200:
                        continue
                    content = response.read().decode("utf-8")
                    data = json.loads(content)

                    if isinstance(data, dict) and "rates" in data and isinstance(data["rates"], dict):
                        cop_rate = data["rates"].get("COP")
                        if cop_rate is not None:
                            val = float(cop_rate)
                            if val > 0:
                                return round(val, 2)
            except Exception:
                continue

        return None

    @staticmethod
    def fetch_rate_async(callback: Callable[[Optional[float]], None]):
        """Ejecuta la consulta en un hilo secundario independiente para no bloquear la interfaz gráfica."""
        def worker():
            try:
                rate = CurrencyService.get_live_usd_to_cop_rate(timeout=4.0)
                callback(rate)
            except Exception:
                callback(None)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
