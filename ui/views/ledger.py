"""
Vista de Libro Mayor (Tabla Unificada Global):
Consolida cronológicamente todos los movimientos de ingresos, egresos, conversiones y rendimientos (USD/COP)
con diseño estilo Excel, alineación milimétrica con anchos fijos de columna, filtros y edición interactiva.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any, List, Tuple
from ui.theme import Theme
from ui.components import (
    ToastNotification,
    ConfirmDialog,
    BalanceWarningDialog,
    EditTransactionModal,
    DuplicateModal
)


class LedgerView(ctk.CTkFrame):
    # Anchos fijos en píxeles para garantizar alineación perfecta
    COL_WIDTHS = {
        "date": 85,
        "module": 105,
        "concept": 180,
        "currency": 50,
        "inflow": 105,
        "outflow": 105,
        "detail": 110,
        "notes": 140,
        "actions": 85
    }

    def __init__(self, master, db_manager, on_data_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.on_data_changed = on_data_changed

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        self.toast = ToastNotification(self)

        # 1. Cabecera
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 12))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="📖 Libro Mayor Unificado",
            font=ctk.CTkFont(family="SF Pro Display", size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Tabla consolidada cronológica tipo Excel con todos los movimientos (USD y COP).",
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # 2. Barra de Filtros y Búsqueda
        filter_card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_DEFAULT)
        filter_card.pack(fill="x", padx=24, pady=(0, 10))

        filter_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_inner.pack(fill="x", padx=16, pady=10)

        self._search_timer = None

        # Buscador en tiempo real con debounce
        self.search_entry = ctk.CTkEntry(
            filter_inner,
            placeholder_text="🔍 Buscar concepto, cliente o notas...",
            width=260,
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda _: self._on_search_key())

        # Filtro de Módulo
        ctk.CTkLabel(filter_inner, text="Módulo:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(side="left", padx=(0, 4))
        self.module_combo = ctk.CTkComboBox(
            filter_inner,
            values=["Todos", "Ingresos USD", "Egresos USD", "Ingresos COP", "Egresos COP", "Conversión", "Inversiones", "Rendimientos"],
            width=135,
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda _: self._refresh_table()
        )
        self.module_combo.set("Todos")
        self.module_combo.pack(side="left", padx=(0, 8))

        # Filtro de Etiquetas (Tags)
        ctk.CTkLabel(filter_inner, text="Tag:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(side="left", padx=(0, 4))
        self.tag_filter_combo = ctk.CTkComboBox(
            filter_inner,
            values=["Todos"],
            width=115,
            height=32,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda _: self._refresh_table()
        )
        self.tag_filter_combo.set("Todos")
        self.tag_filter_combo.pack(side="left", padx=(0, 10))

        # Filtro Temporal Rápido (Por defecto Mes Actual para máximo rendimiento)
        self.date_range_seg = ctk.CTkSegmentedButton(
            filter_inner,
            values=["Mes Actual", "Últimos 30 días", "Año Actual", "Todo"],
            height=30,
            command=lambda _: self._refresh_table()
        )
        self.date_range_seg.set("Mes Actual")
        self.date_range_seg.pack(side="right")


        # 3. Barra de Resumen de Totales
        self.summary_bar = ctk.CTkFrame(self, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=8, height=32)
        self.summary_bar.pack(fill="x", padx=24, pady=(0, 8))

        summary_inner = ctk.CTkFrame(self.summary_bar, fg_color="transparent")
        summary_inner.pack(fill="x", padx=14, pady=6)

        self.lbl_stats_count = ctk.CTkLabel(summary_inner, text="0 registros", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_PRIMARY)
        self.lbl_stats_count.pack(side="left")

        self.lbl_stats_cop = ctk.CTkLabel(summary_inner, text="COP: +$0 / -$0", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_GREEN)
        self.lbl_stats_cop.pack(side="left", padx=(20, 0))

        self.lbl_stats_usd = ctk.CTkLabel(summary_inner, text="USD: +$0.00 / -$0.00", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_BLUE)
        self.lbl_stats_usd.pack(side="left", padx=(20, 0))

        # 4. Tabla Principal con Encabezados estilo Excel
        table_container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_DEFAULT)
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Encabezados de Columna con anchos fijos
        header_row = ctk.CTkFrame(table_container, fg_color=Theme.BG_CARD_SUBTLE, height=36, corner_radius=8)
        header_row.pack(fill="x", padx=8, pady=(8, 4))

        cols = [
            ("Fecha", self.COL_WIDTHS["date"], "w"),
            ("Módulo", self.COL_WIDTHS["module"], "w"),
            ("Concepto / Categoría", self.COL_WIDTHS["concept"], "w"),
            ("Moneda", self.COL_WIDTHS["currency"], "center"),
            ("Ingreso (+)", self.COL_WIDTHS["inflow"], "e"),
            ("Egreso (-)", self.COL_WIDTHS["outflow"], "e"),
            ("Detalle", self.COL_WIDTHS["detail"], "w"),
            ("Notas", self.COL_WIDTHS["notes"], "w"),
            ("Acciones", self.COL_WIDTHS["actions"], "center")
        ]

        for title, width, anchor_pos in cols:
            ctk.CTkLabel(
                header_row,
                text=title,
                width=width,
                anchor=anchor_pos,
                font=ctk.CTkFont(family="SF Pro Text", size=11, weight="bold"),
                text_color=Theme.TEXT_SECONDARY
            ).pack(side="left", padx=4, pady=6)

        # Contenedor Scrollable para las Filas
        self.table_scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        # 5. Barra de Paginación en el pie de la tabla
        self.pagination_frame = ctk.CTkFrame(table_container, fg_color="transparent", height=36)
        self.pagination_frame.pack(fill="x", padx=12, pady=(2, 8))

        self.btn_prev_page = ctk.CTkButton(
            self.pagination_frame,
            text="◀ Anterior",
            width=80,
            height=28,
            corner_radius=6,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11),
            command=self._prev_page
        )
        self.btn_prev_page.pack(side="left")

        self.lbl_page_info = ctk.CTkLabel(
            self.pagination_frame,
            text="Página 1 de 1",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_page_info.pack(side="left", padx=14)

        self.btn_next_page = ctk.CTkButton(
            self.pagination_frame,
            text="Siguiente ▶",
            width=80,
            height=28,
            corner_radius=6,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11),
            command=self._next_page
        )
        self.btn_next_page.pack(side="left")

        self.current_page = 1
        self.page_size = 25

    def _on_search_key(self):
        """Aplica debounce de 250ms al tipear en el buscador para no congelar la UI."""
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(250, self._refresh_table)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_current_page()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._render_current_page()


    def _get_date_filters(self) -> Tuple[Optional[str], Optional[str]]:
        choice = self.date_range_seg.get()
        now = datetime.now()

        if choice == "Mes Actual":
            date_from = now.strftime("%Y-%m-01")
            return date_from, None
        elif choice == "Últimos 30 días":
            date_from = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            return date_from, None
        elif choice == "Año Actual":
            date_from = f"{now.year}-01-01"
            return date_from, None
        else:
            return None, None

    def refresh_data(self):
        # Actualizar lista de tags en el combo
        tags = self.db.get_tags() if hasattr(self.db, "get_tags") else []
        tag_names = ["Todos"] + [t["name"] for t in tags]
        current_tag = self.tag_filter_combo.get()
        self.tag_filter_combo.configure(values=tag_names)
        if current_tag in tag_names:
            self.tag_filter_combo.set(current_tag)
        else:
            self.tag_filter_combo.set("Todos")

        self.current_page = 1
        self._refresh_table()

    def _refresh_table(self):
        mod_filter = self.module_combo.get()
        if mod_filter == "Todos":
            mod_filter = None

        tag_choice = self.tag_filter_combo.get()
        tag_id = None
        if tag_choice != "Todos" and hasattr(self.db, "get_tags"):
            tags = self.db.get_tags()
            for t in tags:
                if t["name"] == tag_choice:
                    tag_id = t["id"]
                    break

        date_from, date_to = self._get_date_filters()
        search_q = self.search_entry.get().strip()

        self.cached_rows = self.db.get_unified_ledger(
            limit=500,
            module_filter=mod_filter,
            date_from=date_from,
            date_to=date_to,
            search_query=search_q,
            tag_id=tag_id
        )

        total_in_cop = sum(r["inflow"] for r in self.cached_rows if r["currency"] == "COP")
        total_out_cop = sum(r["outflow"] for r in self.cached_rows if r["currency"] == "COP")
        total_in_usd = sum(r["inflow"] for r in self.cached_rows if r["currency"] == "USD")
        total_out_usd = sum(r["outflow"] for r in self.cached_rows if r["currency"] == "USD")

        self.lbl_stats_count.configure(text=f"{len(self.cached_rows)} movimientos")
        self.lbl_stats_cop.configure(text=f"COP: +${total_in_cop:,.0f} / -${total_out_cop:,.0f} (Neto: ${total_in_cop - total_out_cop:,.0f})")
        self.lbl_stats_usd.configure(text=f"USD: +${total_in_usd:,.2f} / -${total_out_usd:,.2f} (Neto: ${total_in_usd - total_out_usd:,.2f})")

        self.total_pages = max(1, (len(self.cached_rows) + self.page_size - 1) // self.page_size)
        if self.current_page > self.total_pages:
            self.current_page = 1

        self._render_current_page()

    def _render_current_page(self):
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        self.lbl_page_info.configure(text=f"Página {self.current_page} de {self.total_pages} ({len(self.cached_rows)} total)")
        self.btn_prev_page.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next_page.configure(state="normal" if self.current_page < self.total_pages else "disabled")

        if not self.cached_rows:
            ctk.CTkLabel(
                self.table_scroll,
                text="No se encontraron registros con los filtros seleccionados.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED
            ).pack(pady=40)
            return

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_rows = self.cached_rows[start_idx:end_idx]

        for idx, item in enumerate(page_rows):
            curr = item["currency"]
            inflow = item["inflow"]
            outflow = item["outflow"]

            in_str = f"+${inflow:,.2f}" if (inflow > 0 and curr == "USD") else (f"+${inflow:,.0f}" if inflow > 0 else "-")
            out_str = f"-${outflow:,.2f}" if (outflow > 0 and curr == "USD") else (f"-${outflow:,.0f}" if outflow > 0 else "-")

            bg_col = Theme.BG_CARD_SUBTLE if idx % 2 == 0 else "transparent"
            row_frame = ctk.CTkFrame(self.table_scroll, fg_color=bg_col, corner_radius=6, height=32)
            row_frame.pack(fill="x", pady=1, padx=2)

            # Doble clic en la fila para editar
            row_frame.bind("<Double-Button-1>", lambda e, it=item: self._handle_edit(it))

            # 0. Fecha
            lbl_d = ctk.CTkLabel(row_frame, text=item["date"], width=self.COL_WIDTHS["date"], anchor="w", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_PRIMARY)
            lbl_d.pack(side="left", padx=4, pady=4)
            lbl_d.bind("<Double-Button-1>", lambda e, it=item: self._handle_edit(it))

            # 1. Módulo
            lbl_m = ctk.CTkLabel(row_frame, text=item["module"], width=self.COL_WIDTHS["module"], anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_MUTED)
            lbl_m.pack(side="left", padx=4, pady=4)
            lbl_m.bind("<Double-Button-1>", lambda e, it=item: self._handle_edit(it))

            # 2. Concepto
            lbl_c = ctk.CTkLabel(row_frame, text=item["concept"][:26], width=self.COL_WIDTHS["concept"], anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_PRIMARY)
            lbl_c.pack(side="left", padx=4, pady=4)
            lbl_c.bind("<Double-Button-1>", lambda e, it=item: self._handle_edit(it))

            # 3. Moneda
            curr_col = Theme.ACCENT_GREEN if curr == "COP" else Theme.ACCENT_BLUE
            lbl_cur = ctk.CTkLabel(row_frame, text=curr, width=self.COL_WIDTHS["currency"], anchor="center", font=ctk.CTkFont(size=10, weight="bold"), text_color=curr_col)
            lbl_cur.pack(side="left", padx=4, pady=4)
            lbl_cur.bind("<Double-Button-1>", lambda e, it=item: self._handle_edit(it))

            # 4. Ingreso
            lbl_in = ctk.CTkLabel(row_frame, text=in_str, width=self.COL_WIDTHS["inflow"], anchor="e", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.ACCENT_GREEN if inflow > 0 else Theme.TEXT_MUTED)
            lbl_in.pack(side="left", padx=4, pady=4)
            lbl_in.bind("<Double-Button-1>", lambda e, it=item: self._handle_edit(it))

            # 5. Egreso
            lbl_out = ctk.CTkLabel(row_frame, text=out_str, width=self.COL_WIDTHS["outflow"], anchor="e", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.ACCENT_ROSE if outflow > 0 else Theme.TEXT_MUTED)
            lbl_out.pack(side="left", padx=4, pady=4)
            lbl_out.bind("<Double-Button-1>", lambda e, it=item: self._handle_edit(it))

            # 6. Detalle & Tags
            item_tags = item.get("tags", [])
            tag_str = f" [{', '.join([t['name'] for t in item_tags])}]" if item_tags else ""
            det_text = f"{item['extra_info']}{tag_str}"[:20]
            lbl_det = ctk.CTkLabel(row_frame, text=det_text, width=self.COL_WIDTHS["detail"], anchor="w", font=ctk.CTkFont(size=10), text_color=Theme.ACCENT_INDIGO if item_tags else Theme.TEXT_MUTED)
            lbl_det.pack(side="left", padx=4, pady=4)
            lbl_det.bind("<Double-Button-1>", lambda e, it=item: self._handle_edit(it))

            # 7. Notas
            lbl_not = ctk.CTkLabel(row_frame, text=item["notes"][:22], width=self.COL_WIDTHS["notes"], anchor="w", font=ctk.CTkFont(size=10, slant="italic"), text_color=Theme.TEXT_MUTED)
            lbl_not.pack(side="left", padx=4, pady=4)
            lbl_not.bind("<Double-Button-1>", lambda e, it=item: self._handle_edit(it))

            # 8. Botones de Acción
            btn_box = ctk.CTkFrame(row_frame, width=self.COL_WIDTHS["actions"], fg_color="transparent")
            btn_box.pack(side="left", padx=4, pady=2)

            btn_e = ctk.CTkButton(
                btn_box,
                text="✏️",
                width=24,
                height=22,
                corner_radius=4,
                fg_color="transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda it=item: self._handle_edit(it)
            )
            btn_e.pack(side="left", padx=1)

            btn_dup = ctk.CTkButton(
                btn_box,
                text="📋",
                width=24,
                height=22,
                corner_radius=4,
                fg_color="transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda it=item: self._handle_duplicate(it)
            )
            btn_dup.pack(side="left", padx=1)

            btn_d = ctk.CTkButton(
                btn_box,
                text="🗑️",
                width=24,
                height=22,
                corner_radius=4,
                fg_color="transparent",
                hover_color="#450a0a",
                font=ctk.CTkFont(size=11),
                command=lambda it=item: self._prompt_delete(it)
            )
            btn_d.pack(side="left", padx=1)

    def _handle_edit(self, item: Dict[str, Any]):
        table_name = item["source_table"]
        record = self._fetch_full_record(table_name, item["id"])
        if not record:
            self.toast.show("No se pudo cargar el registro original.", is_error=True)
            return

        EditTransactionModal(
            self.winfo_toplevel(),
            self.db,
            source_table=table_name,
            record=record,
            on_success=self._on_action_success
        )

    def _handle_duplicate(self, item: Dict[str, Any]):
        table_name = item["source_table"]
        record = self._fetch_full_record(table_name, item["id"])
        if not record:
            record = item

        DuplicateModal(
            self.winfo_toplevel(),
            self.db,
            source_table=table_name,
            record=record,
            on_success=self._on_action_success
        )

    def _prompt_delete(self, item: Dict[str, Any]):
        table_name = item["source_table"]
        record_id = item["id"]
        concept = item["concept"]
        curr = item["currency"]
        amt = item["inflow"] if item["inflow"] > 0 else item["outflow"]
        amt_str = f"${amt:,.2f} USD" if curr == "USD" else f"${amt:,.0f} COP"

        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar Registro de Libro Mayor",
            message=f"¿Deseas eliminar este registro de {amt_str} en '{concept}' ({item['module']})?\n\nEsta acción ajustará tu balance contable.",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete(table_name, record_id, force=False)
        )

    def _execute_delete(self, table_name: str, record_id: int, force: bool = False):
        if table_name == "usd_transactions":
            success, msg, warn_data = self.db.delete_usd_transaction(record_id, force=force)
        elif table_name == "cop_transactions":
            success, msg, warn_data = self.db.delete_cop_transaction(record_id, force=force)
        elif table_name == "account_transactions":
            success, msg, warn_data = self.db.delete_account_transaction(record_id, force=force)
        elif table_name == "conversions":
            success, msg, warn_data = self.db.delete_conversion(record_id, force=force)
        else:
            success, msg, warn_data = False, "Tipo de tabla desconocido.", None

        if success:
            self.toast.show(msg, is_error=False)
            self._on_action_success()
        elif msg == "WARNING_NEGATIVE_BALANCE" and warn_data:
            BalanceWarningDialog(
                self.winfo_toplevel(),
                warning_data=warn_data,
                on_force_confirm=lambda: self._execute_delete(table_name, record_id, force=True)
            )
        else:
            self.toast.show(msg, is_error=True)

    def _fetch_full_record(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?;", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def _on_action_success(self):
        self.refresh_data()
        if self.on_data_changed:
            self.on_data_changed()
