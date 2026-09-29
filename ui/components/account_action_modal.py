"""
Modal para registrar Aportes, Retiros y Rendimientos en Cuentas y Fiducias.
Diseño responsivo con pie fijo de botones y cuerpo desplazable.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget
from ui.utils.modal_helper import center_window


class AccountActionModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        account: Dict[str, Any],
        initial_action: str = "YIELD",  # 'TRANSFER_TO', 'TRANSFER_FROM', 'YIELD'
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.account = account
        self.on_success = on_success

        self.title(f"Movimiento en {account['name']}")
        self.geometry("500x560")
        self.minsize(460, 480)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui(initial_action)

    def _center_window(self, parent):
        center_window(self, parent, 500, 560)

    def _build_ui(self, initial_action: str):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Encabezado Fijo Superior
        acc_icon = self.account.get("icon", "📈")
        curr = self.account.get("currency", "COP")
        bal = self.account.get("current_balance", 0.0)
        bal_str = f"${bal:,.2f} USD" if curr == "USD" else f"${bal:,.0f} COP"

        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        ctk.CTkLabel(
            header,
            text=f"{acc_icon} {self.account['name']}",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=f"Saldo actual: {bal_str} • {self.account.get('institution', '')}",
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

        self.btn_submit = ctk.CTkButton(
            btn_row,
            text="Confirmar",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            command=self._handle_submit
        )
        self.btn_submit.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 3. Cuerpo Desplazable Central
        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Selector de Acción
        self.action_seg = ctk.CTkSegmentedButton(
            scroll_body,
            values=["📈 Rendimiento", "📥 Aporte", "📤 Retiro"],
            height=34,
            command=self._on_action_changed
        )
        if initial_action == "TRANSFER_TO":
            self.action_seg.set("📥 Aporte")
        elif initial_action == "TRANSFER_FROM":
            self.action_seg.set("📤 Retiro")
        else:
            self.action_seg.set("📈 Rendimiento")
        self.action_seg.pack(fill="x", padx=6, pady=(0, 10))

        # Indicador de flujo
        self.lbl_info = ctk.CTkLabel(
            scroll_body,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=Theme.ACCENT_GREEN,
            wraplength=400,
            justify="left"
        )
        self.lbl_info.pack(anchor="w", padx=6, pady=(0, 10))

        # Campo Monto
        ctk.CTkLabel(scroll_body, text=f"Monto ({curr}):", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.amount_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text=f"Ej: {'100.00' if curr == 'USD' else '500000'}",
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.amount_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Campo Fecha con DatePickerWidget
        ctk.CTkLabel(scroll_body, text="Fecha del Movimiento:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.date_entry = DatePickerWidget(scroll_body, height=36)
        self.date_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Campo Notas
        ctk.CTkLabel(scroll_body, text="Notas / Concepto:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.notes_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text="Opcional (ej: Rendimiento quincenal / Aporte)",
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.notes_entry.pack(fill="x", padx=6, pady=(0, 12))

        self._on_action_changed(self.action_seg.get())

    def _on_action_changed(self, choice: str):
        curr = self.account.get("currency", "COP")
        if "Rendimiento" in choice:
            self.lbl_info.configure(
                text="📈 Suma ganancias/intereses a la cuenta sin retirar de tu presupuesto operativo.",
                text_color=Theme.ACCENT_GREEN
            )
            self.btn_submit.configure(text="📈 Registrar Rendimiento", fg_color="#10b981", hover_color="#059669")
        elif "Aporte" in choice:
            origen = "Presupuesto COP" if curr == "COP" else "Bóveda USD"
            self.lbl_info.configure(
                text=f"📥 Transfiere dinero desde tu {origen} hacia esta cuenta de inversión.",
                text_color=Theme.ACCENT_BLUE
            )
            self.btn_submit.configure(text=f"📥 Transferir a {self.account['name']}", fg_color="#0284c7", hover_color="#0369a1")
        else:
            destino = "Presupuesto COP" if curr == "COP" else "Bóveda USD"
            self.lbl_info.configure(
                text=f"📤 Retira fondos de la inversión y los devuelve a tu {destino}.",
                text_color=Theme.ACCENT_ROSE
            )
            self.btn_submit.configure(text="📤 Retirar hacia Presupuesto", fg_color="#e11d48", hover_color="#be123c")

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
