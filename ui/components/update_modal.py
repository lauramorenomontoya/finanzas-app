"""
Modal de Notificación de Actualización para Montu.
Presenta las novedades de la versión disponible y permite la descarga directa
del instalador sin comprometer la base de datos local.
"""

import webbrowser
import customtkinter as ctk
from typing import Dict, Any
from ui.theme import Theme
from ui.components.base_modal import BaseModal


class UpdateModal(BaseModal):
    """Ventana emergente que notifica al usuario sobre una nueva versión disponible."""

    def __init__(self, parent, update_info: Dict[str, Any]):
        super().__init__(
            parent=parent,
            title="Actualización Disponible",
            width=500,
            height=450,
            resizable_x=False,
            resizable_y=False
        )

        self.update_info = update_info
        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        main_card = self.create_standard_frame()

        latest_ver = self.update_info.get("latest_version", "")
        current_ver = self.update_info.get("current_version", "")
        release_name = self.update_info.get("release_name", "")
        release_notes = self.update_info.get("release_notes", "")
        download_url = self.update_info.get("download_url", "")

        # 1. Cabecera con Icono
        header_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_MD, Theme.SPACING_XS))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="🚀  ¡Nueva versión disponible!",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title_lbl.pack(anchor="w")

        # Fila de versión actual vs nueva
        ver_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        ver_row.pack(anchor="w", pady=(Theme.SPACING_XS, 0))

        badge_new = ctk.CTkFrame(
            ver_row,
            fg_color=Theme.BG_CARD_SUBTLE,
            corner_radius=Theme.SPACING_SM,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        badge_new.pack(side="left")

        ctk.CTkLabel(
            badge_new,
            text=f"Nueva: v{latest_ver}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            text_color=Theme.ACCENT_GREEN,
            padx=8,
            pady=2
        ).pack()

        ctk.CTkLabel(
            ver_row,
            text=f"(Instalada actualmente: v{current_ver})",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11),
            text_color=Theme.TEXT_MUTED
        ).pack(side="left", padx=(Theme.SPACING_SM, 0))

        # 2. Caja de Novedades (Scrollable si hay muchas notas)
        notes_box = ctk.CTkScrollableFrame(
            main_card,
            fg_color=Theme.BG_CARD_SUBTLE,
            corner_radius=Theme.SPACING_MD,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            height=160
        )
        notes_box.pack(fill="both", expand=True, padx=Theme.SPACING_LG, pady=(Theme.SPACING_SM, Theme.SPACING_SM))

        if release_name and release_name != f"Versión {latest_ver}":
            ctk.CTkLabel(
                notes_box,
                text=release_name,
                font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=13, weight="bold"),
                text_color=Theme.TEXT_PRIMARY,
                anchor="w"
            ).pack(fill="x", pady=(0, Theme.SPACING_XS))

        notes_text = release_notes if release_notes else "Esta versión incluye mejoras generales de rendimiento, corrección de errores y nuevas funcionalidades."
        ctk.CTkLabel(
            notes_box,
            text=notes_text,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_SECONDARY,
            justify="left",
            wraplength=410,
            anchor="w"
        ).pack(fill="x")

        # 3. Aviso de Seguridad de Datos
        safety_banner = ctk.CTkFrame(
            main_card,
            fg_color=Theme.BG_CARD_SUBTLE,
            corner_radius=Theme.SPACING_SM,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        safety_banner.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))

        ctk.CTkLabel(
            safety_banner,
            text="🛡️ Tus finanzas y datos se conservarán automáticamente al actualizar.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11),
            text_color=Theme.TEXT_MUTED,
            padx=10,
            pady=6
        ).pack(anchor="w")

        # 4. Botones de Acción
        btn_row = ctk.CTkFrame(main_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))

        btn_later = ctk.CTkButton(
            btn_row,
            text="Más tarde",
            width=110,
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BORDER_DEFAULT,
            hover_color=Theme.TEXT_MUTED,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        )
        btn_later.pack(side="left")

        btn_download = ctk.CTkButton(
            btn_row,
            text="📥 Descargar Actualización",
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._download_and_close(download_url)
        )
        btn_download.pack(side="right", fill="x", expand=True, padx=(Theme.SPACING_SM, 0))

    def _download_and_close(self, url: str):
        if url:
            webbrowser.open(url)
        self.destroy()
