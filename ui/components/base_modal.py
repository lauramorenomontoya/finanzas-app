import customtkinter as ctk
from typing import Callable, Optional
from ui.theme import Theme
from ui.utils.modal_helper import center_window

class BaseModal(ctk.CTkToplevel):
    """
    Clase base para todos los diálogos y ventanas secundarias de la aplicación.
    Proporciona la estructura estándar (Cabecera, Cuerpo, Footer de botones).
    """
    def __init__(
        self,
        parent,
        title: str,
        width: int = 400,
        height: int = 300,
        resizable_x: bool = False,
        resizable_y: bool = False,
        min_width: int = 0,
        min_height: int = 0
    ):
        super().__init__(parent)
        
        self.title(title)
        self.geometry(f"{width}x{height}")
        if min_width > 0 and min_height > 0:
            self.minsize(min_width, min_height)
            
        self.resizable(resizable_x, resizable_y)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        center_window(self, parent, width, height)

    def create_standard_frame(self, border_color: Optional[str] = None) -> ctk.CTkFrame:
        """Crea y retorna el marco principal unificado para contenido."""
        b_color = border_color if border_color else Theme.BORDER_DEFAULT
        main_frame = ctk.CTkFrame(
            self, 
            fg_color=Theme.BG_CARD, 
            corner_radius=Theme.SPACING_MD, 
            border_width=1, 
            border_color=b_color
        )
        main_frame.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=Theme.SPACING_MD)
        return main_frame

    def create_header(self, parent: ctk.CTkFrame, title: str, icon: str = "") -> ctk.CTkFrame:
        """Crea el encabezado estándar del modal."""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_MD, Theme.SPACING_SM))
        
        display_title = f"{icon} {title}" if icon else title
        ctk.CTkLabel(
            header,
            text=display_title,
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")
        return header

    def create_footer_buttons(self, parent: ctk.CTkFrame, on_confirm: Callable, on_cancel: Callable, confirm_text: str = "Guardar", cancel_text: str = "Cancelar", is_destructive: bool = False):
        """Crea el layout estándar de botones en la parte inferior."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_LG))

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            fg_color=Theme.BORDER_DEFAULT,
            hover_color=Theme.TEXT_MUTED,
            text_color=Theme.TEXT_PRIMARY,
            height=36,
            corner_radius=Theme.SPACING_SM,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=on_cancel
        )
        btn_cancel.pack(side="right", padx=(Theme.SPACING_SM, 0))

        confirm_color = Theme.ERROR if is_destructive else Theme.INFO
        confirm_hover = Theme.ERROR_HOVER if is_destructive else Theme.INFO_HOVER

        btn_confirm = ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            fg_color=confirm_color,
            hover_color=confirm_hover,
            text_color=Theme.TEXT_ON_COLOR,
            height=36,
            corner_radius=Theme.SPACING_SM,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=on_confirm
        )
        btn_confirm.pack(side="right")
        return btn_frame
