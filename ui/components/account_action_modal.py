import customtkinter as ctk
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget
from ui.components.base_modal import BaseModal


class AccountActionModal(BaseModal):
    def __init__(
        self,
        parent,
        db_manager,
        account: Dict[str, Any],
        initial_action: str = "YIELD",  # 'TRANSFER_TO', 'TRANSFER_FROM', 'YIELD'
        on_success: Optional[Callable[[], None]] = None
    ):
        self.db = db_manager
        self.account = account
        self.on_success = on_success
        self.initial_action = initial_action

        super().__init__(
            parent=parent,
            title=f"Movimiento en {account['name']}",
            width=500,
            height=560,
            min_width=460,
            min_height=480
        )

    def build_ui(self):
        main_frame = self.create_standard_frame(self.main_container)

        acc_icon = self.account.get("icon", "📈")
        curr = self.account.get("currency", "COP")
        bal = self.account.get("current_balance", 0.0)
        bal_str = f"${bal:,.2f} USD" if curr == "USD" else f"${bal:,.0f} COP"

        self.create_header(
            parent=main_frame,
            title=f"{acc_icon} {self.account['name']}",
            subtitle=f"Saldo actual: {bal_str} • {self.account.get('institution', '')}"
        )

        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        self.action_seg = ctk.CTkSegmentedButton(
            scroll_body,
            values=["📈 Rendimiento", "📥 Aporte", "📤 Retiro"],
            height=34,
            command=self._on_action_changed
        )
        if self.initial_action == "TRANSFER_TO":
            self.action_seg.set("📥 Aporte")
        elif self.initial_action == "TRANSFER_FROM":
            self.action_seg.set("📤 Retiro")
        else:
            self.action_seg.set("📈 Rendimiento")
        self.action_seg.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        self.lbl_info = ctk.CTkLabel(
            scroll_body,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=Theme.ACCENT_GREEN,
            wraplength=400,
            justify="left"
        )
        self.lbl_info.pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        ctk.CTkLabel(scroll_body, text=f"Monto ({curr}):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.amount_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text=f"Ej: {'100.00' if curr == 'USD' else '500000'}",
            height=36,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.amount_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        ctk.CTkLabel(scroll_body, text="Fecha del Movimiento:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.date_entry = DatePickerWidget(scroll_body, height=36)
        self.date_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        ctk.CTkLabel(scroll_body, text="Notas / Concepto:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.notes_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text="Opcional (ej: Rendimiento quincenal / Aporte)",
            height=36,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.notes_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        self.lbl_error = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_XS))

        footer, btn_cancel, self.btn_submit = self.create_footer_buttons(
            parent=main_frame,
            cancel_command=self.destroy,
            confirm_command=self._handle_submit,
            confirm_text="Confirmar",
            destructive=False
        )
        
        self._on_action_changed(self.action_seg.get())

    def _on_action_changed(self, choice: str):
        curr = self.account.get("currency", "COP")
        if "Rendimiento" in choice:
            self.lbl_info.configure(
                text="📈 Suma ganancias/intereses a la cuenta sin retirar de tu presupuesto operativo.",
                text_color=Theme.ACCENT_GREEN
            )
            self.btn_submit.configure(text="📈 Registrar Rendimiento", fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS)
        elif "Aporte" in choice:
            origen = "Presupuesto COP" if curr == "COP" else "Bóveda USD"
            self.lbl_info.configure(
                text=f"📥 Transfiere dinero desde tu {origen} hacia esta cuenta de inversión.",
                text_color=Theme.ACCENT_BLUE
            )
            self.btn_submit.configure(text=f"📥 Transferir a {self.account['name']}", fg_color=Theme.INFO, hover_color=Theme.INFO_HOVER)
        else:
            destino = "Presupuesto COP" if curr == "COP" else "Bóveda USD"
            self.lbl_info.configure(
                text=f"📤 Retira fondos de la inversión y los devuelve a tu {destino}.",
                text_color=Theme.ACCENT_ROSE
            )
            self.btn_submit.configure(text="📤 Retirar hacia Presupuesto", fg_color=Theme.ERROR, hover_color=Theme.ERROR_HOVER)

    def _handle_submit(self):
        choice = self.action_seg.get()
        amount_raw = self.amount_entry.get().strip().replace(".", "").replace(",", ".")
        date_str = self.date_entry.get().strip()
        notes = self.notes_entry.get().strip()

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa un monto numérico válido mayor a 0.")
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.lbl_error.configure(text="⚠️ La fecha debe tener formato YYYY-MM-DD.")
            return

        acc_id = self.account["id"]

        if "Rendimiento" in choice:
            success, msg = self.db.add_account_yield(acc_id, amount, date_str, notes)
        elif "Aporte" in choice:
            success, msg = self.db.transfer_to_investment(acc_id, amount, date_str, notes)
        else:
            success, msg = self.db.transfer_from_investment(acc_id, amount, date_str, notes)

        if success:
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            self.lbl_error.configure(text=f"⚠️ {msg}")
