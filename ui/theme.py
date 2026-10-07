"""
Definiciones de paleta de color adaptable (Modo Claro / Modo Oscuro) para Control Financiero.
Usa tuplas de CustomTkinter: (color_modo_claro, color_modo_oscuro)
"""


from ui.utils.font_helper import get_font_family


class Theme:
    # Tipografía Multiplataforma
    FONT_DISPLAY = get_font_family("display")
    FONT_TEXT = get_font_family("text")

    # Escala de Espaciado (Grid System)
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 16
    SPACING_LG = 24
    SPACING_XL = 32

    # Fondos
    BG_WINDOW = ("#f8fafc", "#0f172a")       # Fondo de ventana principal
    BG_SIDEBAR = ("#f1f5f9", "#090d16")      # Fondo de barra lateral
    BG_CARD = ("#ffffff", "#1e293b")         # Paneles y tarjetas
    BG_CARD_SUBTLE = ("#f1f5f9", "#0f172a")  # Cajas internas
    BG_INPUT = ("#ffffff", "#0f172a")        # Campos de texto y combos
    BG_PROGRESS_TRACK = ("#e2e8f0", "#334155") # Fondo de barras de progreso

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
    SUCCESS = ("#059669", "#10b981")         # Verde
    SUCCESS_HOVER = ("#047857", "#34d399")
    WARNING = ("#d97706", "#f59e0b")         # Ambar/Naranja
    WARNING_HOVER = ("#b45309", "#fbbf24")
    ERROR = ("#e11d48", "#f43f5e")           # Rojo
    ERROR_HOVER = ("#be123c", "#fb7185")
    INFO = ("#0284c7", "#38bdf8")            # Azul
    INFO_HOVER = ("#0369a1", "#7dd3fc")

    # Banners de estado
    USD_BANNER_BG = ("#e0f2fe", "#082f49")
    USD_BANNER_BORDER = ("#7dd3fc", "#0284c7")
    USD_BANNER_TEXT = ("#0284c7", "#38bdf8")

    COP_BANNER_BG = ("#d1fae5", "#064e3b")
    COP_BANNER_BORDER = ("#6ee7b7", "#10b981")
    COP_BANNER_TEXT = ("#059669", "#10b981")
