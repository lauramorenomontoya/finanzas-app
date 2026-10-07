"""
Modal Rápido para Duplicar Registros Financieros:
Permite clonar compras o ingresos recurrentes cambiando la fecha con un solo clic.
Diseño responsivo con pie fijo de botones y cuerpo desplazable.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget
from ui.utils.modal_helper import center_window

from ui.components.base_modal import BaseModal

class DuplicateModal(BaseModal):
    def __init__(
        self,
        parent,
        db_manager,
        source_table: str,
        record: Dict[str, Any],
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent, title="Duplicar Registro", width=480, height=480, min_width=440, min_height=420, resizable_x=True, resizable_y=True)
        self.db = db_manager
        self.source_table = source_table
        self.record = record
        self.on_success = on_success

        self._build_ui()

    def _build_ui(self):
        main_frame = self.create_standard_frame()

        # 1. Encabezado Fijo Superior
        concept = self.record.get("category") or self.record.get("platform") or self.record.get("concept") or "Movimiento"
        amt = self.record.get("amount") or self.record.get("inflow") or self.record.get("outflow") or 0.0
        curr = self.record.get("currency", "COP")
        amt_str = f"${amt:,.2f} USD" if curr == "USD" else f"${amt:,.0f} COP"

        header = self.create_header(main_frame, "Duplicar Movimiento", icon="📋")
        ctk.CTkLabel(
            header,
            text=f"Base: {concept} ({amt_str})",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # 2. Pie Fijo Inferior con Botones
        self.create_footer_buttons(
            main_frame,
            on_confirm=self._handle_duplicate,
            on_cancel=self.destroy,
            confirm_text="📋 Clonar y Guardar",
            cancel_text="Cancelar",
            is_destructive=False
        )

        # Label de error (se posiciona justo encima de los botones)
        footer_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_container.pack(side="bottom", fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))

        self.lbl_error = ctk.CTkLabel(footer_container, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", pady=(0, 0))

        # 3. Cuerpo Desplazable Central
        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_SM))

        # Campo Nueva Fecha con DatePickerWidget
        ctk.CTkLabel(scroll_body, text="Nueva Fecha de Registro:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.date_entry = DatePickerWidget(scroll_body, height=36)
        self.date_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

        # Campo Notas
        ctk.CTkLabel(scroll_body, text="Nota o Concepto:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))
        self.notes_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=Theme.SPACING_SM, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.notes_entry.insert(0, str(self.record.get("notes", "") or ""))
        self.notes_entry.pack(fill="x", padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_SM))

    def _handle_duplicate(self):
        new_date = self.date_entry.get().strip()
        new_notes = self.notes_entry.get().strip()

        try:
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            self.lbl_error.configure(text="⚠️ Selecciona una fecha válida.")
            return

        success, msg = self.db.duplicate_record(
            source_table=self.source_table,
            record_id=self.record["id"],
            new_date=new_date,
            new_notes=new_notes
        )

        if success:
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            self.lbl_error.configure(text=f"⚠️ {msg}")
