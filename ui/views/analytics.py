"""
Vista de Balance General, Patrimonio Neto Global, Analítica Financiera y Gráficas Visuales.
Consolida el Patrimonio Neto Total en tiempo real (Activos COP + Equivalente USD a TRM - Deuda TC),
con gráficos interactivos embebidos con Matplotlib, desglose de activos y flujo de caja anualizado.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional, Dict, Any, List
from ui.theme import Theme
from ui.components.stat_card import StatCard
from ui.components.toast import ToastNotification
from services.currency_service import CurrencyService

import matplotlib
matplotlib.use("Agg")  # Backend estático para integración nativa con Tkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class AnalyticsView(ctk.CTkFrame):
    def __init__(self, master, db_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.current_year = datetime.now().year
        self.current_rate = self.db.get_latest_exchange_rate()

        self._build_ui()
        self._fetch_rate_on_start()
        self.refresh_data()

    def _build_ui(self):
        self.toast = ToastNotification(self)

        # 1. Cabecera
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 12))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="📈 Balance General & Analítica Financiera",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Consolidación patrimonial multimoneda (COP y USD a TRM en tiempo real), activos, pasivos y reportes.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Controles de Periodo y TRM a la derecha
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right")

        # Badge de Tasa de Referencia en cabecera
        self.trm_badge = ctk.CTkFrame(
            controls_frame,
            fg_color=Theme.BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER_DEFAULT
        )
        self.trm_badge.pack(side="left", padx=(0, 10))

        self.lbl_trm_info = ctk.CTkLabel(
            self.trm_badge,
            text=f"💵 TRM Oficial: 1 USD ≈ ${self.current_rate:,.2f} COP",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.ACCENT_BLUE
        )
        self.lbl_trm_info.pack(padx=10, pady=5)

        ctk.CTkLabel(controls_frame, text="Año:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(side="left", padx=(0, 4))
        years = [str(self.current_year + i) for i in range(-2, 3)]
        self.year_combo = ctk.CTkComboBox(
            controls_frame,
            values=years,
            width=85,
            height=30,
            corner_radius=6,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda _: self.refresh_data()
        )
        self.year_combo.set(str(self.current_year))
        self.year_combo.pack(side="left")

        # 2. Gran Banner de Patrimonio Neto Global Consolidado
        self.net_worth_banner = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        self.net_worth_banner.pack(fill="x", padx=24, pady=(0, 14))

        banner_inner = ctk.CTkFrame(self.net_worth_banner, fg_color="transparent")
        banner_inner.pack(fill="x", padx=20, pady=16)

        # Columna Izquierda: Total Patrimonio Neto
        left_nw = ctk.CTkFrame(banner_inner, fg_color="transparent")
        left_nw.pack(side="left")

        ctk.CTkLabel(
            left_nw,
            text="💎 PATRIMONIO NETO GLOBAL CONSOLIDADO",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            text_color=Theme.ACCENT_BLUE
        ).pack(anchor="w")
        self.lbl_net_worth_cop = ctk.CTkLabel(
            left_nw,
            text="$0 COP",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=28, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_net_worth_cop.pack(anchor="w", pady=(2, 0))

        self.lbl_net_worth_usd = ctk.CTkLabel(
            left_nw,
            text="≈ $0.00 USD",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=14, weight="bold"),
            text_color=Theme.ACCENT_GREEN
        )
        self.lbl_net_worth_usd.pack(anchor="w")

        # Columna Derecha: Control de TRM en vivo
        trm_box = ctk.CTkFrame(banner_inner, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        trm_box.pack(side="right")

        trm_inner = ctk.CTkFrame(trm_box, fg_color="transparent")
        trm_inner.pack(padx=14, pady=10)

        ctk.CTkLabel(
            trm_inner,
            text="Tasa de Cambio Aplicada:",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        self.lbl_trm_applied = ctk.CTkLabel(
            trm_inner,
            text=f"💵 1 USD ≈ ${self.current_rate:,.0f} COP",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.ACCENT_BLUE
        )
        self.lbl_trm_applied.pack(anchor="w", pady=(2, 6))

        trm_row = ctk.CTkFrame(trm_inner, fg_color="transparent")
        trm_row.pack(anchor="w")

        self.btn_live_trm = ctk.CTkButton(
            trm_row,
            text="🌐 TRM en Vivo",
            height=28,
            width=95,
            corner_radius=6,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self._fetch_live_trm
        )
        self.btn_live_trm.pack(side="left", padx=(0, 6))

        self.btn_edit_trm = ctk.CTkButton(
            trm_row,
            text="✏️ Cambiar Tasa",
            height=28,
            width=95,
            corner_radius=6,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            border_width=1,
            border_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self._prompt_manual_trm
        )
        self.btn_edit_trm.pack(side="left")

        # 3. Fila de Tarjetas de Métricas de Activos y Pasivos
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=24, pady=(0, 14))
        self.kpi_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi_cards")

        # Tarjeta 1: Activos COP
        self.card_cop_assets = StatCard(
            self.kpi_container,
            title="Activos Totales COP",
            value="$0 COP",
            subtitle="Liquidez + Fiducias COP",
            icon="🇨🇴",
            accent_color=Theme.ACCENT_GREEN,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_cop_assets.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        # Tarjeta 2: Activos USD
        self.card_usd_assets = StatCard(
            self.kpi_container,
            title="Activos Totales USD",
            value="$0.00 USD",
            subtitle="Bóveda + Inversiones USD",
            icon="💵",
            accent_color=Theme.ACCENT_BLUE,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_usd_assets.grid(row=0, column=1, padx=3, sticky="nsew")

        # Tarjeta 3: Pasivos (Deuda TC)
        self.card_liabilities = StatCard(
            self.kpi_container,
            title="Deuda TC (Pasivos)",
            value="$0 COP",
            subtitle="Deuda a saldar fin de mes",
            icon="💳",
            accent_color=Theme.ACCENT_ROSE,
            bg_color=Theme.BG_CARD,
            border_color="#e11d48"
        )
        self.card_liabilities.grid(row=0, column=2, padx=3, sticky="nsew")

        # Tarjeta 4: Tasa Retención USD
        self.card_usd_retention = StatCard(
            self.kpi_container,
            title="Ahorro Anual USD",
            value="$0.00 USD",
            subtitle="0% Retención de ingresos",
            icon="📈",
            accent_color=Theme.ACCENT_INDIGO,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_usd_retention.grid(row=0, column=3, padx=(6, 0), sticky="nsew")

        # 4. Contenedor Principal con Pestañas
        main_content = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_content.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        content_header = ctk.CTkFrame(main_content, fg_color="transparent")
        content_header.pack(fill="x", padx=18, pady=(14, 8))

        self.tab_seg = ctk.CTkSegmentedButton(
            content_header,
            values=["🌐  Composición de Activos", "📊  Flujo Anualizado", "📈  Gráficas & Reportes"],
            height=32,
            command=self._on_tab_changed
        )
        self.tab_seg.set("🌐  Composición de Activos")
        self.tab_seg.pack(side="left")

        self.lbl_annual_summary = ctk.CTkLabel(
            content_header,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.ACCENT_GREEN
        )
        self.lbl_annual_summary.pack(side="right")

        # Contenedor de Vistas
        self.tab_content = ctk.CTkFrame(main_content, fg_color="transparent")
        self.tab_content.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # Sub-panel 1: Composición de Activos
        self.composition_scroll = ctk.CTkScrollableFrame(self.tab_content, fg_color="transparent")

        # Sub-panel 2: Flujo Anualizado
        self.annual_frame = ctk.CTkFrame(self.tab_content, fg_color="transparent")
        
        tbl_head = ctk.CTkFrame(self.annual_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, height=32)
        tbl_head.pack(fill="x", pady=(0, 6))
        tbl_head.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

        cols = ["Mes", "Ingreso USD", "Gasto USD", "Ahorro USD", "Ingreso COP", "Gastos COP", "Flujo COP", "🌐 Flujo Global"]
        for idx, col_text in enumerate(cols):
            align = "w" if idx == 0 else "e"
            ctk.CTkLabel(
                tbl_head,
                text=col_text.upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=Theme.TEXT_MUTED if idx < 7 else Theme.ACCENT_BLUE
            ).grid(row=0, column=idx, padx=8, pady=6, sticky=align)

        self.months_scroll = ctk.CTkScrollableFrame(self.annual_frame, fg_color="transparent")
        self.months_scroll.pack(fill="both", expand=True)

        # Sub-panel 3: Gráficas & Reportes
        self.charts_scroll = ctk.CTkScrollableFrame(self.tab_content, fg_color="transparent")

        self._show_active_tab()

    def _fetch_rate_on_start(self):
        CurrencyService.fetch_rate_async(self._on_live_rate_fetched)

    def _fetch_live_trm(self):
        self.btn_live_trm.configure(text="⏳ Consultando...", state="disabled")
        CurrencyService.fetch_rate_async(self._on_live_rate_fetched)

    def _on_live_rate_fetched(self, rate: Optional[float]):
        def update():
            self.btn_live_trm.configure(text="🌐 TRM en Vivo", state="normal")
            if rate and rate > 0:
                self.current_rate = rate
                try:
                    self.db.set_setting("official_trm", str(rate))
                except Exception:
                    pass
                self.refresh_data()
                self.toast.show(f"TRM en vivo actualizada: ${rate:,.2f} COP/USD", is_error=False)
            else:
                self.refresh_data()
        self.after(0, update)

    def _prompt_manual_trm(self):
        """Permite al usuario ingresar una tasa personalizada si lo desea."""
        dialog = ctk.CTkInputDialog(
            text=f"Ingresa la tasa de cambio en COP por cada USD:\n(Actual: ${self.current_rate:,.0f} COP)",
            title="Ajustar Tasa de Cambio"
        )
        val = dialog.get_input()
        if val:
            try:
                rate = float(val.strip().replace("$", "").replace(".", "").replace(",", "."))
                if rate > 0:
                    self.current_rate = rate
                    self.refresh_data()
                    self.toast.show(f"Tasa ajustada a ${rate:,.2f} COP/USD", is_error=False)
            except ValueError:
                self.toast.show("Por favor ingresa un número válido.", is_error=True)

    def _on_tab_changed(self, choice: str):
        self._show_active_tab()

    def _show_active_tab(self):
        choice = self.tab_seg.get()
        self.composition_scroll.pack_forget()
        self.annual_frame.pack_forget()
        self.charts_scroll.pack_forget()

        if "Composición" in choice:
            self.lbl_annual_summary.configure(text="")
            self.composition_scroll.pack(fill="both", expand=True)
            self._refresh_composition()
        elif "Flujo" in choice:
            self.annual_frame.pack(fill="both", expand=True)
            self._refresh_annual_table()
        else:
            self.lbl_annual_summary.configure(text="")
            self.charts_scroll.pack(fill="both", expand=True)
            self._refresh_charts()

    def refresh_data(self):
        rate = self.current_rate

        # Actualizar labels de tasa
        if hasattr(self, "lbl_trm_info"):
            self.lbl_trm_info.configure(text=f"💵 TRM Oficial: 1 USD ≈ ${rate:,.2f} COP")
        if hasattr(self, "lbl_trm_applied"):
            self.lbl_trm_applied.configure(text=f"💵 1 USD ≈ ${rate:,.2f} COP")

        net_worth = self.db.get_global_net_worth(exchange_rate=rate)

        # Actualizar Gran Banner
        self.lbl_net_worth_cop.configure(text=f"${net_worth['net_worth_cop']:,.0f} COP")
        self.lbl_net_worth_usd.configure(text=f"≈ ${net_worth['net_worth_usd']:,.2f} USD")

        # Actualizar Tarjetas KPI
        self.card_cop_assets.update_value(
            f"${net_worth['total_cop_assets']:,.0f} COP",
            f"Líquido: ${net_worth['cop_liquid']:,.0f} | Inv: ${net_worth['cop_invested']:,.0f}"
        )
        self.card_usd_assets.update_value(
            f"${net_worth['total_usd_assets']:,.2f} USD",
            f"Equivalente: ${net_worth['total_usd_in_cop']:,.0f} COP"
        )
        self.card_liabilities.update_value(
            f"${net_worth['total_liabilities_cop']:,.0f} COP",
            "Sin deuda pendiente" if net_worth['total_liabilities_cop'] == 0 else "Pasivo exigible fin de mes"
        )

        try:
            year = int(self.year_combo.get())
        except ValueError:
            year = self.current_year
        overview = self.db.get_annual_overview(year)
        totals = overview["totals"]

        self.card_usd_retention.update_value(
            f"${totals['usd_saved']:,.2f} USD",
            f"{totals['usd_savings_rate']:.1f}% Retención Anual"
        )

        self._show_active_tab()

    def _refresh_composition(self):
        for widget in self.composition_scroll.winfo_children():
            widget.destroy()

        net_worth = self.db.get_global_net_worth(exchange_rate=self.current_rate)
        accounts = self.db.get_accounts(only_active=True)

        gross_cop = net_worth["total_cop_assets"] + net_worth["total_usd_in_cop"]

        items = [
            ("💳 Cuenta Operativa Líquida (COP)", net_worth["cop_liquid"], "COP", "#10b981"),
            ("🏦 Bóveda USD (Ahorro Intocable)", net_worth["usd_vault"] * self.current_rate, f"${net_worth['usd_vault']:,.2f} USD", "#0284c7"),
        ]

        for acc in accounts:
            curr = acc["currency"]
            bal = acc["current_balance"]
            val_in_cop = bal if curr == "COP" else bal * self.current_rate
            val_str = f"${bal:,.0f} COP" if curr == "COP" else f"${bal:,.2f} USD"
            icon = acc.get("icon", "📈")
            items.append((f"{icon} {acc['name']} ({acc.get('institution', 'Fiducia')})", val_in_cop, val_str, "#8b5cf6" if curr == "COP" else "#38bdf8"))

        for name, cop_val, label_sub, bar_color in items:
            pct = (cop_val / gross_cop * 100) if gross_cop > 0 else 0

            card = ctk.CTkFrame(self.composition_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=3, padx=2)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(8, 4))

            ctk.CTkLabel(top, text=name, font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=f"${cop_val:,.0f} COP ({pct:.1f}%) • {label_sub}", font=ctk.CTkFont(size=12, weight="bold"), text_color=bar_color).pack(side="right")

            p_bar = ctk.CTkProgressBar(card, height=6, corner_radius=3, fg_color=Theme.BORDER_DEFAULT, progress_color=bar_color)
            p_bar.pack(fill="x", padx=14, pady=(0, 8))
            p_bar.set(min(pct / 100.0, 1.0))

    def _refresh_annual_table(self):
        for widget in self.months_scroll.winfo_children():
            widget.destroy()

        try:
            year = int(self.year_combo.get())
        except ValueError:
            year = self.current_year

        overview = self.db.get_annual_overview(year)
        totals = overview["totals"]

        net_cop = totals["cop_net"]
        usd_saved = totals["usd_saved"]
        global_net_cop = net_cop + (usd_saved * self.current_rate)

        net_prefix = "+" if net_cop >= 0 else ""
        usd_prefix = "+" if usd_saved >= 0 else ""
        global_prefix = "+" if global_net_cop >= 0 else ""
        global_color = Theme.ACCENT_GREEN if global_net_cop >= 0 else Theme.ACCENT_ROSE

        self.lbl_annual_summary.configure(
            text=f"Flujo COP: {net_prefix}${net_cop:,.0f} • Ahorro USD: {usd_prefix}${usd_saved:,.0f} • 🌐 Flujo Global: {global_prefix}${global_net_cop:,.0f} COP",
            text_color=global_color
        )

        for m_data in overview["months"]:
            has_activity = (
                m_data["usd_income"] > 0 or
                m_data.get("usd_spent", 0) > 0 or
                m_data["usd_converted"] > 0 or
                m_data["cop_manual_income"] > 0 or
                m_data["cop_expenses"] > 0
            )

            row_bg = Theme.BG_CARD_SUBTLE if has_activity else "transparent"
            row_frame = ctk.CTkFrame(self.months_scroll, fg_color=row_bg, corner_radius=8, height=36)
            row_frame.pack(fill="x", pady=2, padx=2)
            row_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

            # 0. Mes
            ctk.CTkLabel(
                row_frame,
                text=f"🗓️ {m_data['month_name']}",
                font=ctk.CTkFont(size=12, weight="bold" if has_activity else "normal"),
                text_color=Theme.TEXT_PRIMARY if has_activity else Theme.TEXT_MUTED
            ).grid(row=0, column=0, padx=8, pady=8, sticky="w")

            # 1. Ingreso USD
            usd_inc_str = f"${m_data['usd_income']:,.0f}" if m_data['usd_income'] > 0 else "-"
            ctk.CTkLabel(row_frame, text=usd_inc_str, font=ctk.CTkFont(size=12), text_color=Theme.ACCENT_BLUE if m_data['usd_income'] > 0 else Theme.TEXT_MUTED).grid(row=0, column=1, padx=8, pady=8, sticky="e")

            # 2. Retiro/Gasto USD
            usd_out_tot = m_data["usd_converted"] + m_data.get("usd_spent", 0)
            usd_out_str = f"${usd_out_tot:,.0f}" if usd_out_tot > 0 else "-"
            ctk.CTkLabel(row_frame, text=usd_out_str, font=ctk.CTkFont(size=12), text_color=Theme.ACCENT_INDIGO if usd_out_tot > 0 else Theme.TEXT_MUTED).grid(row=0, column=2, padx=8, pady=8, sticky="e")

            # 3. Ahorro USD
            usd_sav_str = f"${m_data['usd_saved']:,.0f}" if m_data['usd_saved'] != 0 else "-"
            ctk.CTkLabel(row_frame, text=usd_sav_str, font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_GREEN if m_data['usd_saved'] > 0 else Theme.TEXT_MUTED).grid(row=0, column=3, padx=8, pady=8, sticky="e")

            # 4. Ingreso COP
            cop_inc_str = f"${m_data['cop_manual_income']:,.0f}" if m_data['cop_manual_income'] > 0 else "-"
            ctk.CTkLabel(row_frame, text=cop_inc_str, font=ctk.CTkFont(size=12), text_color=Theme.ACCENT_GREEN if m_data['cop_manual_income'] > 0 else Theme.TEXT_MUTED).grid(row=0, column=4, padx=8, pady=8, sticky="e")

            # 5. Gastos COP
            cop_exp_str = f"${m_data['cop_expenses']:,.0f}" if m_data['cop_expenses'] > 0 else "-"
            ctk.CTkLabel(row_frame, text=cop_exp_str, font=ctk.CTkFont(size=12), text_color=Theme.ACCENT_ROSE if m_data['cop_expenses'] > 0 else Theme.TEXT_MUTED).grid(row=0, column=5, padx=8, pady=8, sticky="e")

            # 6. Flujo COP
            m_net = m_data["cop_net"]
            if has_activity:
                m_net_str = f"+${m_net:,.0f}" if m_net >= 0 else f"-${abs(m_net):,.0f}"
                m_net_color = Theme.ACCENT_GREEN if m_net >= 0 else Theme.ACCENT_ROSE
            else:
                m_net_str = "-"
                m_net_color = Theme.TEXT_MUTED
            ctk.CTkLabel(row_frame, text=m_net_str, font=ctk.CTkFont(size=12, weight="bold"), text_color=m_net_color).grid(row=0, column=6, padx=8, pady=8, sticky="e")

            # 7. Flujo Global (COP + USD * TRM)
            m_global = m_net + (m_data["usd_saved"] * self.current_rate)
            if has_activity:
                m_glob_str = f"+${m_global:,.0f}" if m_global >= 0 else f"-${abs(m_global):,.0f}"
                m_glob_color = Theme.ACCENT_GREEN if m_global >= 0 else Theme.ACCENT_ROSE
            else:
                m_glob_str = "-"
                m_glob_color = Theme.TEXT_MUTED
            ctk.CTkLabel(row_frame, text=m_glob_str, font=ctk.CTkFont(size=12, weight="bold"), text_color=m_glob_color).grid(row=0, column=7, padx=8, pady=8, sticky="e")

        # Fila destacada de TOTALES DEL AÑO
        tot_frame = ctk.CTkFrame(self.months_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
        tot_frame.pack(fill="x", pady=(8, 2), padx=2)
        tot_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

        ctk.CTkLabel(tot_frame, text=f"🎯 TOTAL {year}", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).grid(row=0, column=0, padx=8, pady=9, sticky="w")
        ctk.CTkLabel(tot_frame, text=f"${totals['usd_earned']:,.0f}", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_BLUE).grid(row=0, column=1, padx=8, pady=9, sticky="e")

        tot_usd_out = totals["usd_converted"] + totals.get("usd_spent", 0)
        ctk.CTkLabel(tot_frame, text=f"${tot_usd_out:,.0f}", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_INDIGO).grid(row=0, column=2, padx=8, pady=9, sticky="e")
        ctk.CTkLabel(tot_frame, text=f"${totals['usd_saved']:,.0f}", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_GREEN).grid(row=0, column=3, padx=8, pady=9, sticky="e")
        ctk.CTkLabel(tot_frame, text=f"${totals['cop_manual_income']:,.0f}", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_GREEN).grid(row=0, column=4, padx=8, pady=9, sticky="e")
        ctk.CTkLabel(tot_frame, text=f"${totals['cop_expenses']:,.0f}", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_ROSE).grid(row=0, column=5, padx=8, pady=9, sticky="e")

        net_tot_str = f"+${net_cop:,.0f}" if net_cop >= 0 else f"-${abs(net_cop):,.0f}"
        net_tot_color = Theme.ACCENT_GREEN if net_cop >= 0 else Theme.ACCENT_ROSE
        ctk.CTkLabel(tot_frame, text=net_tot_str, font=ctk.CTkFont(size=12, weight="bold"), text_color=net_tot_color).grid(row=0, column=6, padx=8, pady=9, sticky="e")

        glob_tot_str = f"+${global_net_cop:,.0f}" if global_net_cop >= 0 else f"-${abs(global_net_cop):,.0f}"
        glob_tot_color = Theme.ACCENT_GREEN if global_net_cop >= 0 else Theme.ACCENT_ROSE
        ctk.CTkLabel(tot_frame, text=glob_tot_str, font=ctk.CTkFont(size=12, weight="bold"), text_color=glob_tot_color).grid(row=0, column=7, padx=8, pady=9, sticky="e")

    def _refresh_charts(self):
        """Genera y renderiza las gráficas visuales con Matplotlib de forma segura."""
        if not hasattr(self, "_active_figures"):
            self._active_figures = []
        for fig in self._active_figures:
            try:
                fig.clf()
            except Exception:
                pass
        self._active_figures.clear()

        for widget in self.charts_scroll.winfo_children():
            widget.destroy()

        try:
            year = int(self.year_combo.get())
        except ValueError:
            year = self.current_year


        is_dark = (ctk.get_appearance_mode() == "Dark")
        bg_color = "#1e293b" if is_dark else "#ffffff"
        text_color = "#f8fafc" if is_dark else "#0f172a"
        muted_color = "#94a3b8" if is_dark else "#475569"
        grid_color = "#334155" if is_dark else "#e2e8f0"

        # 1. Gráfica de Donut: Gastos COP por Categoría del Mes
        categories = self.db.get_expenses_by_category()
        fig1 = Figure(figsize=(8, 3.2), dpi=100, facecolor=bg_color)
        ax1 = fig1.add_subplot(111)
        ax1.set_facecolor(bg_color)

        if categories:
            top_cats = categories[:6]
            labels = [c["category"][:16] for c in top_cats]
            sizes = [c["total"] for c in top_cats]
            palette = ["#f43f5e", "#fb7185", "#f59e0b", "#8b5cf6", "#38bdf8", "#10b981"]
            
            wedges, texts, autotexts = ax1.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=140,
                colors=palette[:len(sizes)],
                textprops=dict(color=text_color, size=9),
                wedgeprops=dict(width=0.45, edgecolor=bg_color, linewidth=2)
            )
            for at in autotexts:
                at.set_color("#ffffff")
                at.set_weight("bold")
            ax1.set_title("Distribución de Gastos COP por Categoría (Mes Actual)", color=text_color, fontsize=12, fontweight="bold", pad=12)
        else:
            ax1.text(0.5, 0.5, "No hay gastos registrados en el mes actual", color=muted_color, ha="center", va="center", fontsize=11)
            ax1.axis("off")

        chart_card1 = ctk.CTkFrame(self.charts_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        chart_card1.pack(fill="x", pady=6, padx=4)

        canvas1 = FigureCanvasTkAgg(fig1, master=chart_card1)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # 2. Gráfica de Barras: Flujo Mensual (Ingresos vs Gastos vs Superávit)
        overview = self.db.get_annual_overview(year)
        months = [m["month_name"] for m in overview["months"]]
        cop_in = [m["cop_total_income"] / 1000000.0 for m in overview["months"]]
        cop_out = [m["cop_expenses"] / 1000000.0 for m in overview["months"]]

        fig2 = Figure(figsize=(8, 3.4), dpi=100, facecolor=bg_color)
        ax2 = fig2.add_subplot(111)
        ax2.set_facecolor(bg_color)

        import numpy as np
        x = np.arange(len(months))
        width = 0.35

        ax2.bar(x - width/2, cop_in, width, label="Ingresos COP (M)", color="#10b981", alpha=0.9, edgecolor="none")
        ax2.bar(x + width/2, cop_out, width, label="Gastos COP (M)", color="#f43f5e", alpha=0.9, edgecolor="none")

        ax2.set_xticks(x)
        ax2.set_xticklabels(months, color=muted_color, fontsize=9)
        ax2.tick_params(colors=muted_color, labelsize=9)
        ax2.grid(True, linestyle="--", alpha=0.3, color=grid_color, axis="y")
        ax2.set_title(f"Flujo Mensual COP - Año {year} (Millones de Pesos)", color=text_color, fontsize=12, fontweight="bold", pad=12)
        ax2.legend(facecolor=bg_color, edgecolor=grid_color, labelcolor=text_color, fontsize=9)

        for spine in ax2.spines.values():
            spine.set_color(grid_color)

        chart_card2 = ctk.CTkFrame(self.charts_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        chart_card2.pack(fill="x", pady=6, padx=4)

        canvas2 = FigureCanvasTkAgg(fig2, master=chart_card2)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # 3. Gráfica de Línea: Evolución del Patrimonio Neto Global
        history = self.db.get_monthly_net_worth_history(year, exchange_rate=self.current_rate)
        nw_cop_millions = [h["net_worth_cop"] / 1000000.0 for h in history]

        fig3 = Figure(figsize=(8, 3.2), dpi=100, facecolor=bg_color)
        ax3 = fig3.add_subplot(111)
        ax3.set_facecolor(bg_color)

        ax3.plot(months, nw_cop_millions, color="#38bdf8", linewidth=2.5, marker="o", markersize=5, markerfacecolor="#0284c7")
        ax3.fill_between(months, nw_cop_millions, color="#38bdf8", alpha=0.15)

        ax3.tick_params(colors=muted_color, labelsize=9)
        ax3.grid(True, linestyle="--", alpha=0.3, color=grid_color)
        ax3.set_title(f"Evolución del Patrimonio Neto Global - Año {year} (Millones COP a TRM ${self.current_rate:,.0f})", color=text_color, fontsize=12, fontweight="bold", pad=12)

        for spine in ax3.spines.values():
            spine.set_color(grid_color)

        chart_card3 = ctk.CTkFrame(self.charts_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        chart_card3.pack(fill="x", pady=6, padx=4)

        canvas3 = FigureCanvasTkAgg(fig3, master=chart_card3)
        canvas3.draw()
        canvas3.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        self._active_figures.extend([fig1, fig2, fig3])

