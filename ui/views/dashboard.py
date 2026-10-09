"""
Vista Principal (Dashboard) para Montu.
Muestra el estado global de la Bóveda USD, el Presupuesto COP, Deuda de Tarjeta de Crédito,
Inversiones, desglose de gastos y feed de movimientos recientes.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional
from ui.components.stat_card import StatCard
from ui.components.cc_payment_modal import CCPaymentModal
from ui.components.csv_importer_modal import CSVImporterModal
from ui.components.empty_state import EmptyState
from ui.theme import Theme
from services.currency_service import CurrencyService
from controllers.dashboard_controller import DashboardController


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, db_manager, navigate_to: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.controller = DashboardController(db_manager)
        self.navigate_to = navigate_to
        self.exchange_rate = self.controller.get_latest_exchange_rate()
        self.show_banner_details = False

        self._build_ui()
        self.refresh_data()
        self._fetch_rate_on_start()

    def _build_ui(self):
        # 1. Cabecera del Dashboard
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Panel Financiero Principal",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        current_date_str = datetime.now().strftime("%B %Y").capitalize()
        ctk.CTkLabel(
            title_box,
            text=f"Resumen general y métricas de {current_date_str}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Botón CSV en la cabecera
        btn_csv = ctk.CTkButton(
            header_frame,
            text="📄 Importar CSV",
            height=32,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_csv_importer
        )
        btn_csv.pack(side="right")

        # Badge de Tasa de Referencia TRM / Retiro en la cabecera
        self.trm_badge = ctk.CTkFrame(
            header_frame,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.SPACING_SM,
            border_width=1,
            border_color=Theme.BORDER_DEFAULT
        )
        self.trm_badge.pack(side="right", padx=(0, Theme.SPACING_SM))

        self.lbl_trm_info = ctk.CTkLabel(
            self.trm_badge,
            text=f"💵 TRM Oficial: 1 USD ≈ ${self.exchange_rate:,.2f} COP",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.ACCENT_BLUE
        )
        self.lbl_trm_info.pack(padx=Theme.SPACING_SM, pady=Theme.SPACING_XS)

        # 2. Gran Banner de Salud Financiera & Balance Real del Mes (Consolidado COP + USD)
        self.health_banner = ctk.CTkFrame(
            self,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.SPACING_MD,
            border_width=1,
            border_color=Theme.BORDER_DEFAULT
        )
        self.health_banner.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))

        banner_top = ctk.CTkFrame(self.health_banner, fg_color="transparent")
        banner_top.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_SM, Theme.SPACING_XS))

        self.lbl_banner_title = ctk.CTkLabel(
            banner_top,
            text="🌟 SALUD FINANCIERA & BALANCE REAL DEL MES (COP + USD)",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            text_color=Theme.ACCENT_BLUE
        )
        self.lbl_banner_title.pack(side="left")

        top_right_box = ctk.CTkFrame(banner_top, fg_color="transparent")
        top_right_box.pack(side="right")

        self.btn_toggle_details = ctk.CTkButton(
            top_right_box,
            text="Ver desglose ▼",
            width=100,
            height=24,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._toggle_banner_details
        )
        self.btn_toggle_details.pack(side="right", padx=(Theme.SPACING_SM, 0))

        self.badge_status = ctk.CTkLabel(
            top_right_box,
            text="🟢 SUPERÁVIT DEL MES",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=Theme.SUCCESS,
            text_color=Theme.TEXT_ON_COLOR,
            corner_radius=Theme.SPACING_XS,
            padx=Theme.SPACING_SM,
            pady=Theme.SPACING_XS
        )
        self.badge_status.pack(side="right")

        # Fila intermedia: Dos KPIs principales (Resultado Neto Consolidado y Liquidez Real Inmediata)
        kpi_row = ctk.CTkFrame(self.health_banner, fg_color="transparent")
        kpi_row.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))
        kpi_row.grid_columnconfigure((0, 1), weight=1, uniform="kpi_cols")

        # Columna 1: Resultado Neto del Mes
        col_net = ctk.CTkFrame(kpi_row, fg_color="transparent")
        col_net.grid(row=0, column=0, sticky="w", padx=(0, Theme.SPACING_SM))

        ctk.CTkLabel(
            col_net,
            text="Resultado Neto Real del Mes (Ingresos - Gastos):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self.lbl_net_result = ctk.CTkLabel(
            col_net,
            text="+$0 COP",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=26, weight="bold"),
            text_color=Theme.SUCCESS
        )
        self.lbl_net_result.pack(anchor="w", pady=(2, 2))

        self.lbl_net_desc = ctk.CTkLabel(
            col_net,
            text="Ingresos reales generados superaron los gastos.",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_net_desc.pack(anchor="w")

        # Columna 2: Liquidez Inmediata Consolidada
        col_liq = ctk.CTkFrame(kpi_row, fg_color="transparent")
        col_liq.grid(row=0, column=1, sticky="w", padx=(Theme.SPACING_SM, 0))

        ctk.CTkLabel(
            col_liq,
            text="💧 Liquidez Inmediata Total (Bancolombia + Wenia disponible):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self.lbl_real_liquidity = ctk.CTkLabel(
            col_liq,
            text="+$0 COP",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=26, weight="bold"),
            text_color=Theme.INFO
        )
        self.lbl_real_liquidity.pack(anchor="w", pady=(2, 2))

        self.lbl_liq_desc = ctk.CTkLabel(
            col_liq,
            text="Dinero líquido listo para usar sin tocar inversiones.",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_liq_desc.pack(anchor="w")

        # Franja inferior: Comparativa de Ingresos vs Gastos (Expandible)
        self.bottom_strip = ctk.CTkFrame(
            self.health_banner,
            fg_color=Theme.BG_CARD_SUBTLE,
            corner_radius=Theme.SPACING_SM,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE
        )
        # Inicialmente oculta para no sobrecargar el banner

        self.lbl_summary_details = ctk.CTkLabel(
            self.bottom_strip,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_SECONDARY,
            justify="left"
        )
        self.lbl_summary_details.pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_SM)

        # 3. Fila de Tarjetas de Métricas Principales (Stat Cards)
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))
        cards_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        # Tarjeta 1: Bóveda USD
        self.card_usd = StatCard(
            cards_container,
            title="Bóveda USD",
            value="$0.00 USD",
            subtitle="Liquidez en Wenia",
            icon="🏦",
            accent_color=Theme.ACCENT_BLUE,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_usd.grid(row=0, column=0, padx=(0, Theme.SPACING_SM), sticky="nsew")

        # Tarjeta 2: Disponible COP
        self.card_cop = StatCard(
            cards_container,
            title="Disponible Bancolombia",
            value="$0 COP",
            subtitle="Saldo en cuenta corriente/ahorros",
            icon="💳",
            accent_color=Theme.ACCENT_GREEN,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_cop.grid(row=0, column=1, padx=Theme.SPACING_XS, sticky="nsew")

        # Tarjeta 3: Deudas Totales
        self.card_cc_debt = StatCard(
            cards_container,
            title="Deudas Totales",
            value="$0 COP",
            subtitle="TC y compromisos",
            icon="🤝",
            accent_color=Theme.ACCENT_ROSE,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_cc_debt.grid(row=0, column=2, padx=Theme.SPACING_XS, sticky="nsew")
        self.card_cc_debt.bind("<Button-1>", lambda _: self._trigger_nav("debts"))

        # Tarjeta 4: Gastos del Mes COP
        self.card_expenses = StatCard(
            cards_container,
            title="Gastos del Mes",
            value="$0 COP",
            subtitle="Egresos en pesos",
            icon="📉",
            accent_color=Theme.ACCENT_ROSE,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_expenses.grid(row=0, column=3, padx=(Theme.SPACING_SM, 0), sticky="nsew")

        # 4. Contenedor de Dos Columnas (Distribución de Gastos + Movimientos Recientes)
        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))
        content_grid.grid_columnconfigure(0, weight=1, uniform="content_cols")
        content_grid.grid_columnconfigure(1, weight=1, uniform="content_cols")
        content_grid.grid_rowconfigure(0, weight=1)

        # Columna Izquierda: Desglose y Acciones Rápidas
        left_col = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, Theme.SPACING_SM))

        left_header = ctk.CTkFrame(left_col, fg_color="transparent")
        left_header.pack(side="top", fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_SM, Theme.SPACING_XS))

        ctk.CTkLabel(
            left_header,
            text="📊 Gastos por Categoría (Mes Actual)",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        btn_go_budget = ctk.CTkButton(
            left_header,
            text="🎯 Presupuestos",
            width=95,
            height=24,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_GREEN,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._trigger_nav("budget")
        )
        btn_go_budget.pack(side="right")

        # Accesos Rápidos: Empaquetados en la parte inferior para reservar siempre su altura completa
        quick_actions_box = ctk.CTkFrame(left_col, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        quick_actions_box.pack(side="bottom", fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        ctk.CTkLabel(
            quick_actions_box,
            text="⚡ Acciones Rápidas",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=Theme.SPACING_SM, pady=(Theme.SPACING_SM, Theme.SPACING_XS))

        # Rejilla Unificada: 3 columnas perfectamente idénticas en ancho y altura
        actions_grid = ctk.CTkFrame(quick_actions_box, fg_color="transparent")
        actions_grid.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))
        actions_grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="quick_actions")
        actions_grid.grid_rowconfigure((0, 1), weight=1)

        # Fila 0: Entradas y Salidas Operativas
        btn_deposit = ctk.CTkButton(
            actions_grid,
            text="📥 + Ingreso",
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            height=32,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            corner_radius=Theme.SPACING_SM,
            command=lambda: self._trigger_nav("incomes")
        )
        btn_deposit.grid(row=0, column=0, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS, sticky="nsew")

        btn_convert = ctk.CTkButton(
            actions_grid,
            text="🔄 Puente USD",
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            height=32,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            corner_radius=Theme.SPACING_SM,
            command=lambda: self._trigger_nav("conversion")
        )
        btn_convert.grid(row=0, column=1, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS, sticky="nsew")

        btn_expense = ctk.CTkButton(
            actions_grid,
            text="💸 - Egreso",
            fg_color=Theme.ERROR,
            hover_color=Theme.ERROR_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            height=32,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            corner_radius=Theme.SPACING_SM,
            command=lambda: self._trigger_nav("expenses")
        )
        btn_expense.grid(row=0, column=2, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS, sticky="nsew")

        # Fila 1: Compromisos y Navegación
        btn_pay_cc = ctk.CTkButton(
            actions_grid,
            text="💳 Pagar TC",
            fg_color=Theme.ERROR,
            hover_color=Theme.ERROR_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            height=32,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            corner_radius=Theme.SPACING_SM,
            command=self._open_cc_payment
        )
        btn_pay_cc.grid(row=1, column=0, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS, sticky="nsew")

        btn_ledger = ctk.CTkButton(
            actions_grid,
            text="📖 Libro Mayor",
            fg_color=("#cbd5e1", "#334155"),
            hover_color=("#94a3b8", "#475569"),
            text_color=("#0f172a", "#f8fafc"),
            height=32,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            corner_radius=Theme.SPACING_SM,
            command=lambda: self._trigger_nav("ledger")
        )
        btn_ledger.grid(row=1, column=1, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS, sticky="nsew")

        btn_inv = ctk.CTkButton(
            actions_grid,
            text="📈 Inversiones",
            fg_color=("#cbd5e1", "#334155"),
            hover_color=("#94a3b8", "#475569"),
            text_color=("#0f172a", "#f8fafc"),
            height=32,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            corner_radius=Theme.SPACING_SM,
            command=lambda: self._trigger_nav("investments")
        )
        btn_inv.grid(row=1, column=2, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS, sticky="nsew")

        # Área con scroll para el desglose de categorías (toma todo el espacio restante disponible)
        self.categories_scroll = ctk.CTkScrollableFrame(left_col, fg_color="transparent")
        self.categories_scroll.pack(side="top", fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Columna Derecha: Feed de Últimos Movimientos
        right_col = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(Theme.SPACING_SM, 0))

        right_header = ctk.CTkFrame(right_col, fg_color="transparent")
        right_header.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_SM, Theme.SPACING_XS))

        ctk.CTkLabel(
            right_header,
            text="🕒 Últimos Movimientos",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        btn_refresh = ctk.CTkButton(
            right_header,
            text="Actualizar",
            width=75,
            height=24,
            fg_color=Theme.BORDER_DEFAULT,
            hover_color=Theme.TEXT_MUTED,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11),
            corner_radius=Theme.SPACING_XS,
            command=self.refresh_data
        )
        btn_refresh.pack(side="right")

        self.activities_scroll = ctk.CTkScrollableFrame(right_col, fg_color="transparent")
        self.activities_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

    def _toggle_banner_details(self):
        """Alterna la visibilidad del desglose detallado en el banner de salud financiera."""
        self.show_banner_details = not self.show_banner_details
        if self.show_banner_details:
            self.bottom_strip.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))
            self.btn_toggle_details.configure(text="Ocultar ▲")
        else:
            self.bottom_strip.pack_forget()
            self.btn_toggle_details.configure(text="Ver desglose ▼")

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

    def _fetch_rate_on_start(self):
        """Consulta la tasa oficial en segundo plano y actualiza el dashboard suavemente sin destruir widgets."""
        def _on_rate(rate):
            if rate and rate > 0:
                self.controller.save_exchange_rate(rate)
                if abs(rate - self.exchange_rate) > 0.01:
                    try:
                        self.after(0, lambda: self._update_rates_and_banner(rate))
                    except Exception:
                        pass
        CurrencyService.fetch_rate_async(_on_rate)

    def _update_rates_and_banner(self, exchange_rate: float):
        """Actualiza las etiquetas de texto, banner de salud y tarjetas de liquidez sin destruir widgets hijos."""
        self.exchange_rate = exchange_rate
        summary = self.controller.get_consolidated_summary(exchange_rate=self.exchange_rate)

        # 1. Actualizar badge de tasa
        if hasattr(self, "lbl_trm_info") and self.lbl_trm_info.winfo_exists():
            self.lbl_trm_info.configure(text=f"💵 TRM Oficial: 1 USD ≈ ${self.exchange_rate:,.2f} COP")

        # 2. Actualizar Banner de Salud Financiera
        net_result = summary["net_monthly_result"]
        if hasattr(self, "lbl_net_result") and self.lbl_net_result.winfo_exists():
            if net_result >= 0:
                self.lbl_net_result.configure(text=f"+${net_result:,.0f} COP", text_color=Theme.SUCCESS)
                self.badge_status.configure(text="🟢 SUPERÁVIT DEL MES", fg_color=Theme.SUCCESS)
                self.lbl_net_desc.configure(text=f"🎉 ¡Mes positivo! Ganaste ${net_result:,.0f} COP más de lo que gastaste.")
            else:
                self.lbl_net_result.configure(text=f"-${abs(net_result):,.0f} COP", text_color=Theme.ERROR)
                self.badge_status.configure(text="🔴 DÉFICIT DEL MES", fg_color=Theme.ERROR)
                self.lbl_net_desc.configure(text=f"Gastos superaron ingresos por ${abs(net_result):,.0f} COP.")

        # Liquidez Inmediata Consolidada
        net_liq = summary["net_immediate_liquidity"]
        cop_liq = summary["cop_liquid"]
        usd_liq = summary["usd_liquid"]
        usd_cop = summary["usd_liquid_in_cop"]

        if hasattr(self, "lbl_real_liquidity") and self.lbl_real_liquidity.winfo_exists():
            if net_liq >= 0:
                self.lbl_real_liquidity.configure(text=f"+${net_liq:,.0f} COP", text_color=Theme.INFO)
                self.lbl_liq_desc.configure(
                    text=f"Bancolombia: ${cop_liq:,.0f} COP  •  Wenia: ${usd_liq:,.2f} USD (≈ ${usd_cop:,.0f} COP)"
                )
            else:
                self.lbl_real_liquidity.configure(text=f"-${abs(net_liq):,.0f} COP", text_color=Theme.ERROR)
                self.lbl_liq_desc.configure(text="Atención: Saldo líquido total negativo.")

        # Franja detallada inferior
        if hasattr(self, "lbl_summary_details") and self.lbl_summary_details.winfo_exists():
            income_text = f"📥 Ingresos Totales: ${summary['total_consolidated_income']:,.0f} COP  (COP Directo: ${summary['cop_direct_income']:,.0f} | USD: ${summary['usd_income']:,.2f} ≈ ${summary['usd_income_in_cop']:,.0f})"
            expense_text = f"📤 Gastos Totales: ${summary['total_consolidated_expenses']:,.0f} COP  (Fijos: ${summary['cop_fixed']:,.0f} | Variables: ${summary['cop_var']:,.0f})"

            detail_lines = [f"{income_text}\n{expense_text}"]
            if summary.get("extraordinary_purchases"):
                equip_notes = ", ".join([f"{p.get('notes') or 'Compra de activo'} (${p['amount']:,.0f} COP)" for p in summary["extraordinary_purchases"]])
                detail_lines.append(f"💡 Compra de equipo/activo de contado: {equip_notes}. (Gastos corrientes de vida: ${summary['routine_expenses']:,.0f} COP).")

            self.lbl_summary_details.configure(text="\n".join(detail_lines))

            if hasattr(self, "bottom_strip") and self.bottom_strip.winfo_exists():
                if self.show_banner_details:
                    self.bottom_strip.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))
                else:
                    self.bottom_strip.pack_forget()

        # 3. Actualizar Tarjetas de Estadísticas USD y COP
        if hasattr(self, "card_usd") and self.card_usd.winfo_exists():
            self.card_usd.update_value(
                f"${usd_liq:,.2f} USD",
                f"≈ ${usd_cop:,.0f} COP líquidos disponibles"
            )

        if hasattr(self, "card_cop") and self.card_cop.winfo_exists():
            if cop_liq < 0:
                cop_sub = f"Cubierto con USD en Wenia (+${usd_cop:,.0f} COP)"
            else:
                cop_sub = f"Liquidez combinada: +${net_liq:,.0f} COP"
            self.card_cop.update_value(
                f"${cop_liq:,.0f} COP",
                cop_sub
            )

        return summary

    def refresh_data(self):
        """Actualiza todas las métricas, tarjetas y listas del dashboard con visión consolidada."""
        # 1. Actualizar banner de salud, tasa y tarjetas de liquidez
        summary = self._update_rates_and_banner(self.exchange_rate)

        # 2. Actualizar Tarjeta de Deudas Totales
        debts_summary = self.controller.get_debts_summary()
        grand_debt = debts_summary["grand_total_debt"]
        if grand_debt == 0:
            debt_sub = "Sin deudas pendientes 🎉"
        elif debts_summary["personal_remaining"] > 0 and debts_summary["credit_card_debt"] > 0:
            debt_sub = f"TC mes: ${debts_summary['credit_card_debt']:,.0f} | Papá (PC): ${debts_summary['personal_remaining']:,.0f}"
        elif debts_summary["personal_remaining"] > 0:
            debt_sub = f"Préstamo personal: ${debts_summary['personal_remaining']:,.0f}"
        else:
            debt_sub = f"Tarjeta de crédito: ${debts_summary['credit_card_debt']:,.0f}"

        self.card_cc_debt.update_value(
            f"${grand_debt:,.0f} COP",
            debt_sub
        )

        # 3. Actualizar Tarjeta de Gastos del Mes COP
        if summary.get("extraordinary_sum", 0) > 0:
            exp_sub = f"Vida ordinaria: ${summary['routine_expenses']:,.0f} | Activo: ${summary['extraordinary_sum']:,.0f}"
        else:
            exp_sub = f"Fijos: ${summary['cop_fixed']:,.0f} | Variables: ${summary['cop_var']:,.0f}"

        self.card_expenses.update_value(
            f"${summary['cop_expenses']:,.0f} COP",
            exp_sub
        )

        # 4. Actualizar Desglose de Gastos
        self._refresh_categories_breakdown(summary['cop_expenses'])

        # 5. Actualizar Feed de Movimientos Recientes
        self._refresh_activities_feed()

    def _refresh_categories_breakdown(self, total_expenses: float):
        for widget in self.categories_scroll.winfo_children():
            widget.destroy()

        categories, budgets_map = self.controller.get_categories_breakdown_data()

        if not categories:
            empty_state = EmptyState(
                self.categories_scroll,
                icon="📊",
                title="Sin gastos este mes",
                message="Aún no se registran egresos para el periodo actual.",
                compact=True
            )
            empty_state.pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_MD)
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

            item_card = ctk.CTkFrame(self.categories_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            item_card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

            top_row = ctk.CTkFrame(item_card, fg_color="transparent")
            top_row.pack(fill="x", padx=Theme.SPACING_SM, pady=(Theme.SPACING_SM, Theme.SPACING_XS))

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
            progress = ctk.CTkProgressBar(item_card, height=6, corner_radius=Theme.SPACING_XS, fg_color=Theme.BORDER_SUBTLE, progress_color=bar_color)
            progress.pack(fill="x", padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_SM))
            progress.set(bar_ratio)

    def _format_date_heading(self, date_str: str) -> str:
        """Convierte una fecha 'YYYY-MM-DD' en una etiqueta amigable agrupada."""
        try:
            today = datetime.now().date()
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
            diff = (today - dt).days
            months_es = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
            month_str = months_es[dt.month - 1]

            if diff == 0:
                return f"HOY — {dt.day} {month_str}"
            elif diff == 1:
                return f"AYER — {dt.day} {month_str}"
            elif 2 <= diff <= 6:
                days_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                return f"{days_es[dt.weekday()]} — {dt.day} {month_str}"
            else:
                return f"{dt.day} {month_str} {dt.year}"
        except Exception:
            return date_str

    def _refresh_activities_feed(self):
        for widget in self.activities_scroll.winfo_children():
            widget.destroy()

        activities = self.controller.get_recent_activities(limit=12)
        if not activities:
            empty_state = EmptyState(
                self.activities_scroll,
                icon="🕒",
                title="Sin movimientos recientes",
                message="Comienza registrando un ingreso o egreso para activar tus métricas.",
                action_text="+ Registrar Ingreso",
                action_command=lambda: self._trigger_nav("incomes"),
                action_variant="primary"
            )
            empty_state.pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_LG)
            return

        last_date_group = None
        for act in activities:
            act_date = act.get("date")
            if act_date and act_date != last_date_group:
                last_date_group = act_date
                group_frame = ctk.CTkFrame(self.activities_scroll, fg_color="transparent")
                group_frame.pack(fill="x", padx=Theme.SPACING_XS, pady=(Theme.SPACING_SM, 3))

                ctk.CTkLabel(
                    group_frame,
                    text=self._format_date_heading(act_date).upper(),
                    font=ctk.CTkFont(family=Theme.FONT_TEXT, size=10, weight="bold"),
                    text_color=Theme.TEXT_MUTED
                ).pack(side="left")

                ctk.CTkFrame(group_frame, height=1, fg_color=Theme.BORDER_SUBTLE).pack(side="left", fill="x", expand=True, padx=(Theme.SPACING_SM, 2))

            card = ctk.CTkFrame(self.activities_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

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
            top_row.pack(fill="x", padx=Theme.SPACING_SM, pady=(Theme.SPACING_XS, 2))

            icon_lbl = ctk.CTkLabel(top_row, text=badge_icon, font=ctk.CTkFont(size=14))
            icon_lbl.pack(side="left", padx=(0, Theme.SPACING_XS))

            title_lbl = ctk.CTkLabel(
                top_row,
                text=act["title"],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            )
            title_lbl.pack(side="left")

            amount_lbl = ctk.CTkLabel(
                top_row,
                text=act["amount_str"],
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=amount_color
            )
            amount_lbl.pack(side="right")

            # Fila inferior: Fuente y notas
            bottom_row = ctk.CTkFrame(card, fg_color="transparent")
            bottom_row.pack(fill="x", padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_XS))

            source_lbl = ctk.CTkLabel(
                bottom_row,
                text=act['source'],
                font=ctk.CTkFont(size=11),
                text_color=Theme.TEXT_MUTED
            )
            source_lbl.pack(side="left")

            if act.get("notes"):
                notes_lbl = ctk.CTkLabel(
                    bottom_row,
                    text=f"\"{act['notes']}\"",
                    font=ctk.CTkFont(size=11, slant="italic"),
                    text_color=Theme.TEXT_SECONDARY
                )
                notes_lbl.pack(side="right")
