"""
Modal para aplicar la plantilla de gastos fijos recurrentes del mes actual con un solo clic.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional, List, Dict
from ui.theme import Theme
from ui.utils.modal_helper import center_window


from ui.components.base_modal import BaseModal

class RecurringModalDialog(BaseModal):
    def __init__(
        self,
        parent,
        db_manager,
        on_applied: Optional[Callable[[int, float], None]] = None
    ):
        self.db = db_manager
        self.on_applied_cb = on_applied
        self.checkbox_vars: Dict[int, ctk.BooleanVar] = {}

        super().__init__(parent, title="Aplicar Gastos Fijos del Mes", width=520, height=480, min_width=480, min_height=400, resizable_x=False, resizable_y=False)

        self._build_ui()

    def _build_ui(self):
        container = self.create_standard_frame()

        # Encabezado
        header = self.create_header(container, "Cargar Gastos Fijos Recurrentes", icon="⚡")

        current_month = datetime.now().strftime("%B %Y").capitalize()
        ctk.CTkLabel(
            header,
            text=f"Selecciona los gastos fijos que deseas registrar para {current_month}:",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

        # Campo de fecha para registrar los gastos
        date_row = ctk.CTkFrame(container, fg_color="transparent")
        date_row.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        ctk.CTkLabel(
            date_row,
            text="Fecha de Registro:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left", padx=(0, Theme.SPACING_SM))

        from ui.components.date_picker import DatePickerWidget
        self.date_entry = DatePickerWidget(date_row, height=30)
        self.date_entry.pack(side="left", fill="x", expand=True)

        # Selector rápido Todos / Ninguno
        quick_select = ctk.CTkFrame(container, fg_color="transparent")
        quick_select.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))

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
        btn_all.pack(side="left", padx=(0, Theme.SPACING_XS))

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
        self.scroll_frame.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        recurring_list = self.db.get_recurring_expenses(only_active=True)

        if not recurring_list:
            ctk.CTkLabel(
                self.scroll_frame,
                text="No tienes gastos fijos configurados en tu plantilla.\nPuedes añadirlos en la sección de Categorías y Gastos Fijos.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED,
                justify="center"
            ).pack(pady=Theme.SPACING_XL)
        else:
            for item in recurring_list:
                rec_id = item["id"]
                var = ctk.BooleanVar(value=True)
                self.checkbox_vars[rec_id] = var

                card = ctk.CTkFrame(self.scroll_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
                card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

                chk = ctk.CTkCheckBox(
                    card,
                    text=f"{item['category']} - {item['description']}",
                    variable=var,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=Theme.TEXT_PRIMARY,
                    command=self._recalculate_total
                )
                chk.pack(side="left", padx=Theme.SPACING_SM, pady=Theme.SPACING_SM)

                ctk.CTkLabel(
                    card,
                    text=f"${item['amount']:,.0f} COP",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=Theme.ACCENT_ROSE
                ).pack(side="right", padx=Theme.SPACING_SM, pady=Theme.SPACING_SM)

        # Pie con total y botón de aplicar
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD), side="bottom")

        self.lbl_total = ctk.CTkLabel(
            footer,
            text="Total a Registrar: $0 COP",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_total.pack(side="left")

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(side="right")

        btn_cancel = ctk.CTkButton(
            btn_row,
            text="Cancelar",
            fg_color=Theme.BORDER_DEFAULT,
            hover_color=Theme.TEXT_MUTED,
            text_color=Theme.TEXT_PRIMARY,
            height=34,
            corner_radius=Theme.SPACING_SM,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        )
        btn_cancel.pack(side="left", padx=(0, Theme.SPACING_SM))

        self.btn_apply = ctk.CTkButton(
            btn_row,
            text="⚡ Aplicar Gastos",
            fg_color=Theme.ERROR,
            hover_color=Theme.ERROR_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            height=34,
            corner_radius=Theme.SPACING_SM,
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
