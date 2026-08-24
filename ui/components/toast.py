"""
Componente de notificación tipo Toast / Banner de retroalimentación para CustomTkinter.
"""

import customtkinter as ctk


class ToastNotification(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
            fg_color="#1e293b",
            border_color="#334155",
            **kwargs
        )

        self.label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="SF Pro Text", size=13, weight="bold"),
            text_color="#f8fafc"
        )
        self.label.pack(padx=16, pady=10)
        self._after_id = None

    def show(self, message: str, is_error: bool = False, duration_ms: int = 3500):
        """Muestra el mensaje con estilo de éxito o error y se oculta automáticamente."""
        if is_error:
            self.configure(fg_color="#450a0a", border_color="#f43f5e")
            self.label.configure(text=f"⚠️ {message}", text_color="#fecdd3")
        else:
            self.configure(fg_color="#064e3b", border_color="#10b981")
            self.label.configure(text=f"✅ {message}", text_color="#a7f3d0")

        self.pack(fill="x", padx=20, pady=(0, 10))

        if self._after_id:
            self.after_cancel(self._after_id)

        self._after_id = self.after(duration_ms, self.hide)

    def hide(self):
        """Oculta la notificación."""
        self.pack_forget()
