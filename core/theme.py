"""
core/theme.py - Sistema de Diseño y Tema Central ("Dark Finance") para Montu.
Única fuente de la verdad para paleta de colores, tipografía nativa y espaciado.
"""

import platform
from typing import Tuple, Union, Optional
import customtkinter as ctk


def get_resolved_font_family() -> str:
    """
    Resuelve dinámicamente la fuente del sistema disponible en Tkinter con fallback seguro:
    - En macOS: Busca 'SF Pro Text' -> 'SF Pro' -> 'Helvetica Neue' -> 'Helvetica' -> 'Arial'.
    - En Windows: Busca 'Segoe UI' -> 'Arial'.
    - En Linux: Busca 'Ubuntu' -> 'DejaVu Sans' -> 'Arial'.
    """
    available = set()
    try:
        import tkinter as tk
        import tkinter.font as tkfont
        root = tk._default_root
        temp_root = False
        if root is None:
            try:
                root = tk.Tk()
                root.withdraw()
                temp_root = True
            except Exception:
                root = None
        if root is not None:
            available = set(tkfont.families(root))
            if temp_root:
                root.destroy()
    except Exception:
        pass

    if platform.system() == "Darwin":
        for font in ["SF Pro Text", "SF Pro", "Helvetica Neue", "Helvetica"]:
            if font in available:
                return font
        return "Helvetica Neue" if ("Helvetica Neue" in available or not available) else "Arial"
    elif platform.system() == "Windows":
        return "Segoe UI" if ("Segoe UI" in available or not available) else "Arial"
    else:
        for font in ["Ubuntu", "DejaVu Sans"]:
            if font in available:
                return font
        return "Arial"


# Constante base de tipografía (cambiar aquí modifica toda la app, ej. a 'Inter')
FONT_FAMILY = get_resolved_font_family()


class Theme:
    """
    Tokens de diseño "Dark Finance" para Montu.
    Mantiene compatibilidad con tuplas CustomTkinter: (color_modo_claro, color_modo_oscuro).
    """

    # Tipografía del sistema y estilos
    FONT_DISPLAY = FONT_FAMILY
    FONT_TEXT = FONT_FAMILY

    @classmethod
    def font_title(cls, size: int = 24, weight: str = "bold") -> ctk.CTkFont:
        return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

    @classmethod
    def font_subtitle(cls, size: int = 14, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

    @classmethod
    def font_body(cls, size: int = 12, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

    @classmethod
    def font_figures(cls, size: int = 18, weight: str = "bold") -> ctk.CTkFont:
        return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

    # Escala de Espaciado (múltiplos de 8, 12, 16, 24, 32)
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_BASE = 12
    SPACING_MD = 16
    SPACING_LG = 24
    SPACING_XL = 32

    # Radios de esquina moderados (10 a 12 px)
    RADIUS_CARD = 12
    RADIUS_BUTTON = 10
    RADIUS_INPUT = 8
    RADIUS_PILL = 12

    # --- Paleta Dark Finance (Constantes Hex directas) ---
    BG_APP = "#111713"         # Obsidiana (fondo principal)
    BG_PANEL = "#1A211D"       # Carbón (paneles y tarjetas)
    ACCENT = "#75D9A5"         # Esmeralda (acciones principales, saldos positivos, mundo USD / Bóveda)
    ACCENT_HOVER = ("#047857", "#5EC48F")
    ACCENT_USD = "#75D9A5"     # Esmeralda (mundo USD / Bóveda)
    ACCENT_COP = "#E3B368"     # Ámbar suave (mundo COP / Presupuesto)
    TEXT_PRIMARY = "#F0F4F1"   # Marfil frío (texto principal)
    TEXT_SECONDARY = "#8D9B92" # Salvia (texto secundario)
    DANGER = "#D97878"         # Coral (errores y alertas)
    DANGER_HOVER = ("#BE123C", "#C56565")

    # --- Tuplas CustomTkinter (modo claro, modo oscuro Dark Finance) ---
    BG_WINDOW = ("#F4F7F5", "#111713")          # Fondo principal
    BG_SIDEBAR = ("#EAEFEA", "#0D130F")         # Fondo barra lateral
    BG_CARD = ("#FFFFFF", "#1A211D")            # Paneles y tarjetas
    BG_CARD_HOVER = ("#F0F4F1", "#222B25")      # Hover para tarjetas y botones secundarios
    BG_CARD_SUBTLE = ("#F0F4F1", "#151C17")     # Cajas internas y cards secundarias
    BG_INPUT = ("#FFFFFF", "#151C17")           # Campos de entrada
    BG_PROGRESS_TRACK = ("#E2E8F0", "#263029")  # Pistas de barras de progreso

    # Bordes sutiles
    BORDER_DEFAULT = ("#D5DDD7", "#263029")
    BORDER_SIDEBAR = ("#D5DDD7", "#1E2721")
    BORDER_SUBTLE = ("#E2E8E4", "#1E2721")

    # Textos adaptables
    TEXT_MUTED = ("#6B7A70", "#64746A")
    TEXT_ON_COLOR = ("#FFFFFF", "#111713")      # Para botones con fondo brillante
    TEXT_ON_DARK = ("#FFFFFF", "#F0F4F1")

    # Acentos de color semánticos
    ACCENT_GREEN = ("#059669", "#75D9A5")       # Esmeralda
    ACCENT_BLUE = ("#0284C7", "#75D9A5")        # Esmeralda (compatibilidad)
    ACCENT_ROSE = ("#E11D48", "#D97878")        # Coral
    ACCENT_INDIGO = ("#4F46E5", "#75D9A5")
    ACCENT_AMBER = ("#D97706", "#E3B368")       # Ámbar

    # Estados y Feedback
    SUCCESS = ("#059669", "#75D9A5")            # Verde Esmeralda
    SUCCESS_HOVER = ("#047857", "#5EC48F")
    WARNING = ("#D97706", "#E3B368")            # Ámbar
    WARNING_HOVER = ("#B45309", "#CCA057")
    ERROR = ("#E11D48", "#D97878")              # Coral
    ERROR_HOVER = ("#BE123C", "#C56565")
    INFO = ("#0284C7", "#75D9A5")               # Esmeralda
    INFO_HOVER = ("#0369A1", "#5EC48F")

    # Banners de estado por mundo de moneda
    # Mundo USD (Esmeralda)
    USD_BANNER_BG = ("#E6F7EF", "#14221A")
    USD_BANNER_BORDER = ("#75D9A5", "#274734")
    USD_BANNER_TEXT = ("#059669", "#75D9A5")

    # Mundo COP (Ámbar)
    COP_BANNER_BG = ("#FBF4E8", "#292114")
    COP_BANNER_BORDER = ("#E3B368", "#4F3C1D")
    COP_BANNER_TEXT = ("#B45309", "#E3B368")


def get_system_font_family(style: str = "text") -> str:
    """Helper de compatibilidad hacia atrás."""
    return FONT_FAMILY
