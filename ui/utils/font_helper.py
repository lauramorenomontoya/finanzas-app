"""
Utilidad de Tipografía y Fuentes Multiplataforma para Montu.
Re-exporta la lógica central consolidada en core/theme.py.
"""

from core.theme import get_system_font_family as get_font_family, FONT_FAMILY

__all__ = ["get_font_family", "FONT_FAMILY"]
