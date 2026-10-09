"""
Módulo Principal de Egresos & Gastos (Multimoneda: COP y USD):
Permite registrar y gestionar todos los gastos y salidas de dinero tanto en pesos como en dólares directos,
incluyendo el Checklist Interactivo de Gastos Fijos Multimoneda (Agenda To-Do con CTkCheckBox),
pagos con Tarjeta de Crédito, widget de calendario y CRUD total.
"""

from core.constants import Currencies, CurrencyLabels, Platforms, Categories, PaymentMethods, FilterOptions, SettingsTabs
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
    TagSelector,
    PayRecurringDialog,
    EmptyState
)
from controllers.expense_controller import ExpenseController
from ui.theme import Theme
from core.event_bus import EventBus


class ExpensesView(ctk.CTkFrame):
    def __init__(self, master, db_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.controller = ExpenseController(db_manager)
        self.display_limit = 25
        self.checklist_ym = datetime.now().strftime("%Y-%m")

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        self.toast = ToastNotification(self)

        # 1. Cabecera
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_LG, Theme.SPACING_MD))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="💸 Egresos & Gastos",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Control de gastos operativos en COP, consumos directos en USD y agenda de pagos fijos.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Banners de Saldo en Cabecera
        banners_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        banners_box.pack(side="right")

        # Banner COP
        b_cop = ctk.CTkFrame(banners_box, fg_color=Theme.COP_BANNER_BG, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.COP_BANNER_BORDER)
        b_cop.pack(side="left", padx=(0, Theme.SPACING_SM))
        b_cop_in = ctk.CTkFrame(b_cop, fg_color="transparent")
        b_cop_in.pack(padx=Theme.SPACING_SM, pady=Theme.SPACING_XS)
        ctk.CTkLabel(b_cop_in, text="DISPONIBLE COP", font=ctk.CTkFont(size=9, weight="bold"), text_color=Theme.COP_BANNER_TEXT).pack(anchor="e")
        self.lbl_cop_bal = ctk.CTkLabel(b_cop_in, text="$0 COP", font=ctk.CTkFont(size=15, weight="bold"), text_color=Theme.ACCENT_COP)
        self.lbl_cop_bal.pack(anchor="e")

        # Banner USD
        b_usd = ctk.CTkFrame(banners_box, fg_color=Theme.USD_BANNER_BG, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.USD_BANNER_BORDER)
        b_usd.pack(side="left")
        b_usd_in = ctk.CTkFrame(b_usd, fg_color="transparent")
        b_usd_in.pack(padx=Theme.SPACING_SM, pady=Theme.SPACING_XS)
        ctk.CTkLabel(b_usd_in, text="DISPONIBLE USD", font=ctk.CTkFont(size=9, weight="bold"), text_color=Theme.USD_BANNER_TEXT).pack(anchor="e")
        self.lbl_usd_bal = ctk.CTkLabel(b_usd_in, text="$0.00 USD", font=ctk.CTkFont(size=15, weight="bold"), text_color=Theme.ACCENT_USD)
        self.lbl_usd_bal.pack(anchor="e")

        # 2. Contenedor Principal (Formulario Izquierda + Panel Derecho con Pestañas)
        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_LG))
        content_grid.grid_columnconfigure(0, weight=45, uniform="expenses_cols")
        content_grid.grid_columnconfigure(1, weight=55, uniform="expenses_cols")
        content_grid.grid_rowconfigure(0, weight=1)


        # PANEL IZQUIERDO: Formulario de Registro de Gasto
        form_panel = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, Theme.SPACING_SM))

        # Selector de Moneda de Gasto
        self.currency_seg = ctk.CTkSegmentedButton(
            form_panel,
            values=[CurrencyLabels.EXPENSE_COP, CurrencyLabels.EXPENSE_USD],
            selected_color=Theme.ERROR,
            selected_hover_color=Theme.ERROR_HOVER,
            height=34,
            command=self._on_currency_changed
        )
        self.currency_seg.set("🇨🇴 Gasto en COP")
        self.currency_seg.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        # Campo: Categoría
        self.lbl_category = ctk.CTkLabel(
            form_panel,
            text="Categoría de Gasto:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_category.pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))

        self.category_combo = ctk.CTkComboBox(
            form_panel,
            values=Categories.EXPENSE_DEFAULT,
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.category_combo.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Campo: Método de Pago (solo aplica para COP)
        self.lbl_payment = ctk.CTkLabel(
            form_panel,
            text="Método de Pago:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_payment.pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))

        self.payment_combo = ctk.CTkComboBox(
            form_panel,
            values=PaymentMethods.OPTIONS,
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.payment_combo.set("💳 Débito / Cuenta Operativa")
        self.payment_combo.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Campo: Monto
        self.lbl_amount = ctk.CTkLabel(
            form_panel,
            text="Monto en Pesos ($ COP):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_amount.pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))

        self.amount_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: 250000",
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.amount_entry.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Campo: Fecha con DatePicker interactivo
        ctk.CTkLabel(
            form_panel,
            text="Fecha de Gasto:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))

        self.date_picker = DatePickerWidget(form_panel, height=34)
        self.date_picker.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Switch: Gasto Fijo Mensual
        self.fixed_switch = ctk.CTkSwitch(
            form_panel,
            text="Marcar como Gasto Fijo Mensual",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_SECONDARY,
            progress_color=Theme.ERROR
        )
        self.fixed_switch.pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Campo: Notas / Detalle
        ctk.CTkLabel(
            form_panel,
            text="Detalle / Notas:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))

        self.notes_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: Mercado semanal / Suscripción",
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.notes_entry.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Selector de Etiquetas (Tags)
        ctk.CTkLabel(
            form_panel,
            text="🏷️ Etiquetas / Tags:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))

        self.tag_selector = TagSelector(form_panel, self.db)
        self.tag_selector.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        # Botón Guardar
        self.btn_submit = ctk.CTkButton(
            form_panel,
            text="💸 Registrar Egreso COP",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.ERROR,
            hover_color=Theme.ERROR_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            command=self._handle_submit
        )
        self.btn_submit.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        # PANEL DERECHO: Pestañas de (Checklist Gastos Fijos Multimoneda vs Historial Egresos)
        right_panel = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(Theme.SPACING_SM, 0))

        right_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        right_header.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        self.right_view_seg = ctk.CTkSegmentedButton(
            right_header,
            values=FilterOptions.TAB_EXPENSES,
            height=32,
            command=self._on_right_view_changed
        )
        self.right_view_seg.set("📋 Checklist Gastos Fijos (Agenda)")
        self.right_view_seg.pack(side="left")

        # Selector de Mes para la Agenda de Gastos Fijos
        self.month_nav_frame = ctk.CTkFrame(right_header, fg_color="transparent")
        self.month_nav_frame.pack(side="right")

        btn_prev = ctk.CTkButton(
            self.month_nav_frame,
            text="◀",
            width=28,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            command=self._prev_checklist_month
        )
        btn_prev.pack(side="left", padx=Theme.SPACING_XS)

        self.lbl_checklist_month = ctk.CTkLabel(
            self.month_nav_frame,
            text=self._format_month_label(self.checklist_ym),
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            width=115
        )
        self.lbl_checklist_month.pack(side="left", padx=Theme.SPACING_XS)

        btn_next = ctk.CTkButton(
            self.month_nav_frame,
            text="▶",
            width=28,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            command=self._next_checklist_month
        )
        btn_next.pack(side="left", padx=Theme.SPACING_XS)

        btn_today = ctk.CTkButton(
            self.month_nav_frame,
            text="Hoy",
            width=42,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_COP,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._current_checklist_month
        )
        btn_today.pack(side="left", padx=(Theme.SPACING_XS, 0))

        # Contenedor de Vistas Derechas
        self.right_content = ctk.CTkFrame(right_panel, fg_color="transparent")
        self.right_content.pack(fill="both", expand=True, padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_SM))

        # 1. Sub-Panel Checklist Gastos Fijos (Agenda To-Do Multimoneda)
        self.checklist_frame = ctk.CTkFrame(self.right_content, fg_color="transparent")

        self.progress_box = ctk.CTkFrame(self.checklist_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        self.progress_box.pack(fill="x", pady=(0, Theme.SPACING_SM), padx=Theme.SPACING_XS)

        p_inner = ctk.CTkFrame(self.progress_box, fg_color="transparent")
        p_inner.pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_SM)

        p_top = ctk.CTkFrame(p_inner, fg_color="transparent")
        p_top.pack(fill="x")

        self.lbl_checklist_summary = ctk.CTkLabel(
            p_top,
            text="0 de 0 gastos pagados este mes (0%)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_checklist_summary.pack(side="left")

        self.btn_batch_apply = ctk.CTkButton(
            p_top,
            text="⚡ Aplicar Gastos del Mes",
            height=26,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_apply_recurring_modal
        )
        self.btn_batch_apply.pack(side="right")

        self.checklist_progress_bar = ctk.CTkProgressBar(p_inner, height=8, corner_radius=Theme.SPACING_XS, fg_color=Theme.BORDER_DEFAULT, progress_color=Theme.SUCCESS)
        self.checklist_progress_bar.pack(fill="x", pady=(Theme.SPACING_XS, Theme.SPACING_XS))
        self.checklist_progress_bar.set(0.0)

        self.lbl_checklist_pending_amt = ctk.CTkLabel(
            p_inner,
            text="Pendiente: $0 COP • $0.00 USD",
            font=ctk.CTkFont(size=11),
            text_color=Theme.ACCENT_ROSE
        )
        self.lbl_checklist_pending_amt.pack(anchor="w")

        self.checklist_scroll = ctk.CTkScrollableFrame(self.checklist_frame, fg_color="transparent")
        self.checklist_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))

        # 2. Sub-Panel Historial de Movimientos
        self.history_frame = ctk.CTkFrame(self.right_content, fg_color="transparent")

        hist_filter_bar = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        hist_filter_bar.pack(fill="x", pady=(0, Theme.SPACING_SM))

        self.lbl_hist_count = ctk.CTkLabel(hist_filter_bar, text="0 egresos", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_MUTED)
        self.lbl_hist_count.pack(side="left")

        filter_box = ctk.CTkFrame(hist_filter_bar, fg_color="transparent")
        filter_box.pack(side="right")

        self.filter_curr_combo = ctk.CTkComboBox(
            filter_box,
            values=FilterOptions.CURRENCY,
            width=80,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda _: self._refresh_history_feed()
        )
        self.filter_curr_combo.set("Todas")
        self.filter_curr_combo.pack(side="left", padx=(0, Theme.SPACING_XS))

        self.filter_pm_combo = ctk.CTkComboBox(
            filter_box,
            values=PaymentMethods.FILTER,
            width=80,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda _: self._refresh_history_feed()
        )
        self.filter_pm_combo.set("Todos")
        self.filter_pm_combo.pack(side="left")

        self.history_scroll = ctk.CTkScrollableFrame(self.history_frame, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))

        self._on_right_view_changed("📋 Checklist Gastos Fijos (Agenda)")

    def _on_currency_changed(self, choice: str):
        if "COP" in choice:
            self.btn_submit.configure(text="💸 Registrar Egreso COP", fg_color=Theme.ERROR, hover_color=Theme.ERROR_HOVER)
            self.lbl_amount.configure(text="Monto en Pesos ($ COP):")
            self.amount_entry.configure(placeholder_text="Ej: 250000")
            self.lbl_payment.pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))
            self.payment_combo.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))
            self.fixed_switch.configure(state="normal")
            cats = self.controller.get_categories(is_usd_or_type=False)
            if cats:
                self.category_combo.configure(values=cats)
                self.category_combo.set(cats[0])
        else:
            self.btn_submit.configure(text="💸 Registrar Egreso USD", fg_color=Theme.INFO, hover_color=Theme.INFO_HOVER)
            self.lbl_amount.configure(text="Monto en Dólares ($ USD):")
            self.amount_entry.configure(placeholder_text="Ej: 20.00")
            self.payment_combo.pack_forget()
            self.lbl_payment.pack_forget()
            self.fixed_switch.configure(state="disabled")
            cats = self.controller.get_categories(is_usd_or_type=True)
            if cats:
                self.category_combo.configure(values=cats)
                self.category_combo.set(cats[0])

    def _on_right_view_changed(self, choice: str):
        self.checklist_frame.pack_forget()
        self.history_frame.pack_forget()

        if "Checklist" in choice:
            self.month_nav_frame.pack(side="right")
            self.checklist_frame.pack(fill="both", expand=True)
            self._refresh_checklist()
        else:
            self.month_nav_frame.pack_forget()
            self.history_frame.pack(fill="both", expand=True)
            self._refresh_history_feed()

    def _handle_submit(self):
        curr_choice = self.currency_seg.get()
        is_usd = ("USD" in curr_choice)
        category = self.category_combo.get().strip()
        date_str = self.date_picker.get().strip()
        notes = self.notes_entry.get().strip()
        is_fixed = bool(self.fixed_switch.get()) if not is_usd else False
        pm_choice = self.payment_combo.get() if not is_usd else ""
        selected_tag_ids = self.tag_selector.get_selected_tag_ids() if hasattr(self, "tag_selector") else []

        success, msg = self.controller.add_expense(
            amount_str=self.amount_entry.get(),
            category=category,
            date_str=date_str,
            notes=notes,
            is_fixed=is_fixed,
            is_usd=is_usd,
            payment_method_label=pm_choice,
            selected_tag_ids=selected_tag_ids
        )

        if success:
            self.toast.show(msg, is_error=False)
            self.amount_entry.delete(0, "end")
            self.notes_entry.delete(0, "end")
            if hasattr(self, "tag_selector"):
                self.tag_selector.clear()
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")
        else:
            self.toast.show(msg, is_error=True)

    def _open_apply_recurring_modal(self):
        ApplyRecurringModal(
            self.winfo_toplevel(),
            self.db,
            on_success=self._on_recurring_applied
        )

    def _on_recurring_applied(self):
        self.refresh_data()
        EventBus.publish("DATA_UPDATED")
        self.toast.show("¡Gastos fijos aplicados y reflejados en tu balance!", is_error=False)

    def refresh_data(self):
        balances = self.controller.get_balances()
        cop_bal = balances["cop"]
        usd_bal = balances["usd"]
        self.lbl_cop_bal.configure(text=f"${cop_bal:,.0f} COP")
        self.lbl_usd_bal.configure(text=f"${usd_bal:,.2f} USD")

        curr_choice = self.currency_seg.get()
        cats = self.controller.get_categories(is_usd_or_type=("USD" in curr_choice))
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

    def _format_month_label(self, ym: str) -> str:
        """Formatea '2026-09' a 'Septiembre 2026'."""
        try:
            dt = datetime.strptime(ym, "%Y-%m")
            meses = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
            return f"{meses[dt.month - 1]} {dt.year}"
        except Exception:
            return ym

    def _prev_checklist_month(self):
        dt = datetime.strptime(self.checklist_ym, "%Y-%m")
        if dt.month == 1:
            self.checklist_ym = f"{dt.year - 1}-12"
        else:
            self.checklist_ym = f"{dt.year}-{dt.month - 1:02d}"
        self.lbl_checklist_month.configure(text=self._format_month_label(self.checklist_ym))
        self._refresh_checklist()

    def _next_checklist_month(self):
        dt = datetime.strptime(self.checklist_ym, "%Y-%m")
        if dt.month == 12:
            self.checklist_ym = f"{dt.year + 1}-01"
        else:
            self.checklist_ym = f"{dt.year}-{dt.month + 1:02d}"
        self.lbl_checklist_month.configure(text=self._format_month_label(self.checklist_ym))
        self._refresh_checklist()

    def _current_checklist_month(self):
        self.checklist_ym = datetime.now().strftime("%Y-%m")
        self.lbl_checklist_month.configure(text=self._format_month_label(self.checklist_ym))
        self._refresh_checklist()

    def _open_apply_recurring_modal(self):
        ApplyRecurringModal(
            self.winfo_toplevel(),
            self.db,
            target_ym=self.checklist_ym,
            on_success=self.refresh_data
        )

    def _refresh_checklist(self):
        for widget in self.checklist_scroll.winfo_children():
            widget.destroy()

        checklist = self.controller.get_checklist(self.checklist_ym)

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
        m_name = self._format_month_label(self.checklist_ym)
        self.lbl_checklist_summary.configure(
            text=f"{paid_items} de {total_items} gastos pagados para {m_name} ({pct*100:.0f}%)"
        )
        self.lbl_checklist_pending_amt.configure(
            text=f"Pendiente: ${pending_cop:,.0f} COP • ${pending_usd:,.2f} USD"
        )
        short_m = m_name.split()[0]
        self.btn_batch_apply.configure(text=f"⚡ Aplicar Gastos de {short_m}")

        if not checklist:
            EmptyState(
                self.checklist_scroll,
                icon="📋",
                title="Sin gastos fijos configurados",
                message="Configura tu plantilla de gastos fijos y suscripciones en ⚙️ Configuración.",
                compact=True
            ).pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_LG)
            return

        self.checklist_vars = {}
        for item in checklist:
            is_paid = item["is_paid"]
            curr = item.get("currency", "COP")
            card_bg = "#064e3b" if is_paid else Theme.BG_CARD_SUBTLE
            border_col = "#059669" if is_paid else Theme.BORDER_SUBTLE

            card = ctk.CTkFrame(self.checklist_scroll, fg_color=card_bg, corner_radius=Theme.SPACING_SM, border_width=1, border_color=border_col)
            card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_SM)

            # Checkbox interactivo
            chk_var = ctk.IntVar(value=1 if is_paid else 0)
            self.checklist_vars[item["id"]] = chk_var

            chk = ctk.CTkCheckBox(
                row,
                text="",
                width=24,
                variable=chk_var,
                checkbox_height=20,
                checkbox_width=20,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.SUCCESS,
                hover_color=Theme.SUCCESS,
                command=lambda i=item, v=chk_var: self._toggle_checklist_item(i, v.get())
            )
            chk.pack(side="left", padx=(0, Theme.SPACING_SM))

            # Monto a la derecha (empaquetado antes para reservar su espacio completo)
            amt_str = f"${item['amount']:,.2f} USD" if curr == "USD" else f"${item['amount']:,.0f} COP"
            amt_color = Theme.SUCCESS if is_paid else Theme.DANGER
            amt_lbl = ctk.CTkLabel(
                row,
                text=amt_str,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=amt_color
            )
            amt_lbl.pack(side="right", padx=(Theme.SPACING_SM, Theme.SPACING_XS))

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
            if is_paid and item.get("paid_date"):
                display_date = item.get("actual_paid_date") or item["paid_date"]
                if item.get("actual_paid_date") or item["paid_date"][:7] != self.checklist_ym:
                    sub_info = f"✓ Pagado el {display_date} (por anticipado)"
                else:
                    sub_info = f"✓ Pagado el {display_date}"

            ctk.CTkLabel(
                info_box,
                text=sub_info,
                font=ctk.CTkFont(size=10),
                text_color=Theme.TEXT_SECONDARY if not is_paid else "#6ee7b7"
            ).pack(anchor="w")

    def _toggle_checklist_item(self, item: Dict[str, Any], new_state: int):
        if new_state == 1:
            curr_ym = datetime.now().strftime("%Y-%m")
            if self.checklist_ym != curr_ym:
                PayRecurringDialog(
                    self.winfo_toplevel(),
                    item=item,
                    target_ym=self.checklist_ym,
                    on_confirm=lambda d: self._execute_pay(item["id"], d, self.checklist_ym),
                    on_cancel=lambda: self._refresh_checklist()
                )
            else:
                self._execute_pay(item["id"], datetime.now().strftime("%Y-%m-%d"), self.checklist_ym)
        else:
            if item.get("tx_id"):
                m_name = self._format_month_label(self.checklist_ym)
                ConfirmDialog(
                    self.winfo_toplevel(),
                    title="Desmarcar Gasto Fijo",
                    message=f"¿Deseas desmarcar '{item['description']}' como pagado para {m_name}?\n\nEsto eliminará el registro de gasto y restaurará tu saldo disponible.",
                    confirm_text="Desmarcar",
                    on_confirm=lambda: self._execute_unpay(item["tx_id"], item.get("currency", "COP")),
                    on_cancel=lambda: self._refresh_checklist()
                )
            else:
                self._refresh_checklist()

    def _execute_pay(self, item_id: int, date_str: str, target_month: str):
        success, msg, _ = self.controller.pay_recurring(item_id, date_str=date_str, target_month=target_month)
        self.toast.show(msg, is_error=not success)
        self.refresh_data()
        EventBus.publish("DATA_UPDATED")

    def _execute_unpay(self, tx_id: int, currency: str):
        success, msg = self.controller.unpay_recurring(tx_id, currency=currency)
        self.toast.show(msg, is_error=not success)
        self.refresh_data()
        EventBus.publish("DATA_UPDATED")

    # ==========================================
    # HISTORIAL DE EGRESOS
    # ==========================================

    def _refresh_history_feed(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        curr_filter = self.filter_curr_combo.get()
        pm_filter = self.filter_pm_combo.get()
        expenses = self.controller.get_expenses(limit=self.display_limit, currency_filter=curr_filter, payment_method_label=pm_filter)
        self.lbl_hist_count.configure(text=f"({len(expenses)} mostrados)")

        if not expenses:
            EmptyState(
                self.history_scroll,
                icon="💸",
                title="Sin egresos para mostrar",
                message="No se encontraron movimientos que coincidan con los filtros aplicados."
            ).pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_LG)
            return

        for exp in expenses:
            curr = exp["currency"]
            is_usd = (curr == "USD")
            amt = float(exp["amount"])
            amt_str = f"-${amt:,.2f} USD" if is_usd else f"-${amt:,.0f} COP"
            badge = "💵 USD" if is_usd else ("💳 TC" if exp.get("payment_method") == "CREDIT_CARD" else "🇨🇴 COP")
            source_tbl = "usd_transactions" if is_usd else "cop_transactions"

            card = ctk.CTkFrame(self.history_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=Theme.SPACING_SM, pady=(Theme.SPACING_SM, 2))

            ctk.CTkLabel(top, text=f"💸 {exp['category']} [{badge}]", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=amt_str, font=ctk.CTkFont(size=13, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(side="right")

            bottom = ctk.CTkFrame(card, fg_color="transparent")
            bottom.pack(fill="x", padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_SM))

            btn_box = ctk.CTkFrame(bottom, fg_color="transparent")
            btn_box.pack(side="right")

            info = f"{exp['date']}"
            if exp.get("notes"):
                info += f" • {exp['notes']}"

            ctk.CTkLabel(bottom, text=info, font=ctk.CTkFont(size=10), text_color=Theme.TEXT_MUTED, anchor="w").pack(side="left", fill="x", expand=True, padx=(0, Theme.SPACING_XS))


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
            btn_edit.pack(side="left", padx=Theme.SPACING_XS)

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
            btn_dup.pack(side="left", padx=Theme.SPACING_XS)

            btn_del = ctk.CTkButton(
                btn_box,
                text="🗑️",
                width=24,
                height=20,
                fg_color="transparent",
                hover_color=Theme.ERROR_HOVER,
                font=ctk.CTkFont(size=11),
                command=lambda r=exp, st=source_tbl: self._prompt_delete(r, st)
            )
            btn_del.pack(side="left", padx=Theme.SPACING_XS)

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
        success, msg, warn_data = self.controller.delete_expense(record_id, source_table, force=force)

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
        EventBus.publish("DATA_UPDATED")
