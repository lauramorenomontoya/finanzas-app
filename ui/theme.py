"""
ui/theme.py - Re-exportación para retrocompatibilidad con vistas existentes.
La única fuente de verdad del diseño reside en core/theme.py.
"""

from core.theme import Theme, get_system_font_family as get_font_family, FONT_FAMILY

__all__ = ["Theme", "get_font_family", "FONT_FAMILY"]
