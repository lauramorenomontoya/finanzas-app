import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget
from ui.components.base_modal import BaseModal


class CCPaymentModal(BaseModal):
    def __init__(
        self,
        parent,
        db_manager,
        on_success: Optional[Callable[[], None]] = None
    ):
        self.db = db_manager
        self.on_success = on_success

        super().__init__(
            parent=parent,
            title="Pagar Tarjeta de Crédito",
            width=480,
            height=570,
            min_width=440,
            min_height=500
        )

    def build_ui(self):
        main_frame = self.create_standard_frame(self.main_container)

        self.create_header(
            parent=main_frame,
            title="💳 Pago de Tarjeta de Crédito",
            subtitle="Descuenta de tu cuenta operativa para saldar tu deuda de TC."
        )

        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # Tarjeta de Estado de Deuda
        debt_box = ctk.CTkFrame(scroll_body, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        debt_box.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        debt_inner = ctk.CTkFrame(debt_box, fg_color="transparent")
        debt_inner.pack(fill="x", padx=Theme.SPACING_MD, pady=Theme.SPACING_SM)

        current_debt = self.db.get_credit_card_debt()
        cop_bal = self.db.get_cop_balance()

        ctk.CTkLabel(debt_inner, text="DEUDA PENDIENTE TC:", font=ctk.CTkFont(size=10, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(anchor="w")
        ctk.CTkLabel(debt_inner, text=f"${current_debt:,.0f} COP", font=ctk.CTkFont(size=20, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(anchor="w")
        ctk.CTkLabel(debt_inner, text=f"Disponible en cuenta: ${cop_bal:,.0f} COP", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_MUTED).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

        # Campo Monto a Pagar
        ctk.CTkLabel(scroll_body, text="Monto a Pagar ($ COP):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        
        amount_row = ctk.CTkFrame(scroll_body, fg_color="transparent")
        amount_row.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))

        self.amount_entry = ctk.CTkEntry(
            amount_row,
            placeholder_text=f"Ej: {int(current_debt)}",
            height=36,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.amount_entry.insert(0, str(int(current_debt)) if current_debt > 0 else "")
        self.amount_entry.pack(side="left", fill="x", expand=True, padx=(0, Theme.SPACING_SM))

        btn_full_pay = ctk.CTkButton(
            amount_row,
            text="Todo",
            width=55,
            height=36,
            corner_radius=Theme.SPACING_SM,
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
        ).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # Campo Fecha con DatePickerWidget
        ctk.CTkLabel(scroll_body, text="Fecha del Pago:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.date_entry = DatePickerWidget(scroll_body, height=36)
        self.date_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # Campo Notas Opcional
        ctk.CTkLabel(scroll_body, text="Notas / Concepto (Opcional):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.notes_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text="Ej: Abono quincenal / Pago parcial TC",
            height=36,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.notes_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        self.lbl_error = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE, wraplength=420)
        self.lbl_error.pack(anchor="w", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_XS))

        footer, btn_cancel, self.btn_confirm = self.create_footer_buttons(
            parent=main_frame,
            cancel_command=self.destroy,
            confirm_command=self._handle_pay,
            confirm_text="💸 Confirmar Pago",
            destructive=False
        )

        self.btn_confirm.configure(fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS, text_color=Theme.TEXT_ON_COLOR)

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
