"""
Módulo Principal de Ingresos (Multimoneda: USD y COP):
Permite registrar y gestionar de forma clara todas las fuentes de ingresos tanto en dólares como en pesos,
con visualizador de balance disponible, widget de calendario interactivo y opciones de edición/duplicación/eliminación.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List
from ui.components import (
    ToastNotification,
    ConfirmDialog,
    BalanceWarningDialog,
    EditTransactionModal,
    DuplicateModal,
    DatePickerWidget,
    TagSelector,
    EmptyState
)
from ui.theme import Theme


class IncomesView(ctk.CTkFrame):
    def __init__(self, master, db_manager, on_data_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.on_data_changed = on_data_changed
        self.display_limit = 25

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        self.toast = ToastNotification(self)

        # 1. Cabecera
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 14))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="📥 Gestión de Ingresos",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Registro y control de entradas de dinero multimoneda (USD y COP).",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Banners de Saldo en Cabecera (USD y COP)
        banners_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        banners_box.pack(side="right")

        # Banner USD
        b_usd = ctk.CTkFrame(banners_box, fg_color=Theme.USD_BANNER_BG, corner_radius=10, border_width=1, border_color=Theme.USD_BANNER_BORDER)
        b_usd.pack(side="left", padx=(0, 8))
        b_usd_in = ctk.CTkFrame(b_usd, fg_color="transparent")
        b_usd_in.pack(padx=12, pady=6)
        ctk.CTkLabel(b_usd_in, text="BÓVEDA USD", font=ctk.CTkFont(size=9, weight="bold"), text_color=Theme.USD_BANNER_TEXT).pack(anchor="e")
        self.lbl_usd_bal = ctk.CTkLabel(b_usd_in, text="$0.00 USD", font=ctk.CTkFont(size=15, weight="bold"), text_color=Theme.ACCENT_BLUE)
        self.lbl_usd_bal.pack(anchor="e")

        # Banner COP
        b_cop = ctk.CTkFrame(banners_box, fg_color=Theme.COP_BANNER_BG, corner_radius=10, border_width=1, border_color=Theme.COP_BANNER_BORDER)
        b_cop.pack(side="left")
        b_cop_in = ctk.CTkFrame(b_cop, fg_color="transparent")
        b_cop_in.pack(padx=12, pady=6)
        ctk.CTkLabel(b_cop_in, text="DISPONIBLE COP", font=ctk.CTkFont(size=9, weight="bold"), text_color=Theme.COP_BANNER_TEXT).pack(anchor="e")
        self.lbl_cop_bal = ctk.CTkLabel(b_cop_in, text="$0 COP", font=ctk.CTkFont(size=15, weight="bold"), text_color=Theme.ACCENT_GREEN)
        self.lbl_cop_bal.pack(anchor="e")

        # 2. Contenedor Principal (Formulario Izquierda + Historial Derecha)
        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        content_grid.grid_columnconfigure(0, weight=45, uniform="incomes_cols")
        content_grid.grid_columnconfigure(1, weight=55, uniform="incomes_cols")
        content_grid.grid_rowconfigure(0, weight=1)


        # PANEL IZQUIERDO: Formulario de Registro
        form_panel = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Selector de Moneda
        self.currency_seg = ctk.CTkSegmentedButton(
            form_panel,
            values=["💵 Ingreso USD", "🇨🇴 Ingreso COP"],
            selected_color="#0284c7",
            selected_hover_color="#0369a1",
            height=34,
            command=self._on_currency_changed
        )
        self.currency_seg.set("💵 Ingreso USD")
        self.currency_seg.pack(fill="x", padx=18, pady=(16, 12))

        # Campo: Categoría / Concepto
        self.lbl_category = ctk.CTkLabel(
            form_panel,
            text="Categoría de Ingreso:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_category.pack(anchor="w", padx=18, pady=(0, 4))

        self.category_combo = ctk.CTkComboBox(
            form_panel,
            values=["Clientes Internacionales USD", "Consultoría / Freelance USD", "Otros Ingresos USD"],
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.category_combo.pack(fill="x", padx=18, pady=(0, 10))

        # Campo: Plataforma / Cuenta Receptora
        self.lbl_platform = ctk.CTkLabel(
            form_panel,
            text="Plataforma / Cuenta de Recepción:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_platform.pack(anchor="w", padx=18, pady=(0, 4))

        self.platform_combo = ctk.CTkComboBox(
            form_panel,
            values=["Wenia", "ARQ", "Deel", "Binance", "Bancolombia", "Nu", "Transferencia Bancaria", "Otro"],
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.platform_combo.set("Wenia")
        self.platform_combo.pack(fill="x", padx=18, pady=(0, 10))


        # Campo: Monto
        self.lbl_amount = ctk.CTkLabel(
            form_panel,
            text="Monto a Ingresar ($ USD):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_amount.pack(anchor="w", padx=18, pady=(0, 4))

        self.amount_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: 1500.00",
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.amount_entry.pack(fill="x", padx=18, pady=(0, 10))

        # Campo: Fecha con Widget Interactivo DatePicker
        ctk.CTkLabel(
            form_panel,
            text="Fecha de Ingreso:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=18, pady=(0, 4))

        self.date_picker = DatePickerWidget(form_panel, height=34)
        self.date_picker.pack(fill="x", padx=18, pady=(0, 10))

        # Campo: Notas / Descripción
        ctk.CTkLabel(
            form_panel,
            text="Detalle / Notas:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=18, pady=(0, 4))

        self.notes_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: Pago de honorarios / Proyecto",
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.notes_entry.pack(fill="x", padx=18, pady=(0, 10))

        # Selector de Etiquetas (Tags)
        ctk.CTkLabel(
            form_panel,
            text="🏷️ Etiquetas / Tags:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=18, pady=(0, 4))

        self.tag_selector = TagSelector(form_panel, self.db)
        self.tag_selector.pack(fill="x", padx=18, pady=(0, 14))

        # Botón Guardar
        self.btn_submit = ctk.CTkButton(
            form_panel,
            text="📥 Registrar Ingreso USD",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            command=self._handle_submit
        )
        self.btn_submit.pack(fill="x", padx=18, pady=(0, 16))

        # PANEL DERECHO: Historial Unificado de Ingresos
        history_panel = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        history_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        hist_header = ctk.CTkFrame(history_panel, fg_color="transparent")
        hist_header.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            hist_header,
            text="📋 Historial de Ingresos Registrados",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        # Filtro de Moneda en Historial
        self.hist_filter_seg = ctk.CTkSegmentedButton(
            hist_header,
            values=["Todas", "USD", "COP"],
            height=28,
            command=lambda _: self._refresh_incomes_list()
        )
        self.hist_filter_seg.set("Todas")
        self.hist_filter_seg.pack(side="right")

        self.incomes_scroll = ctk.CTkScrollableFrame(history_panel, fg_color="transparent")
        self.incomes_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 16))

    def _on_currency_changed(self, choice: str):
        if "USD" in choice:
            self.btn_submit.configure(text="💾 Guardar Ingreso USD", fg_color="#0284c7", hover_color="#0369a1")
            self.lbl_amount.configure(text="Monto a Ingresar ($ USD):")
            self.amount_entry.configure(placeholder_text="Ej: 1500.00")
            cats = [c["name"] for c in self.db.get_categories("INCOME_USD")]
            if cats:
                self.category_combo.configure(values=cats)
                self.category_combo.set(cats[0])
            self.platform_combo.configure(values=["Wenia", "ARQ", "Deel", "Binance", "Transferencia Bancaria", "Otro"])

            self.platform_combo.set("Wenia")
        else:
            self.btn_submit.configure(text="💾 Guardar Ingreso COP", fg_color="#10b981", hover_color="#059669")
            self.lbl_amount.configure(text="Monto a Ingresar ($ COP):")
            self.amount_entry.configure(placeholder_text="Ej: 3500000")
            cats = [c["name"] for c in self.db.get_categories("INCOME_COP")]
            if cats:
                self.category_combo.configure(values=cats)
                self.category_combo.set(cats[0])
            self.platform_combo.configure(values=["Bancolombia", "Nu Colombia", "Davivienda", "Efectivo", "Otro"])
            self.platform_combo.set("Bancolombia")

    def _handle_submit(self):
        curr_choice = self.currency_seg.get()
        category = self.category_combo.get().strip()
        platform = self.platform_combo.get().strip()
        amount_raw = self.amount_entry.get().strip().replace(".", "").replace(",", ".") if "COP" in curr_choice else self.amount_entry.get().strip().replace(",", ".")
        date_str = self.date_picker.get().strip()
        notes = self.notes_entry.get().strip()

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.toast.show("Por favor ingresa un monto válido mayor a 0.", is_error=True)
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.toast.show("Fecha inválida. Usa el calendario interactivo.", is_error=True)
            return

        try:
            selected_tag_ids = self.tag_selector.get_selected_tag_ids() if hasattr(self, "tag_selector") else []

            if "USD" in curr_choice:
                desc_platform = f"{platform} ({category})" if category else platform
                tx_id = self.db.add_usd_deposit(date_str, desc_platform, amount, notes)
                if selected_tag_ids and tx_id:
                    self.db.set_tags_for_record("usd_transactions", tx_id, selected_tag_ids)
                self.toast.show(f"¡Ingreso de +${amount:,.2f} USD guardado en {platform}!", is_error=False)
            else:
                desc_cat = f"{category} • {platform}" if platform else category
                tx_id = self.db.add_cop_income(date_str, desc_cat, amount, notes)
                if selected_tag_ids and tx_id:
                    self.db.set_tags_for_record("cop_transactions", tx_id, selected_tag_ids)
                self.toast.show(f"¡Ingreso de +${amount:,.0f} COP registrado con éxito!", is_error=False)

            self.amount_entry.delete(0, "end")
            self.notes_entry.delete(0, "end")
            if hasattr(self, "tag_selector"):
                self.tag_selector.clear()
            self.refresh_data()
            if self.on_data_changed:
                self.on_data_changed()
        except Exception as e:
            self.toast.show(f"Error al registrar: {str(e)}", is_error=True)

    def refresh_data(self):
        # Actualizar balances
        usd_bal = self.db.get_usd_balance()
        cop_bal = self.db.get_cop_balance()
        self.lbl_usd_bal.configure(text=f"${usd_bal:,.2f} USD")
        self.lbl_cop_bal.configure(text=f"${cop_bal:,.0f} COP")

        # Refrescar categorías
        curr_choice = self.currency_seg.get()
        cat_type = "INCOME_USD" if "USD" in curr_choice else "INCOME_COP"
        cats = [c["name"] for c in self.db.get_categories(cat_type)]
        if cats:
            current = self.category_combo.get()
            self.category_combo.configure(values=cats)
            if current in cats:
                self.category_combo.set(current)
            else:
                self.category_combo.set(cats[0])

        self._refresh_incomes_list()

    def _refresh_incomes_list(self):
        for widget in self.incomes_scroll.winfo_children():
            widget.destroy()

        filter_curr = self.hist_filter_seg.get()
        incomes = self.db.get_all_incomes(limit=self.display_limit, currency_filter=filter_curr)

        if not incomes:
            EmptyState(
                self.incomes_scroll,
                icon="📥",
                title="Sin ingresos registrados",
                message="No hay entradas de dinero que coincidan con el filtro seleccionado.",
                action_text="Limpiar Filtro" if filter_curr != "Todos" else None,
                action_command=(lambda: self.hist_filter_seg.set("Todos")) if filter_curr != "Todos" else None
            ).pack(fill="x", padx=10, pady=24)
            return

        for inc in incomes:
            curr = inc["currency"]
            is_usd = (curr == "USD")
            amt = float(inc["amount"])
            amt_str = f"+${amt:,.2f} USD" if is_usd else f"+${amt:,.0f} COP"
            badge = "💵 USD" if is_usd else "🇨🇴 COP"
            accent_col = Theme.ACCENT_BLUE if is_usd else Theme.ACCENT_GREEN
            source_tbl = "usd_transactions" if is_usd else "cop_transactions"

            card = ctk.CTkFrame(self.incomes_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=3, padx=2)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 2))

            ctk.CTkLabel(top, text=f"📥 {inc['concept']} [{badge}]", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=amt_str, font=ctk.CTkFont(size=13, weight="bold"), text_color=accent_col).pack(side="right")

            bottom = ctk.CTkFrame(card, fg_color="transparent")
            bottom.pack(fill="x", padx=12, pady=(0, 8))

            btn_box = ctk.CTkFrame(bottom, fg_color="transparent")
            btn_box.pack(side="right")

            info = f"{inc['date']}"
            if inc.get("notes"):
                info += f" • {inc['notes']}"

            ctk.CTkLabel(bottom, text=info, font=ctk.CTkFont(size=10), text_color=Theme.TEXT_MUTED, anchor="w").pack(side="left", fill="x", expand=True, padx=(0, 6))


            btn_edit = ctk.CTkButton(
                btn_box,
                text="✏️",
                width=24,
                height=20,
                fg_color="transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda r=inc, st=source_tbl: self._handle_edit(r, st)
            )
            btn_edit.pack(side="left", padx=1)

            btn_dup = ctk.CTkButton(
                btn_box,
                text="📋",
                width=24,
                height=20,
                fg_color="transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda r=inc, st=source_tbl: self._handle_duplicate(r, st)
            )
            btn_dup.pack(side="left", padx=1)

            btn_del = ctk.CTkButton(
                btn_box,
                text="🗑️",
                width=24,
                height=20,
                fg_color="transparent",
                hover_color="#450a0a",
                font=ctk.CTkFont(size=11),
                command=lambda r=inc, st=source_tbl: self._prompt_delete(r, st)
            )
            btn_del.pack(side="left", padx=1)

    def _handle_edit(self, record: Dict[str, Any], source_table: str):
        EditTransactionModal(
            self.winfo_toplevel(),
            self.db,
            source_table=source_table,
            record=record,
            on_success=self._on_action_success
        )

    def _handle_duplicate(self, record: Dict[str, Any], source_table: str):
        DuplicateModal(
            self.winfo_toplevel(),
            self.db,
            source_table=source_table,
            record=record,
            on_success=self._on_action_success
        )

    def _prompt_delete(self, record: Dict[str, Any], source_table: str):
        curr = record.get("currency", "COP")
        amt = float(record.get("amount", 0))
        amt_str = f"${amt:,.2f} USD" if curr == "USD" else f"${amt:,.0f} COP"
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar Ingreso",
            message=f"¿Deseas eliminar el ingreso de {amt_str} en '{record.get('concept')}'?\n\nEsta acción ajustará tu saldo disponible.",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete(record["id"], source_table, force=False)
        )

    def _execute_delete(self, record_id: int, source_table: str, force: bool = False):
        if source_table == "usd_transactions":
            success, msg, warn_data = self.db.delete_usd_transaction(record_id, force=force)
        else:
            success, msg, warn_data = self.db.delete_cop_transaction(record_id, force=force)

        if success:
            self.toast.show(msg, is_error=False)
            self._on_action_success()
        elif msg == "WARNING_NEGATIVE_BALANCE" and warn_data:
            BalanceWarningDialog(
                self.winfo_toplevel(),
                warning_data=warn_data,
                on_force_confirm=lambda: self._execute_delete(record_id, source_table, force=True)
            )
        else:
            self.toast.show(msg, is_error=True)

    def _on_action_success(self):
        self.refresh_data()
        if self.on_data_changed:
            self.on_data_changed()
