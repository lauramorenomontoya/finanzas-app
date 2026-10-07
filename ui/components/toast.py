"""
Componente de notificación tipo Toast / Banner de retroalimentación moderno para CustomTkinter.
Soporta variantes semánticas: éxito (✅), error (❌), advertencia (⚠️) e información (ℹ️),
con tipografía multiplataforma y bordes suaves.
"""

import customtkinter as ctk
from typing import Optional
from ui.theme import Theme


class ToastNotification(ctk.CTkFrame):
    VARIANTS = {
        "success": {
            "icon": "✅",
            "bg": ("#ecfdf5", "#064e3b"),
            "border": ("#10b981", "#059669"),
            "text": ("#065f46", "#a7f3d0"),
        },
        "error": {
            "icon": "❌",
            "bg": ("#fff1f2", "#450a0a"),
            "border": ("#f43f5e", "#e11d48"),
            "text": ("#9f1239", "#fecdd3"),
        },
        "warning": {
            "icon": "⚠️",
            "bg": ("#fffbeb", "#451a03"),
            "border": ("#f59e0b", "#d97706"),
            "text": ("#92400e", "#fde68a"),
        },
        "info": {
            "icon": "ℹ️",
            "bg": ("#f0f9ff", "#082f49"),
            "border": ("#0284c7", "#0369a1"),
            "text": ("#075985", "#bae6fd"),
        }
    }

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=Theme.SPACING_SM,
            border_width=1,
            fg_color=("#f1f5f9", "#1e293b"),
            border_color=("#cbd5e1", "#334155"),
            **kwargs
        )

        self.label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.label.pack(padx=Theme.SPACING_MD, pady=Theme.SPACING_SM)
        self._after_id = None

    def show(self, message: str, is_error: bool = False, variant: Optional[str] = None, duration_ms: int = 3500):
        """Muestra el mensaje con estilo semántico y se oculta automáticamente."""
        if variant is None:
            variant = "error" if is_error else "success"

        cfg = self.VARIANTS.get(variant, self.VARIANTS["info"])
        icon = cfg["icon"]

        # Evitar doble icono si el mensaje ya lo incluye
        display_text = message if message.startswith(icon) else f"{icon}  {message}"

        self.configure(fg_color=cfg["bg"], border_color=cfg["border"])
        self.label.configure(text=display_text, text_color=cfg["text"])

        self.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))

        if self._after_id:
            self.after_cancel(self._after_id)

        self._after_id = self.after(duration_ms, self.hide)

    def hide(self):
        """Oculta la notificación."""
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self.pack_forget()
