"""
Módulo Principal de Egresos & Gastos (Multimoneda: COP y USD):
Permite registrar y gestionar todos los gastos y salidas de dinero tanto en pesos como en dólares directos,
incluyendo el Checklist Interactivo de Gastos Fijos Multimoneda (Agenda To-Do con CTkCheckBox),
pagos con Tarjeta de Crédito, widget de calendario y CRUD total.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List
from ui.components import (
    ToastNotification,
    ConfirmDialog,
    RecurringModalDialog,
    BalanceWarningDialog,
    EditTransactionModal,
    DuplicateModal,
    DatePickerWidget,
    ApplyRecurringModal,
    TagSelector
)
from ui.theme import Theme


class ExpensesView(ctk.CTkFrame):
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
            text="💸 Egresos & Gastos",
            font=ctk.CTkFont(family="SF Pro Display", size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Control de gastos operativos en COP, consumos directos en USD y agenda de pagos fijos.",
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Banners de Saldo en Cabecera
        banners_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        banners_box.pack(side="right")

        # Banner COP
        b_cop = ctk.CTkFrame(banners_box, fg_color=Theme.COP_BANNER_BG, corner_radius=10, border_width=1, border_color=Theme.COP_BANNER_BORDER)
        b_cop.pack(side="left", padx=(0, 8))
        b_cop_in = ctk.CTkFrame(b_cop, fg_color="transparent")
        b_cop_in.pack(padx=12, pady=6)
        ctk.CTkLabel(b_cop_in, text="DISPONIBLE COP", font=ctk.CTkFont(size=9, weight="bold"), text_color=Theme.COP_BANNER_TEXT).pack(anchor="e")
        self.lbl_cop_bal = ctk.CTkLabel(b_cop_in, text="$0 COP", font=ctk.CTkFont(size=15, weight="bold"), text_color=Theme.ACCENT_GREEN)
        self.lbl_cop_bal.pack(anchor="e")

        # Banner USD
        b_usd = ctk.CTkFrame(banners_box, fg_color=Theme.USD_BANNER_BG, corner_radius=10, border_width=1, border_color=Theme.USD_BANNER_BORDER)
        b_usd.pack(side="left")
        b_usd_in = ctk.CTkFrame(b_usd, fg_color="transparent")
        b_usd_in.pack(padx=12, pady=6)
        ctk.CTkLabel(b_usd_in, text="DISPONIBLE USD", font=ctk.CTkFont(size=9, weight="bold"), text_color=Theme.USD_BANNER_TEXT).pack(anchor="e")
        self.lbl_usd_bal = ctk.CTkLabel(b_usd_in, text="$0.00 USD", font=ctk.CTkFont(size=15, weight="bold"), text_color=Theme.ACCENT_BLUE)
        self.lbl_usd_bal.pack(anchor="e")

        # 2. Contenedor Principal (Formulario Izquierda + Panel Derecho con Pestañas)
        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        content_grid.grid_columnconfigure(0, weight=45, uniform="expenses_cols")
        content_grid.grid_columnconfigure(1, weight=55, uniform="expenses_cols")
        content_grid.grid_rowconfigure(0, weight=1)


        # PANEL IZQUIERDO: Formulario de Registro de Gasto
        form_panel = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Selector de Moneda de Gasto
        self.currency_seg = ctk.CTkSegmentedButton(
            form_panel,
            values=["🇨🇴 Gasto en COP", "💵 Gasto Directo USD"],
            selected_color="#e11d48",
            selected_hover_color="#be123c",
            height=34,
            command=self._on_currency_changed
        )
        self.currency_seg.set("🇨🇴 Gasto en COP")
        self.currency_seg.pack(fill="x", padx=18, pady=(16, 10))

        # Campo: Categoría
        self.lbl_category = ctk.CTkLabel(
            form_panel,
            text="Categoría de Gasto:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_category.pack(anchor="w", padx=18, pady=(0, 4))

        self.category_combo = ctk.CTkComboBox(
            form_panel,
            values=["Arriendo / Hipoteca", "Servicios Públicos", "Alimentación / Mercado", "Otros Gastos"],
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.category_combo.pack(fill="x", padx=18, pady=(0, 10))

        # Campo: Método de Pago (solo aplica para COP)
        self.lbl_payment = ctk.CTkLabel(
            form_panel,
            text="Método de Pago:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_payment.pack(anchor="w", padx=18, pady=(0, 4))

        self.payment_combo = ctk.CTkComboBox(
            form_panel,
            values=["💳 Débito / Cuenta Operativa", "💳 Tarjeta de Crédito", "💵 Efectivo"],
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.payment_combo.set("💳 Débito / Cuenta Operativa")
        self.payment_combo.pack(fill="x", padx=18, pady=(0, 10))

        # Campo: Monto
        self.lbl_amount = ctk.CTkLabel(
            form_panel,
            text="Monto en Pesos ($ COP):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_amount.pack(anchor="w", padx=18, pady=(0, 4))

        self.amount_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: 250000",
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.amount_entry.pack(fill="x", padx=18, pady=(0, 10))

        # Campo: Fecha con DatePicker interactivo
        ctk.CTkLabel(
            form_panel,
            text="Fecha de Gasto:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=18, pady=(0, 4))

        self.date_picker = DatePickerWidget(form_panel, height=34)
        self.date_picker.pack(fill="x", padx=18, pady=(0, 10))

        # Switch: Gasto Fijo Mensual
        self.fixed_switch = ctk.CTkSwitch(
            form_panel,
            text="Marcar como Gasto Fijo Mensual",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_SECONDARY,
            progress_color="#f43f5e"
        )
        self.fixed_switch.pack(anchor="w", padx=18, pady=(0, 10))

        # Campo: Notas / Detalle
        ctk.CTkLabel(
            form_panel,
            text="Detalle / Notas:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=18, pady=(0, 4))

        self.notes_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: Mercado semanal / Suscripción",
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
            text="💸 Registrar Egreso COP",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#e11d48",
            hover_color="#be123c",
            text_color="#ffffff",
            command=self._handle_submit
        )
        self.btn_submit.pack(fill="x", padx=18, pady=(0, 16))

        # PANEL DERECHO: Pestañas de (Checklist Gastos Fijos Multimoneda vs Historial Egresos)
        right_panel = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        right_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        right_header.pack(fill="x", padx=16, pady=(14, 8))

        self.right_view_seg = ctk.CTkSegmentedButton(
            right_header,
            values=["📋 Checklist Gastos Fijos (Agenda)", "📑 Movimientos de Egresos"],
            height=32,
            command=self._on_right_view_changed
        )
        self.right_view_seg.set("📋 Checklist Gastos Fijos (Agenda)")
        self.right_view_seg.pack(side="left")

        # Contenedor de Vistas Derechas
        self.right_content = ctk.CTkFrame(right_panel, fg_color="transparent")
        self.right_content.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # 1. Sub-Panel Checklist Gastos Fijos (Agenda To-Do Multimoneda)
        self.checklist_frame = ctk.CTkFrame(self.right_content, fg_color="transparent")

        self.progress_box = ctk.CTkFrame(self.checklist_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
        self.progress_box.pack(fill="x", pady=(0, 8), padx=4)

        p_inner = ctk.CTkFrame(self.progress_box, fg_color="transparent")
        p_inner.pack(fill="x", padx=12, pady=10)

        p_top = ctk.CTkFrame(p_inner, fg_color="transparent")
        p_top.pack(fill="x")

        self.lbl_checklist_summary = ctk.CTkLabel(
            p_top,
            text="0 de 0 gastos pagados este mes (0%)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_checklist_summary.pack(side="left")

        btn_batch_apply = ctk.CTkButton(
            p_top,
            text="⚡ Aplicar Gastos del Mes",
            height=26,
            corner_radius=6,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_apply_recurring_modal
        )
        btn_batch_apply.pack(side="right")

        self.checklist_progress_bar = ctk.CTkProgressBar(p_inner, height=8, corner_radius=4, fg_color=Theme.BORDER_DEFAULT, progress_color="#10b981")
        self.checklist_progress_bar.pack(fill="x", pady=(6, 4))
        self.checklist_progress_bar.set(0.0)

        self.lbl_checklist_pending_amt = ctk.CTkLabel(
            p_inner,
            text="Pendiente: $0 COP • $0.00 USD",
            font=ctk.CTkFont(size=11),
            text_color=Theme.ACCENT_ROSE
        )
        self.lbl_checklist_pending_amt.pack(anchor="w")

        self.checklist_scroll = ctk.CTkScrollableFrame(self.checklist_frame, fg_color="transparent")
        self.checklist_scroll.pack(fill="both", expand=True, padx=2, pady=(0, 6))

        # 2. Sub-Panel Historial de Movimientos
        self.history_frame = ctk.CTkFrame(self.right_content, fg_color="transparent")

        hist_filter_bar = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        hist_filter_bar.pack(fill="x", pady=(0, 8))

        self.lbl_hist_count = ctk.CTkLabel(hist_filter_bar, text="0 egresos", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_MUTED)
        self.lbl_hist_count.pack(side="left")

        filter_box = ctk.CTkFrame(hist_filter_bar, fg_color="transparent")
        filter_box.pack(side="right")

        self.filter_curr_combo = ctk.CTkComboBox(
            filter_box,
            values=["Todas", "COP", "USD"],
            width=80,
            height=28,
            corner_radius=6,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda _: self._refresh_history_feed()
        )
        self.filter_curr_combo.set("Todas")
        self.filter_curr_combo.pack(side="left", padx=(0, 6))

        self.filter_pm_combo = ctk.CTkComboBox(
            filter_box,
            values=["Todos", "Débito", "TC"],
            width=80,
            height=28,
            corner_radius=6,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda _: self._refresh_history_feed()
        )
        self.filter_pm_combo.set("Todos")
        self.filter_pm_combo.pack(side="left")

        self.history_scroll = ctk.CTkScrollableFrame(self.history_frame, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=2, pady=(0, 6))

        self._on_right_view_changed("📋 Checklist Gastos Fijos (Agenda)")

    def _on_currency_changed(self, choice: str):
        if "COP" in choice:
            self.btn_submit.configure(text="💸 Registrar Egreso COP", fg_color="#e11d48", hover_color="#be123c")
            self.lbl_amount.configure(text="Monto en Pesos ($ COP):")
            self.amount_entry.configure(placeholder_text="Ej: 250000")
            self.lbl_payment.pack(anchor="w", padx=18, pady=(0, 4))
            self.payment_combo.pack(fill="x", padx=18, pady=(0, 10))
            self.fixed_switch.configure(state="normal")
            cats = [c["name"] for c in self.db.get_categories("EXPENSE_COP")]
            if cats:
                self.category_combo.configure(values=cats)
                self.category_combo.set(cats[0])
        else:
            self.btn_submit.configure(text="💸 Registrar Egreso USD", fg_color="#0284c7", hover_color="#0369a1")
            self.lbl_amount.configure(text="Monto en Dólares ($ USD):")
            self.amount_entry.configure(placeholder_text="Ej: 20.00")
            self.payment_combo.pack_forget()
            self.lbl_payment.pack_forget()
            self.fixed_switch.configure(state="disabled")
            cats = [c["name"] for c in self.db.get_categories("EXPENSE_USD")]
            if cats:
                self.category_combo.configure(values=cats)
                self.category_combo.set(cats[0])

    def _on_right_view_changed(self, choice: str):
        self.checklist_frame.pack_forget()
        self.history_frame.pack_forget()

        if "Checklist" in choice:
            self.checklist_frame.pack(fill="both", expand=True)
            self._refresh_checklist()
        else:
            self.history_frame.pack(fill="both", expand=True)
            self._refresh_history_feed()

    def _handle_submit(self):
        curr_choice = self.currency_seg.get()
        is_cop = ("COP" in curr_choice)
        category = self.category_combo.get().strip()
        amount_raw = self.amount_entry.get().strip().replace(".", "").replace(",", ".") if is_cop else self.amount_entry.get().strip().replace(",", ".")
        date_str = self.date_picker.get().strip()
        notes = self.notes_entry.get().strip()
        is_fixed = bool(self.fixed_switch.get()) if is_cop else False
        pm_choice = self.payment_combo.get()

        pm_code = "DEBIT"
        if "Tarjeta de Crédito" in pm_choice:
            pm_code = "CREDIT_CARD"
        elif "Efectivo" in pm_choice:
            pm_code = "CASH"

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.toast.show("Ingresa un monto válido mayor a 0.", is_error=True)
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.toast.show("Fecha inválida. Usa el selector de calendario.", is_error=True)
            return

        try:
            selected_tag_ids = self.tag_selector.get_selected_tag_ids() if hasattr(self, "tag_selector") else []

            if is_cop:
                tx_id = self.db.add_cop_expense(date_str, category, amount, is_fixed=is_fixed, payment_method=pm_code, notes=notes)
                if selected_tag_ids and tx_id:
                    self.db.set_tags_for_record("cop_transactions", tx_id, selected_tag_ids)
                tipo_str = "Fijo" if is_fixed else "Variable"
                pm_label = " (TC)" if pm_code == "CREDIT_CARD" else ""
                self.toast.show(f"Egreso COP {tipo_str}{pm_label} de ${amount:,.0f} registrado.", is_error=False)
            else:
                current_bal = self.db.get_usd_balance()
                if amount > current_bal:
                    self.toast.show(f"⚠️ Saldo insuficiente en USD (${current_bal:,.2f}) para gastar ${amount:,.2f}.", is_error=True)
                    return
                tx_id = self.db.add_usd_expense(date_str, category, amount, notes=notes)
                if selected_tag_ids and tx_id:
                    self.db.set_tags_for_record("usd_transactions", tx_id, selected_tag_ids)
                self.toast.show(f"Egreso USD de ${amount:,.2f} registrado en '{category}'.", is_error=False)

            self.amount_entry.delete(0, "end")
            self.notes_entry.delete(0, "end")
            if hasattr(self, "tag_selector"):
                self.tag_selector.clear()
            self.refresh_data()
            if self.on_data_changed:
                self.on_data_changed()
        except Exception as e:
            self.toast.show(f"Error al registrar: {str(e)}", is_error=True)

    def _open_apply_recurring_modal(self):
        ApplyRecurringModal(
            self.winfo_toplevel(),
            self.db,
            on_success=self._on_recurring_applied
        )

    def _on_recurring_applied(self):
        self.refresh_data()
        if self.on_data_changed:
            self.on_data_changed()
        self.toast.show("¡Gastos fijos aplicados y reflejados en tu balance!", is_error=False)

    def refresh_data(self):
        cop_bal = self.db.get_cop_balance()
        usd_bal = self.db.get_usd_balance()
        self.lbl_cop_bal.configure(text=f"${cop_bal:,.0f} COP")
        self.lbl_usd_bal.configure(text=f"${usd_bal:,.2f} USD")

        curr_choice = self.currency_seg.get()
        cat_type = "EXPENSE_COP" if "COP" in curr_choice else "EXPENSE_USD"
        cats = [c["name"] for c in self.db.get_categories(cat_type)]
        if cats:
            current = self.category_combo.get()
            self.category_combo.configure(values=cats)
            if current in cats:
                self.category_combo.set(current)
            else:
                self.category_combo.set(cats[0])

        self._refresh_checklist()
        self._refresh_history_feed()

    # ==========================================
    # CHECKLIST MULTIMONEDA
    # ==========================================

    def _refresh_checklist(self):
        for widget in self.checklist_scroll.winfo_children():
            widget.destroy()

        checklist = self.db.get_recurring_checklist_status()

        total_items = len(checklist)
        paid_items = sum(1 for i in checklist if i["is_paid"])

        total_cop = sum(i["amount"] for i in checklist if i.get("currency", "COP") == "COP")
        paid_cop = sum(i["amount"] for i in checklist if i.get("currency", "COP") == "COP" and i["is_paid"])
        pending_cop = total_cop - paid_cop

        total_usd = sum(i["amount"] for i in checklist if i.get("currency", "COP") == "USD")
        paid_usd = sum(i["amount"] for i in checklist if i.get("currency", "COP") == "USD" and i["is_paid"])
        pending_usd = total_usd - paid_usd

        pct = (paid_items / total_items) if total_items > 0 else 0.0
        self.checklist_progress_bar.set(pct)
        self.lbl_checklist_summary.configure(
            text=f"{paid_items} de {total_items} gastos pagados este mes ({pct*100:.0f}%)"
        )
        self.lbl_checklist_pending_amt.configure(
            text=f"Pendiente: ${pending_cop:,.0f} COP • ${pending_usd:,.2f} USD"
        )

        if not checklist:
            ctk.CTkLabel(
                self.checklist_scroll,
                text="No hay gastos fijos configurados en la plantilla.\nPuedes agregarlos en ⚙️ Configuración.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED,
                justify="center"
            ).pack(pady=30)
            return

        for item in checklist:
            is_paid = item["is_paid"]
            curr = item.get("currency", "COP")
            card_bg = "#064e3b" if is_paid else Theme.BG_CARD_SUBTLE
            border_col = "#059669" if is_paid else Theme.BORDER_SUBTLE

            card = ctk.CTkFrame(self.checklist_scroll, fg_color=card_bg, corner_radius=10, border_width=1, border_color=border_col)
            card.pack(fill="x", pady=3, padx=2)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=10)

            # Checkbox interactivo
            chk_var = ctk.IntVar(value=1 if is_paid else 0)
            chk = ctk.CTkCheckBox(
                row,
                text="",
                width=24,
                variable=chk_var,
                checkbox_height=20,
                checkbox_width=20,
                corner_radius=5,
                fg_color="#10b981",
                hover_color="#059669",
                command=lambda i=item, v=chk_var: self._toggle_checklist_item(i, v.get())
            )
            chk.pack(side="left", padx=(0, 10))

            # Monto a la derecha (empaquetado antes para reservar su espacio completo)
            amt_str = f"${item['amount']:,.2f} USD" if curr == "USD" else f"${item['amount']:,.0f} COP"
            amt_color = "#34d399" if is_paid else Theme.ACCENT_ROSE
            amt_lbl = ctk.CTkLabel(
                row,
                text=amt_str,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=amt_color
            )
            amt_lbl.pack(side="right", padx=(8, 6))

            # Info del gasto en el centro
            info_box = ctk.CTkFrame(row, fg_color="transparent")
            info_box.pack(side="left", fill="both", expand=True)

            title_color = "#a7f3d0" if is_paid else Theme.TEXT_PRIMARY
            curr_badge = f"[{curr}] "
            desc_text = f"{curr_badge}{item['category']} • {item['description']}"

            ctk.CTkLabel(
                info_box,
                text=desc_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=title_color
            ).pack(anchor="w")

            sub_info = f"Vencimiento habitual: Día {item['due_day']}"
            if is_paid and item["paid_date"]:
                sub_info = f"✓ Pagado el {item['paid_date']}"

            ctk.CTkLabel(
                info_box,
                text=sub_info,
                font=ctk.CTkFont(size=10),
                text_color="#94a3b8" if not is_paid else "#6ee7b7"
            ).pack(anchor="w")

    def _toggle_checklist_item(self, item: Dict[str, Any], new_state: int):
        if new_state == 1:
            success, msg, _ = self.db.pay_recurring_item(item["id"])
            self.toast.show(msg, is_error=not success)
            self.refresh_data()
            if self.on_data_changed:
                self.on_data_changed()
        else:
            if item["tx_id"]:
                ConfirmDialog(
                    self.winfo_toplevel(),
                    title="Desmarcar Gasto Fijo",
                    message=f"¿Deseas desmarcar '{item['description']}' como pagado?\n\nEsto eliminará el registro de gasto y restaurará tu saldo disponible.",
                    confirm_text="Desmarcar",
                    on_confirm=lambda: self._execute_unpay(item["tx_id"], item.get("currency", "COP"))
                )
            else:
                self._refresh_checklist()

    def _execute_unpay(self, tx_id: int, currency: str):
        success, msg = self.db.unpay_recurring_item(tx_id, currency=currency)
        self.toast.show(msg, is_error=not success)
        self.refresh_data()
        if self.on_data_changed:
            self.on_data_changed()

    # ==========================================
    # HISTORIAL DE EGRESOS
    # ==========================================

    def _refresh_history_feed(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        curr_filter = self.filter_curr_combo.get()
        pm_filter = self.filter_pm_combo.get()
        pm_code = None
        if pm_filter == "TC":
            pm_code = "CREDIT_CARD"
        elif pm_filter == "Débito":
            pm_code = "DEBIT"

        expenses = self.db.get_all_expenses(limit=self.display_limit, currency_filter=curr_filter, payment_method=pm_code)
        self.lbl_hist_count.configure(text=f"({len(expenses)} mostrados)")

        if not expenses:
            ctk.CTkLabel(
                self.history_scroll,
                text="No hay egresos para mostrar con estos filtros.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED
            ).pack(pady=40)
            return

        for exp in expenses:
            curr = exp["currency"]
            is_usd = (curr == "USD")
            amt = float(exp["amount"])
            amt_str = f"-${amt:,.2f} USD" if is_usd else f"-${amt:,.0f} COP"
            badge = "💵 USD" if is_usd else ("💳 TC" if exp.get("payment_method") == "CREDIT_CARD" else "🇨🇴 COP")
            source_tbl = "usd_transactions" if is_usd else "cop_transactions"

            card = ctk.CTkFrame(self.history_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=3, padx=2)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 2))

            ctk.CTkLabel(top, text=f"💸 {exp['category']} [{badge}]", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=amt_str, font=ctk.CTkFont(size=13, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(side="right")

            bottom = ctk.CTkFrame(card, fg_color="transparent")
            bottom.pack(fill="x", padx=12, pady=(0, 8))

            btn_box = ctk.CTkFrame(bottom, fg_color="transparent")
            btn_box.pack(side="right")

            info = f"{exp['date']}"
            if exp.get("notes"):
                info += f" • {exp['notes']}"

            ctk.CTkLabel(bottom, text=info, font=ctk.CTkFont(size=10), text_color=Theme.TEXT_MUTED, anchor="w").pack(side="left", fill="x", expand=True, padx=(0, 6))


            btn_edit = ctk.CTkButton(
                btn_box,
                text="✏️",
                width=24,
                height=20,
                fg_color="transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda r=exp, st=source_tbl: self._handle_edit(r, st)
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
                command=lambda r=exp, st=source_tbl: self._handle_duplicate(r, st)
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
                command=lambda r=exp, st=source_tbl: self._prompt_delete(r, st)
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
            title="Eliminar Egreso",
            message=f"¿Deseas eliminar el egreso de {amt_str} en '{record.get('category')}'?\n\nEsta acción ajustará tu saldo disponible.",
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
