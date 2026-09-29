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


class EditTransactionModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        source_table: str,
        record: Dict[str, Any],
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.source_table = source_table
        self.record = record
        self.on_success = on_success

        self.title("Editar Registro Financiero")
        self.geometry("520x620")
        self.minsize(480, 520)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui()

    def _center_window(self, parent):
        center_window(self, parent, 520, 620)

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Encabezado Fijo Superior
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        ctk.CTkLabel(
            header,
            text="✏️ Modificar Registro",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        mod_label = "Ingresos / Bóveda USD" if self.source_table == "usd_transactions" else (
            "Presupuesto / Egresos COP" if self.source_table == "cop_transactions" else (
                "Puente Conversión" if self.source_table == "conversions" else "Inversiones"
            )
        )
        ctk.CTkLabel(
            header,
            text=f"Módulo: {mod_label} • ID: #{self.record.get('id', '')}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # 2. Pie Fijo Inferior con Botones (SIEMPRE VISIBLE)
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=(0, 16))

        self.lbl_error = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", pady=(0, 6))

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(fill="x")

        btn_cancel = ctk.CTkButton(
            btn_row,
            text="Cancelar",
            font=ctk.CTkFont(size=12),
            height=38,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_SECONDARY,
            command=self.destroy
        )
        btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_save = ctk.CTkButton(
            btn_row,
            text="💾 Guardar Cambios",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            command=self._handle_save
        )
        btn_save.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 3. Cuerpo Desplazable Central
        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        # Campo Fecha con DatePickerWidget
        ctk.CTkLabel(scroll_body, text="Fecha del Movimiento:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.date_entry = DatePickerWidget(scroll_body, initial_date=str(self.record.get("date", datetime.now().strftime("%Y-%m-%d"))), height=36)
        self.date_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Campos específicos según la tabla de origen
        if self.source_table == "usd_transactions":
            # Plataforma
            ctk.CTkLabel(scroll_body, text="Plataforma / Origen USD:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
            self.category_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.category_entry.insert(0, str(self.record.get("platform", "")))
            self.category_entry.pack(fill="x", padx=6, pady=(0, 12))

            # Monto USD
            ctk.CTkLabel(scroll_body, text="Monto en Dólares ($ USD):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
            self.amount_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.amount_entry.insert(0, str(self.record.get("amount", "")))
            self.amount_entry.pack(fill="x", padx=6, pady=(0, 12))

        elif self.source_table == "cop_transactions":
            # Categoría
            ctk.CTkLabel(scroll_body, text="Categoría del Movimiento:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
            self.category_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.category_entry.insert(0, str(self.record.get("category", "")))
            self.category_entry.pack(fill="x", padx=6, pady=(0, 12))

            # Monto COP
            ctk.CTkLabel(scroll_body, text="Monto en Pesos ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
            self.amount_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.amount_entry.insert(0, str(int(float(self.record.get("amount", 0)))))
            self.amount_entry.pack(fill="x", padx=6, pady=(0, 12))

            # Fila: Método de Pago y Switch Gasto Fijo
            row_opts = ctk.CTkFrame(scroll_body, fg_color="transparent")
            row_opts.pack(fill="x", padx=6, pady=(0, 12))

            self.payment_combo = ctk.CTkComboBox(
                row_opts,
                values=["Débito / Cuenta", "Tarjeta de Crédito", "Efectivo"],
                height=34,
                width=170,
                corner_radius=6,
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
                progress_color="#f43f5e"
            )
            if self.record.get("is_fixed", 0) == 1:
                self.fixed_switch.select()
            self.fixed_switch.pack(side="right")

        elif self.source_table == "conversions":
            # Monto USD
            ctk.CTkLabel(scroll_body, text="Monto Retirado ($ USD):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
            self.amount_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.amount_entry.insert(0, str(self.record.get("usd_amount", "")))
            self.amount_entry.pack(fill="x", padx=6, pady=(0, 12))

            # Tasa de cambio
            ctk.CTkLabel(scroll_body, text="Tasa de Cambio (COP/USD):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
            self.rate_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.rate_entry.insert(0, str(self.record.get("exchange_rate", "")))
            self.rate_entry.pack(fill="x", padx=6, pady=(0, 12))

        else:  # account_transactions
            ctk.CTkLabel(scroll_body, text="Monto del Movimiento:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
            self.amount_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
            self.amount_entry.insert(0, str(self.record.get("amount", "")))
            self.amount_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Campo Notas
        ctk.CTkLabel(scroll_body, text="Notas / Descripción Detallada:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.notes_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.notes_entry.insert(0, str(self.record.get("notes", "") or ""))
        self.notes_entry.pack(fill="x", padx=6, pady=(0, 14))

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
