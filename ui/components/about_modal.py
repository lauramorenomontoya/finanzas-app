"""
Modal 'Acerca de...' (About) para Montu.
Muestra información de versión, descripción del sistema y firma de autoría de Laura Moreno Montoya.
"""

import os
import customtkinter as ctk
from typing import Optional
from ui.theme import Theme
from ui.components.base_modal import BaseModal
from core.constants import APP_VERSION, APP_AUTHOR, APP_COPYRIGHT, APP_NAME_VISIBLE, get_asset_path



class AboutModal(BaseModal):
    """Ventana modal elegante con los créditos y datos de autoría de la aplicación."""

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            title=f"Acerca de {APP_NAME_VISIBLE}",
            width=460,
            height=430,
            resizable_x=False,
            resizable_y=False
        )

        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        main_card = self.create_standard_frame()

        # 1. Encabezado con Icono y Título
        header_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_LG, Theme.SPACING_SM))

        official_logo_path = get_asset_path("montu_logo_sin_eslogan_alpha.png")
        if os.path.exists(official_logo_path):
            try:
                from PIL import Image
                logo_pil = Image.open(official_logo_path)
                bbox = logo_pil.getbbox()
                if bbox:
                    logo_pil = logo_pil.crop(bbox)
                aspect = logo_pil.width / max(1, logo_pil.height)
                target_w = 190
                target_h = max(28, int(target_w / aspect))
                self.about_logo_img = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(target_w, target_h))
                icon_lbl = ctk.CTkLabel(
                    header_frame,
                    image=self.about_logo_img,
                    text=""
                )
                icon_lbl.pack(anchor="center", pady=(0, Theme.SPACING_SM))
            except Exception:
                icon_lbl = ctk.CTkLabel(header_frame, text="M", font=ctk.CTkFont(size=32, weight="bold"))
                icon_lbl.pack(anchor="center", pady=(0, Theme.SPACING_XS))
                app_name = ctk.CTkLabel(
                    header_frame,
                    text=APP_NAME_VISIBLE,
                    font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=22, weight="bold"),
                    text_color=Theme.TEXT_PRIMARY
                )
                app_name.pack(anchor="center")
        else:
            logo_path = get_asset_path("logo.png")
            if os.path.exists(logo_path):
                try:
                    from PIL import Image
                    logo_pil = Image.open(logo_path)
                    self.about_logo_img = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(44, 44))
                    icon_lbl = ctk.CTkLabel(
                        header_frame,
                        image=self.about_logo_img,
                        text=""
                    )
                except Exception:
                    icon_lbl = ctk.CTkLabel(header_frame, text="M", font=ctk.CTkFont(size=32, weight="bold"))
            else:
                icon_lbl = ctk.CTkLabel(header_frame, text="M", font=ctk.CTkFont(size=32, weight="bold"))
            icon_lbl.pack(anchor="center", pady=(0, Theme.SPACING_XS))

            app_name = ctk.CTkLabel(
                header_frame,
                text=APP_NAME_VISIBLE,
                font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=22, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            )
            app_name.pack(anchor="center")

        # Badge de versión
        version_badge = ctk.CTkFrame(
            header_frame,
            fg_color=Theme.BG_CARD_SUBTLE,
            corner_radius=Theme.SPACING_SM,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        version_badge.pack(anchor="center", pady=(Theme.SPACING_XS, 0))

        ctk.CTkLabel(
            version_badge,
            text=f"Versión {APP_VERSION}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            text_color=Theme.ACCENT_BLUE,
            padx=10,
            pady=2
        ).pack()

        # 2. Descripción breve
        desc_lbl = ctk.CTkLabel(
            main_card,
            text="Gestor integral de finanzas personales, presupuestos,\npatrimonio e inversiones multimoneda (USD & COP).",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_SECONDARY,
            justify="center"
        )
        desc_lbl.pack(padx=Theme.SPACING_LG, pady=(Theme.SPACING_SM, Theme.SPACING_MD))

        # 3. Tarjeta destacada de Autoría
        author_box = ctk.CTkFrame(
            main_card,
            fg_color=Theme.BG_CARD_SUBTLE,
            corner_radius=Theme.SPACING_MD,
            border_width=1,
            border_color=Theme.BORDER_DEFAULT
        )
        author_box.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))

        ctk.CTkLabel(
            author_box,
            text="✨ Creado & Desarrollado por",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="normal"),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="center", pady=(Theme.SPACING_SM, 2))

        ctk.CTkLabel(
            author_box,
            text=APP_AUTHOR,
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="center", pady=(0, Theme.SPACING_SM))

        # 4. Derechos de Autor
        copyright_lbl = ctk.CTkLabel(
            main_card,
            text=APP_COPYRIGHT,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=10),
            text_color=Theme.TEXT_MUTED,
            justify="center"
        )
        copyright_lbl.pack(padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))

        # 5. Botón de Cerrar
        btn_close = ctk.CTkButton(
            main_card,
            text="Cerrar",
            width=120,
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        )
        btn_close.pack(anchor="center", pady=(0, Theme.SPACING_MD))
