"""
Modal de Búsqueda Global Rápida (Cmd+K / Ctrl+K).
Permite buscar instantáneamente en todo el historial financiero con resultados interactivos y navegación directa.
"""

import customtkinter as ctk
from typing import Callable, Optional, List, Dict, Any
from ui.theme import Theme


class GlobalSearchModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        navigate_to: Optional[Callable[[str], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.navigate_to = navigate_to
        self.search_job = None

        self.title("Búsqueda Global Rápida")
        self.geometry("740x520")
        self.minsize(650, 420)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui()

        # Atajos de teclado para cerrar
        self.bind("<Escape>", lambda _: self.destroy())

    def _center_window(self, parent):
        self.update_idletasks()
        try:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            x = parent_x + (parent_w - 740) // 2
            y = parent_y + (parent_h - 520) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self):
        main_card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_card.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Barra de Búsqueda Superior
        search_box = ctk.CTkFrame(main_card, fg_color=Theme.BG_INPUT, corner_radius=10, border_width=1, border_color=Theme.BORDER_DEFAULT)
        search_box.pack(fill="x", padx=16, pady=(16, 10))

        search_inner = ctk.CTkFrame(search_box, fg_color="transparent")
        search_inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(
            search_inner,
            text="🔍",
            font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=(0, 8))

        self.entry_query = ctk.CTkEntry(
            search_inner,
            placeholder_text="Escribe para buscar movimientos, conceptos, clientes, notas o tags...",
            height=34,
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(size=14)
        )
        self.entry_query.pack(side="left", fill="x", expand=True)
        self.entry_query.focus_set()
        self.entry_query.bind("<KeyRelease>", self._on_key_release)

        btn_clear = ctk.CTkButton(
            search_inner,
            text="✕",
            width=28,
            height=28,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_MUTED,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._clear_search
        )
        btn_clear.pack(side="right")

        # 2. Encabezado de Resultados
        results_header = ctk.CTkFrame(main_card, fg_color="transparent")
        results_header.pack(fill="x", padx=18, pady=(0, 6))

        self.lbl_results_count = ctk.CTkLabel(
            results_header,
            text="Comienza a escribir para ver resultados en tiempo real",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_results_count.pack(side="left")

        # 3. Lista de Resultados con Scroll
        self.results_scroll = ctk.CTkScrollableFrame(main_card, fg_color=Theme.BG_INPUT, corner_radius=8)
        self.results_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # 4. Barra Inferior con Ayuda de Atajos
        footer = ctk.CTkFrame(main_card, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(
            footer,
            text="💡 Tip: Presiona Escape para cerrar • Clic en un resultado para navegar a su módulo",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED
        ).pack(side="left")

        # Cargar últimos movimientos al abrir
        self._execute_search("")

    def _clear_search(self):
        self.entry_query.delete(0, "end")
        self._execute_search("")

    def _on_key_release(self, event):
        if event.keysym in ("Escape", "Up", "Down", "Return"):
            return

        if self.search_job:
            self.after_cancel(self.search_job)

        query = self.entry_query.get().strip()
        self.search_job = self.after(200, lambda: self._execute_search(query))

    def _execute_search(self, query: str):
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        results = self.db.get_unified_ledger(limit=30, search_query=query if query else None)

        if not results:
            self.lbl_results_count.configure(text=f"No se encontraron resultados para '{query}'")
            empty_box = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
            empty_box.pack(expand=True, pady=40)
            ctk.CTkLabel(
                empty_box,
                text="🔍 Sin coincidencias",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=Theme.TEXT_MUTED
            ).pack()
            return

        count_str = f"{len(results)} movimientos encontrados" if query else "Últimos movimientos registrados:"
        self.lbl_results_count.configure(text=count_str)

        for row_data in results:
            mod = row_data["module"]
            curr = row_data["currency"]
            inflow = row_data["inflow"]
            outflow = row_data["outflow"]

            # Definir color e importe
            if inflow > 0:
                amt_str = f"+${inflow:,.2f} USD" if curr == "USD" else f"+${inflow:,.0f} COP"
                amt_color = Theme.ACCENT_GREEN
            else:
                amt_str = f"-${outflow:,.2f} USD" if curr == "USD" else f"-${outflow:,.0f} COP"
                amt_color = Theme.ACCENT_ROSE

            # Tarjeta de resultado interactiva
            card = ctk.CTkFrame(self.results_scroll, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=2, padx=2)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=8)

            # Badge de módulo
            badge_color = "#0284c7" if "USD" in mod else ("#6366f1" if "Conversión" in mod else "#10b981")
            mod_badge = ctk.CTkLabel(
                inner,
                text=f" {mod} ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=badge_color,
                text_color="#ffffff",
                corner_radius=4
            )
            mod_badge.pack(side="left", padx=(0, 8))

            # Monto a la derecha
            amt_lbl = ctk.CTkLabel(
                inner,
                text=amt_str,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=amt_color
            )
            amt_lbl.pack(side="right", padx=(8, 2))

            # Info central
            info_box = ctk.CTkFrame(inner, fg_color="transparent")
            info_box.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(
                info_box,
                text=f"{row_data['date']} • {row_data['concept']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(anchor="w")

            sub_notes = row_data["notes"] if row_data["notes"] else row_data["extra_info"]
            if sub_notes:
                ctk.CTkLabel(
                    info_box,
                    text=sub_notes,
                    font=ctk.CTkFont(size=10),
                    text_color=Theme.TEXT_MUTED
                ).pack(anchor="w")

            # Acción al hacer clic
            card.bind("<Button-1>", lambda _, m=mod: self._on_result_clicked(m))
            inner.bind("<Button-1>", lambda _, m=mod: self._on_result_clicked(m))
            info_box.bind("<Button-1>", lambda _, m=mod: self._on_result_clicked(m))

    def _on_result_clicked(self, module_name: str):
        if not self.navigate_to:
            self.destroy()
            return

        if "Ingreso" in module_name:
            self.navigate_to("incomes")
        elif "Egreso" in module_name:
            self.navigate_to("expenses")
        elif "Conversión" in module_name:
            self.navigate_to("conversion")
        elif "Inversión" in module_name or "Rendimiento" in module_name:
            self.navigate_to("investments")
        else:
            self.navigate_to("ledger")

        self.destroy()
