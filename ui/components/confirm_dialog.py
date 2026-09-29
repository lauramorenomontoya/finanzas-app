"""
Diálogo modal de confirmación moderno para CustomTkinter.
"""

import customtkinter as ctk
from typing import Callable, Optional
from ui.theme import Theme
from ui.utils.modal_helper import center_window


class ConfirmDialog(ctk.CTkToplevel):
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
        super().__init__(parent)
        self.on_confirm_cb = on_confirm
        self.on_cancel_cb = on_cancel

        self.title(title)
        self.geometry("420x210")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_WINDOW)

        # Configurar como modal
        self.transient(parent)
        self.grab_set()

        # Centrar sobre la ventana padre
        self._center_window(parent)

        self._build_ui(title, message, confirm_text, cancel_text)

    def _center_window(self, parent):
        center_window(self, parent, 420, 210)

    def _build_ui(self, title: str, message: str, confirm_text: str, cancel_text: str):
        content = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_DEFAULT)
        content.pack(fill="both", expand=True, padx=16, pady=16)

        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            header_frame,
            text=f"🗑️ {title}",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            content,
            text=message,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_SECONDARY,
            wraplength=350,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 16))

        # Botones de acción
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16), side="bottom")

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            fg_color=Theme.BORDER_DEFAULT,
            hover_color=Theme.TEXT_MUTED,
            text_color=Theme.TEXT_PRIMARY,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._handle_cancel
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_confirm = ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            fg_color="#e11d48",
            hover_color="#be123c",
            text_color="#ffffff",
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._handle_confirm
        )
        btn_confirm.pack(side="right")

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
