"""
Modal para Editar Categorías con Color Picker Visual y Cuadrícula de Emojis:
Permite modificar el nombre, icono y color sin ingresar códigos hexadecimales manualmente.
Diseño responsivo con pie fijo de botones y cuerpo desplazable.
"""

import customtkinter as ctk
from typing import Callable, Dict, Any, Optional
from ui.theme import Theme
from ui.utils.modal_helper import center_window


from ui.components.base_modal import BaseModal

class EditCategoryModal(BaseModal):
    COLOR_PALETTE = [
        "#10b981", "#059669", "#0284c7", "#38bdf8",
        "#6366f1", "#8b5cf6", "#a855f7", "#ec4899",
        "#f43f5e", "#e11d48", "#f97316", "#f59e0b",
        "#eab308", "#06b6d4", "#0f766e", "#64748b"
    ]

    EMOJI_PRESETS = [
        "💼", "💻", "🌐", "🚀", "💰", "💵", "💳",
        "🛒", "🏠", "💡", "🚗", "🍽️", "📱", "📚",
        "💊", "⚠️", "🤖", "☁️", "🎨", "🏷️", "📦",
        "📈", "🏦", "💜", "🏖️", "🎮", "🏋️", "✈️"
    ]

    def __init__(
        self,
        parent,
        db_manager,
        category: Dict[str, Any],
        on_success: Optional[Callable[[], None]] = None
    ):
        self.db = db_manager
        self.category = category
        self.on_success = on_success

        self.selected_color = str(category.get("color", "#38bdf8"))
        self.selected_icon = str(category.get("icon", "🏷️"))

        super().__init__(parent, title="Editar Categoría", width=500, height=580, min_width=460, min_height=480, resizable_x=True, resizable_y=True)

        self._build_ui()

    def _build_ui(self):
        main_frame = self.create_standard_frame()

        # 1. Encabezado Fijo Superior
        header = self.create_header(main_frame, "Modificar Categoría", icon="✏️")

        type_names = {
            "INCOME_USD": "Ingresos USD",
            "EXPENSE_USD": "Gastos Directos USD",
            "INCOME_COP": "Ingresos COP",
            "EXPENSE_COP": "Gastos COP"
        }
        type_str = type_names.get(self.category.get("type", ""), self.category.get("type", ""))

        ctk.CTkLabel(
            header,
            text=f"Módulo: {type_str}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # 2. Pie Fijo Inferior con Botones
        self.create_footer_buttons(
            main_frame,
            on_confirm=self._handle_save,
            on_cancel=self.destroy,
            confirm_text="💾 Guardar Cambios",
            cancel_text="Cancelar",
            is_destructive=False
        )

        footer_error_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_error_container.pack(side="bottom", fill="x", padx=Theme.SPACING_LG, pady=(0, 0))

        self.lbl_error = ctk.CTkLabel(footer_error_container, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", pady=(0, Theme.SPACING_XS))

        # 3. Cuerpo Desplazable Central
        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Campo Nombre
        ctk.CTkLabel(scroll_body, text="Nombre de la Categoría:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(Theme.SPACING_XS, Theme.SPACING_XS))
        self.name_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.name_entry.insert(0, str(self.category.get("name", "")))
        self.name_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # Selector Visual de Emojis (Cuadrícula)
        ctk.CTkLabel(scroll_body, text="Selecciona un Ícono / Emoji:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))

        emoji_grid_frame = ctk.CTkFrame(scroll_body, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        emoji_grid_frame.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))
        emoji_grid_frame.grid_columnconfigure(tuple(range(7)), weight=1)

        self.emoji_buttons: Dict[str, ctk.CTkButton] = {}
        for idx, em in enumerate(self.EMOJI_PRESETS):
            r = idx // 7
            c = idx % 7
            is_sel = (em == self.selected_icon)
            btn = ctk.CTkButton(
                emoji_grid_frame,
                text=em,
                width=34,
                height=32,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.INFO if is_sel else "transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=14),
                command=lambda e=em: self._select_emoji(e)
            )
            btn.grid(row=r, column=c, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)
            self.emoji_buttons[em] = btn

        # Selector Visual de Color (Color Palette Picker)
        ctk.CTkLabel(scroll_body, text="Selecciona el Color:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))

        color_palette_frame = ctk.CTkFrame(scroll_body, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        color_palette_frame.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))
        color_palette_frame.grid_columnconfigure(tuple(range(8)), weight=1)

        self.color_buttons: Dict[str, ctk.CTkButton] = {}
        for idx, col in enumerate(self.COLOR_PALETTE):
            r = idx // 8
            c = idx % 8
            is_sel = (col.lower() == self.selected_color.lower())
            btn = ctk.CTkButton(
                color_palette_frame,
                text="✓" if is_sel else "",
                width=30,
                height=28,
                corner_radius=Theme.SPACING_XS,
                fg_color=col,
                hover_color=col,
                border_color=Theme.TEXT_ON_COLOR,
                border_width=2 if is_sel else 0,
                text_color=Theme.TEXT_ON_COLOR,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda cl=col: self._select_color(cl)
            )
            btn.grid(row=r, column=c, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)
            self.color_buttons[col] = btn

    def _select_emoji(self, emoji: str):
        self.selected_icon = emoji
        for em, btn in self.emoji_buttons.items():
            btn.configure(fg_color=Theme.INFO if em == emoji else "transparent")

    def _select_color(self, color_hex: str):
        self.selected_color = color_hex
        for col, btn in self.color_buttons.items():
            is_sel = (col.lower() == color_hex.lower())
            btn.configure(
                text="✓" if is_sel else "",
                border_width=2 if is_sel else 0
            )

    def _handle_save(self):
        name = self.name_entry.get().strip()
        cat_id = self.category["id"]

        if not name:
            self.lbl_error.configure(text="⚠️ El nombre de la categoría no puede estar vacío.")
            return

        try:
            success = self.db.update_category(cat_id, name, self.selected_icon, self.selected_color)
            if success:
                if self.on_success:
                    self.on_success()
                self.destroy()
            else:
                self.lbl_error.configure(text="⚠️ No se pudo actualizar la categoría.")
        except Exception as e:
            self.lbl_error.configure(text=f"⚠️ Error: {str(e)}")
