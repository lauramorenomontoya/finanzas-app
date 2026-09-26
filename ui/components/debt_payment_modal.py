"""
Modal para Registrar Abonos a una Deuda Personal en CustomTkinter.
Permite ingresar el monto a abonar, seleccionar fecha, notas y descontar automáticamente del saldo disponible en COP.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget


class DebtPaymentModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        debt: Dict[str, Any],
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.debt = debt
        self.on_success = on_success

        self.title(f"Abonar a Deuda - {debt['creditor']}")
        self.geometry("480x620")
        self.minsize(440, 520)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui()

    def _center_window(self, parent):
        self.update_idletasks()
        try:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            x = parent_x + (parent_w - 480) // 2
            y = parent_y + (parent_h - 620) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Encabezado Fijo
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            header,
            text=f"💰 Registrar Abono a {self.debt['creditor']}",
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Registra un pago parcial o total para amortizar tu deuda",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(main_frame, height=1, fg_color=Theme.BORDER_SUBTLE).pack(fill="x", padx=20, pady=(4, 10))

        # 2. Pie Fijo de Botones
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=(10, 16))

        self.lbl_error = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=Theme.ACCENT_ROSE
        )
        self.lbl_error.pack(anchor="w", pady=(0, 6))

        btn_box = ctk.CTkFrame(footer, fg_color="transparent")
        btn_box.pack(fill="x")

        btn_cancel = ctk.CTkButton(
            btn_box,
            text="Cancelar",
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            height=36,
            corner_radius=8,
            command=self.destroy
        )
        btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_save = ctk.CTkButton(
            btn_box,
            text="Confirmar Abono",
            fg_color=Theme.ACCENT_GREEN,
            hover_color="#059669",
            text_color="#ffffff",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self._confirm_payment
        )
        btn_save.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # 3. Contenedor Desplazable del Formulario
        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=0)

        # Tarjeta informativa de Saldos
        card_info = ctk.CTkFrame(scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        card_info.pack(fill="x", pady=(0, 14), padx=2)

        info_inner = ctk.CTkFrame(card_info, fg_color="transparent")
        info_inner.pack(fill="x", padx=14, pady=12)

        # Fila 1: Total y Pendiente
        row1 = ctk.CTkFrame(info_inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            row1,
            text=f"Deuda Total: ${self.debt['total_amount']:,.0f} {self.debt['currency']}",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(side="left")

        ctk.CTkLabel(
            row1,
            text=f"Ya Abonado: ${self.debt['total_paid']:,.0f}",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.ACCENT_BLUE
        ).pack(side="right")

        # Fila 2: Saldo Restante en Grande
        row2 = ctk.CTkFrame(info_inner, fg_color="transparent")
        row2.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(
            row2,
            text="Saldo Pendiente:",
            font=ctk.CTkFont(family="SF Pro Text", size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            row2,
            text=f"${self.debt['remaining_amount']:,.0f} {self.debt['currency']}",
            font=ctk.CTkFont(family="SF Pro Display", size=16, weight="bold"),
            text_color=Theme.ACCENT_ROSE
        ).pack(side="right")

        # Saldo en cuenta disponible
        cop_balance = self.db.get_cop_balance()
        ctk.CTkLabel(
            info_inner,
            text=f"💰 Tu saldo disponible en cuenta: ${cop_balance:,.0f} COP",
            font=ctk.CTkFont(family="SF Pro Text", size=11, weight="bold"),
            text_color=Theme.ACCENT_GREEN
        ).pack(anchor="w", pady=(4, 0))

        # Campo: Monto a Abonar
        ctk.CTkLabel(
            scroll,
            text="Monto a Abonar *",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 2))

        self.entry_amount = ctk.CTkEntry(
            scroll,
            placeholder_text="Ej: 500000",
            height=35,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(family="SF Pro Text", size=13)
        )
        self.entry_amount.pack(fill="x", pady=(0, 6))

        # Botones Rápidos de Monto (Atajos)
        quick_box = ctk.CTkFrame(scroll, fg_color="transparent")
        quick_box.pack(fill="x", pady=(0, 12))

        rem = self.debt["remaining_amount"]
        btn_25 = ctk.CTkButton(
            quick_box,
            text="25%",
            width=65,
            height=26,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            command=lambda: self._set_quick_amount(rem * 0.25)
        )
        btn_25.pack(side="left", padx=(0, 4))

        btn_50 = ctk.CTkButton(
            quick_box,
            text="50%",
            width=65,
            height=26,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            command=lambda: self._set_quick_amount(rem * 0.50)
        )
        btn_50.pack(side="left", padx=4)

        btn_all = ctk.CTkButton(
            quick_box,
            text="Total Pendiente",
            height=26,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            command=lambda: self._set_quick_amount(rem)
        )
        btn_all.pack(side="left", padx=4)

        # Campo: Fecha del Abono
        ctk.CTkLabel(
            scroll,
            text="Fecha del Abono *",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 2))

        self.date_picker = DatePickerWidget(scroll, initial_date=datetime.now().strftime("%Y-%m-%d"))
        self.date_picker.pack(fill="x", pady=(0, 12))

        # Campo: Notas del Abono
        ctk.CTkLabel(
            scroll,
            text="Notas / Detalle (Opcional)",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 2))

        self.entry_notes = ctk.CTkEntry(
            scroll,
            placeholder_text="Ej: Abono de quincena, transferencia Bancolombia...",
            height=35,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(family="SF Pro Text", size=13)
        )
        self.entry_notes.pack(fill="x", pady=(0, 14))

        # Casilla: Descontar de Saldo COP
        self.var_deduct = ctk.BooleanVar(value=True)
        self.chk_deduct = ctk.CTkCheckBox(
            scroll,
            text="Descontar automáticamente de mi saldo disponible COP (Egreso)",
            variable=self.var_deduct,
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_PRIMARY,
            fg_color=Theme.ACCENT_GREEN,
            hover_color="#059669"
        )
        self.chk_deduct.pack(anchor="w", pady=(0, 10))

    def _set_quick_amount(self, amount: float):
        amount = round(amount)
        self.entry_amount.delete(0, "end")
        self.entry_amount.insert(0, str(amount))

    def _confirm_payment(self):
        amount_raw = self.entry_amount.get().strip().replace("$", "").replace(",", "").replace(".", "")
        date = self.date_picker.get_date()
        notes = self.entry_notes.get().strip()
        deduct = self.var_deduct.get()

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa un monto numérico válido mayor a 0.")
            return

        if amount > self.debt["remaining_amount"]:
            self.lbl_error.configure(text=f"⚠️ El abono (${amount:,.0f}) supera el saldo pendiente (${self.debt['remaining_amount']:,.0f}).")
            return

        success, msg = self.db.add_debt_payment(
            debt_id=self.debt["id"],
            amount=amount,
            date=date,
            notes=notes,
            deduct_from_balance=deduct
        )

        if not success:
            self.lbl_error.configure(text=f"❌ {msg}")
            return

        if self.on_success:
            self.on_success()
        self.destroy()
