"""
Servicio para consulta de tasa de cambio en vivo (USD -> COP).
Consume APIs públicas y gratuitas sin API Key (open.er-api.com y exchangerate-api.com).
Incluye timeout estricto, headers de navegador y manejo asíncrono para garantizar fluidez en la UI.
"""

import json
import threading
import ssl
import urllib.request
import urllib.error
from typing import Callable, Optional


class CurrencyService:
    DEFAULT_RATE = 3100.0

    API_URLS = [
        "https://open.er-api.com/v6/latest/USD",
        "https://api.exchangerate-api.com/v4/latest/USD"
    ]

    @staticmethod
    def get_live_usd_to_cop_rate(timeout: float = 4.0) -> Optional[float]:
        """
        Obtiene la tasa de cambio USD -> COP en tiempo real desde APIs públicas gratuitas.
        Extrae el valor del campo 'COP' dentro del diccionario 'rates'.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }

        try:
            ctx = ssl.create_default_context()
        except Exception:
            ctx = None

        for url in CurrencyService.API_URLS:
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

                    # Extraer el valor de COP en 'rates'
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
