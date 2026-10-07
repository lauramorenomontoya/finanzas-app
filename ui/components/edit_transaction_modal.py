"""
Modal Universal para Editar Cualquier Registro:
Soporta edición de transacciones USD, gastos/ingresos COP, conversiones y movimientos de inversión.
Diseño responsivo con pie fijo de Guardar/Cancelar y cuerpo desplazable.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget
from ui.utils.modal_helper import center_window


from ui.components.base_modal import BaseModal

class EditTransactionModal(BaseModal):
    def __init__(
        self,
        parent,
        db_manager,
        source_table: str,
        record: Dict[str, Any],
        on_success: Optional[Callable[[], None]] = None
    ):
        self.db = db_manager
        self.source_table = source_table
        self.record = record
        self.on_success = on_success

        super().__init__(parent, title="Editar Registro Financiero", width=520, height=620, min_width=480, min_height=520, resizable_x=True, resizable_y=True)

        self._build_ui()

    def _build_ui(self):
        main_frame = self.create_standard_frame()

        # 1. Encabezado Fijo Superior
        mod_label = "Ingresos / Bóveda USD" if self.source_table == "usd_transactions" else (
            "Presupuesto / Egresos COP" if self.source_table == "cop_transactions" else (
                "Puente Conversión" if self.source_table == "conversions" else "Inversiones"
            )
        )
        
        header = self.create_header(main_frame, "Modificar Registro", icon="✏️")
        ctk.CTkLabel(
            header,
            text=f"Módulo: {mod_label} • ID: #{self.record.get('id', '')}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # 2. Pie Fijo Inferior con Botones
        self.create_footer_buttons(
            main_frame,
            on_confirm=self._handle_save,
            on_cancel=self.destroy,
            confirm_text="💾 Guardar Cambios",
            cancel_text="Cancelar",
            is_destructive=False
        )

        footer_error_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_error_container.pack(side="bottom", fill="x", padx=Theme.SPACING_LG, pady=(0, 0))

        self.lbl_error = ctk.CTkLabel(footer_error_container, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", pady=(0, Theme.SPACING_XS))

        # 3. Cuerpo Desplazable Central
        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Campo Fecha con DatePickerWidget
        ctk.CTkLabel(scroll_body, text="Fecha del Movimiento:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.date_entry = DatePickerWidget(scroll_body, initial_date=str(self.record.get("date", datetime.now().strftime("%Y-%m-%d"))), height=36)
        self.date_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # Campos específicos según la tabla de origen
        if self.source_table == "usd_transactions":
            # Plataforma
            ctk.CTkLabel(scroll_body, text="Plataforma / Origen USD:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
            self.category_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.category_entry.insert(0, str(self.record.get("platform", "")))
            self.category_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

            # Monto USD
            ctk.CTkLabel(scroll_body, text="Monto en Dólares ($ USD):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
            self.amount_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.amount_entry.insert(0, str(self.record.get("amount", "")))
            self.amount_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        elif self.source_table == "cop_transactions":
            # Categoría
            ctk.CTkLabel(scroll_body, text="Categoría del Movimiento:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
            self.category_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.category_entry.insert(0, str(self.record.get("category", "")))
            self.category_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

            # Monto COP
            ctk.CTkLabel(scroll_body, text="Monto en Pesos ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
            self.amount_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.amount_entry.insert(0, str(int(float(self.record.get("amount", 0)))))
            self.amount_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

            # Fila: Método de Pago y Switch Gasto Fijo
            row_opts = ctk.CTkFrame(scroll_body, fg_color="transparent")
            row_opts.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

            self.payment_combo = ctk.CTkComboBox(
                row_opts,
                values=["Débito / Cuenta", "Tarjeta de Crédito", "Efectivo"],
                height=34,
                width=170,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.BG_INPUT,
                border_color=Theme.BORDER_DEFAULT,
                dropdown_fg_color=Theme.BG_CARD
            )
            pm = self.record.get("payment_method", "DEBIT")
            pm_map = {"CREDIT_CARD": "Tarjeta de Crédito", "CASH": "Efectivo", "DEBIT": "Débito / Cuenta"}
            self.payment_combo.set(pm_map.get(pm, "Débito / Cuenta"))
            self.payment_combo.pack(side="left")

            self.fixed_switch = ctk.CTkSwitch(
                row_opts,
                text="Gasto Fijo",
                font=ctk.CTkFont(size=11),
                text_color=Theme.TEXT_SECONDARY,
                progress_color=Theme.ERROR
            )
            if self.record.get("is_fixed", 0) == 1:
                self.fixed_switch.select()
            self.fixed_switch.pack(side="right")

        elif self.source_table == "conversions":
            # Monto USD
            ctk.CTkLabel(scroll_body, text="Monto Retirado ($ USD):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
            self.amount_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.amount_entry.insert(0, str(self.record.get("usd_amount", "")))
            self.amount_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

            # Tasa de cambio
            ctk.CTkLabel(scroll_body, text="Tasa de Cambio (COP/USD):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
            self.rate_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.rate_entry.insert(0, str(self.record.get("exchange_rate", "")))
            self.rate_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        else:  # account_transactions
            ctk.CTkLabel(scroll_body, text="Monto del Movimiento:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
            self.amount_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.amount_entry.insert(0, str(self.record.get("amount", "")))
            self.amount_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # Campo Notas
        ctk.CTkLabel(scroll_body, text="Notas / Descripción Detallada:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.notes_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.notes_entry.insert(0, str(self.record.get("notes", "") or ""))
        self.notes_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_MD))

    def _handle_save(self):
        date_str = self.date_entry.get().strip()
        notes = self.notes_entry.get().strip()
        rec_id = self.record["id"]

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.lbl_error.configure(text="⚠️ La fecha debe tener formato YYYY-MM-DD.")
            return

        try:
            if self.source_table == "usd_transactions":
                platform = self.category_entry.get().strip()
                amt = float(self.amount_entry.get().strip().replace(",", "."))
                if not platform or amt <= 0:
                    raise ValueError()
                success, msg = self.db.update_usd_transaction(rec_id, date_str, platform, amt, notes)

            elif self.source_table == "cop_transactions":
                category = self.category_entry.get().strip()
                amt = float(self.amount_entry.get().strip().replace(".", "").replace(",", "."))
                if not category or amt <= 0:
                    raise ValueError()
                is_fixed = bool(self.fixed_switch.get())
                pm_choice = self.payment_combo.get()
                pm_code = "CREDIT_CARD" if "Tarjeta" in pm_choice else ("CASH" if "Efectivo" in pm_choice else "DEBIT")
                success, msg = self.db.update_cop_transaction(rec_id, date_str, category, amt, is_fixed, pm_code, notes)

            elif self.source_table == "conversions":
                usd_amt = float(self.amount_entry.get().strip().replace(",", "."))
                rate = float(self.rate_entry.get().strip().replace(",", "."))
                if usd_amt <= 0 or rate <= 0:
                    raise ValueError()
                success, msg = self.db.update_conversion(rec_id, date_str, usd_amt, rate, notes)

            else:  # account_transactions
                amt = float(self.amount_entry.get().strip().replace(".", "").replace(",", "."))
                if amt <= 0:
                    raise ValueError()
                success, msg = self.db.update_account_transaction(rec_id, date_str, amt, notes)

            if success:
                if self.on_success:
                    self.on_success()
                self.destroy()
            else:
                self.lbl_error.configure(text=f"⚠️ {msg}")

        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa valores numéricos válidos mayores a 0.")
        except Exception as e:
            self.lbl_error.configure(text=f"⚠️ Error: {str(e)}")
