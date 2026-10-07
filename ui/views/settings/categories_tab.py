import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from core.constants import SettingsTabs
from ui.components import EditCategoryModal, ConfirmDialog
from core.event_bus import EventBus

class CategoriesTab(ctk.CTkFrame):
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

    def __init__(self, master, controller, toast, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.toast = toast

        self.selected_new_color = "#38bdf8"
        self.selected_new_emoji = "🏷️"

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=45, uniform="settings_cat")
        self.grid_columnconfigure(1, weight=55, uniform="settings_cat")
        self.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Formulario Nueva Categoría
        form_panel = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, Theme.SPACING_SM))

        ctk.CTkLabel(
            form_panel,
            text="➕ Añadir Nueva Categoría",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=Theme.SPACING_MD, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        # Selector de Tipo
        ctk.CTkLabel(form_panel, text="Módulo / Tipo:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))
        self.cat_type_combo = ctk.CTkComboBox(
            form_panel,
            values=SettingsTabs.CATEGORY_TYPES,
            height=32,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda _: self.refresh_data()
        )
        self.cat_type_combo.set("Ingresos USD")
        self.cat_type_combo.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Nombre
        ctk.CTkLabel(form_panel, text="Nombre de la Categoría:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))
        self.cat_name_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: Clientes Internacionales / Software",
            height=32,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.cat_name_entry.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Selector de Emoji (Grid)
        ctk.CTkLabel(form_panel, text="Ícono / Emoji:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))
        emoji_grid = ctk.CTkFrame(form_panel, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        emoji_grid.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))
        emoji_grid.grid_columnconfigure(tuple(range(7)), weight=1)

        self.new_cat_emoji_btns = {}
        for idx, em in enumerate(self.EMOJI_PRESETS[:14]):
            r = idx // 7
            c = idx % 7
            is_sel = (em == self.selected_new_emoji)
            btn = ctk.CTkButton(
                emoji_grid,
                text=em,
                width=28,
                height=26,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.INFO if is_sel else "transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=12),
                command=lambda e=em: self._select_new_emoji(e)
            )
            btn.grid(row=r, column=c, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)
            self.new_cat_emoji_btns[em] = btn

        # Selector de Color (Paleta)
        ctk.CTkLabel(form_panel, text="Color de la Categoría:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))
        palette_grid = ctk.CTkFrame(form_panel, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        palette_grid.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))
        palette_grid.grid_columnconfigure(tuple(range(8)), weight=1)

        self.new_cat_color_btns = {}
        for idx, col in enumerate(self.COLOR_PALETTE):
            r = idx // 8
            c = idx % 8
            is_sel = (col.lower() == self.selected_new_color.lower())
            btn = ctk.CTkButton(
                palette_grid,
                text="✓" if is_sel else "",
                width=24,
                height=22,
                corner_radius=Theme.SPACING_XS,
                fg_color=col,
                hover_color=col,
                border_color=Theme.TEXT_ON_COLOR,
                border_width=2 if is_sel else 0,
                text_color=Theme.TEXT_ON_COLOR,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda cl=col: self._select_new_color(cl)
            )
            btn.grid(row=r, column=c, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)
            self.new_cat_color_btns[col] = btn

        # Botón Guardar
        self.btn_save_cat = ctk.CTkButton(
            form_panel,
            text="💾 Guardar Categoría",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            command=self._handle_save_category
        )
        self.btn_save_cat.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        # Panel Derecho: Lista de Categorías
        list_panel = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        list_panel.grid(row=0, column=1, sticky="nsew", padx=(Theme.SPACING_SM, 0))

        list_header = ctk.CTkFrame(list_panel, fg_color="transparent")
        list_header.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        ctk.CTkLabel(
            list_header,
            text="📋 Categorías Registradas",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.lbl_cat_count = ctk.CTkLabel(list_header, text="0 categorías", font=ctk.CTkFont(size=12), text_color=Theme.TEXT_MUTED)
        self.lbl_cat_count.pack(side="right")

        self.cat_scroll = ctk.CTkScrollableFrame(list_panel, fg_color="transparent")
        self.cat_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

    def _select_new_emoji(self, emoji: str):
        self.selected_new_emoji = emoji
        for em, btn in self.new_cat_emoji_btns.items():
            btn.configure(fg_color=Theme.INFO if em == emoji else "transparent")

    def _select_new_color(self, color_hex: str):
        self.selected_new_color = color_hex
        for col, btn in self.new_cat_color_btns.items():
            is_sel = (col.lower() == color_hex.lower())
            btn.configure(
                text="✓" if is_sel else "",
                border_width=2 if is_sel else 0
            )

    def _get_current_type_code(self) -> str:
        selected = self.cat_type_combo.get()
        if "Ingresos USD" in selected:
            return "INCOME_USD"
        elif "Gastos Directos USD" in selected or ("Gasto" in selected and "USD" in selected):
            return "EXPENSE_USD"
        elif "Ingresos COP" in selected:
            return "INCOME_COP"
        else:
            return "EXPENSE_COP"

    def refresh_data(self):
        for widget in self.cat_scroll.winfo_children():
            widget.destroy()

        type_code = self._get_current_type_code()
        categories = self.controller.get_categories(type_code)

        self.lbl_cat_count.configure(text=f"{len(categories)} categorías")

        if not categories:
            ctk.CTkLabel(
                self.cat_scroll,
                text="No hay categorías configuradas para este módulo.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED
            ).pack(pady=Theme.SPACING_XL)
            return

        for cat in categories:
            card = ctk.CTkFrame(self.cat_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

            left_row = ctk.CTkFrame(card, fg_color="transparent")
            left_row.pack(side="left", fill="y", padx=Theme.SPACING_SM, pady=Theme.SPACING_SM)

            icon = cat.get("icon", "🏷️")
            col = cat.get("color", "#38bdf8")
            
            dot = ctk.CTkLabel(left_row, text="●", font=ctk.CTkFont(size=14), text_color=col)
            dot.pack(side="left", padx=(0, Theme.SPACING_XS))

            ctk.CTkLabel(left_row, text=f"{icon}  {cat['name']}", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(side="left")

            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=Theme.SPACING_SM, pady=Theme.SPACING_XS)

            btn_edit_cat = ctk.CTkButton(
                btn_box,
                text="✏️",
                width=26,
                height=22,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.BG_INPUT,
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda c=cat: self._handle_edit_category(c)
            )
            btn_edit_cat.pack(side="left", padx=Theme.SPACING_XS)

            del_btn = ctk.CTkButton(
                btn_box,
                text="🗑️",
                width=26,
                height=22,
                corner_radius=Theme.SPACING_XS,
                fg_color="transparent",
                hover_color=Theme.ERROR_HOVER,
                font=ctk.CTkFont(size=11),
                command=lambda cid=cat["id"], name=cat["name"]: self._prompt_delete_category(cid, name)
            )
            del_btn.pack(side="left", padx=Theme.SPACING_XS)

    def _handle_save_category(self):
        name = self.cat_name_entry.get()
        cat_type = self._get_current_type_code()
        
        success, msg = self.controller.add_category(name, cat_type, self.selected_new_emoji, self.selected_new_color)
        self.toast.show(msg, is_error=not success)
        if success:
            self.cat_name_entry.delete(0, "end")
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")

    def _prompt_delete_category(self, cat_id: int, cat_name: str):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar Categoría",
            message=f"¿Deseas eliminar la categoría '{cat_name}'?",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete_category(cat_id)
        )

    def _execute_delete_category(self, cat_id: int):
        success, msg = self.controller.delete_category(cat_id)
        self.toast.show(msg, is_error=not success)
        if success:
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")

    def _handle_edit_category(self, category: Dict[str, Any]):
        EditCategoryModal(
            self.winfo_toplevel(),
            self.controller.db,
            category=category,
            on_success=self._on_category_saved
        )

    def _on_category_saved(self):
        self.toast.show("Categoría actualizada correctamente.", is_error=False)
        self.refresh_data()
        EventBus.publish("DATA_UPDATED")
