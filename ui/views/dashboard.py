"""
Vista Principal (Dashboard) para Control Financiero.
Muestra el estado global de la Bóveda USD, el Presupuesto COP, Deuda de Tarjeta de Crédito,
Inversiones, desglose de gastos y feed de movimientos recientes.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional
from ui.components.stat_card import StatCard
from ui.components.cc_payment_modal import CCPaymentModal
from ui.components.csv_importer_modal import CSVImporterModal
from ui.theme import Theme


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, db_manager, navigate_to: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.navigate_to = navigate_to

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # 1. Cabecera del Dashboard
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 14))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Panel Financiero Principal",
            font=ctk.CTkFont(family="SF Pro Display", size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        current_date_str = datetime.now().strftime("%B %Y").capitalize()
        ctk.CTkLabel(
            title_box,
            text=f"Resumen general y métricas de {current_date_str}",
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Botón CSV en la cabecera
        btn_csv = ctk.CTkButton(
            header_frame,
            text="📄 Importar CSV",
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_csv_importer
        )
        btn_csv.pack(side="right")

        # 2. Fila de Tarjetas de Métricas Principales (Stat Cards)
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="x", padx=24, pady=(0, 16))
        cards_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        # Tarjeta 1: Bóveda USD (Ahorro Intocable)
        self.card_usd = StatCard(
            cards_container,
            title="Bóveda USD",
            value="$0.00 USD",
            subtitle="Fondo de ahorro intocable",
            icon="🏦",
            accent_color=Theme.ACCENT_BLUE,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_usd.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        # Tarjeta 2: Presupuesto Disponible COP
        self.card_cop = StatCard(
            cards_container,
            title="Disponible COP",
            value="$0 COP",
            subtitle="Liquidez en cuenta",
            icon="💳",
            accent_color=Theme.ACCENT_GREEN,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_cop.grid(row=0, column=1, padx=4, sticky="nsew")

        # Tarjeta 3: Deudas Totales (TC + Personales)
        self.card_cc_debt = StatCard(
            cards_container,
            title="Deudas Totales",
            value="$0 COP",
            subtitle="TC y deudas personales",
            icon="💳",
            accent_color=Theme.ACCENT_ROSE,
            bg_color=Theme.BG_CARD,
            border_color="#e11d48"
        )
        self.card_cc_debt.grid(row=0, column=2, padx=4, sticky="nsew")
        self.card_cc_debt.bind("<Button-1>", lambda _: self._navigate("debts"))

        # Tarjeta 4: Gastos del Mes COP
        self.card_expenses = StatCard(
            cards_container,
            title="Gastos del Mes",
            value="$0 COP",
            subtitle="Gastos en pesos",
            icon="📉",
            accent_color=Theme.ACCENT_ROSE,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_expenses.grid(row=0, column=3, padx=(8, 0), sticky="nsew")

        # 3. Contenedor de Dos Columnas (Distribución de Gastos + Movimientos Recientes)
        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        content_grid.grid_columnconfigure(0, weight=1, uniform="content_cols")
        content_grid.grid_columnconfigure(1, weight=1, uniform="content_cols")
        content_grid.grid_rowconfigure(0, weight=1)

        # Columna Izquierda: Desglose y Acciones Rápidas
        left_col = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        left_header = ctk.CTkFrame(left_col, fg_color="transparent")
        left_header.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            left_header,
            text="📊 Gastos por Categoría (Mes Actual)",
            font=ctk.CTkFont(family="SF Pro Display", size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        btn_go_budget = ctk.CTkButton(
            left_header,
            text="🎯 Presupuestos",
            width=100,
            height=26,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_GREEN,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._trigger_nav("budget")
        )
        btn_go_budget.pack(side="right")

        # Área con scroll para el desglose de categorías
        self.categories_scroll = ctk.CTkScrollableFrame(left_col, fg_color="transparent", height=180)
        self.categories_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        # Accesos Rápidos
        quick_actions_box = ctk.CTkFrame(left_col, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        quick_actions_box.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(
            quick_actions_box,
            text="⚡ Acciones Rápidas",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=12, pady=(8, 6))

        # Fila 1 de Acciones Rápidas
        actions_btn_frame1 = ctk.CTkFrame(quick_actions_box, fg_color="transparent")
        actions_btn_frame1.pack(fill="x", padx=10, pady=(0, 6))
        actions_btn_frame1.grid_columnconfigure((0, 1, 2), weight=1)

        btn_deposit = ctk.CTkButton(
            actions_btn_frame1,
            text="📥 + Ingreso",
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            command=lambda: self._trigger_nav("incomes")
        )
        btn_deposit.grid(row=0, column=0, padx=3, sticky="ew")

        btn_convert = ctk.CTkButton(
            actions_btn_frame1,
            text="🔄 Puente USD->COP",
            fg_color="#6366f1",
            hover_color="#4f46e5",
            text_color="#ffffff",
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            command=lambda: self._trigger_nav("conversion")
        )
        btn_convert.grid(row=0, column=1, padx=3, sticky="ew")

        btn_expense = ctk.CTkButton(
            actions_btn_frame1,
            text="💸 - Egreso",
            fg_color="#e11d48",
            hover_color="#be123c",
            text_color="#ffffff",
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            command=lambda: self._trigger_nav("expenses")
        )
        btn_expense.grid(row=0, column=2, padx=3, sticky="ew")

        # Fila 2 de Acciones Rápidas (Inversiones, Pagar TC, Libro Mayor)
        actions_btn_frame2 = ctk.CTkFrame(quick_actions_box, fg_color="transparent")
        actions_btn_frame2.pack(fill="x", padx=10, pady=(0, 8))
        actions_btn_frame2.grid_columnconfigure((0, 1, 2), weight=1)

        btn_ledger = ctk.CTkButton(
            actions_btn_frame2,
            text="📖 Libro Mayor",
            fg_color="#334155",
            hover_color="#475569",
            text_color="#38bdf8",
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            command=lambda: self._trigger_nav("ledger")
        )
        btn_ledger.grid(row=0, column=0, padx=3, sticky="ew")

        btn_pay_cc = ctk.CTkButton(
            actions_btn_frame2,
            text="💳 Pagar TC",
            fg_color="#059669",
            hover_color="#047857",
            text_color="#ffffff",
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            command=self._open_cc_payment
        )
        btn_pay_cc.grid(row=0, column=1, padx=3, sticky="ew")

        btn_inv = ctk.CTkButton(
            actions_btn_frame2,
            text="📈 Inversiones",
            fg_color="#0f766e",
            hover_color="#115e59",
            text_color="#ffffff",
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            command=lambda: self._trigger_nav("investments")
        )
        btn_inv.grid(row=0, column=2, padx=3, sticky="ew")

        # Columna Derecha: Feed de Últimos Movimientos
        right_col = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        right_header = ctk.CTkFrame(right_col, fg_color="transparent")
        right_header.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            right_header,
            text="🕒 Últimos Movimientos",
            font=ctk.CTkFont(family="SF Pro Display", size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        btn_refresh = ctk.CTkButton(
            right_header,
            text="Actualizar",
            width=75,
            height=26,
            fg_color=Theme.BORDER_DEFAULT,
            hover_color=Theme.TEXT_MUTED,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11),
            corner_radius=6,
            command=self.refresh_data
        )
        btn_refresh.pack(side="right")

        self.activities_scroll = ctk.CTkScrollableFrame(right_col, fg_color="transparent")
        self.activities_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 16))

    def _trigger_nav(self, route: str):
        if self.navigate_to:
            self.navigate_to(route)

    def _open_cc_payment(self):
        CCPaymentModal(
            self.winfo_toplevel(),
            self.db,
            on_success=self.refresh_data
        )

    def _open_csv_importer(self):
        CSVImporterModal(
            self.winfo_toplevel(),
            self.db,
            on_success=self.refresh_data
        )

    def refresh_data(self):
        """Actualiza todas las métricas, tarjetas y listas del dashboard."""
        usd_balance = self.db.get_usd_balance()
        cop_balance = self.db.get_cop_balance()
        metrics = self.db.get_monthly_metrics()
        cc_debt = self.db.get_credit_card_debt()

        # Actualizar Tarjetas
        self.card_usd.update_value(
            f"${usd_balance:,.2f} USD",
            f"Total ahorrado: ${self.db.get_usd_total_saved_all_time():,.2f} USD"
        )
        self.card_cop.update_value(
            f"${cop_balance:,.0f} COP",
            "Disponible en cuenta"
        )
        debts_summary = self.db.get_debts_summary()
        grand_debt = debts_summary["grand_total_debt"]
        if grand_debt == 0:
            debt_sub = "Sin deudas pendientes 🎉"
        elif debts_summary["personal_remaining"] > 0 and debts_summary["credit_card_debt"] > 0:
            debt_sub = f"TC: ${debts_summary['credit_card_debt']:,.0f} | Papá/Pers: ${debts_summary['personal_remaining']:,.0f}"
        elif debts_summary["personal_remaining"] > 0:
            debt_sub = f"{debts_summary['active_debts_count']} deuda(s) personal(es)"
        else:
            debt_sub = "Tarjeta de crédito por pagar"

        self.card_cc_debt.update_value(
            f"${grand_debt:,.0f} COP",
            debt_sub
        )
        self.card_expenses.update_value(
            f"${metrics['cop_total_expenses']:,.0f} COP",
            f"Débito: ${metrics['cop_cash_debit_expenses']:,.0f} | TC: ${metrics['cop_cc_expenses']:,.0f}"
        )

        # Actualizar Desglose de Gastos
        self._refresh_categories_breakdown(metrics['cop_total_expenses'])

        # Actualizar Feed de Movimientos Recientes
        self._refresh_activities_feed()

    def _refresh_categories_breakdown(self, total_expenses: float):
        for widget in self.categories_scroll.winfo_children():
            widget.destroy()

        categories = self.db.get_expenses_by_category()
        budgets_map = {b["category"]: b["budget"] for b in self.db.get_category_budgets()}

        if not categories:
            empty_lbl = ctk.CTkLabel(
                self.categories_scroll,
                text="No hay gastos registrados este mes 🎉",
                font=ctk.CTkFont(size=12),
                text_color="#64748b"
            )
            empty_lbl.pack(pady=30)
            return

        for item in categories:
            cat_name = item["category"]
            amount = item["total"]
            count = item["count"]
            b_amt = budgets_map.get(cat_name, 0.0)

            if b_amt > 0:
                pct = (amount / b_amt * 100.0)
                if pct >= 100:
                    bar_color = "#f43f5e"
                elif pct >= 75:
                    bar_color = "#f59e0b"
                else:
                    bar_color = "#10b981"
                text_label = f"${amount:,.0f} / ${b_amt:,.0f} ({pct:.0f}%)"
                val_color = bar_color
                bar_ratio = min(pct / 100.0, 1.0)
            else:
                pct = (amount / total_expenses * 100) if total_expenses > 0 else 0
                bar_color = "#64748b"
                text_label = f"${amount:,.0f} COP"
                val_color = Theme.TEXT_SECONDARY
                bar_ratio = min(pct / 100.0, 1.0)

            item_card = ctk.CTkFrame(self.categories_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
            item_card.pack(fill="x", pady=4, padx=2)

            top_row = ctk.CTkFrame(item_card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 4))

            ctk.CTkLabel(
                top_row,
                text=f"{cat_name} ({count})",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(side="left")

            ctk.CTkLabel(
                top_row,
                text=text_label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=val_color
            ).pack(side="right")

            # Barra de progreso visual
            progress = ctk.CTkProgressBar(item_card, height=6, corner_radius=3, fg_color=Theme.BORDER_SUBTLE, progress_color=bar_color)
            progress.pack(fill="x", padx=10, pady=(0, 8))
            progress.set(bar_ratio)

    def _refresh_activities_feed(self):
        for widget in self.activities_scroll.winfo_children():
            widget.destroy()

        activities = self.db.get_recent_activities(limit=8)
        if not activities:
            empty_lbl = ctk.CTkLabel(
                self.activities_scroll,
                text="Aún no hay movimientos registrados.\n¡Usa las acciones rápidas para comenzar!",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED,
                justify="center"
            )
            empty_lbl.pack(pady=40)
            return

        for act in activities:
            card = ctk.CTkFrame(self.activities_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=4, padx=2)

            # Estilo según tipo
            if act["color_type"] == "income_usd":
                badge_icon = "💵"
                amount_color = Theme.ACCENT_BLUE
            elif act["color_type"] == "expense_cop":
                badge_icon = "📉"
                amount_color = Theme.ACCENT_ROSE
            elif act["color_type"] == "cc_payment":
                badge_icon = "💳"
                amount_color = Theme.ACCENT_INDIGO
            elif act["color_type"] == "yield_income":
                badge_icon = "📈"
                amount_color = Theme.ACCENT_GREEN
            elif act["color_type"] == "investment_out":
                badge_icon = "🏦"
                amount_color = Theme.ACCENT_BLUE
            else:  # transfer_cop
                badge_icon = "🔄"
                amount_color = Theme.ACCENT_GREEN

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(8, 2))

            icon_lbl = ctk.CTkLabel(top_row, text=badge_icon, font=ctk.CTkFont(size=14))
            icon_lbl.pack(side="left", padx=(0, 6))

            title_lbl = ctk.CTkLabel(
                top_row,
                text=act["title"],
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            )
            title_lbl.pack(side="left")

            amount_lbl = ctk.CTkLabel(
                top_row,
                text=act["amount_str"],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=amount_color
            )
            amount_lbl.pack(side="right")

            # Fila inferior: Fecha y notas
            bottom_row = ctk.CTkFrame(card, fg_color="transparent")
            bottom_row.pack(fill="x", padx=12, pady=(0, 8))

            date_lbl = ctk.CTkLabel(
                bottom_row,
                text=f"{act['date']} • {act['source']}",
                font=ctk.CTkFont(size=10),
                text_color=Theme.TEXT_MUTED
            )
            date_lbl.pack(side="left")

            if act["notes"]:
                notes_lbl = ctk.CTkLabel(
                    bottom_row,
                    text=f"\"{act['notes']}\"",
                    font=ctk.CTkFont(size=10, slant="italic"),
                    text_color="#94a3b8"
                )
                notes_lbl.pack(side="right")
