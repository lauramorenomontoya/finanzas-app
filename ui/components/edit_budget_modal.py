"""
Modales para el Módulo de Presupuestos & Metas Financieras:
1. CategoryBudgetModal: Asigna o edita el presupuesto límite de una categoría.
2. MonthlyTargetsModal: Configura metas del mes (Ingreso estimado, Provisión moto, Ahorro, Inversión).
3. BudgetSettingsModal: Personaliza los porcentajes de los 4 Pilares Financieros.
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from ui.utils.modal_helper import center_window


from ui.components.base_modal import BaseModal

class CategoryBudgetModal(BaseModal):
    def __init__(
        self,
        parent,
        db_manager,
        year_month: str,
        category: str,
        current_budget: float = 0.0,
        currency: str = "COP",
        current_notes: str = "",
        on_success: Optional[Callable[[], None]] = None
    ):
        self.db = db_manager
        self.year_month = year_month
        self.category = category
        self.currency = currency
        self.on_success = on_success

        super().__init__(parent, title=f"Presupuesto: {category}", width=460, height=440, min_width=420, min_height=400, resizable_x=True, resizable_y=True)

        self._build_ui(current_budget, current_notes)

    def _build_ui(self, current_budget: float, current_notes: str):
        main_frame = self.create_standard_frame()

        # Encabezado
        header = self.create_header(main_frame, f"Límite para {self.category}", icon="🎯")

        ctk.CTkLabel(
            header,
            text=f"Periodo: {self.year_month} • Moneda: {self.currency}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Pie fijo de botones
        self.create_footer_buttons(
            main_frame,
            on_confirm=self._handle_save,
            on_cancel=self.destroy,
            confirm_text="💾 Guardar Límite",
            cancel_text="Cancelar",
            is_destructive=False
        )
        
        footer_error_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_error_container.pack(side="bottom", fill="x", padx=Theme.SPACING_LG, pady=(0, 0))

        self.lbl_error = ctk.CTkLabel(footer_error_container, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", pady=(0, Theme.SPACING_XS))

        # Cuerpo
        body = ctk.CTkFrame(main_frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))

        ctk.CTkLabel(
            body,
            text=f"Monto Presupuestado Mensual (${self.currency}):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(Theme.SPACING_SM, Theme.SPACING_XS))

        self.amount_entry = ctk.CTkEntry(
            body,
            placeholder_text="Ej: 500000",
            height=38,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        if current_budget > 0:
            self.amount_entry.insert(0, str(int(current_budget) if self.currency == "COP" else current_budget))
        self.amount_entry.pack(fill="x", pady=(0, Theme.SPACING_SM))

        ctk.CTkLabel(
            body,
            text="💡 Ingresa 0 para eliminar el límite presupuestado de esta categoría.",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, Theme.SPACING_MD))

        ctk.CTkLabel(
            body,
            text="Notas / Justificación (Opcional):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, Theme.SPACING_XS))

        self.notes_entry = ctk.CTkEntry(
            body,
            placeholder_text="Ej: Techo acordado para salidas del mes",
            height=36,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.notes_entry.insert(0, current_notes)
        self.notes_entry.pack(fill="x")

    def _handle_save(self):
        raw = self.amount_entry.get().strip().replace("$", "").replace("COP", "").replace(" ", "").replace("\xa0", "")
        if not raw:
            raw = "0"
        
        # Limpiar separadores
        if "," in raw and "." in raw:
            raw = raw.replace(".", "").replace(",", ".")
        elif "," in raw:
            raw = raw.replace(",", ".")
        elif "." in raw:
            parts = raw.split(".")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
                raw = "".join(parts)

        try:
            amount = float(raw)
            if amount < 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa un monto numérico válido mayor o igual a 0.")
            return

        notes = self.notes_entry.get().strip()
        success, msg = self.db.set_category_budget(
            year_month=self.year_month,
            category=self.category,
            amount=amount,
            currency=self.currency,
            notes=notes
        )

        if success:
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            self.lbl_error.configure(text=f"⚠️ {msg}")


class MonthlyTargetsModal(BaseModal):
    def __init__(
        self,
        parent,
        db_manager,
        year_month: str,
        on_success: Optional[Callable[[], None]] = None
    ):
        self.db = db_manager
        self.year_month = year_month
        self.on_success = on_success

        super().__init__(parent, title=f"Metas Financieras ({year_month})", width=520, height=600, min_width=480, min_height=540, resizable_x=True, resizable_y=True)

        self._build_ui()

    def _build_ui(self):
        targets = self.db.get_monthly_targets(self.year_month)

        main_frame = self.create_standard_frame()

        # Encabezado
        header = self.create_header(main_frame, f"Metas & Ahorro ({self.year_month})", icon="🎯")

        ctk.CTkLabel(
            header,
            text="Define tus ingresos previstos, fondo de moto y metas de inversión.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Pie fijo de botones
        self.create_footer_buttons(
            main_frame,
            on_confirm=self._handle_save,
            on_cancel=self.destroy,
            confirm_text="💾 Guardar Metas",
            cancel_text="Cancelar",
            is_destructive=False
        )

        footer_error_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_error_container.pack(side="bottom", fill="x", padx=Theme.SPACING_LG, pady=(0, 0))

        self.lbl_error = ctk.CTkLabel(footer_error_container, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", pady=(0, Theme.SPACING_XS))

        # Cuerpo scrollable
        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # 1. Ingreso Estimado
        ctk.CTkLabel(scroll, text="📥 Ingreso Total Previsto para el Mes ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(Theme.SPACING_XS, 2))
        self.inc_entry = ctk.CTkEntry(scroll, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.inc_entry.insert(0, str(int(targets.get("estimated_income_cop", 0))))
        self.inc_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # 2. Provisión Moto Fiducuenta
        ctk.CTkLabel(scroll, text="🏍️ Provisión Moto Fiducuenta ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_GREEN).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        ctk.CTkLabel(scroll, text="Fondo fijo mensual destinado a SOAT, tecno, impuestos y mantenimientos anuales.", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.moto_entry = ctk.CTkEntry(scroll, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.moto_entry.insert(0, str(int(targets.get("moto_target_cop", 150000))))
        self.moto_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # 3. Meta Inversión (Fidurenta / Trii)
        ctk.CTkLabel(scroll, text="📈 Meta de Inversión Mensual ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_BLUE).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        ctk.CTkLabel(scroll, text="Capital a transferir este mes a Fidurenta Bancolombia, Trii u otros activos.", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.invest_entry = ctk.CTkEntry(scroll, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.invest_entry.insert(0, str(int(targets.get("invest_target_cop", 0))))
        self.invest_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # 4. Ahorro de Emergencia / Mis Cosas
        ctk.CTkLabel(scroll, text="🛡️ Ahorro de Emergencia & Metas Personales ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_INDIGO).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.savings_entry = ctk.CTkEntry(scroll, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.savings_entry.insert(0, str(int(targets.get("emergency_savings_target_cop", 0))))
        self.savings_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # 5. Notas
        ctk.CTkLabel(scroll, text="Notas del Mes (Opcional):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.notes_entry = ctk.CTkEntry(scroll, placeholder_text="Ej: Priorizar pago de moto y aporte a Fidurenta", height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=12))
        self.notes_entry.insert(0, targets.get("notes", ""))
        self.notes_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

    def _parse_num(self, val_str: str) -> float:
        s = val_str.strip().replace("$", "").replace("COP", "").replace(" ", "").replace("\xa0", "")
        if not s:
            return 0.0
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        elif "." in s:
            parts = s.split(".")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
                s = "".join(parts)
        return float(s)

    def _handle_save(self):
        try:
            inc = self._parse_num(self.inc_entry.get())
            moto = self._parse_num(self.moto_entry.get())
            invest = self._parse_num(self.invest_entry.get())
            savings = self._parse_num(self.savings_entry.get())
            if inc < 0 or moto < 0 or invest < 0 or savings < 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa montos válidos mayores o iguales a 0.")
            return

        notes = self.notes_entry.get().strip()
        success, msg = self.db.save_monthly_targets(
            year_month=self.year_month,
            estimated_income_cop=inc,
            moto_target_cop=moto,
            emergency_savings_target_cop=savings,
            invest_target_cop=invest,
            notes=notes
        )

        if success:
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            self.lbl_error.configure(text=f"⚠️ {msg}")


class BudgetSettingsModal(BaseModal):
    def __init__(
        self,
        parent,
        db_manager,
        on_success: Optional[Callable[[], None]] = None
    ):
        self.db = db_manager
        self.on_success = on_success

        super().__init__(parent, title="Reglas Financieras (4 Pilares)", width=500, height=560, min_width=460, min_height=500, resizable_x=True, resizable_y=True)

        self._build_ui()

    def _build_ui(self):
        settings = self.db.get_budget_settings()

        main_frame = self.create_standard_frame()

        # Encabezado
        header = self.create_header(main_frame, "Distribución de los 4 Pilares", icon="⚖️")

        ctk.CTkLabel(
            header,
            text="Configura tus porcentajes ideales (inspirado en la regla 50/30/20). La suma debe ser 100%.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Pie fijo de botones
        self.create_footer_buttons(
            main_frame,
            on_confirm=self._handle_save,
            on_cancel=self.destroy,
            confirm_text="💾 Guardar Porcentajes",
            cancel_text="Cancelar",
            is_destructive=False
        )

        footer_error_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_error_container.pack(side="bottom", fill="x", padx=Theme.SPACING_LG, pady=(0, 0))

        self.lbl_sum = ctk.CTkLabel(footer_error_container, text="Suma actual: 100%", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_GREEN)
        self.lbl_sum.pack(anchor="w", pady=(0, Theme.SPACING_XS))

        # Cuerpo
        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Campo 1: Necesidades & Fijos (50%)
        ctk.CTkLabel(scroll, text="🏠 Pilar 1: Necesidades & Gastos Fijos (%):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(Theme.SPACING_XS, 2))
        self.needs_entry = ctk.CTkEntry(scroll, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.needs_entry.insert(0, str(settings["needs_pct"]))
        self.needs_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))
        self.needs_entry.bind("<KeyRelease>", lambda _: self._update_sum())

        # Campo 2: Provisiones & Ahorro (15%)
        ctk.CTkLabel(scroll, text="🛡️ Pilar 2: Provisiones (Moto) & Ahorro Emergencia (%):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_GREEN).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.savings_entry = ctk.CTkEntry(scroll, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.savings_entry.insert(0, str(settings["savings_pct"]))
        self.savings_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))
        self.savings_entry.bind("<KeyRelease>", lambda _: self._update_sum())

        # Campo 3: Inversión (10%)
        ctk.CTkLabel(scroll, text="📈 Pilar 3: Inversiones (Fidurenta / Trii) (%):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_BLUE).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.invest_entry = ctk.CTkEntry(scroll, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.invest_entry.insert(0, str(settings["invest_pct"]))
        self.invest_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))
        self.invest_entry.bind("<KeyRelease>", lambda _: self._update_sum())

        # Campo 4: Dinero Libre para Disfrutar (25%)
        ctk.CTkLabel(scroll, text="🎉 Pilar 4: Dinero Libre para Disfrutar (%):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.lifestyle_entry = ctk.CTkEntry(scroll, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.lifestyle_entry.insert(0, str(settings["lifestyle_pct"]))
        self.lifestyle_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))
        self.lifestyle_entry.bind("<KeyRelease>", lambda _: self._update_sum())

        # Provisión Moto mensual por defecto
        ctk.CTkLabel(scroll, text="🏍️ Provisión Moto Mensual por Defecto ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(Theme.SPACING_XS, 2))
        self.moto_def_entry = ctk.CTkEntry(scroll, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.moto_def_entry.insert(0, str(int(settings.get("default_moto_amount", 150000))))
        self.moto_def_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))

        self._update_sum()

    def _update_sum(self):
        try:
            n = float(self.needs_entry.get() or 0)
            s = float(self.savings_entry.get() or 0)
            i = float(self.invest_entry.get() or 0)
            l = float(self.lifestyle_entry.get() or 0)
            total = round(n + s + i + l, 2)
            if total == 100.0:
                self.lbl_sum.configure(text=f"✅ Suma total: {total}% (Perfecto)", text_color=Theme.ACCENT_GREEN)
            else:
                self.lbl_sum.configure(text=f"⚠️ Suma total: {total}% (Debe ser exactamente 100%)", text_color=Theme.ACCENT_ROSE)
        except ValueError:
            self.lbl_sum.configure(text="⚠️ Revisa los números ingresados.", text_color=Theme.ACCENT_ROSE)

    def _handle_save(self):
        try:
            n = float(self.needs_entry.get())
            s = float(self.savings_entry.get())
            i = float(self.invest_entry.get())
            l = float(self.lifestyle_entry.get())
            moto_def = float(self.moto_def_entry.get().replace(".", "").replace(",", "").replace("$", ""))
            total = round(n + s + i + l, 2)
            if total != 100.0:
                self.lbl_sum.configure(text=f"⚠️ La suma debe ser exactamente 100% (actual: {total}%).", text_color=Theme.ACCENT_ROSE)
                return
        except ValueError:
            self.lbl_sum.configure(text="⚠️ Ingresa porcentajes numéricos válidos.", text_color=Theme.ACCENT_ROSE)
            return

        success, msg = self.db.update_budget_settings(n, s, i, l, moto_def)
        if success:
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            self.lbl_sum.configure(text=f"⚠️ {msg}", text_color=Theme.ACCENT_ROSE)
