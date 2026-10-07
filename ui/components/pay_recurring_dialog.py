"""
Diálogo para registrar el pago de un gasto fijo, con selección de fecha y confirmación de período.
Ideal para pagos realizados por anticipado antes del mes siguiente o en meses específicos.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget
from ui.utils.modal_helper import center_window


from ui.components.base_modal import BaseModal

class PayRecurringDialog(BaseModal):
    def __init__(
        self,
        parent,
        item: Dict[str, Any],
        target_ym: str,
        on_confirm: Callable[[str], None],
        on_cancel: Optional[Callable[[], None]] = None
    ):
        self.item = item
        self.target_ym = target_ym
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        super().__init__(parent, title="Registrar Pago de Gasto Fijo", width=460, height=340, min_width=420, min_height=320)

        self._build_ui()

    def _format_month(self, ym: str) -> str:
        try:
            dt = datetime.strptime(ym, "%Y-%m")
            meses = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
            return f"{meses[dt.month - 1]} {dt.year}"
        except Exception:
            return ym

    def _build_ui(self):
        card = self.create_standard_frame()

        # 1. Cabecera
        header = self.create_header(card, "Registrar Pago de Gasto Fijo", icon="📅")

        curr = self.item.get("currency", "COP")
        amt = self.item.get("amount", 0)
        amt_str = f"${amt:,.2f} USD" if curr == "USD" else f"${amt:,.0f} COP"
        m_name = self._format_month(self.target_ym)

        # 2. Tarjeta resumen del gasto
        box = ctk.CTkFrame(card, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        box.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        b_in = ctk.CTkFrame(box, fg_color="transparent")
        b_in.pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_SM)

        ctk.CTkLabel(
            b_in,
            text=f"{self.item.get('description', '')} ({self.item.get('category', '')})",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        row_info = ctk.CTkFrame(b_in, fg_color="transparent")
        row_info.pack(fill="x", pady=(Theme.SPACING_XS, 0))

        ctk.CTkLabel(
            row_info,
            text=f"Monto: {amt_str}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.SUCCESS
        ).pack(side="left")

        ctk.CTkLabel(
            row_info,
            text=f"🗓️ Para: {m_name}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.ACCENT_BLUE
        ).pack(side="right")

        # 3. Selector de Fecha de Pago
        ctk.CTkLabel(
            card,
            text="Fecha en que realizas el pago (hoy):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))

        self.date_picker = DatePickerWidget(card, height=34)
        self.date_picker.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        hint_text = f"💡 Se descontará hoy de tu saldo disponible y quedará imputado contablemente en {m_name}, apareciendo en su Balance General y Presupuesto sin consumir el presupuesto del mes actual."
        ctk.CTkLabel(
            card,
            text=hint_text,
            font=ctk.CTkFont(size=10),
            text_color=Theme.TEXT_MUTED,
            wraplength=380,
            justify="left"
        ).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        # 4. Botones
        self.create_footer_buttons(
            card,
            on_confirm=self._handle_confirm,
            on_cancel=self._handle_cancel,
            confirm_text="✅ Confirmar Pago",
            cancel_text="Cancelar",
            is_destructive=False
        )

    def _handle_cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self.destroy()

    def _handle_confirm(self):
        date_str = self.date_picker.get().strip()
        self.on_confirm(date_str)
        self.destroy()
