"""
Diálogo modal de confirmación moderno para CustomTkinter.
"""

import customtkinter as ctk
from typing import Callable, Optional
from ui.theme import Theme
from ui.components.base_modal import BaseModal


class ConfirmDialog(BaseModal):
    def __init__(
        self,
        parent,
        title: str = "Confirmar eliminación",
        message: str = "¿Estás seguro de que deseas eliminar este registro? Esta acción no se puede deshacer.",
        confirm_text: str = "Eliminar",
        cancel_text: str = "Cancelar",
        on_confirm: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent, title=title, width=420, height=210)
        
        self.on_confirm_cb = on_confirm
        self.on_cancel_cb = on_cancel

        self._build_ui(title, message, confirm_text, cancel_text)

    def _build_ui(self, title: str, message: str, confirm_text: str, cancel_text: str):
        content = self.create_standard_frame()
        self.create_header(content, title, icon="🗑️")

        ctk.CTkLabel(
            content,
            text=message,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_SECONDARY,
            wraplength=350,
            justify="left"
        ).pack(anchor="w", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_LG), expand=True)

        self.create_footer_buttons(
            content,
            on_confirm=self._handle_confirm,
            on_cancel=self._handle_cancel,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            is_destructive=True
        )

    def _handle_confirm(self):
        self.grab_release()
        self.destroy()
        if self.on_confirm_cb:
            self.on_confirm_cb()

    def _handle_cancel(self):
        self.grab_release()
        self.destroy()
        if self.on_cancel_cb:
            self.on_cancel_cb()
