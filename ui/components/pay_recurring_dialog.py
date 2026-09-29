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


class PayRecurringDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        item: Dict[str, Any],
        target_ym: str,
        on_confirm: Callable[[str], None],
        on_cancel: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.item = item
        self.target_ym = target_ym
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        self.title("Registrar Pago de Gasto Fijo")
        self.geometry("460x340")
        self.minsize(420, 320)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)
        self._build_ui()

    def _center_window(self, parent):
        center_window(self, parent, 460, 340)

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
        card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Cabecera
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 10))

        ctk.CTkLabel(
            header,
            text="📅 Registrar Pago de Gasto Fijo",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        curr = self.item.get("currency", "COP")
        amt = self.item.get("amount", 0)
        amt_str = f"${amt:,.2f} USD" if curr == "USD" else f"${amt:,.0f} COP"
        m_name = self._format_month(self.target_ym)

        # 2. Tarjeta resumen del gasto
        box = ctk.CTkFrame(card, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        box.pack(fill="x", padx=16, pady=(0, 12))

        b_in = ctk.CTkFrame(box, fg_color="transparent")
        b_in.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            b_in,
            text=f"{self.item.get('description', '')} ({self.item.get('category', '')})",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        row_info = ctk.CTkFrame(b_in, fg_color="transparent")
        row_info.pack(fill="x", pady=(4, 0))

        ctk.CTkLabel(
            row_info,
            text=f"Monto: {amt_str}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10b981"
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
        ).pack(anchor="w", padx=16, pady=(0, 4))

        self.date_picker = DatePickerWidget(card, height=34)
        self.date_picker.pack(fill="x", padx=16, pady=(0, 8))

        hint_text = f"💡 Se descontará hoy de tu saldo disponible y quedará imputado contablemente en {m_name}, apareciendo en su Balance General y Presupuesto sin consumir el presupuesto del mes actual."
        ctk.CTkLabel(
            card,
            text=hint_text,
            font=ctk.CTkFont(size=10),
            text_color=Theme.TEXT_MUTED,
            wraplength=380,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 14))

        # 4. Botones
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        btn_cancel = ctk.CTkButton(
            btn_row,
            text="Cancelar",
            height=34,
            width=90,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self._handle_cancel
        )
        btn_cancel.pack(side="left", padx=(0, 8))

        btn_confirm = ctk.CTkButton(
            btn_row,
            text="✅ Confirmar Pago",
            height=34,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._handle_confirm
        )
        btn_confirm.pack(side="right", fill="x", expand=True)

    def _handle_cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self.destroy()

    def _handle_confirm(self):
        date_str = self.date_picker.get().strip()
        self.on_confirm(date_str)
        self.destroy()
