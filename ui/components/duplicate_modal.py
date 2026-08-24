"""
Modal Rápido para Duplicar Registros Financieros:
Permite clonar compras o ingresos recurrentes cambiando la fecha con un solo clic.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from ui.theme import Theme


from ui.components.date_picker import DatePickerWidget


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
        self.geometry("460x400")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Encabezado
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            header,
            text="📋 Duplicar Movimiento",
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        concept = self.record.get("category") or self.record.get("platform") or self.record.get("concept") or "Movimiento"
        amt = self.record.get("amount") or self.record.get("inflow") or self.record.get("outflow") or 0.0
        curr = self.record.get("currency", "COP")
        amt_str = f"${amt:,.2f} USD" if curr == "USD" else f"${amt:,.0f} COP"

        ctk.CTkLabel(
            header,
            text=f"Base: {concept} ({amt_str})",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Campo Nueva Fecha con DatePickerWidget
        ctk.CTkLabel(main_frame, text="Nueva Fecha de Registro:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 4))
        self.date_entry = DatePickerWidget(main_frame, height=36)
        self.date_entry.pack(fill="x", padx=20, pady=(0, 12))

        # Campo Notas
        ctk.CTkLabel(main_frame, text="Nota o Concepto:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 4))
        self.notes_entry = ctk.CTkEntry(main_frame, height=36, corner_radius=8, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_DEFAULT, font=ctk.CTkFont(size=13))
        self.notes_entry.insert(0, str(self.record.get("notes", "") or ""))
        self.notes_entry.pack(fill="x", padx=20, pady=(0, 14))

        self.lbl_error = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", padx=20, pady=(0, 8))

        btn_clone = ctk.CTkButton(
            main_frame,
            text="📋 Clonar y Guardar Registro",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            command=self._handle_duplicate
        )
        btn_clone.pack(fill="x", padx=20, pady=(0, 10))

    def _set_today(self):
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def _handle_duplicate(self):
        new_date = self.date_entry.get().strip()
        new_notes = self.notes_entry.get().strip()
        rec_id = self.record["id"]

        try:
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            self.lbl_error.configure(text="⚠️ La fecha debe tener formato YYYY-MM-DD.")
            return

        success, msg = self.db.duplicate_record(
            source_table=self.source_table,
            record_id=rec_id,
            new_date=new_date,
            new_notes=new_notes
        )

        if success:
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            self.lbl_error.configure(text=f"⚠️ {msg}")
