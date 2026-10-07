"""
Diálogo Inteligente de Seguridad de Saldos:
Explica el impacto financiero de una eliminación que generaría saldo negativo y permite forzarla o cancelarla.
"""

import customtkinter as ctk
from typing import Callable, Dict, Any, Optional
from ui.theme import Theme

from ui.components.base_modal import BaseModal

class BalanceWarningDialog(BaseModal):
    def __init__(
        self,
        parent,
        warning_data: Dict[str, Any],
        on_force_confirm: Callable[[], None],
        on_cancel: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent, title="⚠️ Advertencia de Seguridad de Saldo", width=520, height=440)
        self.warning_data = warning_data
        self.on_force_confirm = on_force_confirm
        self.on_cancel_cb = on_cancel

        self._build_ui()

    def _build_ui(self):
        main_frame = self.create_standard_frame(border_color=Theme.ERROR)

        # Encabezado
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        ctk.CTkLabel(
            header,
            text="⚠️ Saldo Insuficiente para Revertir",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=18, weight="bold"),
            text_color=Theme.ACCENT_ROSE
        ).pack(anchor="w")

        curr = self.warning_data.get("currency", "COP")
        desc = self.warning_data.get("description", "Eliminación de movimiento")
        curr_bal = self.warning_data.get("current_balance", 0.0)
        deduct_amt = self.warning_data.get("amount_to_deduct", 0.0)
        res_bal = self.warning_data.get("resulting_balance", 0.0)

        curr_fmt = f"${curr_bal:,.2f} USD" if curr == "USD" else f"${curr_bal:,.0f} COP"
        deduct_fmt = f"-${deduct_amt:,.2f} USD" if curr == "USD" else f"-${deduct_amt:,.0f} COP"
        res_fmt = f"${res_bal:,.2f} USD" if curr == "USD" else f"${res_bal:,.0f} COP"

        ctk.CTkLabel(
            header,
            text=f"Operación: {desc}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED,
            wraplength=440,
            justify="left"
        ).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

        # Tarjeta de Comparación de Balances
        stats_box = ctk.CTkFrame(main_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        stats_box.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))

        stats_inner = ctk.CTkFrame(stats_box, fg_color="transparent")
        stats_inner.pack(fill="x", padx=Theme.SPACING_MD, pady=Theme.SPACING_SM)

        # Fila 1: Saldo actual
        r1 = ctk.CTkFrame(stats_inner, fg_color="transparent")
        r1.pack(fill="x", pady=Theme.SPACING_XS)
        ctk.CTkLabel(r1, text="Saldo actual disponible:", font=ctk.CTkFont(size=12), text_color=Theme.TEXT_SECONDARY).pack(side="left")
        ctk.CTkLabel(r1, text=curr_fmt, font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(side="right")

        # Fila 2: Descuento a aplicar
        r2 = ctk.CTkFrame(stats_inner, fg_color="transparent")
        r2.pack(fill="x", pady=Theme.SPACING_XS)
        ctk.CTkLabel(r2, text="Monto que se descontará:", font=ctk.CTkFont(size=12), text_color=Theme.TEXT_SECONDARY).pack(side="left")
        ctk.CTkLabel(r2, text=deduct_fmt, font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(side="right")

        # Divisor
        ctk.CTkFrame(stats_inner, height=1, fg_color=Theme.BORDER_DEFAULT).pack(fill="x", pady=Theme.SPACING_XS)

        # Fila 3: Saldo Resultante (Negativo)
        r3 = ctk.CTkFrame(stats_inner, fg_color="transparent")
        r3.pack(fill="x", pady=Theme.SPACING_XS)
        ctk.CTkLabel(r3, text="Saldo resultante proyectado:", font=ctk.CTkFont(size=13, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(r3, text=res_fmt, font=ctk.CTkFont(size=14, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(side="right")

        # Mensaje explicativo
        explanation_frame = ctk.CTkFrame(main_frame, fg_color=Theme.ERROR_HOVER, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.ERROR)
        explanation_frame.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))

        ctk.CTkLabel(
            explanation_frame,
            text="💡 ¿Qué puedes hacer?\n• Cancelar y eliminar primero los gastos asociados a estos fondos.\n• O Forzar la eliminación si necesitas corregir un error histórico. Tu balance reflejará el saldo negativo hasta que registres nuevos ingresos.",
            font=ctk.CTkFont(size=11),
            text_color=Theme.ERROR,
            wraplength=420,
            justify="left"
        ).pack(padx=Theme.SPACING_SM, pady=Theme.SPACING_SM)

        self.create_footer_buttons(
            main_frame,
            on_confirm=self._handle_force,
            on_cancel=self._handle_cancel,
            confirm_text="⚠️ Forzar Eliminación",
            cancel_text="Cancelar",
            is_destructive=True
        )

    def _handle_cancel(self):
        self.grab_release()
        self.destroy()
        if self.on_cancel_cb:
            self.on_cancel_cb()

    def _handle_force(self):
        self.grab_release()
        self.destroy()
        if self.on_force_confirm:
            self.on_force_confirm()
