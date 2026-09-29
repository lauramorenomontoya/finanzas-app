"""
Modal para Aplicar Gastos Fijos del Mes de Forma Masiva con un Solo Clic.
Permite seleccionar qué pagos programados registrar en bloque con fecha personalizable.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any
from ui.theme import Theme
from ui.components.date_picker import DatePickerWidget
from ui.utils.modal_helper import center_window


class ApplyRecurringModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        target_ym: Optional[str] = None,
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.target_ym = target_ym or datetime.now().strftime("%Y-%m")
        self.on_success = on_success
        self.check_vars: Dict[int, ctk.IntVar] = {}
        self.items_data: List[Dict[str, Any]] = []

        self.title("Aplicar Gastos Fijos del Mes")
        self.geometry("680x560")
        self.minsize(620, 480)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._load_data()
        self._build_ui()

    def _center_window(self, parent):
        center_window(self, parent, 680, 560)

    def _format_month_name(self, ym: str) -> str:
        try:
            dt = datetime.strptime(ym, "%Y-%m")
            meses = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
            return f"{meses[dt.month - 1]} {dt.year}"
        except Exception:
            return ym

    def _load_data(self):
        all_status = self.db.get_recurring_checklist_status(self.target_ym)
        # Filtrar únicamente los que no han sido pagados
        self.items_data = [item for item in all_status if not item["is_paid"]]

    def _build_ui(self):
        main_card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_card.pack(fill="both", expand=True, padx=18, pady=18)

        m_name = self._format_month_name(self.target_ym)
        self.title(f"Aplicar Gastos Fijos - {m_name}")

        # 1. Cabecera
        header = ctk.CTkFrame(main_card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            header,
            text=f"📅 Aplicar Gastos Fijos de {m_name}",
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=f"Registra masivamente los gastos periódicos pendientes para {m_name}.",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # 2. Barra de Configuración: Fecha y Acciones Rápidas
        config_bar = ctk.CTkFrame(main_card, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        config_bar.pack(fill="x", padx=18, pady=(0, 10))

        config_inner = ctk.CTkFrame(config_bar, fg_color="transparent")
        config_inner.pack(fill="x", padx=12, pady=8)

        # Selector de Fecha
        date_box = ctk.CTkFrame(config_inner, fg_color="transparent")
        date_box.pack(side="left")

        ctk.CTkLabel(
            date_box,
            text="Fecha de Registro:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 8))

        self.date_picker = DatePickerWidget(date_box, width=130, height=30)
        self.date_picker.pack(side="left")

        # Botones de selección rápida
        btn_box = ctk.CTkFrame(config_inner, fg_color="transparent")
        btn_box.pack(side="right")

        btn_all = ctk.CTkButton(
            btn_box,
            text="Marcar Todos",
            height=28,
            width=100,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_BLUE,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            command=self._select_all
        )
        btn_all.pack(side="left", padx=3)

        btn_none = ctk.CTkButton(
            btn_box,
            text="Desmarcar",
            height=28,
            width=90,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_MUTED,
            font=ctk.CTkFont(size=11),
            corner_radius=6,
            command=self._deselect_all
        )
        btn_none.pack(side="left", padx=3)

        # 3. Lista con Scroll de Gastos Pendientes
        self.scroll_frame = ctk.CTkScrollableFrame(main_card, fg_color=Theme.BG_INPUT, corner_radius=8)
        self.scroll_frame.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        if not self.items_data:
            empty_box = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            empty_box.pack(expand=True, pady=40)
            ctk.CTkLabel(
                empty_box,
                text="🎉 ¡Excelente! No hay gastos fijos pendientes este mes.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.ACCENT_GREEN
            ).pack()
            ctk.CTkLabel(
                empty_box,
                text="Todos los gastos de la plantilla ya se encuentran registrados.",
                font=ctk.CTkFont(size=11),
                text_color=Theme.TEXT_MUTED
            ).pack(pady=(4, 0))
        else:
            for item in self.items_data:
                item_id = item["id"]
                curr = item.get("currency", "COP")

                row_card = ctk.CTkFrame(self.scroll_frame, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
                row_card.pack(fill="x", pady=2, padx=2)

                inner_row = ctk.CTkFrame(row_card, fg_color="transparent")
                inner_row.pack(fill="x", padx=10, pady=8)

                var = ctk.IntVar(value=1)
                self.check_vars[item_id] = var

                chk = ctk.CTkCheckBox(
                    inner_row,
                    text="",
                    width=24,
                    variable=var,
                    checkbox_height=18,
                    checkbox_width=18,
                    corner_radius=4,
                    fg_color="#10b981",
                    hover_color="#059669",
                    command=self._update_summary
                )
                chk.pack(side="left", padx=(0, 8))

                # Monto a la derecha primero
                amt_str = f"${item['amount']:,.2f} USD" if curr == "USD" else f"${item['amount']:,.0f} COP"
                amt_lbl = ctk.CTkLabel(
                    inner_row,
                    text=amt_str,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=Theme.ACCENT_ROSE
                )
                amt_lbl.pack(side="right", padx=(8, 4))

                # Info central
                info_box = ctk.CTkFrame(inner_row, fg_color="transparent")
                info_box.pack(side="left", fill="both", expand=True)

                ctk.CTkLabel(
                    info_box,
                    text=f"[{curr}] {item['category']} • {item['description']}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=Theme.TEXT_PRIMARY
                ).pack(anchor="w")

                ctk.CTkLabel(
                    info_box,
                    text=f"Día sugerido de pago: {item['due_day']}",
                    font=ctk.CTkFont(size=10),
                    text_color=Theme.TEXT_MUTED
                ).pack(anchor="w")

        # 4. Pie de Página con Resumen y Botón de Aplicar
        footer = ctk.CTkFrame(main_card, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 14))

        self.lbl_summary = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_summary.pack(side="left")

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(side="right")

        btn_cancel = ctk.CTkButton(
            btn_row,
            text="Cancelar",
            height=36,
            width=90,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self.destroy
        )
        btn_cancel.pack(side="left", padx=(0, 8))

        self.btn_apply = ctk.CTkButton(
            btn_row,
            text="✅ Aplicar Gastos Seleccionados",
            height=36,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._handle_apply
        )
        self.btn_apply.pack(side="left")

        self._update_summary()

    def _select_all(self):
        for var in self.check_vars.values():
            var.set(1)
        self._update_summary()

    def _deselect_all(self):
        for var in self.check_vars.values():
            var.set(0)
        self._update_summary()

    def _update_summary(self):
        selected_ids = [item_id for item_id, var in self.check_vars.items() if var.get() == 1]
        count = len(selected_ids)

        selected_items = [i for i in self.items_data if i["id"] in selected_ids]
        tot_cop = sum(i["amount"] for i in selected_items if i.get("currency", "COP") == "COP")
        tot_usd = sum(i["amount"] for i in selected_items if i.get("currency", "COP") == "USD")

        self.lbl_summary.configure(
            text=f"Seleccionados: {count} de {len(self.items_data)} ( ${tot_cop:,.0f} COP • ${tot_usd:,.2f} USD )"
        )
        if count == 0 or not self.items_data:
            self.btn_apply.configure(state="disabled", text="Ningún gasto seleccionado")
        else:
            self.btn_apply.configure(state="normal", text=f"✅ Aplicar {count} Gasto{'s' if count > 1 else ''}")

    def _handle_apply(self):
        selected_ids = [item_id for item_id, var in self.check_vars.items() if var.get() == 1]
        if not selected_ids:
            return

        date_str = self.date_picker.get().strip()

        self.btn_apply.configure(state="disabled", text="⏳ Registrando...")
        self.update_idletasks()

        res = self.db.apply_recurring_batch(selected_ids, date_str=date_str, target_month=self.target_ym)

        if res.get("success"):
            applied = res.get("applied", 0)
            m_name = self._format_month_name(self.target_ym)
            messagebox.showinfo(
                "Gastos Fijos Aplicados",
                f"¡Operación completada con éxito!\n\nSe registraron {applied} gastos fijos para {m_name} con fecha {date_str}."
            )
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            errors = "\n".join(res.get("errors", ["Error desconocido"]))
            messagebox.showerror("Error al aplicar gastos", f"Ocurrió un error al registrar los gastos:\n{errors}")
            self.btn_apply.configure(state="normal", text="Reintentar Aplicar")
