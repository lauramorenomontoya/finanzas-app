"""
Modal para registrar Pagos de Tarjeta de Crédito en CustomTkinter.
Diseño responsivo con pie fijo de botones y cuerpo desplazable.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget
from ui.utils.modal_helper import center_window


class CCPaymentModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.on_success = on_success

        self.title("Pagar Tarjeta de Crédito")
        self.geometry("480x570")
        self.minsize(440, 500)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui()

    def _center_window(self, parent):
        center_window(self, parent, 480, 570)

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Encabezado Fijo
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        ctk.CTkLabel(
            header,
            text="💳 Pago de Tarjeta de Crédito",
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Descuenta de tu cuenta operativa para saldar tu deuda de TC.",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # 2. Pie Fijo Inferior con Botones (SIEMPRE VISIBLE)
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=(0, 16))

        self.lbl_error = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE, wraplength=420)
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

        btn_confirm = ctk.CTkButton(
            btn_row,
            text="💸 Confirmar Pago",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            command=self._handle_pay
        )
        btn_confirm.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 3. Cuerpo Central
        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Tarjeta de Estado de Deuda
        debt_box = ctk.CTkFrame(scroll_body, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        debt_box.pack(fill="x", padx=6, pady=(0, 12))

        debt_inner = ctk.CTkFrame(debt_box, fg_color="transparent")
        debt_inner.pack(fill="x", padx=14, pady=10)

        current_debt = self.db.get_credit_card_debt()
        cop_bal = self.db.get_cop_balance()

        ctk.CTkLabel(debt_inner, text="DEUDA PENDIENTE TC:", font=ctk.CTkFont(size=10, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(anchor="w")
        ctk.CTkLabel(debt_inner, text=f"${current_debt:,.0f} COP", font=ctk.CTkFont(size=20, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(anchor="w")
        ctk.CTkLabel(debt_inner, text=f"Disponible en cuenta: ${cop_bal:,.0f} COP", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        # Campo Monto a Pagar
        ctk.CTkLabel(scroll_body, text="Monto a Pagar ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        
        amount_row = ctk.CTkFrame(scroll_body, fg_color="transparent")
        amount_row.pack(fill="x", padx=6, pady=(0, 4))

        self.amount_entry = ctk.CTkEntry(
            amount_row,
            placeholder_text=f"Ej: {int(current_debt)}",
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.amount_entry.insert(0, str(int(current_debt)) if current_debt > 0 else "")
        self.amount_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_full_pay = ctk.CTkButton(
            amount_row,
            text="Todo",
            width=55,
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_GREEN,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._set_full_amount(current_debt)
        )
        btn_full_pay.pack(side="right")

        ctk.CTkLabel(
            scroll_body,
            text="💡 Puedes abonar una parte o presionar 'Todo' para saldarla completa.",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", padx=6, pady=(0, 10))

        # Campo Fecha con DatePickerWidget
        ctk.CTkLabel(scroll_body, text="Fecha del Pago:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.date_entry = DatePickerWidget(scroll_body, height=36)
        self.date_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Campo Notas Opcional
        ctk.CTkLabel(scroll_body, text="Notas / Concepto (Opcional):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.notes_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text="Ej: Abono quincenal / Pago parcial TC",
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.notes_entry.pack(fill="x", padx=6, pady=(0, 12))

    def _set_full_amount(self, debt: float):
        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, str(int(debt)))

    def _clean_cop_amount(self, raw: str) -> float:
        s = raw.strip().replace("$", "").replace("COP", "").replace("\xa0", "").replace(" ", "")
        if not s:
            raise ValueError("Monto vacío")

        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            parts = s.split(",")
            if len(parts) > 2:
                s = "".join(parts)
            elif len(parts) == 2 and len(parts[1]) == 3:
                s = "".join(parts)
            else:
                s = s.replace(",", ".")
        elif "." in s:
            parts = s.split(".")
            if len(parts) > 2:
                s = "".join(parts)
            elif len(parts) == 2 and len(parts[1]) == 3:
                s = "".join(parts)

        val = float(s)
        if val <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return val

    def _handle_pay(self):
        try:
            amount = self._clean_cop_amount(self.amount_entry.get())
        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa un monto válido mayor a 0.")
            return

        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.lbl_error.configure(text="⚠️ Selecciona una fecha válida.")
            return

        notes = self.notes_entry.get().strip()

        try:
            success, msg = self.db.pay_credit_card(date=date_str, amount=amount, notes=notes)
            if success:
                if self.on_success:
                    self.on_success()
                self.destroy()
            else:
                self.lbl_error.configure(text=f"⚠️ {msg}")
        except Exception as e:
            self.lbl_error.configure(text=f"⚠️ Error al registrar pago: {str(e)}")
