"""
Ventana Principal y Controlador de Interfaz Gráfica para Control Financiero.
Desarrollada con CustomTkinter con módulos de 'Ingresos' y 'Egresos' multimoneda,
búsqueda global (Cmd+K), sincronización reactiva y arquitectura modular.
"""

import customtkinter as ctk
from typing import Dict
from database.db_manager import DatabaseManager
from ui.theme import Theme
from ui.components import CSVImporterModal, GlobalSearchModal
from ui.views.dashboard import DashboardView
from ui.views.incomes import IncomesView
from ui.views.expenses import ExpensesView
from ui.views.conversion import ConversionView
from ui.views.investments import InvestmentsView
from ui.views.ledger import LedgerView
from ui.views.analytics import AnalyticsView
from ui.views.settings import SettingsView


class FinancialApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Configuración de Tema y Aspecto
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Control Financiero | Ingresos, Egresos & Patrimonio Multimoneda")
        self.geometry("1240x790")
        self.minsize(1050, 660)

        # Inicialización de la Base de Datos y Respaldo Automático
        self.db = DatabaseManager()
        self.db.create_backup()

        # Layout Principal: Sidebar + Área de Contenido
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

        # Atajos de Teclado Globales (Cmd+K en macOS, Ctrl+K en Windows/Linux)
        self.bind_all("<Command-k>", lambda e: self._open_global_search())
        self.bind_all("<Control-k>", lambda e: self._open_global_search())

        # Iniciar en el Dashboard
        self.show_view("dashboard")

    def _build_sidebar(self):
        """Construye la barra de navegación lateral."""
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=Theme.BG_SIDEBAR, border_width=1, border_color=Theme.BORDER_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # 1. Logotipo y Título de la Aplicación
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=18, pady=(22, 14))

        app_title = ctk.CTkLabel(
            brand_frame,
            text="💎 Finanzas Pro",
            font=ctk.CTkFont(family="SF Pro Display", size=19, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        app_title.pack(anchor="w")

        app_subtitle = ctk.CTkLabel(
            brand_frame,
            text="Gestor Multimoneda USD & COP",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=Theme.TEXT_MUTED
        )
        app_subtitle.pack(anchor="w", pady=(2, 0))

        # Botón de Búsqueda Rápida Spotlight (Cmd+K)
        btn_search = ctk.CTkButton(
            self.sidebar,
            text="🔍  Buscar... (⌘K)",
            anchor="w",
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BG_CARD,
            text_color=Theme.TEXT_MUTED,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            command=self._open_global_search
        )
        btn_search.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=Theme.BORDER_SIDEBAR).pack(fill="x", padx=16, pady=(0, 10))

        # 2. Botones de Navegación
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

        nav_items = [
            ("dashboard", "📊  Panel Principal"),
            ("incomes", "📥  Ingresos (USD / COP)"),
            ("expenses", "💸  Egresos & Gastos"),
            ("conversion", "🔄  Puente USD ➔ COP"),
            ("investments", "📈  Cuentas & Inversiones"),
            ("ledger", "📖  Libro Mayor"),
            ("analytics", "📊  Balance General"),
            ("settings", "⚙️  Configuración & CRUD"),
        ]

        for view_key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(family="SF Pro Text", size=13, weight="bold"),
                fg_color="transparent",
                text_color=Theme.TEXT_SECONDARY,
                hover_color=Theme.BG_CARD,
                command=lambda key=view_key: self.show_view(key)
            )
            btn.pack(fill="x", padx=14, pady=2)
            self.nav_buttons[view_key] = btn

        # Botón Importar CSV
        btn_csv = ctk.CTkButton(
            self.sidebar,
            text="📄  Importador CSV",
            anchor="w",
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_BLUE,
            command=self._open_csv_importer
        )
        btn_csv.pack(fill="x", padx=14, pady=(10, 4))

        # 3. Sección Inferior del Sidebar
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=16, pady=16)

        # Widget de Balance Rápido
        self.quick_balance_box = ctk.CTkFrame(footer_frame, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        self.quick_balance_box.pack(fill="x", pady=(0, 10))

        quick_inner = ctk.CTkFrame(self.quick_balance_box, fg_color="transparent")
        quick_inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(
            quick_inner,
            text="SALDOS DISPONIBLES",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        self.lbl_sidebar_usd = ctk.CTkLabel(
            quick_inner,
            text="USD: $0.00",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.ACCENT_BLUE
        )
        self.lbl_sidebar_usd.pack(anchor="w", pady=(2, 0))

        self.lbl_sidebar_cop = ctk.CTkLabel(
            quick_inner,
            text="COP: $0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.ACCENT_GREEN
        )
        self.lbl_sidebar_cop.pack(anchor="w")

        # Selector de Modo Oscuro / Claro
        theme_row = ctk.CTkFrame(footer_frame, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            theme_row,
            text="Modo Oscuro",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left")

        self.theme_switch = ctk.CTkSwitch(
            theme_row,
            text="",
            width=36,
            command=self._toggle_theme
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="right")

        # Indicador de Backup
        backup_info = self.db.get_last_backup_info()
        backup_text = f"🛡️ Backup: {backup_info}" if backup_info else "🛡️ Backup: Activo"
        self.lbl_backup_status = ctk.CTkLabel(
            footer_frame,
            text=backup_text,
            font=ctk.CTkFont(size=10),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_backup_status.pack(anchor="w")

    def _build_content_area(self):
        """Inicializa el contenedor donde se muestran las diferentes vistas."""
        self.content_container = ctk.CTkFrame(self, fg_color=Theme.BG_WINDOW, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Diccionario de vistas cargadas bajo demanda (Lazy Loading)
        self.views: Dict[str, Any] = {}
        self.current_view_key = None

    def get_or_create_view(self, view_key: str):
        """Instancia la vista únicamente cuando el usuario la solicita por primera vez."""
        # Alias
        if view_key == "usd_vault":
            view_key = "incomes"
        elif view_key == "cop_budget":
            view_key = "expenses"

        if view_key in self.views:
            return self.views[view_key]

        view = None
        if view_key == "dashboard":
            view = DashboardView(self.content_container, self.db, navigate_to=self.show_view)
        elif view_key == "incomes":
            view = IncomesView(self.content_container, self.db, on_data_changed=self.on_data_updated)
        elif view_key == "expenses":
            view = ExpensesView(self.content_container, self.db, on_data_changed=self.on_data_updated)
        elif view_key == "conversion":
            view = ConversionView(self.content_container, self.db, on_data_changed=self.on_data_updated)
        elif view_key == "investments":
            view = InvestmentsView(self.content_container, self.db, on_data_changed=self.on_data_updated)
        elif view_key == "ledger":
            view = LedgerView(self.content_container, self.db, on_data_changed=self.on_data_updated)
        elif view_key == "analytics":
            view = AnalyticsView(self.content_container, self.db)
        elif view_key == "settings":
            view = SettingsView(self.content_container, self.db, on_data_changed=self.on_data_updated)

        if view:
            self.views[view_key] = view
            if view_key == "incomes":
                self.views["usd_vault"] = view
            elif view_key == "expenses":
                self.views["cop_budget"] = view

        return view

    def show_view(self, view_key: str):
        """Cambia la vista activa y resalta el botón correspondiente en la barra lateral."""
        if view_key == "usd_vault":
            view_key = "incomes"
        elif view_key == "cop_budget":
            view_key = "expenses"

        view = self.get_or_create_view(view_key)
        if not view:
            return

        if self.current_view_key and self.current_view_key in self.views:
            self.views[self.current_view_key].pack_forget()

        view.pack(fill="both", expand=True)
        self.current_view_key = view_key

        if hasattr(view, "refresh_data"):
            view.refresh_data()

        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.configure(fg_color=Theme.BG_CARD, text_color=Theme.ACCENT_BLUE)
            else:
                btn.configure(fg_color="transparent", text_color=Theme.TEXT_SECONDARY)

        self._update_sidebar_balances()

    def on_data_updated(self):
        """Refresca los balances globales del sidebar y sincroniza la vista activa visible."""
        self._update_sidebar_balances()

        # Refrescar únicamente la vista activa actual (las demás se refrescan bajo demanda al seleccionarlas)
        if self.current_view_key:
            active_view = self.views.get(self.current_view_key)
            if active_view and hasattr(active_view, "refresh_data"):
                active_view.refresh_data()


    def _update_sidebar_balances(self):
        usd_bal = self.db.get_usd_balance()
        cop_bal = self.db.get_cop_balance()
        self.lbl_sidebar_usd.configure(text=f"USD: ${usd_bal:,.2f}")
        self.lbl_sidebar_cop.configure(text=f"COP: ${cop_bal:,.0f}")

    def _open_global_search(self):
        GlobalSearchModal(
            self,
            self.db,
            navigate_to=self.show_view
        )

    def _open_csv_importer(self):
        CSVImporterModal(
            self,
            self.db,
            on_success=self.on_data_updated
        )

    def _toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
