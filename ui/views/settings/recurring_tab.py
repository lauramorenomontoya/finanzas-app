import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from core.constants import CurrencyLabels, Categories
from ui.components import ConfirmDialog, EditRecurringModal
from core.event_bus import EventBus

class RecurringTab(ctk.CTkFrame):
    def __init__(self, master, controller, toast, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.toast = toast

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=45, uniform="settings_rec")
        self.grid_columnconfigure(1, weight=55, uniform="settings_rec")
        self.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Formulario
        form_panel = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, Theme.SPACING_SM))

        ctk.CTkLabel(
            form_panel,
            text="➕ Añadir Gasto Fijo Recurrente",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=Theme.SPACING_MD, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        # Selector de Moneda
        ctk.CTkLabel(form_panel, text="Moneda del Gasto Fijo:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))
        self.rec_curr_seg = ctk.CTkSegmentedButton(
            form_panel,
            values=[CurrencyLabels.COP, CurrencyLabels.USD],
            height=30,
            command=self._on_rec_currency_changed
        )
        self.rec_curr_seg.set("🇨🇴 Pesos (COP)")
        self.rec_curr_seg.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        ctk.CTkLabel(form_panel, text="Categoría:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))
        self.rec_cat_combo = ctk.CTkComboBox(
            form_panel,
            values=Categories.EXPENSE_DEFAULT_COP,
            height=32,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        self.rec_cat_combo.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        ctk.CTkLabel(form_panel, text="Descripción / Concepto:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))
        self.rec_desc_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: Pago arriendo mensual / ChatGPT Plus",
            height=32,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.rec_desc_entry.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        self.lbl_rec_amt = ctk.CTkLabel(form_panel, text="Monto Estimado ($ COP):", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY)
        self.lbl_rec_amt.pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))

        self.rec_amount_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: 1500000",
            height=32,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.rec_amount_entry.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        ctk.CTkLabel(form_panel, text="Día habitual de pago (1 al 31):", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_XS))
        self.rec_day_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: 1",
            height=32,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.rec_day_entry.insert(0, "1")
        self.rec_day_entry.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        self.btn_save_rec = ctk.CTkButton(
            form_panel,
            text="💾 Guardar en Plantilla",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.ERROR,
            hover_color=Theme.ERROR_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            command=self._handle_save_recurring
        )
        self.btn_save_rec.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        # Panel Derecho: Lista
        list_panel = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        list_panel.grid(row=0, column=1, sticky="nsew", padx=(Theme.SPACING_SM, 0))

        list_header = ctk.CTkFrame(list_panel, fg_color="transparent")
        list_header.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        ctk.CTkLabel(
            list_header,
            text="📋 Plantilla de Gastos Fijos Multimoneda",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.lbl_rec_total = ctk.CTkLabel(list_header, text="COP: $0 • USD: $0", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.ACCENT_ROSE)
        self.lbl_rec_total.pack(side="right")

        self.rec_scroll = ctk.CTkScrollableFrame(list_panel, fg_color="transparent")
        self.rec_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

    def _on_rec_currency_changed(self, choice: str):
        if "USD" in choice:
            self.lbl_rec_amt.configure(text="Monto Estimado ($ USD):")
            self.rec_amount_entry.configure(placeholder_text="Ej: 20.00")
            cats = [c["name"] for c in self.controller.get_categories("EXPENSE_USD")]
            if cats:
                self.rec_cat_combo.configure(values=cats)
                self.rec_cat_combo.set(cats[0])
        else:
            self.lbl_rec_amt.configure(text="Monto Estimado ($ COP):")
            self.rec_amount_entry.configure(placeholder_text="Ej: 1500000")
            cats = [c["name"] for c in self.controller.get_categories("EXPENSE_COP")]
            if cats:
                self.rec_cat_combo.configure(values=cats)
                self.rec_cat_combo.set(cats[0])

    def refresh_data(self):
        for widget in self.rec_scroll.winfo_children():
            widget.destroy()

        items = self.controller.get_recurring_expenses()
        total_cop = 0.0
        total_usd = 0.0

        if not items:
            ctk.CTkLabel(
                self.rec_scroll,
                text="No hay gastos fijos registrados en la plantilla.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED
            ).pack(pady=Theme.SPACING_XL)
            self.lbl_rec_total.configure(text="COP: $0 • USD: $0")
            return

        for item in items:
            amount_val = float(item.get("amount", item.get("estimated_amount", 0.0)))
            if item["currency"] == "COP":
                total_cop += amount_val
            else:
                total_usd += amount_val

            card = ctk.CTkFrame(self.rec_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=Theme.SPACING_MD, pady=Theme.SPACING_SM)

            left_box = ctk.CTkFrame(inner, fg_color="transparent")
            left_box.pack(side="left", fill="both", expand=True)

            active_badge = "" if item.get("is_active", 1) == 1 else " (Inactivo)"
            ctk.CTkLabel(
                left_box,
                text=f"{item['description']}{active_badge}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.TEXT_PRIMARY if item.get("is_active", 1) == 1 else Theme.TEXT_MUTED
            ).pack(anchor="w")

            curr = item["currency"]
            bal_str = f"${amount_val:,.2f} USD" if curr == "USD" else f"${amount_val:,.0f} COP"
            ctk.CTkLabel(
                left_box,
                text=f"Categoría: {item['category']} • Día de pago: {item['due_day']} • Monto: {bal_str}",
                font=ctk.CTkFont(size=11),
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

            btns = ctk.CTkFrame(inner, fg_color="transparent")
            btns.pack(side="right")

            btn_edit = ctk.CTkButton(
                btns,
                text="✏️ Editar",
                width=65,
                height=28,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.BG_INPUT,
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda r=item: self._handle_edit_recurring(r)
            )
            btn_edit.pack(side="left", padx=Theme.SPACING_XS)

            btn_del = ctk.CTkButton(
                btns,
                text="🗑️",
                width=28,
                height=28,
                corner_radius=Theme.SPACING_XS,
                fg_color="transparent",
                hover_color=Theme.ERROR_HOVER,
                font=ctk.CTkFont(size=11),
                command=lambda rid=item["id"], desc=item["description"]: self._prompt_delete_recurring(rid, desc)
            )
            btn_del.pack(side="left")

        self.lbl_rec_total.configure(text=f"COP: ${total_cop:,.0f} • USD: ${total_usd:,.2f}")

    def _handle_save_recurring(self):
        curr_choice = self.rec_curr_seg.get()
        currency = "USD" if "USD" in curr_choice else "COP"
        category = self.rec_cat_combo.get()
        description = self.rec_desc_entry.get()
        
        # Clean numeric input
        amount_raw = self.rec_amount_entry.get().strip()
        if currency == "COP":
            amount_raw = amount_raw.replace(".", "").replace(",", ".")
        else:
            amount_raw = amount_raw.replace(",", ".")

        day_raw = self.rec_day_entry.get()

        success, msg = self.controller.add_recurring_expense(category, description, amount_raw, currency, day_raw)
        self.toast.show(msg, is_error=not success)
        if success:
            self.rec_desc_entry.delete(0, "end")
            self.rec_amount_entry.delete(0, "end")
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")

    def _prompt_delete_recurring(self, rec_id: int, description: str):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar de Plantilla",
            message=f"¿Deseas eliminar '{description}' de la plantilla de gastos fijos?",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete_recurring(rec_id)
        )

    def _execute_delete_recurring(self, rec_id: int):
        success, msg = self.controller.delete_recurring_expense(rec_id)
        self.toast.show(msg, is_error=not success)
        if success:
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")

    def _handle_edit_recurring(self, item: Dict[str, Any]):
        EditRecurringModal(
            self.winfo_toplevel(),
            self.controller.db,
            recurring_item=item,
            on_success=self._on_recurring_saved
        )

    def _on_recurring_saved(self):
        self.toast.show("Gasto fijo actualizado en la plantilla.", is_error=False)
        self.refresh_data()
        EventBus.publish("DATA_UPDATED")
