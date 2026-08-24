"""
Modal para editar un Gasto Fijo Recurrente en la Plantilla Multimoneda (COP/USD).
Permite modificar la categoría, descripción, monto, moneda y día sugerido de pago.
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme


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
        self.geometry("480x490")
        self.minsize(440, 460)
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_WINDOW)

        # Modal focus y centrado
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
            y = parent_y + (parent_h - 490) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Encabezado
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(18, 12))

        ctk.CTkLabel(
            header,
            text="✏️ Modificar Gasto Fijo",
            font=ctk.CTkFont(family="SF Pro Display", size=17, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Actualiza los parámetros de este pago en tu plantilla recurrente.",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(2, 0))

        # 2. Selector de Moneda
        ctk.CTkLabel(container, text="Moneda del Gasto:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        
        curr = self.item.get("currency", "COP")
        self.curr_seg = ctk.CTkSegmentedButton(
            container,
            values=["🇨🇴 Pesos (COP)", "💵 Dólares (USD)"],
            height=32,
            command=self._on_currency_changed
        )
        self.curr_seg.set("💵 Dólares (USD)" if curr == "USD" else "🇨🇴 Pesos (COP)")
        self.curr_seg.pack(fill="x", padx=18, pady=(0, 10))

        # 3. Selector de Categoría
        ctk.CTkLabel(container, text="Categoría:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        
        self.cat_combo = ctk.CTkComboBox(
            container,
            values=[],
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.cat_combo.pack(fill="x", padx=18, pady=(0, 10))
        self._populate_categories(curr)

        # 4. Descripción
        ctk.CTkLabel(container, text="Descripción / Concepto:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        self.desc_entry = ctk.CTkEntry(
            container,
            placeholder_text="Ej: Pago arriendo / Suscripción",
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.desc_entry.insert(0, str(self.item.get("description", "")))
        self.desc_entry.pack(fill="x", padx=18, pady=(0, 10))

        # 5. Monto
        self.lbl_amt = ctk.CTkLabel(
            container,
            text="Monto Estimado ($ USD):" if curr == "USD" else "Monto Estimado ($ COP):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.lbl_amt.pack(anchor="w", padx=18, pady=(0, 2))

        self.amount_entry = ctk.CTkEntry(
            container,
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
        self.amount_entry.pack(fill="x", padx=18, pady=(0, 10))

        # 6. Día sugerido de pago
        ctk.CTkLabel(container, text="Día sugerido de pago (1 al 31):", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=18, pady=(0, 2))
        self.day_entry = ctk.CTkEntry(
            container,
            placeholder_text="Ej: 5",
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.day_entry.insert(0, str(self.item.get("due_day", 1)))
        self.day_entry.pack(fill="x", padx=18, pady=(0, 10))

        # Mensaje de Error
        self.lbl_error = ctk.CTkLabel(container, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", padx=18, pady=(0, 6))

        # Botones de Acción
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(0, 14))

        btn_cancel = ctk.CTkButton(
            btn_row,
            text="Cancelar",
            font=ctk.CTkFont(size=12),
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_SECONDARY,
            command=self.destroy
        )
        btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_save = ctk.CTkButton(
            btn_row,
            text="💾 Guardar Cambios",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            corner_radius=8,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            command=self._handle_save
        )
        btn_save.pack(side="right", fill="x", expand=True, padx=(6, 0))

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
        amt_raw = self.amount_entry.get().strip().replace(".", "").replace(",", ".") if currency == "COP" else self.amount_entry.get().strip().replace(",", ".")
        day_raw = self.day_entry.get().strip()

        if not description:
            self.lbl_error.configure(text="⚠️ La descripción no puede estar vacía.")
            return

        try:
            amount = float(amt_raw)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ Ingresa un monto numérico válido mayor a 0.")
            return

        try:
            due_day = int(day_raw)
            if not (1 <= due_day <= 31):
                due_day = 1
        except ValueError:
            due_day = 1

        rec_id = self.item["id"]

        try:
            success = self.db.update_recurring_expense(
                rec_id=rec_id,
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
                self.lbl_error.configure(text="⚠️ No se pudo actualizar el gasto fijo.")
        except Exception as e:
            self.lbl_error.configure(text=f"⚠️ Error: {str(e)}")
