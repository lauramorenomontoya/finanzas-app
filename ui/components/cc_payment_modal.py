"""
Modal para registrar Pagos de Tarjeta de Crédito en CustomTkinter.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable
from ui.theme import Theme


class CCPaymentModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        on_success: Callable[[], None] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.on_success = on_success

        self.title("Pagar Tarjeta de Crédito")
        self.geometry("450x420")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Encabezado
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 12))

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

        # Tarjeta de Estado de Deuda
        debt_box = ctk.CTkFrame(main_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        debt_box.pack(fill="x", padx=20, pady=(0, 14))

        debt_inner = ctk.CTkFrame(debt_box, fg_color="transparent")
        debt_inner.pack(fill="x", padx=14, pady=10)

        current_debt = self.db.get_credit_card_debt()
        cop_bal = self.db.get_cop_balance()

        ctk.CTkLabel(debt_inner, text="DEUDA PENDIENTE TC:", font=ctk.CTkFont(size=10, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(anchor="w")
        ctk.CTkLabel(debt_inner, text=f"${current_debt:,.0f} COP", font=ctk.CTkFont(size=20, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(anchor="w")
        ctk.CTkLabel(debt_inner, text=f"Disponible en cuenta: ${cop_bal:,.0f} COP", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        # Campo Monto a Pagar
        ctk.CTkLabel(main_frame, text="Monto a Pagar ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 4))
        
        amount_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        amount_row.pack(fill="x", padx=20, pady=(0, 12))

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

        # Campo Fecha con DatePickerWidget
        ctk.CTkLabel(main_frame, text="Fecha del Pago:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 4))
        from ui.components.date_picker import DatePickerWidget
        self.date_entry = DatePickerWidget(main_frame, height=36)
        self.date_entry.pack(fill="x", padx=20, pady=(0, 12))

        # Mensaje de error
        self.lbl_error = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", padx=20, pady=(0, 8))

        # Botón Confirmar Pago
        btn_confirm = ctk.CTkButton(
            main_frame,
            text="💸 Confirmar Pago de Tarjeta",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            command=self._handle_pay
        )
        btn_confirm.pack(fill="x", padx=20, pady=(0, 10))

    def _set_full_amount(self, debt: float):
        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, str(int(debt)))

    def _handle_pay(self):
        amount_raw = self.amount_entry.get().strip().replace(".", "").replace(",", "")
        date_str = self.date_entry.get().strip()

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa un monto válido mayor a 0.")
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.lbl_error.configure(text="⚠️ La fecha debe tener formato YYYY-MM-DD.")
            return

        success, msg = self.db.pay_credit_card(date_str, amount)
        if success:
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            self.lbl_error.configure(text=f"⚠️ {msg}")
