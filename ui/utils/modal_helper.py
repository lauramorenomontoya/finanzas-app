"""
Utilidades para ventanas modales y diálogos en CustomTkinter.
"""

from typing import Optional


def center_window(window, parent=None, width: Optional[int] = None, height: Optional[int] = None):
    """
    Centra una ventana emergente o modal con respecto a su ventana padre,
    o con respecto a la pantalla si el padre no está disponible.
    """
    window.update_idletasks()
    try:
        w = width or window.winfo_width()
        h = height or window.winfo_height()

        # Si aún no ha renderizado dimensiones reales
        if w <= 1:
            w = 480
        if h <= 1:
            h = 400

        if parent and parent.winfo_exists():
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            x = parent_x + (parent_w - w) // 2
            y = parent_y + (parent_h - h) // 2
        else:
            screen_w = window.winfo_screenwidth()
            screen_h = window.winfo_screenheight()
            x = (screen_w - w) // 2
            y = (screen_h - h) // 2

        window.geometry(f"+{max(0, x)}+{max(0, y)}")
    except Exception:
        pass
