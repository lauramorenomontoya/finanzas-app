"""
Vista de Configuración y Panel CRUD:
Gestión Dinámica de Categorías (con Color Picker y Cuadrícula de Emojis), Cuentas/Fiducias de Inversión y Plantilla de Gastos Fijos Multimoneda (COP y USD).
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any, List
from ui.theme import Theme
from ui.components import (
    ToastNotification,
    ConfirmDialog,
    EditAccountModal,
    EditCategoryModal,
    EditRecurringModal,
    CSVImporterModal
)


class SettingsView(ctk.CTkFrame):
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

    def __init__(self, master, db_manager, on_data_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.on_data_changed = on_data_changed

        self.selected_new_color = "#38bdf8"
        self.selected_new_emoji = "🏷️"

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        self.toast = ToastNotification(self)

        # 1. Cabecera
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 14))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_box,
            text="⚙️ Configuración & Personalización",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Administra categorías (con paleta de color y emojis), cuentas de inversión y gastos fijos multimoneda.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        btn_import = ctk.CTkButton(
            header_frame,
            text="📥 Importar CSV / Notion",
            height=36,
            corner_radius=8,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_importer
        )
        btn_import.pack(side="right")

        # 2. Selector de Sección (Categorías vs Cuentas vs Gastos Fijos)
        self.section_seg = ctk.CTkSegmentedButton(
            self,
            values=["🏷️  Categorías", "🏦  Cuentas & Fiducias", "📋  Gastos Fijos Multimoneda"],
            height=36,
            command=self._on_section_changed
        )
        self.section_seg.set("🏷️  Categorías")
        self.section_seg.pack(fill="x", padx=24, pady=(0, 14))

        # 3. Contenedor de contenido
        self.content_box = ctk.CTkFrame(self, fg_color="transparent")
        self.content_box.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Construir subsecciones
        self._build_categories_section()
        self._build_accounts_section()
        self._build_recurring_section()

        self._show_active_section()

    def _open_importer(self):
        CSVImporterModal(self, self.db, on_success=self._on_import_completed)

    def _on_import_completed(self):
        self.toast.show("¡Datos de CSV / Notion importados exitosamente!", "success")
        self.refresh_data()
        if self.on_data_changed:
            self.on_data_changed()

    # ==========================================
    # SUBSECCIÓN: CATEGORÍAS (CRUD CON COLOR PICKER & EMOJIS)
    # ==========================================

    def _build_categories_section(self):
        self.cat_frame = ctk.CTkFrame(self.content_box, fg_color="transparent")
        self.cat_frame.grid_columnconfigure(0, weight=45, uniform="settings_cat")
        self.cat_frame.grid_columnconfigure(1, weight=55, uniform="settings_cat")
        self.cat_frame.grid_rowconfigure(0, weight=1)


        # Panel Izquierdo: Formulario Nueva Categoría
        form_panel = ctk.CTkFrame(self.cat_frame, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            form_panel,
            text="➕ Añadir Nueva Categoría",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=18, pady=(16, 10))

        # Selector de Tipo
        ctk.CTkLabel(form_panel, text="Módulo / Tipo:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        self.cat_type_combo = ctk.CTkComboBox(
            form_panel,
            values=["Ingresos USD", "Gastos Directos USD", "Ingresos COP", "Gastos COP"],
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda _: self._refresh_categories_list()
        )
        self.cat_type_combo.set("Ingresos USD")
        self.cat_type_combo.pack(fill="x", padx=18, pady=(0, 8))

        # Nombre
        ctk.CTkLabel(form_panel, text="Nombre de la Categoría:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        self.cat_name_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: Clientes Internacionales / Software",
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.cat_name_entry.pack(fill="x", padx=18, pady=(0, 8))

        # Selector de Emoji (Grid)
        ctk.CTkLabel(form_panel, text="Ícono / Emoji:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        emoji_grid = ctk.CTkFrame(form_panel, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
        emoji_grid.pack(fill="x", padx=18, pady=(0, 8))
        emoji_grid.grid_columnconfigure(tuple(range(7)), weight=1)

        self.new_cat_emoji_btns = {}
        for idx, em in enumerate(self.EMOJI_PRESETS[:14]):  # Mostrar 14 presets principales
            r = idx // 7
            c = idx % 7
            is_sel = (em == self.selected_new_emoji)
            btn = ctk.CTkButton(
                emoji_grid,
                text=em,
                width=28,
                height=26,
                corner_radius=5,
                fg_color="#0284c7" if is_sel else "transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=12),
                command=lambda e=em: self._select_new_emoji(e)
            )
            btn.grid(row=r, column=c, padx=2, pady=2)
            self.new_cat_emoji_btns[em] = btn

        # Selector de Color (Paleta)
        ctk.CTkLabel(form_panel, text="Color de la Categoría:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        palette_grid = ctk.CTkFrame(form_panel, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
        palette_grid.pack(fill="x", padx=18, pady=(0, 12))
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
                corner_radius=5,
                fg_color=col,
                hover_color=col,
                border_color="#ffffff",
                border_width=2 if is_sel else 0,
                text_color="#ffffff",
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda cl=col: self._select_new_color(cl)
            )
            btn.grid(row=r, column=c, padx=2, pady=2)
            self.new_cat_color_btns[col] = btn

        # Botón Guardar
        self.btn_save_cat = ctk.CTkButton(
            form_panel,
            text="💾 Guardar Categoría",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=8,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            command=self._handle_save_category
        )
        self.btn_save_cat.pack(fill="x", padx=18, pady=(0, 16))

        # Panel Derecho: Lista de Categorías con botones Editar ✏️ y Eliminar 🗑️
        list_panel = ctk.CTkFrame(self.cat_frame, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        list_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        list_header = ctk.CTkFrame(list_panel, fg_color="transparent")
        list_header.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            list_header,
            text="📋 Categorías Registradas",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.lbl_cat_count = ctk.CTkLabel(list_header, text="0 categorías", font=ctk.CTkFont(size=12), text_color=Theme.TEXT_MUTED)
        self.lbl_cat_count.pack(side="right")

        self.cat_scroll = ctk.CTkScrollableFrame(list_panel, fg_color="transparent")
        self.cat_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 16))

    def _select_new_emoji(self, emoji: str):
        self.selected_new_emoji = emoji
        for em, btn in self.new_cat_emoji_btns.items():
            btn.configure(fg_color="#0284c7" if em == emoji else "transparent")

    def _select_new_color(self, color_hex: str):
        self.selected_new_color = color_hex
        for col, btn in self.new_cat_color_btns.items():
            is_sel = (col.lower() == color_hex.lower())
            btn.configure(
                text="✓" if is_sel else "",
                border_width=2 if is_sel else 0
            )

    # ==========================================
    # SUBSECCIÓN: CUENTAS Y FIDUCIAS (CRUD)
    # ==========================================

    def _build_accounts_section(self):
        self.acc_frame = ctk.CTkFrame(self.content_box, fg_color="transparent")
        self.acc_frame.grid_columnconfigure(0, weight=1)
        self.acc_frame.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(self.acc_frame, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        panel.grid(row=0, column=0, sticky="nsew")

        p_header = ctk.CTkFrame(panel, fg_color="transparent")
        p_header.pack(fill="x", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            p_header,
            text="🏦 Administración de Cuentas, Bolsillos y Fiducias",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        btn_new_acc = ctk.CTkButton(
            p_header,
            text="➕ Añadir Cuenta",
            height=32,
            corner_radius=8,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._handle_create_account
        )
        btn_new_acc.pack(side="right")

        self.accounts_crud_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.accounts_crud_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    # ==========================================
    # SUBSECCIÓN: GASTOS FIJOS MULTIMONEDA
    # ==========================================

    def _build_recurring_section(self):
        self.rec_frame = ctk.CTkFrame(self.content_box, fg_color="transparent")
        self.rec_frame.grid_columnconfigure(0, weight=45, uniform="settings_rec")
        self.rec_frame.grid_columnconfigure(1, weight=55, uniform="settings_rec")
        self.rec_frame.grid_rowconfigure(0, weight=1)


        # Panel Izquierdo: Formulario
        form_panel = ctk.CTkFrame(self.rec_frame, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            form_panel,
            text="➕ Añadir Gasto Fijo Recurrente",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=18, pady=(16, 10))

        # Selector de Moneda para el Gasto Fijo
        ctk.CTkLabel(form_panel, text="Moneda del Gasto Fijo:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        self.rec_curr_seg = ctk.CTkSegmentedButton(
            form_panel,
            values=["🇨🇴 Pesos (COP)", "💵 Dólares (USD)"],
            height=30,
            command=self._on_rec_currency_changed
        )
        self.rec_curr_seg.set("🇨🇴 Pesos (COP)")
        self.rec_curr_seg.pack(fill="x", padx=18, pady=(0, 8))

        ctk.CTkLabel(form_panel, text="Categoría:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        self.rec_cat_combo = ctk.CTkComboBox(
            form_panel,
            values=["Arriendo / Hipoteca", "Servicios Públicos (Luz, Agua, Gas)", "Alimentación / Mercado", "Otros Gastos COP"],
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.rec_cat_combo.pack(fill="x", padx=18, pady=(0, 8))

        ctk.CTkLabel(form_panel, text="Descripción / Concepto:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        self.rec_desc_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: Pago arriendo mensual / ChatGPT Plus",
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.rec_desc_entry.pack(fill="x", padx=18, pady=(0, 8))

        self.lbl_rec_amt = ctk.CTkLabel(form_panel, text="Monto Estimado ($ COP):", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY)
        self.lbl_rec_amt.pack(anchor="w", padx=18, pady=(0, 2))

        self.rec_amount_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: 1500000",
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.rec_amount_entry.pack(fill="x", padx=18, pady=(0, 8))

        ctk.CTkLabel(form_panel, text="Día habitual de pago (1 al 31):", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        self.rec_day_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: 1",
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.rec_day_entry.insert(0, "1")
        self.rec_day_entry.pack(fill="x", padx=18, pady=(0, 14))

        self.btn_save_rec = ctk.CTkButton(
            form_panel,
            text="💾 Guardar en Plantilla",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=8,
            fg_color="#e11d48",
            hover_color="#be123c",
            text_color="#ffffff",
            command=self._handle_save_recurring
        )
        self.btn_save_rec.pack(fill="x", padx=18, pady=(0, 16))

        # Panel Derecho: Lista
        list_panel = ctk.CTkFrame(self.rec_frame, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        list_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        list_header = ctk.CTkFrame(list_panel, fg_color="transparent")
        list_header.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            list_header,
            text="📋 Plantilla de Gastos Fijos Multimoneda",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.lbl_rec_total = ctk.CTkLabel(list_header, text="COP: $0 • USD: $0", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.ACCENT_ROSE)
        self.lbl_rec_total.pack(side="right")

        self.rec_scroll = ctk.CTkScrollableFrame(list_panel, fg_color="transparent")
        self.rec_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 16))

    def _on_rec_currency_changed(self, choice: str):
        if "USD" in choice:
            self.lbl_rec_amt.configure(text="Monto Estimado ($ USD):")
            self.rec_amount_entry.configure(placeholder_text="Ej: 20.00")
            cats = [c["name"] for c in self.db.get_categories("EXPENSE_USD")]
            if cats:
                self.rec_cat_combo.configure(values=cats)
                self.rec_cat_combo.set(cats[0])
        else:
            self.lbl_rec_amt.configure(text="Monto Estimado ($ COP):")
            self.rec_amount_entry.configure(placeholder_text="Ej: 1500000")
            cats = [c["name"] for c in self.db.get_categories("EXPENSE_COP")]
            if cats:
                self.rec_cat_combo.configure(values=cats)
                self.rec_cat_combo.set(cats[0])

    # ==========================================
    # GESTIÓN DE VISTAS Y REFRESH
    # ==========================================

    def _on_section_changed(self, choice: str):
        self._show_active_section()

    def _show_active_section(self):
        choice = self.section_seg.get()
        self.cat_frame.pack_forget()
        self.acc_frame.pack_forget()
        self.rec_frame.pack_forget()

        if "Categorías" in choice:
            self.cat_frame.pack(fill="both", expand=True)
            self._refresh_categories_list()
        elif "Cuentas" in choice:
            self.acc_frame.pack(fill="both", expand=True)
            self._refresh_accounts_crud_list()
        else:
            self.rec_frame.pack(fill="both", expand=True)
            self._refresh_recurring_list()

    def refresh_data(self):
        self._refresh_categories_list()
        self._refresh_accounts_crud_list()
        self._refresh_recurring_list()

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

    def _refresh_categories_list(self):
        for widget in self.cat_scroll.winfo_children():
            widget.destroy()

        type_code = self._get_current_type_code()
        categories = self.db.get_categories(type_code)

        self.lbl_cat_count.configure(text=f"{len(categories)} categorías")

        if not categories:
            ctk.CTkLabel(
                self.cat_scroll,
                text="No hay categorías configuradas para este módulo.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED
            ).pack(pady=30)
            return

        for cat in categories:
            card = ctk.CTkFrame(self.cat_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=3, padx=2)

            left_row = ctk.CTkFrame(card, fg_color="transparent")
            left_row.pack(side="left", fill="y", padx=12, pady=8)

            icon = cat.get("icon", "🏷️")
            col = cat.get("color", "#38bdf8")
            
            # Badge con color
            dot = ctk.CTkLabel(left_row, text="●", font=ctk.CTkFont(size=14), text_color=col)
            dot.pack(side="left", padx=(0, 6))

            ctk.CTkLabel(left_row, text=f"{icon}  {cat['name']}", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(side="left")

            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=10, pady=6)

            btn_edit_cat = ctk.CTkButton(
                btn_box,
                text="✏️",
                width=26,
                height=22,
                corner_radius=4,
                fg_color=Theme.BG_INPUT,
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda c=cat: self._handle_edit_category(c)
            )
            btn_edit_cat.pack(side="left", padx=2)

            del_btn = ctk.CTkButton(
                btn_box,
                text="🗑️",
                width=26,
                height=22,
                corner_radius=4,
                fg_color="transparent",
                hover_color="#450a0a",
                font=ctk.CTkFont(size=11),
                command=lambda cid=cat["id"], name=cat["name"]: self._prompt_delete_category(cid, name)
            )
            del_btn.pack(side="left", padx=2)

    def _refresh_accounts_crud_list(self):
        for widget in self.accounts_crud_scroll.winfo_children():
            widget.destroy()

        accounts = self.db.get_accounts(only_active=False)

        if not accounts:
            ctk.CTkLabel(
                self.accounts_crud_scroll,
                text="No hay cuentas registradas.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED
            ).pack(pady=30)
            return

        for acc in accounts:
            card = ctk.CTkFrame(self.accounts_crud_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=4, padx=2)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=10)

            left_box = ctk.CTkFrame(inner, fg_color="transparent")
            left_box.pack(side="left", fill="both", expand=True)

            icon = acc.get("icon", "📈")
            active_badge = "" if acc.get("is_active", 1) == 1 else " (Inactiva)"
            ctk.CTkLabel(
                left_box,
                text=f"{icon}  {acc['name']}{active_badge}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.TEXT_PRIMARY if acc.get("is_active", 1) == 1 else Theme.TEXT_MUTED
            ).pack(anchor="w")

            curr = acc["currency"]
            bal_str = f"${acc['current_balance']:,.2f} USD" if curr == "USD" else f"${acc['current_balance']:,.0f} COP"
            ctk.CTkLabel(
                left_box,
                text=f"Institución: {acc.get('institution', 'N/A')} • Moneda: {curr} • Saldo: {bal_str}",
                font=ctk.CTkFont(size=11),
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w", pady=(2, 0))

            btns = ctk.CTkFrame(inner, fg_color="transparent")
            btns.pack(side="right")

            btn_edit = ctk.CTkButton(
                btns,
                text="✏️ Editar",
                width=65,
                height=28,
                corner_radius=6,
                fg_color=Theme.BG_INPUT,
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda a=acc: self._handle_edit_account(a)
            )
            btn_edit.pack(side="left", padx=4)

            btn_del = ctk.CTkButton(
                btns,
                text="🗑️",
                width=28,
                height=28,
                corner_radius=6,
                fg_color="transparent",
                hover_color="#450a0a",
                font=ctk.CTkFont(size=11),
                command=lambda aid=acc["id"], aname=acc["name"]: self._prompt_delete_account(aid, aname)
            )
            btn_del.pack(side="left")

    def _refresh_recurring_list(self):
        for widget in self.rec_scroll.winfo_children():
            widget.destroy()

        items = self.db.get_recurring_expenses()
        tot_cop = sum(i["amount"] for i in items if i["is_active"] and i.get("currency", "COP") == "COP")
        tot_usd = sum(i["amount"] for i in items if i["is_active"] and i.get("currency", "COP") == "USD")
        self.lbl_rec_total.configure(text=f"Plantilla: ${tot_cop:,.0f} COP • ${tot_usd:,.2f} USD")

        if not items:
            ctk.CTkLabel(
                self.rec_scroll,
                text="No tienes gastos fijos en la plantilla aún.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED,
                justify="center"
            ).pack(pady=40)
            return

        for rec in items:
            curr = rec.get("currency", "COP")
            is_usd = (curr == "USD")
            amt_str = f"${rec['amount']:,.2f} USD" if is_usd else f"${rec['amount']:,.0f} COP"

            card = ctk.CTkFrame(self.rec_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=4, padx=2)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(8, 2))

            ctk.CTkLabel(
                top_row,
                text=f"📌 [{curr}] {rec['category']} • {rec['description']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(side="left")

            ctk.CTkLabel(
                top_row,
                text=amt_str,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.ACCENT_ROSE
            ).pack(side="right")

            bottom_row = ctk.CTkFrame(card, fg_color="transparent")
            bottom_row.pack(fill="x", padx=12, pady=(0, 8))

            ctk.CTkLabel(
                bottom_row,
                text=f"Día sugerido: {rec['due_day']} de cada mes",
                font=ctk.CTkFont(size=10),
                text_color=Theme.TEXT_MUTED
            ).pack(side="left")

            btn_box = ctk.CTkFrame(bottom_row, fg_color="transparent")
            btn_box.pack(side="right")

            btn_edit_rec = ctk.CTkButton(
                btn_box,
                text="✏️",
                width=24,
                height=20,
                corner_radius=4,
                fg_color=Theme.BG_INPUT,
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda r=rec: self._handle_edit_recurring(r)
            )
            btn_edit_rec.pack(side="left", padx=(0, 4))

            del_btn = ctk.CTkButton(
                btn_box,
                text="🗑️",
                width=24,
                height=20,
                corner_radius=4,
                fg_color="transparent",
                hover_color="#450a0a",
                font=ctk.CTkFont(size=11),
                command=lambda rid=rec["id"], desc=rec["description"]: self._prompt_delete_recurring(rid, desc)
            )
            del_btn.pack(side="left")

    def _handle_edit_recurring(self, item: Dict[str, Any]):
        EditRecurringModal(
            self.winfo_toplevel(),
            self.db,
            recurring_item=item,
            on_success=self._on_recurring_saved
        )

    def _on_recurring_saved(self):
        self.toast.show("Gasto fijo actualizado en la plantilla.", is_error=False)
        self._refresh_recurring_list()
        if self.on_data_changed:
            self.on_data_changed()

    # ==========================================
    # MANEJADORES DE EVENTOS CRUD
    # ==========================================

    def _handle_edit_category(self, category: Dict[str, Any]):
        EditCategoryModal(
            self.winfo_toplevel(),
            self.db,
            category=category,
            on_success=self._on_category_saved
        )

    def _on_category_saved(self):
        self.toast.show("Categoría actualizada correctamente.", is_error=False)
        self._refresh_categories_list()
        if self.on_data_changed:
            self.on_data_changed()

    def _handle_create_account(self):
        EditAccountModal(
            self.winfo_toplevel(),
            self.db,
            account=None,
            on_success=self._on_account_saved
        )

    def _handle_edit_account(self, account: Dict[str, Any]):
        EditAccountModal(
            self.winfo_toplevel(),
            self.db,
            account=account,
            on_success=self._on_account_saved
        )

    def _on_account_saved(self):
        self.toast.show("Cuenta guardada correctamente.", is_error=False)
        self.refresh_data()
        if self.on_data_changed:
            self.on_data_changed()

    def _handle_save_category(self):
        name = self.cat_name_entry.get().strip()
        cat_type = self._get_current_type_code()

        if not name:
            self.toast.show("Por favor ingresa un nombre para la categoría.", is_error=True)
            return

        try:
            self.db.add_category(name, cat_type, self.selected_new_emoji, self.selected_new_color)
            self.toast.show(f"¡Categoría '{name}' agregada con éxito!", is_error=False)
            self.cat_name_entry.delete(0, "end")
            self._refresh_categories_list()
            if self.on_data_changed:
                self.on_data_changed()
        except Exception as e:
            self.toast.show(f"Error al guardar: {str(e)}", is_error=True)

    def _handle_save_recurring(self):
        curr_choice = self.rec_curr_seg.get()
        currency = "USD" if "USD" in curr_choice else "COP"
        category = self.rec_cat_combo.get().strip()
        description = self.rec_desc_entry.get().strip()
        amount_raw = self.rec_amount_entry.get().strip().replace(".", "").replace(",", ".") if currency == "COP" else self.rec_amount_entry.get().strip().replace(",", ".")
        day_raw = self.rec_day_entry.get().strip()

        if not description:
            self.toast.show("Por favor ingresa una descripción para el gasto fijo.", is_error=True)
            return

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.toast.show("Ingresa un monto válido mayor a 0.", is_error=True)
            return

        try:
            due_day = int(day_raw)
            if not (1 <= due_day <= 31):
                due_day = 1
        except ValueError:
            due_day = 1

        try:
            self.db.add_recurring_expense(category, description, amount, currency=currency, due_day=due_day)
            self.toast.show(f"¡Gasto fijo '{description}' agregado a la plantilla!", is_error=False)
            self.rec_desc_entry.delete(0, "end")
            self.rec_amount_entry.delete(0, "end")
            self._refresh_recurring_list()
            if self.on_data_changed:
                self.on_data_changed()
        except Exception as e:
            self.toast.show(f"Error al guardar: {str(e)}", is_error=True)

    def _prompt_delete_category(self, cat_id: int, cat_name: str):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar Categoría",
            message=f"¿Deseas eliminar la categoría '{cat_name}'?",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete_category(cat_id)
        )

    def _execute_delete_category(self, cat_id: int):
        success, msg = self.db.delete_category(cat_id)
        self.toast.show(msg, is_error=not success)
        if success:
            self._refresh_categories_list()
            if self.on_data_changed:
                self.on_data_changed()

    def _prompt_delete_account(self, acc_id: int, acc_name: str):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar / Archivar Cuenta",
            message=f"¿Deseas eliminar o desactivar la cuenta '{acc_name}'?",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete_account(acc_id)
        )

    def _execute_delete_account(self, acc_id: int):
        success, msg = self.db.delete_account(acc_id)
        self.toast.show(msg, is_error=not success)
        if success:
            self._refresh_accounts_crud_list()
            if self.on_data_changed:
                self.on_data_changed()

    def _prompt_delete_recurring(self, rec_id: int, description: str):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar de Plantilla",
            message=f"¿Deseas eliminar '{description}' de la plantilla de gastos fijos?",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete_recurring(rec_id)
        )

    def _execute_delete_recurring(self, rec_id: int):
        self.db.delete_recurring_expense(rec_id)
        self.toast.show("Gasto fijo eliminado de la plantilla.", is_error=False)
        self._refresh_recurring_list()
        if self.on_data_changed:
            self.on_data_changed()
