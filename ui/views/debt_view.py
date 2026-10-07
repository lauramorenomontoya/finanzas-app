"""
Vista Ejecutiva de Control de Deudas & Préstamos:
Centraliza el seguimiento de:
1. Deudas Personales / Terceros (con cálculo de abonos, saldo restante y amortización).
2. Deuda de Tarjeta de Crédito (integrada con CCPaymentModal).
3. Métricas consolidadas de pasivos y obligaciones financieras.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional, Dict, Any, List
from ui.theme import Theme
from ui.components.stat_card import StatCard
from ui.components.toast import ToastNotification
from ui.components.confirm_dialog import ConfirmDialog
from ui.components.add_debt_modal import AddDebtModal
from ui.components.debt_payment_modal import DebtPaymentModal
from ui.components.debt_history_modal import DebtHistoryModal
from ui.components.cc_payment_modal import CCPaymentModal
from ui.components.empty_state import EmptyState
from controllers.debt_controller import DebtController
from core.event_bus import EventBus


class DebtView(ctk.CTkFrame):
    def __init__(self, master, db_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = DebtController(db_manager)
        self.filter_status = "ALL"  # ALL, ACTIVE, PAID
        self.view_mode = "PAYABLE"   # PAYABLE, RECEIVABLE

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        self.toast = ToastNotification(self)

        # 1. Cabecera Principal
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_LG, Theme.SPACING_SM))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="💳 Control de Deudas & Préstamos",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Seguimiento unificado de deudas personales, cuentas por cobrar a terceros y tarjeta de crédito.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

        # Botones de Acción en Cabecera
        btn_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_box.pack(side="right")

        btn_cc_pay = ctk.CTkButton(
            btn_box,
            text="💳 Pagar Tarjeta",
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.ERROR,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12, weight="bold"),
            command=self._open_cc_payment_modal
        )
        btn_cc_pay.pack(side="left", padx=(0, Theme.SPACING_SM))

        btn_add_debt = ctk.CTkButton(
            btn_box,
            text="+ Nueva Deuda (Debo)",
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12, weight="bold"),
            command=lambda: self._open_add_debt_modal(initial_type="PAYABLE")
        )
        btn_add_debt.pack(side="left", padx=(0, Theme.SPACING_SM))

        btn_add_receivable = ctk.CTkButton(
            btn_box,
            text="+ Prestar / Por Cobrar",
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.ACCENT_BLUE,
            hover_color=Theme.INFO,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12, weight="bold"),
            command=lambda: self._open_add_debt_modal(initial_type="RECEIVABLE")
        )
        btn_add_receivable.pack(side="left")

        # 2. Tarjetas de Métricas Principales (Stat Cards)
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))
        cards_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        self.card_total_debt = StatCard(
            cards_container,
            title="Deuda Consolidada",
            value="$0 COP",
            subtitle="Obligación total por pagar",
            icon="🚨",
            accent_color=Theme.ACCENT_ROSE,
            bg_color=Theme.BG_CARD,
            border_color=Theme.ERROR
        )
        self.card_total_debt.grid(row=0, column=0, padx=(0, Theme.SPACING_SM), sticky="nsew")

        self.card_cc_debt = StatCard(
            cards_container,
            title="Tarjeta de Crédito",
            value="$0 COP",
            subtitle="Cupo utilizado a corte",
            icon="💳",
            accent_color="#f43f5e",
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_cc_debt.grid(row=0, column=1, padx=Theme.SPACING_XS, sticky="nsew")

        self.card_personal_debt = StatCard(
            cards_container,
            title="Mis Deudas (Debo)",
            value="$0 COP",
            subtitle="0 deudas activas",
            icon="🤝",
            accent_color="#f59e0b",
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_personal_debt.grid(row=0, column=2, padx=Theme.SPACING_XS, sticky="nsew")

        self.card_receivables = StatCard(
            cards_container,
            title="Por Cobrar (Me Deben)",
            value="$0 COP",
            subtitle="0 por cobrar",
            icon="📥",
            accent_color=Theme.ACCENT_GREEN,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_receivables.grid(row=0, column=3, padx=(Theme.SPACING_SM, 0), sticky="nsew")

        # 3. Contenedor Desplazable de Contenido
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))

        # Selector de Vista: Mis Deudas (Pasivos) vs Dinero que me deben (Por Cobrar)
        self.seg_view_mode = ctk.CTkSegmentedButton(
            self.scroll_area,
            values=["Mis Deudas (Pasivos)", "Dinero que me deben (Por Cobrar)"],
            height=34,
            corner_radius=Theme.SPACING_SM,
            command=self._on_view_mode_changed
        )
        self.seg_view_mode.set("Mis Deudas (Pasivos)")
        self.seg_view_mode.pack(fill="x", pady=(0, Theme.SPACING_MD))

        # Sección Tarjeta de Crédito
        self.cc_section = ctk.CTkFrame(self.scroll_area, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_DEFAULT)
        self.cc_section.pack(fill="x", pady=(0, Theme.SPACING_MD))

        # Sección Lista de Deudas / Cuentas por Cobrar
        self.personal_section = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.personal_section.pack(fill="both", expand=True)

    def _on_view_mode_changed(self, value: str):
        if value == "Dinero que me deben (Por Cobrar)":
            self.view_mode = "RECEIVABLE"
        else:
            self.view_mode = "PAYABLE"
        self.filter_status = "ALL"
        self.refresh_data()

    def refresh_data(self):
        """Actualiza todas las métricas, tarjetas y listas."""
        summary = self.controller.get_debts_summary()

        # Actualizar Stat Cards
        self.card_total_debt.set_value(f"${summary['grand_total_debt']:,.0f} COP")
        self.card_cc_debt.set_value(f"${summary['credit_card_debt']:,.0f} COP")
        self.card_personal_debt.set_value(f"${summary['personal_payable_remaining']:,.0f} COP")
        self.card_personal_debt.set_subtitle(f"{summary['active_debts_count']} activas pendientes")
        self.card_receivables.set_value(f"${summary['personal_receivable_remaining']:,.0f} COP")
        self.card_receivables.set_subtitle(f"{summary['active_receivables_count']} personas me deben")

        if self.view_mode == "PAYABLE":
            self.cc_section.pack(fill="x", pady=(0, Theme.SPACING_MD))
            self._render_cc_section(summary['credit_card_debt'])
        else:
            self.cc_section.pack_forget()

        self._render_debts_list()

    def _render_cc_section(self, cc_debt: float):
        """Dibuja el bloque informativo y de pago de la Tarjeta de Crédito."""
        for w in self.cc_section.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self.cc_section, fg_color="transparent")
        header.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(
            left,
            text="💳 Tarjeta de Crédito (Saldo al Corte)",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        status_desc = "Tienes deuda pendiente por pagar a fin de mes" if cc_debt > 0 else "Al día: No tienes deuda acumulada en tarjeta de crédito"
        ctk.CTkLabel(
            left,
            text=status_desc,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkLabel(
            right,
            text=f"${cc_debt:,.0f} COP",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=20, weight="bold"),
            text_color=Theme.ERROR if cc_debt > 0 else Theme.ACCENT_GREEN
        ).pack(side="left", padx=(0, Theme.SPACING_SM))

        btn_pay = ctk.CTkButton(
            right,
            text="Pagar Tarjeta",
            width=110,
            height=30,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.ERROR if cc_debt > 0 else Theme.BG_CARD_SUBTLE,
            hover_color=Theme.ERROR_HOVER if cc_debt > 0 else Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_ON_COLOR if cc_debt > 0 else Theme.TEXT_MUTED,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12, weight="bold"),
            state="normal" if cc_debt > 0 else "disabled",
            command=self._open_cc_payment_modal
        )
        btn_pay.pack(side="right")

    def _render_debts_list(self):
        """Dibuja la lista de deudas o cuentas por cobrar según el modo seleccionado."""
        for w in self.personal_section.winfo_children():
            w.destroy()

        is_receivable = self.view_mode == "RECEIVABLE"

        # Barra de Control de la sección
        ctrl_bar = ctk.CTkFrame(self.personal_section, fg_color="transparent")
        ctrl_bar.pack(fill="x", pady=(0, Theme.SPACING_SM))

        sec_title = "📥 Dinero que me deben (Cuentas por Cobrar a Terceros)" if is_receivable else "📋 Mis Deudas Personales (Pasivos por Pagar)"
        ctk.CTkLabel(
            ctrl_bar,
            text=sec_title,
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        # Filtro de estado
        filter_options = ["Todas", "Por Cobrar", "Cobradas"] if is_receivable else ["Todas", "Solo Activas", "Liquidadas"]
        self.seg_filter = ctk.CTkSegmentedButton(
            ctrl_bar,
            values=filter_options,
            height=28,
            corner_radius=Theme.SPACING_XS,
            command=self._on_filter_changed
        )
        if self.filter_status == "ALL":
            current_val = "Todas"
        elif self.filter_status == "ACTIVE":
            current_val = "Por Cobrar" if is_receivable else "Solo Activas"
        else:
            current_val = "Cobradas" if is_receivable else "Liquidadas"

        self.seg_filter.set(current_val)
        self.seg_filter.pack(side="right")

        # Consultar deudas según filtro y modo de vista
        status_param = None if self.filter_status == "ALL" else self.filter_status
        debts = self.controller.get_debts(status=status_param, debt_type=self.view_mode)

        if not debts:
            empty_title = (
                "No tienes préstamos por cobrar registrados"
                if is_receivable else
                "No tienes deudas registradas"
            )
            empty_msg = (
                "Registra préstamos o compras hechas para terceros para controlar tus cobros."
                if is_receivable else
                "Registra compromisos u obligaciones pendientes para planificar su pago."
            )
            cta_text = "+ Prestar / Por Cobrar" if is_receivable else "+ Nueva Deuda (Debo)"
            cta_cmd = (
                (lambda: self._open_add_debt_modal(initial_type="RECEIVABLE"))
                if is_receivable else
                (lambda: self._open_add_debt_modal(initial_type="PAYABLE"))
            )
            EmptyState(
                self.personal_section,
                icon="📥" if is_receivable else "🤝",
                title=empty_title,
                message=empty_msg,
                action_text=cta_text,
                action_command=cta_cmd,
                action_variant="primary" if is_receivable else "destructive"
            ).pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_LG)
            return

        for d in debts:
            self._build_debt_card(d)

    def _build_debt_card(self, debt: Dict[str, Any]):
        """Construye la tarjeta visual para cada deuda personal o cuenta por cobrar."""
        card = ctk.CTkFrame(self.personal_section, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_DEFAULT)
        card.pack(fill="x", pady=Theme.SPACING_XS)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=Theme.SPACING_MD, pady=Theme.SPACING_MD)

        is_receivable = debt.get("debt_type") == "RECEIVABLE"
        is_paid = debt["status"] == "PAID"

        # Fila Superior: Nombre, Estado y Botones de Acción
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, Theme.SPACING_SM))

        title_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        title_frame.pack(side="left")

        icon = "📥" if is_receivable else "🤝"
        ctk.CTkLabel(
            title_frame,
            text=f"{icon} {debt['creditor']}",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        # Badge de Estado
        if is_receivable:
            badge_text = "COBRADO COMPLETO 🎉" if is_paid else "POR COBRAR"
        else:
            badge_text = "LIQUIDADA 🎉" if is_paid else "ACTIVA"

        badge_color = Theme.ACCENT_GREEN if is_paid else "#f59e0b"
        badge_bg = Theme.COP_BANNER_BG if is_paid else ("#fef3c7", "#78350f")

        badge = ctk.CTkLabel(
            title_frame,
            text=f"  {badge_text}  ",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=10, weight="bold"),
            text_color=badge_color,
            fg_color=badge_bg,
            corner_radius=Theme.SPACING_XS,
            pady=Theme.SPACING_XS
        )
        badge.pack(side="left", padx=Theme.SPACING_SM)

        # Botones de Acción a la derecha
        actions_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        actions_frame.pack(side="right")

        if not is_paid:
            btn_action_text = "💵 Registrar Pago" if is_receivable else "💰 Abonar"
            btn_action_color = Theme.ACCENT_BLUE if is_receivable else Theme.ACCENT_GREEN
            btn_hover_color = "#0284c7" if is_receivable else "#059669"
            btn_pay = ctk.CTkButton(
                actions_frame,
                text=btn_action_text,
                width=115 if is_receivable else 80,
                height=28,
                corner_radius=Theme.SPACING_XS,
                fg_color=btn_action_color,
                hover_color=btn_hover_color,
                text_color=Theme.TEXT_ON_COLOR,
                font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
                command=lambda d=debt: self._open_payment_modal(d)
            )
            btn_pay.pack(side="left", padx=Theme.SPACING_XS)

        hist_label = f"📜 Pagos ({debt['payments_count']})" if is_receivable else f"📜 Abonos ({debt['payments_count']})"
        btn_history = ctk.CTkButton(
            actions_frame,
            text=hist_label,
            width=95,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11),
            command=lambda did=debt['id']: self._open_history_modal(did)
        )
        btn_history.pack(side="left", padx=Theme.SPACING_XS)

        btn_edit = ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=30,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color="transparent",
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_SECONDARY,
            command=lambda d=debt: self._open_add_debt_modal(d)
        )
        btn_edit.pack(side="left", padx=Theme.SPACING_XS)

        btn_delete = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=30,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color="transparent",
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_ROSE,
            command=lambda did=debt['id'], name=debt['creditor']: self._confirm_delete_debt(did, name)
        )
        btn_delete.pack(side="left", padx=Theme.SPACING_XS)

        # Fila Central: Métricas Numéricas
        mid_row = ctk.CTkFrame(inner, fg_color="transparent")
        mid_row.pack(fill="x", pady=(2, Theme.SPACING_XS))

        lbl_total = "Total Prestado" if is_receivable else "Total"
        lbl_paid = "Cobrado" if is_receivable else "Abonado"
        lbl_remaining = "Pendiente por Cobrar" if is_receivable else "Saldo Restante"

        ctk.CTkLabel(
            mid_row,
            text=f"{lbl_total}: ${debt['total_amount']:,.0f} {debt['currency']}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(side="left")

        ctk.CTkLabel(
            mid_row,
            text=f"{lbl_paid}: ${debt['total_paid']:,.0f} ({debt['percent_paid']}%)",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13, weight="bold"),
            text_color=Theme.ACCENT_GREEN
        ).pack(side="left", padx=Theme.SPACING_MD)

        ctk.CTkLabel(
            mid_row,
            text=f"{lbl_remaining}: ${debt['remaining_amount']:,.0f} {debt['currency']}",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.ACCENT_ROSE if not is_paid else Theme.TEXT_MUTED
        ).pack(side="right")

        # Barra de Progreso
        pct = debt["percent_paid"] / 100.0
        pbar = ctk.CTkProgressBar(inner, height=8, corner_radius=Theme.SPACING_XS)
        pbar.pack(fill="x", pady=(2, Theme.SPACING_XS))
        pbar.set(pct)
        if pct >= 1.0:
            pbar.configure(progress_color=Theme.ACCENT_GREEN)
        elif pct >= 0.5:
            pbar.configure(progress_color=Theme.ACCENT_BLUE)
        else:
            pbar.configure(progress_color=Theme.WARNING)

        # Fila Inferior: Detalles de fecha y notas
        bot_row = ctk.CTkFrame(inner, fg_color="transparent")
        bot_row.pack(fill="x")

        date_label = "📅 Prestado" if is_receivable else "📅 Adquirida"
        date_text = f"{date_label}: {debt['start_date']}"
        if debt["due_date"]:
            date_text += f"  |  ⏰ Límite: {debt['due_date']}"
        if debt["last_payment_date"]:
            last_word = "Último cobro" if is_receivable else "Último abono"
            date_text += f"  |  {last_word}: {debt['last_payment_date']}"

        ctk.CTkLabel(
            bot_row,
            text=date_text,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11),
            text_color=Theme.TEXT_MUTED
        ).pack(side="left")

        if debt["notes"]:
            ctk.CTkLabel(
                bot_row,
                text=f"📝 {debt['notes']}",
                font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, slant="italic"),
                text_color=Theme.TEXT_SECONDARY
            ).pack(side="right")

    def _on_filter_changed(self, value: str):
        if value in ("Solo Activas", "Por Cobrar"):
            self.filter_status = "ACTIVE"
        elif value in ("Liquidadas", "Cobradas"):
            self.filter_status = "PAID"
        else:
            self.filter_status = "ALL"
        self._render_debts_list()

    def _open_add_debt_modal(self, debt: Optional[Dict[str, Any]] = None, initial_type: Optional[str] = None):
        def on_saved():
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")
            self.toast.show("¡Registro guardado correctamente!")

        init_t = initial_type or self.view_mode
        AddDebtModal(self.winfo_toplevel(), self.controller.db, debt=debt, initial_type=init_t, on_success=on_saved)

    def _open_payment_modal(self, debt: Dict[str, Any]):
        def on_paid():
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")
            action_desc = "Pago recibido" if debt.get("debt_type") == "RECEIVABLE" else "Abono"
            self.toast.show(f"¡{action_desc} de {debt['creditor']} registrado!")

        DebtPaymentModal(self.winfo_toplevel(), self.controller.db, debt=debt, on_success=on_paid)

    def _open_history_modal(self, debt_id: int):
        def on_changed():
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")

        DebtHistoryModal(self.winfo_toplevel(), self.controller.db, debt_id=debt_id, on_data_changed=on_changed)

    def _open_cc_payment_modal(self):
        def on_cc_paid():
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")
            self.toast.show("¡Pago de Tarjeta de Crédito registrado!")

        CCPaymentModal(self.winfo_toplevel(), self.controller.db, on_success=on_cc_paid)

    def _confirm_delete_debt(self, debt_id: int, creditor: str):
        def on_confirmed():
            success = self.controller.delete_debt(debt_id)
            if success:
                self.refresh_data()
                EventBus.publish("DATA_UPDATED")
                self.toast.show(f"Registro de {creditor} eliminado.")

        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar Registro",
            message=f"¿Estás seguro de eliminar el registro de {creditor}?\nEsta acción eliminará también el historial de abonos o pagos asociados.",
            on_confirm=on_confirmed
        )
