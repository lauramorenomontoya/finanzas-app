"""
Vista Ejecutiva de Presupuesto por 3 Pilares Financieros (50 / 25 / 25):
- Pilar 1: Necesidades & Gastos Fijos (50%) -> Compromiso, pagado y pendiente.
- Pilar 2: Ahorro, Provisiones & Inversión (25%) -> Provisión Moto Fiducuenta ($150k), Fondo de Emergencia e Inversiones (Fidurenta/Trii).
- Pilar 3: Dinero Libre para Disfrutar (25%) -> Cupo disponible, gastado real, margen y desglose detallado con compras individuales.

Semáforo de alto contraste: 🟢 Verde, 🟡 Amarillo, 🔴 Rojo.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from ui.theme import Theme
from ui.components.toast import ToastNotification
from ui.components.edit_budget_modal import CategoryBudgetModal, MonthlyTargetsModal, BudgetSettingsModal


class BudgetView(ctk.CTkFrame):
    def __init__(self, master, db_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.current_ym = datetime.now().strftime("%Y-%m")
        self.active_currency = "COP"

        self.show_p1_details = False
        self.show_p3_details = False
        self.expanded_categories: Set[str] = set()

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        self.toast = ToastNotification(self)

        # 1. Cabecera Principal
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 10))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🎯 Presupuesto & 3 Pilares Financieros",
            font=ctk.CTkFont(family="SF Pro Display", size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Control visual de fijos (50%), protección y patrimonio (25%), y dinero libre para disfrutar (25%).",
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Controles de Periodo y Moneda
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right")

        self.currency_seg = ctk.CTkSegmentedButton(
            controls_frame,
            values=["🇨🇴 COP", "💵 USD"],
            height=30,
            command=self._on_currency_changed
        )
        self.currency_seg.set("🇨🇴 COP")
        self.currency_seg.pack(side="left", padx=(0, 10))

        btn_prev = ctk.CTkButton(
            controls_frame,
            text="◀",
            width=32,
            height=30,
            corner_radius=6,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            command=self._prev_month
        )
        btn_prev.pack(side="left", padx=2)

        self.lbl_month = ctk.CTkLabel(
            controls_frame,
            text=self.current_ym,
            font=ctk.CTkFont(family="SF Pro Display", size=14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            width=80
        )
        self.lbl_month.pack(side="left", padx=4)

        btn_next = ctk.CTkButton(
            controls_frame,
            text="▶",
            width=32,
            height=30,
            corner_radius=6,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            command=self._next_month
        )
        btn_next.pack(side="left", padx=2)

        btn_today = ctk.CTkButton(
            controls_frame,
            text="Hoy",
            width=50,
            height=30,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_BLUE,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._go_current_month
        )
        btn_today.pack(side="left", padx=(4, 0))

        # 2. CUERPO DESPLAZABLE PRINCIPAL
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # ------------------------------------------------------------------
        # BANNER MAESTRO: DINERO SEGURO PARA GASTAR (Safe-to-Spend)
        # ------------------------------------------------------------------
        self.banner_card = ctk.CTkFrame(self.main_scroll, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        self.banner_card.pack(fill="x", pady=(0, 14))

        banner_inner = ctk.CTkFrame(self.banner_card, fg_color="transparent")
        banner_inner.pack(fill="x", padx=20, pady=16)

        banner_left = ctk.CTkFrame(banner_inner, fg_color="transparent")
        banner_left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            banner_left,
            text="🛡️ DINERO SEGURO PARA GASTAR LIBREMENTE (PILAR 3)",
            font=ctk.CTkFont(family="SF Pro Text", size=11, weight="bold"),
            text_color=Theme.ACCENT_GREEN
        ).pack(anchor="w")

        self.lbl_safe_to_spend = ctk.CTkLabel(
            banner_left,
            text="$0 COP",
            font=ctk.CTkFont(family="SF Pro Display", size=32, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_safe_to_spend.pack(anchor="w", pady=(2, 0))

        self.lbl_safe_desc = ctk.CTkLabel(
            banner_left,
            text="",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_safe_desc.pack(anchor="w", pady=(2, 0))

        # Columna Derecha del Banner: Ritmo Diario + Botones de Configuración
        banner_right = ctk.CTkFrame(banner_inner, fg_color="transparent")
        banner_right.pack(side="right", padx=(14, 0))

        r_box = ctk.CTkFrame(banner_right, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        r_box.pack(fill="x", pady=(0, 8))

        r_inner = ctk.CTkFrame(r_box, fg_color="transparent")
        r_inner.pack(padx=16, pady=10)

        ctk.CTkLabel(r_inner, text="RITMO DIARIO SUGERIDO", font=ctk.CTkFont(size=10, weight="bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        self.lbl_daily_budget = ctk.CTkLabel(r_inner, text="$0 COP / día", font=ctk.CTkFont(size=16, weight="bold"), text_color=Theme.ACCENT_BLUE)
        self.lbl_daily_budget.pack(anchor="w", pady=(2, 0))
        self.lbl_days_left = ctk.CTkLabel(r_inner, text="", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_SECONDARY)
        self.lbl_days_left.pack(anchor="w")

        btn_row = ctk.CTkFrame(banner_right, fg_color="transparent")
        btn_row.pack(fill="x")

        btn_settings = ctk.CTkButton(
            btn_row,
            text="⚙️ Reglas (50/25/25)",
            height=28,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_budget_settings
        )
        btn_settings.pack(side="left", padx=(0, 4))

        btn_targets = ctk.CTkButton(
            btn_row,
            text="🎯 Metas del Mes",
            height=28,
            corner_radius=6,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_monthly_targets
        )
        btn_targets.pack(side="left")

        # ------------------------------------------------------------------
        # CONTENEDOR DE LOS 3 PILARES SIMPLIFICADOS
        # ------------------------------------------------------------------

        # ==========================================
        # PILAR 1: NECESIDADES & GASTOS FIJOS (50%)
        # ==========================================
        self.p1_card = ctk.CTkFrame(self.main_scroll, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        self.p1_card.pack(fill="x", pady=(0, 14))

        p1_top = ctk.CTkFrame(self.p1_card, fg_color="transparent")
        p1_top.pack(fill="x", padx=20, pady=(16, 8))

        p1_title_box = ctk.CTkFrame(p1_top, fg_color="transparent")
        p1_title_box.pack(side="left")

        ctk.CTkLabel(
            p1_title_box,
            text="🏠 PILAR 1: NECESIDADES & GASTOS FIJOS (50%)",
            font=ctk.CTkFont(family="SF Pro Display", size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            p1_title_box,
            text="Arriendo/Hogar, mamá, servicios públicos, seguridad social, seguros y compromisos obligatorios.",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Semáforo Pilar 1
        self.p1_badge = ctk.CTkLabel(
            p1_top,
            text="🟢 EN RANGO SEGURO",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff",
            fg_color="#059669",
            corner_radius=6,
            padx=10,
            pady=4
        )
        self.p1_badge.pack(side="right")

        # Métricas Fijos (Compromiso, Pagado, Pendiente)
        p1_metrics = ctk.CTkFrame(self.p1_card, fg_color="transparent")
        p1_metrics.pack(fill="x", padx=20, pady=(4, 10))
        p1_metrics.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="p1_cols")

        self.p1_lbl_budget = self._create_metric_cell(p1_metrics, 0, "LÍMITE SUGERIDO (50%):", "$0 COP", Theme.TEXT_PRIMARY)
        self.p1_lbl_committed = self._create_metric_cell(p1_metrics, 1, "COMPROMISO FIJOS TOTAL:", "$0 COP", Theme.ACCENT_BLUE)
        self.p1_lbl_paid = self._create_metric_cell(p1_metrics, 2, "PAGADO A LA FECHA:", "$0 COP", Theme.ACCENT_GREEN)
        self.p1_lbl_pending = self._create_metric_cell(p1_metrics, 3, "POR PAGAR RESTANTE:", "$0 COP", Theme.ACCENT_ROSE)

        # Barra de progreso Pilar 1
        self.p1_progress = ctk.CTkProgressBar(self.p1_card, height=12, corner_radius=6, fg_color="#334155", progress_color="#10b981")
        self.p1_progress.pack(fill="x", padx=20, pady=(0, 6))

        p1_foot = ctk.CTkFrame(self.p1_card, fg_color="transparent")
        p1_foot.pack(fill="x", padx=20, pady=(0, 14))

        self.p1_status_text = ctk.CTkLabel(p1_foot, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY)
        self.p1_status_text.pack(side="left")

        self.btn_toggle_p1 = ctk.CTkButton(
            p1_foot,
            text="👁️ Ver lista de gastos fijos ▾",
            width=170,
            height=26,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_BLUE,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._toggle_p1_details
        )
        self.btn_toggle_p1.pack(side="right")

        # Contenedor desplegable de fijos
        self.p1_details_box = ctk.CTkFrame(self.p1_card, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)

        # =========================================================
        # PILAR 2: AHORRO, PROVISIONES & INVERSIÓN (25%) [UNIFICADOS]
        # ==========================================
        self.p2_card = ctk.CTkFrame(self.main_scroll, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        self.p2_card.pack(fill="x", pady=(0, 14))

        p2_top = ctk.CTkFrame(self.p2_card, fg_color="transparent")
        p2_top.pack(fill="x", padx=20, pady=(16, 8))

        p2_title_box = ctk.CTkFrame(p2_top, fg_color="transparent")
        p2_title_box.pack(side="left")

        ctk.CTkLabel(
            p2_title_box,
            text="💰 PILAR 2: AHORRO, PROVISIONES & INVERSIÓN (25%)",
            font=ctk.CTkFont(family="SF Pro Display", size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            p2_title_box,
            text="Construcción patrimonial: Provisión moto en Fiducuenta ($150k fijos), Fondo de Emergencias e Inversiones (Fidurenta/Trii).",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Semáforo Pilar 2
        self.p2_badge = ctk.CTkLabel(
            p2_top,
            text="🟢 METAS AL DÍA",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff",
            fg_color="#059669",
            corner_radius=6,
            padx=10,
            pady=4
        )
        self.p2_badge.pack(side="right")

        # Métricas de Ahorro e Inversión (4 Columnas)
        p2_metrics = ctk.CTkFrame(self.p2_card, fg_color="transparent")
        p2_metrics.pack(fill="x", padx=20, pady=(4, 10))
        p2_metrics.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="p2_cols")

        self.p2_lbl_target_total = self._create_metric_cell(p2_metrics, 0, "META CONSOLIDADA (25%):", "$0 COP", Theme.ACCENT_BLUE)
        self.p2_lbl_moto = self._create_metric_cell(p2_metrics, 1, "PROVISIÓN MOTO (FIDUCUENTA):", "$150.000 COP", Theme.ACCENT_GREEN)
        self.p2_lbl_emergency = self._create_metric_cell(p2_metrics, 2, "FONDO DE EMERGENCIA:", "$0 COP", Theme.TEXT_PRIMARY)
        self.p2_lbl_invest = self._create_metric_cell(p2_metrics, 3, "INVERSIÓN (FIDURENTA/TRII):", "$0 COP", Theme.ACCENT_BLUE)

        self.p2_progress = ctk.CTkProgressBar(self.p2_card, height=12, corner_radius=6, fg_color="#334155", progress_color="#10b981")
        self.p2_progress.pack(fill="x", padx=20, pady=(0, 6))

        p2_foot = ctk.CTkFrame(self.p2_card, fg_color="transparent")
        p2_foot.pack(fill="x", padx=20, pady=(0, 14))

        self.p2_status_text = ctk.CTkLabel(p2_foot, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY)
        self.p2_status_text.pack(side="left")

        # ==========================================
        # PILAR 3: DINERO LIBRE PARA DISFRUTAR (25%)
        # ==========================================
        self.p3_card = ctk.CTkFrame(self.main_scroll, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        self.p3_card.pack(fill="x", pady=(0, 14))

        p3_top = ctk.CTkFrame(self.p3_card, fg_color="transparent")
        p3_top.pack(fill="x", padx=20, pady=(16, 8))

        p3_title_box = ctk.CTkFrame(p3_top, fg_color="transparent")
        p3_title_box.pack(side="left")

        ctk.CTkLabel(
            p3_title_box,
            text="🎉 PILAR 3: DINERO LIBRE PARA DISFRUTAR (25%)",
            font=ctk.CTkFont(family="SF Pro Display", size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            p3_title_box,
            text="¡Gastos de estilo de vida sin culpa! Restaurantes, salidas, entretenimiento, compras y gustos personales.",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Semáforo Ultra Notorio Pilar 3
        self.p3_badge = ctk.CTkLabel(
            p3_top,
            text="🟢 EN RANGO SEGURO",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff",
            fg_color="#059669",
            corner_radius=6,
            padx=12,
            pady=5
        )
        self.p3_badge.pack(side="right")

        p3_metrics = ctk.CTkFrame(self.p3_card, fg_color="transparent")
        p3_metrics.pack(fill="x", padx=20, pady=(4, 10))
        p3_metrics.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="p3_cols")

        self.p3_lbl_limit = self._create_metric_cell(p3_metrics, 0, "CUPO LIBRE DISPONIBLE (25%):", "$0 COP", Theme.ACCENT_BLUE)
        self.p3_lbl_spent = self._create_metric_cell(p3_metrics, 1, "GASTADO REAL EN EL MES:", "$0 COP", Theme.ACCENT_ROSE)
        self.p3_lbl_remaining = self._create_metric_cell(p3_metrics, 2, "MARGEN RESTANTE SIN CULPA:", "$0 COP", Theme.ACCENT_GREEN)
        self.p3_lbl_daily = self._create_metric_cell(p3_metrics, 3, "DISPONIBLE POR DÍA RESTANTE:", "$0 COP / día", Theme.TEXT_PRIMARY)

        # Barra de progreso gruesa y brillante
        self.p3_progress = ctk.CTkProgressBar(self.p3_card, height=14, corner_radius=7, fg_color="#334155", progress_color="#10b981")
        self.p3_progress.pack(fill="x", padx=20, pady=(0, 6))

        p3_foot = ctk.CTkFrame(self.p3_card, fg_color="transparent")
        p3_foot.pack(fill="x", padx=20, pady=(0, 14))

        self.p3_status_text = ctk.CTkLabel(p3_foot, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY)
        self.p3_status_text.pack(side="left")

        self.btn_toggle_p3 = ctk.CTkButton(
            p3_foot,
            text="👁️ Ver desglose y detalle de compras ▾",
            width=230,
            height=26,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_BLUE,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._toggle_p3_details
        )
        self.btn_toggle_p3.pack(side="right")

        # Contenedor desplegable de categorías variables y detalle de transacciones
        self.p3_details_box = ctk.CTkFrame(self.p3_card, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)

    def _create_metric_cell(self, parent, col: int, label: str, value: str, color) -> ctk.CTkLabel:
        box = ctk.CTkFrame(parent, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
        box.grid(row=0, column=col, sticky="nsew", padx=4, pady=2)
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(padx=12, pady=8)

        ctk.CTkLabel(
            inner,
            text=label,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        val_lbl = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(family="SF Pro Display", size=15, weight="bold"),
            text_color=color
        )
        val_lbl.pack(anchor="w", pady=(2, 0))
        return val_lbl

    # ==========================================
    # MANEJADORES DE ESTADO Y TOGGLES
    # ==========================================

    def _on_currency_changed(self, val: str):
        self.active_currency = "COP" if "COP" in val else "USD"
        self.refresh_data()

    def _prev_month(self):
        y, m = map(int, self.current_ym.split("-"))
        m -= 1
        if m < 1:
            m = 12
            y -= 1
        self.current_ym = f"{y:04d}-{m:02d}"
        self.lbl_month.configure(text=self.current_ym)
        self.refresh_data()

    def _next_month(self):
        y, m = map(int, self.current_ym.split("-"))
        m += 1
        if m > 12:
            m = 1
            y += 1
        self.current_ym = f"{y:04d}-{m:02d}"
        self.lbl_month.configure(text=self.current_ym)
        self.refresh_data()

    def _go_current_month(self):
        self.current_ym = datetime.now().strftime("%Y-%m")
        self.lbl_month.configure(text=self.current_ym)
        self.refresh_data()

    def _toggle_p1_details(self):
        self.show_p1_details = not self.show_p1_details
        if self.show_p1_details:
            self.p1_details_box.pack(fill="x", padx=20, pady=(0, 14))
            self.btn_toggle_p1.configure(text="🔼 Ocultar lista de gastos fijos")
            self._render_p1_details()
        else:
            self.p1_details_box.pack_forget()
            self.btn_toggle_p1.configure(text="👁️ Ver lista de gastos fijos ▾")

    def _toggle_p3_details(self):
        self.show_p3_details = not self.show_p3_details
        if self.show_p3_details:
            self.p3_details_box.pack(fill="x", padx=20, pady=(0, 14))
            self.btn_toggle_p3.configure(text="🔼 Ocultar desglose de compras")
            self._render_p3_details()
        else:
            self.p3_details_box.pack_forget()
            self.btn_toggle_p3.configure(text="👁️ Ver desglose y detalle de compras ▾")

    # ==========================================
    # ACTUALIZACIÓN DE DATOS Y SEMÁFOROS
    # ==========================================

    def refresh_data(self):
        overview = self.db.get_budget_overview(self.current_ym)
        curr = self.active_currency

        # -------------------------------------------------------------
        # BANNER MAESTRO SAFE-TO-SPEND (PILAR 3)
        # -------------------------------------------------------------
        safe_amt = overview["safe_to_spend"]
        safe_str = f"${safe_amt:,.0f} COP" if curr == "COP" else f"${safe_amt:,.2f} USD"
        self.lbl_safe_to_spend.configure(text=safe_str)

        daily_val = overview["daily_safe_budget"]
        self.lbl_daily_budget.configure(text=f"${daily_val:,.0f} COP / día" if curr == "COP" else f"${daily_val:,.2f} USD / día")
        self.lbl_days_left.configure(text=f"{overview['days_left']} días restantes en {self.current_ym}")

        if safe_amt > 0:
            self.lbl_safe_to_spend.configure(text_color="#10b981")
            self.lbl_safe_desc.configure(
                text=f"¡Tienes {safe_str} libres para disfrutar este mes! Fijos, provisión de moto y ahorro/inversión ya están reservados."
            )
        else:
            self.lbl_safe_to_spend.configure(text_color="#f43f5e")
            base_inc = overview["base_income"]
            fixed_tot = overview["total_fixed_obligations"]
            sav_tot = overview["total_savings_and_invest"]
            var_spent = overview["actual_var_spent"]
            if var_spent > 0 and (base_inc - fixed_tot - sav_tot - var_spent) < 0:
                diff = abs(base_inc - fixed_tot - sav_tot - var_spent)
                self.lbl_safe_desc.configure(
                    text=f"⚠️ Has consumido ${var_spent:,.0f} COP en compras variables. Se superó el margen ideal del mes en ${diff:,.0f} COP."
                )
            elif base_inc <= 0:
                self.lbl_safe_desc.configure(
                    text=f"💡 Aún no hay ingresos registrados para {self.current_ym}. Define un ingreso previsto en 'Metas del Mes'."
                )
            else:
                self.lbl_safe_desc.configure(
                    text="Tu capacidad libre para gastos variables en este periodo es $0 tras reservar fijos y ahorro/inversión."
                )

        # -------------------------------------------------------------
        # PILAR 1: GASTOS FIJOS (50%)
        # -------------------------------------------------------------
        p1_limit = overview["p1_target"]
        committed = overview["total_fixed_obligations"]
        paid = overview["fixed_paid"]
        pending = overview["pending_fixed"]

        self.p1_lbl_budget.configure(text=f"${p1_limit:,.0f} COP")
        self.p1_lbl_committed.configure(text=f"${committed:,.0f} COP")
        self.p1_lbl_paid.configure(text=f"${paid:,.0f} COP")
        self.p1_lbl_pending.configure(text=f"${pending:,.0f} COP")

        # Progreso de pago de fijos
        pct_paid = (paid / committed * 100.0) if committed > 0 else 100.0
        self.p1_progress.set(min(pct_paid / 100.0, 1.0))

        if pending == 0:
            self.p1_badge.configure(text="🟢 TODOS LOS FIJOS PAGADOS", fg_color="#059669")
            self.p1_progress.configure(progress_color="#10b981")
            self.p1_status_text.configure(text="✅ 100% de los gastos fijos del mes han sido cubiertos.", text_color="#10b981")
        elif committed > p1_limit and p1_limit > 0:
            self.p1_badge.configure(text="🔴 FIJOS EXCEDEN EL 50%", fg_color="#e11d48")
            self.p1_progress.configure(progress_color="#f43f5e")
            self.p1_status_text.configure(text=f"⚠️ Tus gastos fijos (${committed:,.0f}) superan la meta del 50% (${p1_limit:,.0f}).", text_color="#f43f5e")
        else:
            self.p1_badge.configure(text="🟡 PAGOS PENDIENTES POR VENCER", fg_color="#d97706")
            self.p1_progress.configure(progress_color="#f59e0b")
            self.p1_status_text.configure(text=f"Llevas pagado el {pct_paid:.0f}% (${paid:,.0f} COP). Quedan ${pending:,.0f} COP por saldar.", text_color=Theme.TEXT_SECONDARY)

        if self.show_p1_details:
            self._render_p1_details()

        # -------------------------------------------------------------
        # PILAR 2: AHORRO, PROVISIONES & INVERSIÓN (25%) [UNIFICADO]
        # -------------------------------------------------------------
        p2_target_total = overview.get("p_savings_invest_target", overview["p2_target"] + overview["p3_target"])
        moto_goal = overview["moto_target"]
        moto_done = overview["moto_contributed"]
        em_goal = overview["savings_target"]
        inv_goal = overview["invest_target"]
        if inv_goal <= 0:
            inv_goal = overview["p3_target"]
        inv_done = overview["total_invested_actual"]

        total_saved_invested = moto_done + inv_done
        total_p2_goal = max(p2_target_total, moto_goal + em_goal + inv_goal)

        self.p2_lbl_target_total.configure(text=f"${total_p2_goal:,.0f} COP")
        moto_status = f"${moto_done:,.0f} / ${moto_goal:,.0f}"
        self.p2_lbl_moto.configure(text=moto_status)
        self.p2_lbl_emergency.configure(text=f"Meta: ${em_goal:,.0f} COP")
        self.p2_lbl_invest.configure(text=f"${inv_done:,.0f} / ${inv_goal:,.0f}")

        pct_p2 = (total_saved_invested / total_p2_goal * 100.0) if total_p2_goal > 0 else 0.0
        self.p2_progress.set(min(pct_p2 / 100.0, 1.0))

        # Semáforo consolidado de Ahorro e Inversión
        moto_ok = moto_done >= moto_goal
        inv_ok = inv_done >= inv_goal if inv_goal > 0 else True

        if pct_p2 >= 100.0:
            self.p2_badge.configure(text="🟢 METAS 100% CUMPLIDAS", fg_color="#059669")
            self.p2_progress.configure(progress_color="#10b981")
            self.p2_status_text.configure(
                text=f"🎉 ¡Excelente! Provisión de moto asegurada y meta global de ahorro/inversión completada (${total_saved_invested:,.0f} COP).",
                text_color="#10b981"
            )
        elif moto_ok:
            self.p2_badge.configure(text="🟢 MOTO AL DÍA (EN PROCESO)", fg_color="#059669")
            self.p2_progress.configure(progress_color="#10b981")
            self.p2_status_text.configure(
                text=f"✅ Provisión de moto blindada ($150.000 COP en Fiducuenta). Llevas aportado el {pct_p2:.0f}% del pilar (${total_saved_invested:,.0f} COP).",
                text_color="#10b981"
            )
        else:
            self.p2_badge.configure(text="🟡 PENDIENTE MOTO (FIDUCUENTA)", fg_color="#d97706")
            self.p2_progress.configure(progress_color="#f59e0b")
            self.p2_status_text.configure(
                text=f"⚠️ Recuerda transferir ${moto_goal - moto_done:,.0f} COP a Fiducuenta para blindar SOAT y gastos anuales de la moto.",
                text_color="#f59e0b"
            )

        # -------------------------------------------------------------
        # PILAR 3: DINERO LIBRE PARA DISFRUTAR (25%)
        # -------------------------------------------------------------
        p3_limit = overview["p4_target"]  # lifestyle_pct
        var_spent = overview["actual_var_spent"]
        free_remaining = p3_limit - var_spent

        self.p3_lbl_limit.configure(text=f"${p3_limit:,.0f} COP")
        self.p3_lbl_spent.configure(text=f"${var_spent:,.0f} COP")

        if free_remaining >= 0:
            self.p3_lbl_remaining.configure(text=f"+${free_remaining:,.0f} COP", text_color="#10b981")
        else:
            self.p3_lbl_remaining.configure(text=f"-${abs(free_remaining):,.0f} COP", text_color="#f43f5e")

        daily_free = max(0.0, free_remaining) / max(1, overview["days_left"])
        self.p3_lbl_daily.configure(text=f"${daily_free:,.0f} COP / día")

        # SEMÁFORO ULTRA NOTORIO PILAR 3
        pct_p3 = (var_spent / p3_limit * 100.0) if p3_limit > 0 else (100.0 if var_spent > 0 else 0.0)
        self.p3_progress.set(min(pct_p3 / 100.0, 1.0))

        if pct_p3 >= 100.0 or free_remaining < 0:
            over_val = abs(free_remaining)
            self.p3_badge.configure(text="🔴 SOBREGIRADO", fg_color="#e11d48")
            self.p3_progress.configure(progress_color="#f43f5e")
            self.p3_status_text.configure(
                text=f"🚨 ALERTA: Has gastado el {pct_p3:.0f}% (${var_spent:,.0f} COP). Te has sobregirado en ${over_val:,.0f} COP frente a tu cupo libre.",
                text_color="#f43f5e"
            )
        elif pct_p3 >= 75.0:
            self.p3_badge.configure(text="🟡 ATENCIÓN: CERCA AL LÍMITE", fg_color="#d97706")
            self.p3_progress.configure(progress_color="#f59e0b")
            self.p3_status_text.configure(
                text=f"⚠️ PRECAUCIÓN: Llevas consumido el {pct_p3:.0f}% de tu dinero libre. Te restan ${free_remaining:,.0f} COP para el resto del mes.",
                text_color="#f59e0b"
            )
        else:
            self.p3_badge.configure(text="🟢 EN RANGO SEGURO", fg_color="#059669")
            self.p3_progress.configure(progress_color="#10b981")
            self.p3_status_text.configure(
                text=f"🎉 EXCELENTE: Solo has consumido el {pct_p3:.0f}% (${var_spent:,.0f} COP). Tienes ${free_remaining:,.0f} COP totalmente libres para disfrutar.",
                text_color="#10b981"
            )

        if self.show_p3_details:
            self._render_p3_details()

    # ==========================================
    # DESGLOSE DESPLEGABLE PILAR 1 (GASTOS FIJOS)
    # ==========================================

    def _render_p1_details(self):
        for widget in self.p1_details_box.winfo_children():
            widget.destroy()

        checklist = self.db.get_recurring_checklist_status(self.current_ym)
        cop_items = [i for i in checklist if i.get("currency") == "COP"]

        if not cop_items:
            ctk.CTkLabel(self.p1_details_box, text="No hay gastos fijos registrados en la plantilla.", font=ctk.CTkFont(size=12), text_color=Theme.TEXT_MUTED).pack(pady=12)
            return

        ctk.CTkLabel(self.p1_details_box, text="📋 Checklist de Gastos Fijos de este Mes:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=14, pady=(10, 6))

        for item in cop_items:
            row = ctk.CTkFrame(self.p1_details_box, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=3)

            is_paid = item.get("is_paid", False)
            status_dot = "🟢 Pagado" if is_paid else f"🟡 Pendiente (Vence día {item.get('due_day', '')})"
            status_clr = "#10b981" if is_paid else "#f59e0b"

            ctk.CTkLabel(row, text=f"• {item.get('description')} ({item.get('category')})", font=ctk.CTkFont(size=12), text_color=Theme.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(row, text=f"${item.get('amount', 0):,.0f} COP • {status_dot}", font=ctk.CTkFont(size=12, weight="bold"), text_color=status_clr).pack(side="right")

    # ==========================================
    # DESGLOSE CON PREVISUALIZACIÓN DE COMPRAS (PILAR 3)
    # ==========================================

    def _render_p3_details(self):
        for widget in self.p3_details_box.winfo_children():
            widget.destroy()

        cats = self.db.get_category_budgets(self.current_ym, self.active_currency)
        fixed_cats = {"Hogar & Servicios", "Servicios Públicos", "Arriendo / Hipoteca", "Imprevistos & Emergencias"}
        var_cats = [c for c in cats if c["category"] not in fixed_cats and c.get("spent", 0.0) > 0]

        if not var_cats:
            ctk.CTkLabel(self.p3_details_box, text="No hay gastos variables registrados en este mes.", font=ctk.CTkFont(size=12), text_color=Theme.TEXT_MUTED).pack(pady=12)
            return

        ctk.CTkLabel(
            self.p3_details_box,
            text="🏷️ Desglose de Gastos Variables (Haz clic en '👁️ Ver compras' para auditar cada gasto):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=14, pady=(10, 8))

        # Ordenar categorías por gasto descendente (las de mayor gasto primero)
        var_cats.sort(key=lambda c: c.get("spent", 0.0), reverse=True)

        for cat in var_cats:
            cat_name = cat.get("category", "")
            spent = cat.get("spent", 0.0)
            tx_count = cat.get("tx_count", 0)
            icon = cat.get("icon", "🏷️")

            card_cat = ctk.CTkFrame(self.p3_details_box, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card_cat.pack(fill="x", padx=12, pady=4)

            head_row = ctk.CTkFrame(card_cat, fg_color="transparent")
            head_row.pack(fill="x", padx=12, pady=8)

            ctk.CTkLabel(
                head_row,
                text=f"{icon}  {cat_name}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(side="left")

            is_expanded = cat_name in self.expanded_categories
            btn_toggle = ctk.CTkButton(
                head_row,
                text="🔼 Ocultar compras" if is_expanded else "👁️ Ver compras ▾",
                width=130,
                height=24,
                corner_radius=6,
                fg_color=Theme.BG_CARD_SUBTLE,
                hover_color=Theme.BORDER_DEFAULT,
                text_color=Theme.ACCENT_BLUE,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda cn=cat_name: self._toggle_category_expansion(cn)
            )
            btn_toggle.pack(side="right", padx=(8, 0))

            ctk.CTkLabel(
                head_row,
                text=f"${spent:,.0f} COP ({tx_count} compras)",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.ACCENT_ROSE
            ).pack(side="right")

            # Si la categoría está expandida, renderizar las transacciones individuales
            if is_expanded:
                tx_box = ctk.CTkFrame(card_cat, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=6)
                tx_box.pack(fill="x", padx=10, pady=(0, 10))

                tx_list = self.db.get_category_expenses_detail(self.current_ym, cat_name, self.active_currency)
                if not tx_list:
                    ctk.CTkLabel(tx_box, text="No se encontraron detalles.", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_MUTED).pack(pady=6)
                else:
                    for tx in tx_list:
                        tx_row = ctk.CTkFrame(tx_box, fg_color="transparent")
                        tx_row.pack(fill="x", padx=12, pady=3)

                        # Fecha formateada (e.g. "18 Sep")
                        dt_raw = tx.get("date", "")
                        try:
                            dt_obj = datetime.strptime(dt_raw, "%Y-%m-%d")
                            dt_str = dt_obj.strftime("%d %b")
                        except Exception:
                            dt_str = dt_raw

                        # Método de pago
                        pm = tx.get("payment_method", "DEBIT")
                        pm_str = "💳 TC" if pm == "CREDIT_CARD" else "🏦 Débito"

                        # Descripción / Nota
                        notes = tx.get("notes", "").strip()
                        desc_text = notes if notes else "Gasto sin nota"

                        left_text = f"• {dt_str} | {desc_text}  ({pm_str})"
                        ctk.CTkLabel(
                            tx_row,
                            text=left_text,
                            font=ctk.CTkFont(size=12),
                            text_color=Theme.TEXT_SECONDARY
                        ).pack(side="left")

                        amt = tx.get("amount", 0.0)
                        ctk.CTkLabel(
                            tx_row,
                            text=f"${amt:,.0f} COP",
                            font=ctk.CTkFont(size=12, weight="bold"),
                            text_color=Theme.TEXT_PRIMARY
                        ).pack(side="right")

    def _toggle_category_expansion(self, cat_name: str):
        if cat_name in self.expanded_categories:
            self.expanded_categories.remove(cat_name)
        else:
            self.expanded_categories.add(cat_name)
        self._render_p3_details()

    # ==========================================
    # MODALES
    # ==========================================

    def _open_budget_settings(self):
        BudgetSettingsModal(
            self.winfo_toplevel(),
            self.db,
            on_success=self.refresh_data
        )

    def _open_monthly_targets(self):
        MonthlyTargetsModal(
            self.winfo_toplevel(),
            self.db,
            year_month=self.current_ym,
            on_success=self.refresh_data
        )
