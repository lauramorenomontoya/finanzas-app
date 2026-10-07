"""
Componente de Tarjeta de Estadísticas / Balance para CustomTkinter.
Diseño moderno con bordes redondeados, acentos de color y tipografía clara.
"""

import customtkinter as ctk
from typing import Optional, Union, Tuple
from ui.theme import Theme


class StatCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        value: str,
        subtitle: str = "",
        icon: str = "💵",
        accent_color: Union[str, Tuple[str, str]] = ("#0284c7", "#38bdf8"),
        bg_color: Union[str, Tuple[str, str]] = Theme.BG_CARD,
        border_color: Union[str, Tuple[str, str]] = Theme.BORDER_DEFAULT,
        width: int = 220,
        height: int = 104,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=bg_color,
            border_color=border_color,
            border_width=1,
            corner_radius=Theme.SPACING_MD,
            width=width,
            height=height,
            **kwargs
        )

        self.accent_color = accent_color
        self.grid_columnconfigure(0, weight=1)

        # Barra superior de acento de color
        self.accent_bar = ctk.CTkFrame(
            self,
            height=3,
            corner_radius=Theme.SPACING_XS,
            fg_color=accent_color
        )
        self.accent_bar.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_XS, 0))

        # Fila superior: Ícono y Título
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_XS, 2))

        self.icon_label = ctk.CTkLabel(
            top_frame,
            text=icon,
            font=ctk.CTkFont(size=18),
            text_color=accent_color
        )
        self.icon_label.pack(side="left", padx=(0, Theme.SPACING_SM))

        self.title_label = ctk.CTkLabel(
            top_frame,
            text=title.upper(),
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.title_label.pack(side="left")

        # Valor principal grande (con auto-escala según longitud)
        val_str = str(value)
        font_size = 19 if len(val_str) > 17 else (22 if len(val_str) > 13 else 24)
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=font_size, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.value_label.pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, 2))

        # Subtítulo explicativo
        self.subtitle_label = ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11),
            text_color=Theme.TEXT_MUTED
        )
        self.subtitle_label.pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

    def update_value(self, new_value: str, new_subtitle: Optional[str] = None):
        """Actualiza el texto del valor y opcionalmente el subtítulo con tipografía adaptativa."""
        val_str = str(new_value)
        font_size = 19 if len(val_str) > 17 else (22 if len(val_str) > 13 else 24)
        self.value_label.configure(
            text=new_value,
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=font_size, weight="bold")
        )
        if new_subtitle is not None:
            self.subtitle_label.configure(text=new_subtitle)

    def set_value(self, new_value: str):
        """Alias para actualizar el valor."""
        self.update_value(new_value)

    def set_subtitle(self, new_subtitle: str):
        """Alias para actualizar el subtítulo."""
        self.subtitle_label.configure(text=new_subtitle)

    def update_accent(self, new_accent: Union[str, Tuple[str, str]]):
        """Actualiza el color de acento y la barra superior."""
        self.accent_color = new_accent
        self.accent_bar.configure(fg_color=new_accent)
        self.icon_label.configure(text_color=new_accent)

