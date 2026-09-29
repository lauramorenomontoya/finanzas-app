"""
Modal para editar un Gasto Fijo Recurrente en la Plantilla Multimoneda (COP/USD).
Permite modificar la categoría, descripción, monto, moneda y día sugerido de pago.
Diseño responsivo con pie fijo de botones y cuerpo desplazable.
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from ui.utils.modal_helper import center_window


class EditRecurringModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        recurring_item: Dict[str, Any],
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.item = recurring_item
        self.on_success = on_success

        self.title("Editar Gasto Fijo Recurrente")
        self.geometry("500x580")
        self.minsize(460, 480)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui()

    def _center_window(self, parent):
        center_window(self, parent, 500, 580)

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Encabezado Fijo Superior
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            header,
            text="✏️ Modificar Gasto Fijo",
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Actualiza los parámetros de este pago en tu plantilla recurrente.",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(2, 0))

        # 2. Pie Fijo Inferior con Botones (SIEMPRE VISIBLE)
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=18, pady=(0, 16))

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

        btn_save = ctk.CTkButton(
            btn_row,
            text="💾 Guardar Cambios",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            command=self._handle_save
        )
        btn_save.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 3. Cuerpo Desplazable Central
        scroll_body = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Selector de Moneda
        ctk.CTkLabel(scroll_body, text="Moneda del Gasto:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 2))
        
        curr = self.item.get("currency", "COP")
        self.curr_seg = ctk.CTkSegmentedButton(
            scroll_body,
            values=["🇨🇴 Pesos (COP)", "💵 Dólares (USD)"],
            height=32,
            command=self._on_currency_changed
        )
        self.curr_seg.set("💵 Dólares (USD)" if curr == "USD" else "🇨🇴 Pesos (COP)")
        self.curr_seg.pack(fill="x", padx=6, pady=(0, 12))

        # Selector de Categoría
        ctk.CTkLabel(scroll_body, text="Categoría:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 2))
        
        self.cat_combo = ctk.CTkComboBox(
            scroll_body,
            values=[],
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.cat_combo.pack(fill="x", padx=6, pady=(0, 12))
        self._populate_categories(curr)

        # Descripción
        ctk.CTkLabel(scroll_body, text="Descripción / Concepto:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 2))
        self.desc_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text="Ej: Pago arriendo / Suscripción",
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.desc_entry.insert(0, str(self.item.get("description", "")))
        self.desc_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Monto
        self.lbl_amt = ctk.CTkLabel(
            scroll_body,
            text="Monto Estimado ($ USD):" if curr == "USD" else "Monto Estimado ($ COP):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_amt.pack(anchor="w", padx=6, pady=(0, 2))

        self.amount_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text="Ej: 1500000",
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        amt_val = self.item.get("amount", 0)
        amt_str = f"{amt_val:.2f}" if curr == "USD" else str(int(amt_val))
        self.amount_entry.insert(0, amt_str)
        self.amount_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Día sugerido de pago
        ctk.CTkLabel(scroll_body, text="Día sugerido de pago (1 al 31):", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 2))
        self.day_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text="Ej: 5",
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.day_entry.insert(0, str(self.item.get("due_day", 1)))
        self.day_entry.pack(fill="x", padx=6, pady=(0, 12))

    def _populate_categories(self, currency: str):
        cat_type = "EXPENSE_USD" if currency == "USD" else "EXPENSE_COP"
        cats = [c["name"] for c in self.db.get_categories(cat_type)]
        current_cat = self.item.get("category", "")
        if current_cat and current_cat not in cats:
            cats.insert(0, current_cat)
        if not cats:
            cats = ["Otros Gastos"]
        self.cat_combo.configure(values=cats)
        if current_cat in cats:
            self.cat_combo.set(current_cat)
        else:
            self.cat_combo.set(cats[0])

    def _on_currency_changed(self, choice: str):
        if "USD" in choice:
            self.lbl_amt.configure(text="Monto Estimado ($ USD):")
            self._populate_categories("USD")
        else:
            self.lbl_amt.configure(text="Monto Estimado ($ COP):")
            self._populate_categories("COP")

    def _handle_save(self):
        curr_choice = self.curr_seg.get()
        currency = "USD" if "USD" in curr_choice else "COP"
        category = self.cat_combo.get().strip()
        description = self.desc_entry.get().strip()
        amt_raw = self.amount_entry.get().strip()
        day_raw = self.day_entry.get().strip()

        if not description:
            self.lbl_error.configure(text="⚠️ Ingresa una descripción para el gasto fijo.")
            return

        try:
            if currency == "COP":
                amount = float(amt_raw.replace(".", "").replace(",", "."))
            else:
                amount = float(amt_raw.replace(",", "."))

            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa un monto numérico válido mayor a 0.")
            return

        try:
            due_day = int(day_raw)
            if not (1 <= due_day <= 31):
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ El día de pago debe ser un número entre 1 y 31.")
            return

        success = self.db.update_recurring_expense(
            rec_id=self.item["id"],
            category=category,
            description=description,
            amount=amount,
            currency=currency,
            due_day=due_day,
            is_active=self.item.get("is_active", 1)
        )

        if success:
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            self.lbl_error.configure(text="⚠️ Error al actualizar el gasto fijo en la base de datos.")
