"""
ui/utils/icon_helper.py - Helper central para íconos lineales limpios en CustomTkinter.
Carga y tinta íconos PNG desde assets/icons con soporte para modo claro y modo oscuro.
"""

import os
from typing import Tuple, Dict, Optional
from PIL import Image
import customtkinter as ctk


class IconHelper:
    _cache: Dict[str, ctk.CTkImage] = {}
    _base_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons"))

    @classmethod
    def _hex_to_rgb(cls, hex_color: str) -> Tuple[int, int, int]:
        clean = hex_color.lstrip("#")
        if len(clean) == 6:
            return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))
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
        size: Tuple[int, int] = (14, 14),
        light_color: str = "#475569",
        dark_color: str = "#8D9B92"
    ) -> Optional[ctk.CTkImage]:
        """
        Retorna un CTkImage tintado según la paleta.
        Usa caché interna para optimizar rendimiento.
        """
        cache_key = f"{name}_{size}_{light_color}_{dark_color}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        icon_path = os.path.join(cls._base_dir, f"{name}.png")
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
