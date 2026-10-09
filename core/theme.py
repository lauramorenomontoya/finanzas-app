"""
core/theme.py - Sistema de Diseño y Tema Central ("Dark Finance") para Montu.
Única fuente de la verdad para paleta de colores, tipografía nativa y espaciado.
"""

import platform


def get_system_font_family(style: str = "text") -> str:
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


# Constante base de tipografía (SF Pro en macOS; cambiar aquí para migrar a Inter globalmente)
FONT_FAMILY = get_system_font_family("text")


class Theme:
    """
    Tokens de diseño para Montu.
    Mantiene compatibilidad con tuplas CustomTkinter: (color_modo_claro, color_modo_oscuro).
    """

    # Tipografía
    FONT_DISPLAY = get_system_font_family("display")
    FONT_TEXT = get_system_font_family("text")

    # Escala de Espaciado (múltiplos de 8, 12, 16, 24, 32)
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 16
    SPACING_LG = 24
    SPACING_XL = 32

    # Radios de esquina moderados (10 a 12 px)
    RADIUS_CARD = 12
    RADIUS_BUTTON = 10
    RADIUS_INPUT = 8
    RADIUS_PILL = 12

    # Fondos
    BG_WINDOW = ("#f8fafc", "#0f172a")          # Fondo de ventana principal
    BG_SIDEBAR = ("#f1f5f9", "#090d16")         # Fondo de barra lateral
    BG_CARD = ("#ffffff", "#1e293b")            # Paneles y tarjetas
    BG_CARD_SUBTLE = ("#f1f5f9", "#0f172a")     # Cajas internas
    BG_INPUT = ("#ffffff", "#0f172a")           # Campos de texto y combos
    BG_PROGRESS_TRACK = ("#e2e8f0", "#334155")  # Fondo de barras de progreso

    # Bordes
    BORDER_DEFAULT = ("#cbd5e1", "#334155")
    BORDER_SIDEBAR = ("#cbd5e1", "#1e293b")
    BORDER_SUBTLE = ("#e2e8f0", "#1e293b")

    # Textos
    TEXT_PRIMARY = ("#0f172a", "#f8fafc")
    TEXT_SECONDARY = ("#334155", "#94a3b8")
    TEXT_MUTED = ("#475569", "#94a3b8")
    TEXT_ON_COLOR = ("#ffffff", "#ffffff")

    # Acentos (Paleta Primaria)
    ACCENT_BLUE = ("#0284c7", "#38bdf8")
    ACCENT_GREEN = ("#059669", "#10b981")
    ACCENT_ROSE = ("#e11d48", "#f43f5e")
    ACCENT_INDIGO = ("#4f46e5", "#818cf8")

    # Colores Semánticos (Status)
    SUCCESS = ("#059669", "#10b981")            # Verde / Esmeralda
    SUCCESS_HOVER = ("#047857", "#34d399")
    WARNING = ("#d97706", "#f59e0b")            # Ámbar
    WARNING_HOVER = ("#b45309", "#fbbf24")
    ERROR = ("#e11d48", "#f43f5e")              # Coral / Rojo
    ERROR_HOVER = ("#be123c", "#fb7185")
    INFO = ("#0284c7", "#38bdf8")               # Azul
    INFO_HOVER = ("#0369a1", "#7dd3fc")

    # Banners de estado y mundos de moneda (USD = Esmeralda / Azul, COP = Ámbar)
    USD_BANNER_BG = ("#e0f2fe", "#082f49")
    USD_BANNER_BORDER = ("#7dd3fc", "#0284c7")
    USD_BANNER_TEXT = ("#0284c7", "#38bdf8")

    COP_BANNER_BG = ("#d1fae5", "#064e3b")
    COP_BANNER_BORDER = ("#6ee7b7", "#10b981")
    COP_BANNER_TEXT = ("#059669", "#10b981")
