"""
Componente reutilizable de Estado Vacío (Empty State) para Montu.
Diseñado con estética moderna y jerarquía visual: Icono grande, Título en FONT_DISPLAY,
descripción explicativa en FONT_TEXT y botón de llamada a la acción (CTA) opcional.
"""

import customtkinter as ctk
from typing import Optional, Callable
from ui.theme import Theme


class EmptyState(ctk.CTkFrame):
    def __init__(
        self,
        master,
        icon: str = "📭",
        title: str = "No hay datos para mostrar",
        message: str = "Aún no se han registrado elementos en esta sección.",
        action_text: Optional[str] = None,
        action_command: Optional[Callable] = None,
        action_variant: str = "primary",  # "primary", "destructive", "neutral"
        compact: bool = False,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.action_command = action_command
        pad_y = (10, 10) if compact else (24, 24)
        icon_size = 28 if compact else 40
        title_size = 13 if compact else 15
        msg_size = 11 if compact else 12

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill="both", pady=pad_y)

        # 1. Badge/Icono grande
        icon_box = ctk.CTkFrame(
            container,
            width=50 if compact else 64,
            height=50 if compact else 64,
            corner_radius=Theme.SPACING_LG if compact else 32,
            fg_color=Theme.BG_CARD_SUBTLE,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        icon_box.pack(pady=(0, 8 if compact else 12))
        icon_box.pack_propagate(False)

        lbl_icon = ctk.CTkLabel(
            icon_box,
            text=icon,
            font=ctk.CTkFont(size=icon_size)
        )
        lbl_icon.place(relx=0.5, rely=0.5, anchor="center")

        # 2. Título de Estado Vacío
        lbl_title = ctk.CTkLabel(
            container,
            text=title,
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=title_size, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        lbl_title.pack(pady=(0, Theme.SPACING_XS))

        # 3. Mensaje / Descripción
        if message:
            lbl_msg = ctk.CTkLabel(
                container,
                text=message,
                font=ctk.CTkFont(family=Theme.FONT_TEXT, size=msg_size),
                text_color=Theme.TEXT_MUTED,
                justify="center"
            )
            lbl_msg.pack(pady=(0, 12 if action_text else 4))

        # 4. Botón de Acción Opcional (CTA)
        if action_text and action_command:
            if action_variant == "primary":
                fg_btn = Theme.ACCENT_BLUE
                hover_btn = "#0369a1"
                txt_color = "#ffffff"
            elif action_variant == "destructive":
                fg_btn = "#e11d48"
                hover_btn = "#be123c"
                txt_color = "#ffffff"
            else:
                fg_btn = Theme.BG_CARD
                hover_btn = Theme.BORDER_DEFAULT
                txt_color = Theme.TEXT_PRIMARY

            btn_cta = ctk.CTkButton(
                container,
                text=action_text,
                height=30 if compact else 34,
                corner_radius=Theme.SPACING_SM,
                fg_color=fg_btn,
                hover_color=hover_btn,
                text_color=txt_color,
                font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12, weight="bold"),
                command=action_command
            )
            btn_cta.pack(pady=(Theme.SPACING_XS, 0))
