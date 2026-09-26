"""
Modal para Crear o Editar una Deuda / Préstamo en CustomTkinter.
Permite registrar acreedor, monto total, moneda, fecha y notas explicativas.
Diseño responsivo con pie fijo de botones y cuerpo desplazable.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget


class AddDebtModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        debt: Optional[Dict[str, Any]] = None,
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.debt = debt
        self.on_success = on_success

        is_edit = debt is not None
        self.title("Editar Deuda" if is_edit else "Registrar Nueva Deuda")
        self.geometry("480x560")
        self.minsize(440, 500)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_WINDOW)

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
            x = parent_x + (parent_w - 480) // 2
            y = parent_y + (parent_h - 560) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Encabezado Fijo
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        title_text = "✏️ Editar Deuda" if self.debt else "🤝 Registrar Nueva Deuda"
        ctk.CTkLabel(
            header,
            text=title_text,
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        subtitle_text = "Modifica los datos de la obligación" if self.debt else "Ingresa los datos del préstamo o deuda personal/institucional"
        ctk.CTkLabel(
            header,
            text=subtitle_text,
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(main_frame, height=1, fg_color=Theme.BORDER_SUBTLE).pack(fill="x", padx=20, pady=(4, 12))

        # 2. Pie Fijo de Botones
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=(10, 16))

        self.lbl_error = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=Theme.ACCENT_ROSE
        )
        self.lbl_error.pack(anchor="w", pady=(0, 6))

        btn_box = ctk.CTkFrame(footer, fg_color="transparent")
        btn_box.pack(fill="x")

        btn_cancel = ctk.CTkButton(
            btn_box,
            text="Cancelar",
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            height=36,
            corner_radius=8,
            command=self.destroy
        )
        btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 6))

        save_label = "Guardar Cambios" if self.debt else "Registrar Deuda"
        btn_save = ctk.CTkButton(
            btn_box,
            text=save_label,
            fg_color=Theme.ACCENT_BLUE,
            hover_color="#0284c7",
            text_color="#ffffff",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self._save_debt
        )
        btn_save.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # 3. Contenedor Desplazable del Formulario
        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=0)

        # Campo: Acreedor / Prestamista
        ctk.CTkLabel(
            scroll,
            text="Acreedor / Prestamista *",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(4, 2))

        self.entry_creditor = ctk.CTkEntry(
            scroll,
            placeholder_text="Ej: Papá, Banco, Amigo...",
            height=35,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(family="SF Pro Text", size=13)
        )
        self.entry_creditor.pack(fill="x", pady=(0, 12))
        if self.debt:
            self.entry_creditor.insert(0, self.debt["creditor"])

        # Campo: Monto Total
        ctk.CTkLabel(
            scroll,
            text="Monto Total Prestado *",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 2))

        self.entry_amount = ctk.CTkEntry(
            scroll,
            placeholder_text="Ej: 7590000",
            height=35,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(family="SF Pro Text", size=13)
        )
        self.entry_amount.pack(fill="x", pady=(0, 12))
        if self.debt:
            self.entry_amount.insert(0, f"{self.debt['total_amount']:,.0f}".replace(",", ""))

        # Campo: Moneda
        ctk.CTkLabel(
            scroll,
            text="Moneda",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 2))

        self.seg_currency = ctk.CTkSegmentedButton(
            scroll,
            values=["COP", "USD"],
            height=32,
            corner_radius=8
        )
        current_curr = self.debt.get("currency", "COP") if self.debt else "COP"
        self.seg_currency.set(current_curr)
        self.seg_currency.pack(fill="x", pady=(0, 12))

        # Campo: Fecha de Inicio / Adquisición
        ctk.CTkLabel(
            scroll,
            text="Fecha de Adquisición *",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 2))

        init_date = self.debt.get("start_date") if self.debt else datetime.now().strftime("%Y-%m-%d")
        self.date_picker = DatePickerWidget(scroll, initial_date=init_date)
        self.date_picker.pack(fill="x", pady=(0, 12))

        # Campo: Fecha Límite Opcional
        ctk.CTkLabel(
            scroll,
            text="Fecha Límite Estimada (Opcional)",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 2))

        self.entry_due_date = ctk.CTkEntry(
            scroll,
            placeholder_text="AAAA-MM-DD (ej: 2026-12-31)",
            height=35,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(family="SF Pro Text", size=13)
        )
        self.entry_due_date.pack(fill="x", pady=(0, 12))
        if self.debt and self.debt.get("due_date"):
            self.entry_due_date.insert(0, str(self.debt["due_date"]))

        # Campo: Notas
        ctk.CTkLabel(
            scroll,
            text="Notas / Motivo (Opcional)",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 2))

        self.entry_notes = ctk.CTkEntry(
            scroll,
            placeholder_text="Ej: Préstamo para gastos personales / emergencia...",
            height=35,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(family="SF Pro Text", size=13)
        )
        self.entry_notes.pack(fill="x", pady=(0, 14))
        if self.debt and self.debt.get("notes"):
            self.entry_notes.insert(0, self.debt["notes"])

    def _save_debt(self):
        creditor = self.entry_creditor.get().strip()
        amount_raw = self.entry_amount.get().strip().replace("$", "").replace(",", "").replace(".", "")
        currency = self.seg_currency.get()
        start_date = self.date_picker.get_date()
        due_date = self.entry_due_date.get().strip() or None
        notes = self.entry_notes.get().strip()

        if not creditor:
            self.lbl_error.configure(text="⚠️ Ingresa el nombre del acreedor o prestamista.")
            return

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa un monto numérico válido mayor a 0.")
            return

        if self.debt:
            success = self.db.update_debt(
                debt_id=self.debt["id"],
                creditor=creditor,
                total_amount=amount,
                start_date=start_date,
                due_date=due_date,
                notes=notes
            )
            if not success:
                self.lbl_error.configure(text="❌ No se pudo actualizar la deuda.")
                return
        else:
            try:
                self.db.add_debt(
                    creditor=creditor,
                    total_amount=amount,
                    currency=currency,
                    start_date=start_date,
                    due_date=due_date,
                    notes=notes
                )
            except Exception as e:
                self.lbl_error.configure(text=f"❌ Error al guardar: {e}")
                return

        if self.on_success:
            self.on_success()
        self.destroy()
