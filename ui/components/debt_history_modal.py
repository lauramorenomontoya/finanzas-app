"""
Modal para Consultar el Historial de Abonos de una Deuda.
Permite ver fechas, montos, notas y eliminar abonos con restitución automática del saldo bancario.
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from ui.components.confirm_dialog import ConfirmDialog
from ui.utils.modal_helper import center_window


class DebtHistoryModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        debt_id: int,
        on_data_changed: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.debt_id = debt_id
        self.on_data_changed = on_data_changed

        self.title("Historial de Abonos")
        self.geometry("540x620")
        self.minsize(480, 500)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui()

    def _center_window(self, parent):
        center_window(self, parent, 540, 620)

    def _build_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        self.main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        self._render_content()

    def _render_content(self):
        # Limpiar contenedor principal
        for w in self.main_frame.winfo_children():
            w.destroy()

        debt = self.db.get_debt_by_id(self.debt_id)
        if not debt:
            ctk.CTkLabel(self.main_frame, text="Deuda no encontrada.", font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        is_receivable = debt.get("debt_type") == "RECEIVABLE"

        # 1. Encabezado Fijo
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        hist_title = f"📜 Historial de Pagos: {debt['creditor']}" if is_receivable else f"📜 Historial de Abonos: {debt['creditor']}"
        hist_sub = "Registros de pagos y amortización a tu favor a la fecha" if is_receivable else "Registros de amortización y pagos a la fecha"
        ctk.CTkLabel(
            header,
            text=hist_title,
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=hist_sub,
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(self.main_frame, height=1, fg_color=Theme.BORDER_SUBTLE).pack(fill="x", padx=20, pady=(4, 10))

        # Tarjeta de Progreso de la Deuda
        summary_card = ctk.CTkFrame(self.main_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        summary_card.pack(fill="x", padx=20, pady=(0, 12))

        inner_card = ctk.CTkFrame(summary_card, fg_color="transparent")
        inner_card.pack(fill="x", padx=14, pady=10)

        row_nums = ctk.CTkFrame(inner_card, fg_color="transparent")
        row_nums.pack(fill="x", pady=(0, 6))

        total_lbl = "Prestado" if is_receivable else "Total"
        paid_lbl = "Cobrado" if is_receivable else "Abonado"
        rem_lbl = "Por Cobrar" if is_receivable else "Pendiente"

        ctk.CTkLabel(
            row_nums,
            text=f"{total_lbl}: ${debt['total_amount']:,.0f} {debt['currency']}",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left")

        ctk.CTkLabel(
            row_nums,
            text=f"{paid_lbl}: ${debt['total_paid']:,.0f} ({debt['percent_paid']}%)",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.ACCENT_GREEN
        ).pack(side="left", padx=12)

        ctk.CTkLabel(
            row_nums,
            text=f"{rem_lbl}: ${debt['remaining_amount']:,.0f}",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.ACCENT_ROSE
        ).pack(side="right")

        # Barra de Progreso
        pct = debt["percent_paid"] / 100.0
        pbar = ctk.CTkProgressBar(inner_card, height=8, corner_radius=4)
        pbar.pack(fill="x", pady=(4, 0))
        pbar.set(pct)
        if pct >= 1.0:
            pbar.configure(progress_color=Theme.ACCENT_GREEN)
        elif pct >= 0.5:
            pbar.configure(progress_color=Theme.ACCENT_BLUE)
        else:
            pbar.configure(progress_color="#f59e0b")

        # 2. Pie Fijo con Botón Cerrar
        footer = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=(10, 16))

        btn_close = ctk.CTkButton(
            footer,
            text="Cerrar",
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            height=36,
            corner_radius=8,
            command=self.destroy
        )
        btn_close.pack(fill="x")

        # 3. Lista de Abonos Desplazable
        scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=0)

        payments = self.db.get_debt_payments(self.debt_id)
        if not payments:
            empty_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=40)
            ctk.CTkLabel(
                empty_frame,
                text="ℹ️ No hay abonos registrados para esta deuda todavía.",
                font=ctk.CTkFont(family="SF Pro Text", size=13),
                text_color=Theme.TEXT_MUTED
            ).pack()
            return

        for p in payments:
            item_frame = ctk.CTkFrame(scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
            item_frame.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(item_frame, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            # Columna izquierda: Fecha y notas
            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            row_top = ctk.CTkFrame(left, fg_color="transparent")
            row_top.pack(anchor="w")

            ctk.CTkLabel(
                row_top,
                text=f"📅 {p['date']}",
                font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(side="left")

            if p["transaction_id"]:
                badge = ctk.CTkLabel(
                    row_top,
                    text="💳 Descontado de cuenta",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=Theme.ACCENT_GREEN,
                    fg_color=Theme.COP_BANNER_BG,
                    corner_radius=4,
                    padx=6,
                    pady=1
                )
                badge.pack(side="left", padx=8)

            note_text = p["notes"] if p["notes"] else "Sin notas adicionales"
            ctk.CTkLabel(
                left,
                text=note_text,
                font=ctk.CTkFont(family="SF Pro Text", size=11),
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w", pady=(2, 0))

            # Columna derecha: Monto y botón eliminar
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")

            ctk.CTkLabel(
                right,
                text=f"+${p['amount']:,.0f}",
                font=ctk.CTkFont(family="SF Pro Display", size=15, weight="bold"),
                text_color=Theme.ACCENT_GREEN
            ).pack(side="left", padx=(0, 10))

            btn_del = ctk.CTkButton(
                right,
                text="🗑️",
                width=30,
                height=28,
                corner_radius=6,
                fg_color="transparent",
                hover_color=Theme.BORDER_DEFAULT,
                text_color=Theme.ACCENT_ROSE,
                command=lambda pid=p["id"]: self._delete_payment(pid)
            )
            btn_del.pack(side="right")

    def _delete_payment(self, payment_id: int):
        def on_confirm():
            success, msg = self.db.delete_debt_payment(payment_id)
            if success:
                if self.on_data_changed:
                    self.on_data_changed()
                self._render_content()

        ConfirmDialog(
            self,
            title="Eliminar Abono",
            message="¿Estás seguro de eliminar este abono? Si se descontó de tu cuenta, el saldo será restituido automáticamente.",
            on_confirm=on_confirm
        )
