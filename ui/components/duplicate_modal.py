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


class DuplicateModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        source_table: str,
        record: Dict[str, Any],
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.source_table = source_table
        self.record = record
        self.on_success = on_success

        self.title("Duplicar Registro")
        self.geometry("480x480")
        self.minsize(440, 420)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui()

    def _center_window(self, parent):
        center_window(self, parent, 480, 480)

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Encabezado Fijo Superior
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        ctk.CTkLabel(
            header,
            text="📋 Duplicar Movimiento",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        concept = self.record.get("category") or self.record.get("platform") or self.record.get("concept") or "Movimiento"
        amt = self.record.get("amount") or self.record.get("inflow") or self.record.get("outflow") or 0.0
        curr = self.record.get("currency", "COP")
        amt_str = f"${amt:,.2f} USD" if curr == "USD" else f"${amt:,.0f} COP"

        ctk.CTkLabel(
            header,
            text=f"Base: {concept} ({amt_str})",
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

        btn_clone = ctk.CTkButton(
            btn_row,
            text="📋 Clonar y Guardar",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            command=self._handle_duplicate
        )
        btn_clone.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 3. Cuerpo Desplazable Central
        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Campo Nueva Fecha con DatePickerWidget
        ctk.CTkLabel(scroll_body, text="Nueva Fecha de Registro:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.date_entry = DatePickerWidget(scroll_body, height=36)
        self.date_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Campo Notas
        ctk.CTkLabel(scroll_body, text="Nota o Concepto:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.notes_entry = ctk.CTkEntry(scroll_body, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.notes_entry.insert(0, str(self.record.get("notes", "") or ""))
        self.notes_entry.pack(fill="x", padx=6, pady=(0, 12))

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
