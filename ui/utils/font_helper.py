"""
Utilidad de Tipografía y Fuentes Multiplataforma para Control Financiero.
Detecta el sistema operativo para aplicar la mejor fuente nativa disponible
(SF Pro en macOS, Segoe UI en Windows, Ubuntu/DejaVu en Linux).
"""

import platform


def get_font_family(style: str = "text") -> str:
    """
    Retorna la familia tipográfica recomendada según la plataforma:
    - style='display': Para cabeceras, títulos y valores numéricos grandes.
    - style='text': Para cuerpo de texto, etiquetas y botones.
    """
    sys_name = platform.system()
    if sys_name == "Darwin":  # macOS
        return "SF Pro Display" if style == "display" else "SF Pro Text"
    elif sys_name == "Windows":  # Windows
        return "Segoe UI"
    else:  # Linux y otros
        return "Ubuntu" if style == "display" else "DejaVu Sans"
