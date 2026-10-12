"""
ui/utils/icon_helper.py - Helper central para íconos lineales limpios en CustomTkinter.
Carga y tinta íconos PNG desde assets/icons con soporte para modo claro y modo oscuro.
"""

import os
from typing import Tuple, Dict, Optional, Union
from PIL import Image
import customtkinter as ctk


import sys

class IconHelper:
    _cache: Dict[str, ctk.CTkImage] = {}

    @classmethod
    def _get_base_dir(cls) -> str:
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return os.path.join(meipass, "assets", "icons")
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons"))

    @classmethod
    def clear_cache(cls):
        """Limpia la caché de imágenes (esencial al recrear ventanas Tkinter en tests)."""
        cls._cache.clear()


    @classmethod
    def _hex_to_rgb(cls, hex_color: str) -> Tuple[int, int, int]:

        if not hex_color or not isinstance(hex_color, str):
            return (255, 255, 255)
        clean = hex_color.lstrip("#")
        if len(clean) == 6:
            try:
                return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))
            except ValueError:
                return (255, 255, 255)
        return (255, 255, 255)

    @classmethod
    def _tint_image(cls, src_path: str, color_hex: str) -> Image.Image:
        img = Image.open(src_path).convert("RGBA")
        r, g, b = cls._hex_to_rgb(color_hex)
        alpha = img.split()[3]
        tinted = Image.new("RGBA", img.size, (r, g, b, 255))
        tinted.putalpha(alpha)
        return tinted

    @classmethod
    def get_icon(
        cls,
        name: str,
        size: Union[int, Tuple[int, int]] = (14, 14),
        color: Optional[Union[str, Tuple[str, str]]] = None,
        light_color: Optional[str] = None,
        dark_color: Optional[str] = None
    ) -> Optional[ctk.CTkImage]:
        """
        Retorna un CTkImage tintado según la paleta.
        Acepta size como int o tupla (w, h).
        Acepta color como string hex o tupla (light, dark) de CustomTkinter.
        """
        if isinstance(size, int):
            size = (size, size)

        if color is not None:
            if isinstance(color, (tuple, list)) and len(color) >= 2:
                light_color = str(color[0])
                dark_color = str(color[1])
            elif isinstance(color, str):
                light_color = color
                dark_color = color

        if not light_color:
            light_color = "#475569"
        if not dark_color:
            dark_color = "#8D9B92"

        cache_key = f"{name}_{size}_{light_color}_{dark_color}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        icon_path = os.path.join(cls._get_base_dir(), f"{name}.png")
        if not os.path.exists(icon_path):
            return None


        try:
            light_img = cls._tint_image(icon_path, light_color)
            dark_img = cls._tint_image(icon_path, dark_color)
            ctk_img = ctk.CTkImage(light_image=light_img, dark_image=dark_img, size=size)
            cls._cache[cache_key] = ctk_img
            return ctk_img
        except Exception:
            return None

