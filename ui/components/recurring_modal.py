"""
Modal para aplicar la plantilla de gastos fijos recurrentes del mes actual con un solo clic.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional, List, Dict
from ui.theme import Theme


class RecurringModalDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        on_applied: Optional[Callable[[int, float], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.on_applied_cb = on_applied
        self.checkbox_vars: Dict[int, ctk.BooleanVar] = {}

        self.title("Aplicar Gastos Fijos del Mes")
        self.geometry("520x480")
        self.minsize(480, 400)
        self.configure(fg_color=Theme.BG_WINDOW)

        # Modal
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
            x = parent_x + (parent_w - 520) // 2
            y = parent_y + (parent_h - 480) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Encabezado
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(18, 10))

        ctk.CTkLabel(
            header,
            text="⚡ Cargar Gastos Fijos Recurrentes",
            font=ctk.CTkFont(family="SF Pro Display", size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        current_month = datetime.now().strftime("%B %Y").capitalize()
        ctk.CTkLabel(
            header,
            text=f"Selecciona los gastos fijos que deseas registrar para {current_month}:",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        # Campo de fecha para registrar los gastos
        date_row = ctk.CTkFrame(container, fg_color="transparent")
        date_row.pack(fill="x", padx=18, pady=(0, 10))

        ctk.CTkLabel(
            date_row,
            text="Fecha de Registro:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 8))

        from ui.components.date_picker import DatePickerWidget
        self.date_entry = DatePickerWidget(date_row, height=30)
        self.date_entry.pack(side="left", fill="x", expand=True)

        # Selector rápido Todos / Ninguno
        quick_select = ctk.CTkFrame(container, fg_color="transparent")
        quick_select.pack(fill="x", padx=18, pady=(0, 6))

        btn_all = ctk.CTkButton(
            quick_select,
            text="Marcar Todos",
            width=90,
            height=24,
            fg_color=Theme.BORDER_DEFAULT,
            hover_color=Theme.TEXT_MUTED,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=10),
            command=self._select_all
        )
        btn_all.pack(side="left", padx=(0, 6))

        btn_none = ctk.CTkButton(
            quick_select,
            text="Desmarcar",
            width=80,
            height=24,
            fg_color=Theme.BORDER_DEFAULT,
            hover_color=Theme.TEXT_MUTED,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=10),
            command=self._deselect_all
        )
        btn_none.pack(side="left")

        # Lista de gastos fijos con scroll
        self.scroll_frame = ctk.CTkScrollableFrame(container, fg_color="transparent", height=200)
        self.scroll_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        recurring_list = self.db.get_recurring_expenses(only_active=True)

        if not recurring_list:
            ctk.CTkLabel(
                self.scroll_frame,
                text="No tienes gastos fijos configurados en tu plantilla.\nPuedes añadirlos en la sección de Categorías y Gastos Fijos.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED,
                justify="center"
            ).pack(pady=30)
        else:
            for item in recurring_list:
                rec_id = item["id"]
                var = ctk.BooleanVar(value=True)
                self.checkbox_vars[rec_id] = var

                card = ctk.CTkFrame(self.scroll_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
                card.pack(fill="x", pady=3, padx=2)

                chk = ctk.CTkCheckBox(
                    card,
                    text=f"{item['category']} - {item['description']}",
                    variable=var,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=Theme.TEXT_PRIMARY,
                    command=self._recalculate_total
                )
                chk.pack(side="left", padx=10, pady=8)

                ctk.CTkLabel(
                    card,
                    text=f"${item['amount']:,.0f} COP",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=Theme.ACCENT_ROSE
                ).pack(side="right", padx=10, pady=8)

        # Pie con total y botón de aplicar
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 16), side="bottom")

        self.lbl_total = ctk.CTkLabel(
            footer,
            text="Total a Registrar: $0 COP",
            font=ctk.CTkFont(family="SF Pro Display", size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_total.pack(side="left")

        btn_cancel = ctk.CTkButton(
            footer,
            text="Cancelar",
            fg_color=Theme.BORDER_DEFAULT,
            hover_color=Theme.TEXT_MUTED,
            text_color=Theme.TEXT_PRIMARY,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        self.btn_apply = ctk.CTkButton(
            footer,
            text="⚡ Aplicar Gastos",
            fg_color="#e11d48",
            hover_color="#be123c",
            text_color="#ffffff",
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._handle_apply
        )
        self.btn_apply.pack(side="right")

        self._recalculate_total()

    def _select_all(self):
        for var in self.checkbox_vars.values():
            var.set(True)
        self._recalculate_total()

    def _deselect_all(self):
        for var in self.checkbox_vars.values():
            var.set(False)
        self._recalculate_total()

    def _recalculate_total(self):
        recurring_list = self.db.get_recurring_expenses(only_active=True)
        total = 0.0
        for item in recurring_list:
            if item["id"] in self.checkbox_vars and self.checkbox_vars[item["id"]].get():
                total += item["amount"]
        self.lbl_total.configure(text=f"Total a Registrar: ${total:,.0f} COP")

    def _handle_apply(self):
        selected_ids = [rec_id for rec_id, var in self.checkbox_vars.items() if var.get()]
        if not selected_ids:
            return

        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            date_str = datetime.now().strftime("%Y-%m-%d")

        count, total = self.db.apply_recurring_expenses(date_str, selected_ids)
        self.grab_release()
        self.destroy()

        if self.on_applied_cb:
            self.on_applied_cb(count, total)
