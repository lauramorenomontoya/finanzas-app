"""
Ventana Principal y Controlador de Interfaz Gráfica para Montu.
Desarrollada con CustomTkinter con módulos de 'Ingresos' y 'Egresos' multimoneda,
búsqueda global (Cmd+K), sincronización reactiva y arquitectura modular.
"""

import customtkinter as ctk
from typing import Dict, Any
from database.db_manager import DatabaseManager
from ui.theme import Theme
from ui.components import CSVImporterModal, GlobalSearchModal, AboutModal, UpdateModal
from services.update_service import UpdateService
from ui.views.dashboard import DashboardView
from ui.views.incomes import IncomesView
from ui.views.expenses import ExpensesView
from ui.views.conversion import ConversionView
from ui.views.investments import InvestmentsView
from ui.views.ledger import LedgerView
from ui.views.analytics import AnalyticsView
from ui.views.settings_view import SettingsView
from ui.views.budget_view import BudgetView
from ui.views.debt_view import DebtView
from core.event_bus import EventBus
from core.constants import APP_VERSION, APP_NAME_VISIBLE, get_asset_path
import os
import sys


class FinancialApp(ctk.CTk):

    def __init__(self, db_manager=None, db_path=None):
        super().__init__()
        from ui.utils.scroll_helper import ScrollHelper
        ScrollHelper.enable_smooth_scrolling()

        # Configuración de Tema y Aspecto
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(f"{APP_NAME_VISIBLE} v{APP_VERSION} | Ingresos, Egresos & Patrimonio Multimoneda")
        self._set_app_icon()

        # Configuración de Ventana Adaptativa y Centrada
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        target_w = int(screen_w * 0.86)
        target_h = int(screen_h * 0.85)
        default_w = min(1420, max(1200, target_w))
        default_h = min(920, max(780, target_h))

        # Ajuste de seguridad si la pantalla es menor al tamaño ideal
        if default_w >= screen_w:
            default_w = max(1000, screen_w - 40)
        if default_h >= screen_h:
            default_h = max(660, screen_h - 70)

        self.minsize(1080, 680)
        pos_x = max(0, (screen_w - default_w) // 2)
        pos_y = max(0, (screen_h - default_h) // 2)
        self.geometry(f"{default_w}x{default_h}+{pos_x}+{pos_y}")

        # Inicialización de la Base de Datos y Respaldo Automático
        if db_manager is not None:
            self.db = db_manager
        elif db_path is not None:
            self.db = DatabaseManager(db_path)
        else:
            self.db = DatabaseManager()
            self.db.create_backup()


        # Layout Principal: Sidebar + Área de Contenido
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

        # Atajos de Teclado Globales (Cmd+K en macOS, Ctrl+K en Windows/Linux, F1 para Acerca de)
        self.bind_all("<Command-k>", lambda e: self._open_global_search())
        self.bind_all("<Control-k>", lambda e: self._open_global_search())
        self.bind_all("<F1>", lambda e: self._open_about_modal())

        # Configurar menús de sistema nativos (About en macOS y Menú Ayuda en Windows)
        self._setup_system_menus()

        # Suscribirse al bus de eventos globales
        EventBus.subscribe("DATA_UPDATED", self.on_data_updated)

        # Iniciar en el Dashboard
        self.show_view("dashboard")

        # Verificación automática de actualizaciones en segundo plano (2s tras abrir)
        self.after(2000, self._check_updates_background)

    def _set_app_icon(self):
        """Configura el ícono de la ventana según la plataforma."""
        try:
            if sys.platform.startswith("win"):
                ico_path = get_asset_path("icon.ico")
                if os.path.exists(ico_path):
                    self.iconbitmap(ico_path)
            elif sys.platform.startswith("linux"):
                icon_path = get_asset_path("icon.png")
                if os.path.exists(icon_path):
                    from PIL import Image, ImageTk
                    pil_img = Image.open(icon_path).resize((64, 64), Image.Resampling.LANCZOS)
                    self._tk_icon = ImageTk.PhotoImage(pil_img)
                    self.iconphoto(False, self._tk_icon)
            # En macOS Cocoa el ícono lo gestiona el Bundle .app (icon.icns) nativamente en el Dock.
        except Exception:
            pass


    def _build_sidebar(self):
        """Construye la barra de navegación lateral."""
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=Theme.BG_SIDEBAR, border_width=1, border_color=Theme.BORDER_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # 1. Logotipo y Título de la Aplicación
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_LG, Theme.SPACING_MD))

        brand_header = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_header.pack(fill="x")

        logo_path = get_asset_path("logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image
                logo_pil = Image.open(logo_path)
                self.sidebar_logo_img = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(30, 30))
                lbl_logo = ctk.CTkLabel(brand_header, image=self.sidebar_logo_img, text="")
                lbl_logo.pack(side="left", padx=(0, Theme.SPACING_SM))
            except Exception:
                pass

        title_col = ctk.CTkFrame(brand_header, fg_color="transparent")
        title_col.pack(side="left", fill="both")

        app_title = ctk.CTkLabel(
            title_col,
            text=APP_NAME_VISIBLE,
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=20, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        app_title.pack(anchor="w")

        app_subtitle = ctk.CTkLabel(
            brand_frame,
            text=f"Finanzas Multimoneda v{APP_VERSION}",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11),
            text_color=Theme.TEXT_MUTED
        )
        app_subtitle.pack(anchor="w", pady=(Theme.SPACING_XS, 0))


        # Botón de Búsqueda Rápida Spotlight (Cmd+K)
        btn_search = ctk.CTkButton(
            self.sidebar,
            text="Buscar... (⌘K)",
            anchor="w",
            height=32,
            corner_radius=Theme.SPACING_SM,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BG_CARD,
            text_color=Theme.TEXT_MUTED,
            border_width=1,
            border_color=Theme.BORDER_SUBTLE,
            command=self._open_global_search
        )
        btn_search.pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=Theme.BORDER_SIDEBAR).pack(fill="x", padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

        # 2. Contenedor de Navegación por Grupos (Scrollable para pantallas de cualquier tamaño)
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.nav_pills: Dict[str, ctk.CTkFrame] = {}

        nav_scroll = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=Theme.BORDER_DEFAULT,
            scrollbar_button_hover_color=Theme.TEXT_MUTED
        )
        nav_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_XS, pady=(0, Theme.SPACING_XS))

        nav_groups = [
            ("FINANZAS", [
                ("dashboard", "Panel Principal"),
                ("incomes", "Bóveda USD / Ingresos"),
                ("expenses", "Egresos & Gastos"),
            ]),
            ("PLANIFICACIÓN", [
                ("budget", "Presupuesto & Metas"),
                ("debts", "Control de Deudas"),
                ("conversion", "Puente USD ➔ COP"),
            ]),
            ("PATRIMONIO", [
                ("investments", "Cuentas & Inversiones"),
                ("ledger", "Libro Mayor"),
                ("analytics", "Balance General"),
            ]),
            ("SISTEMA", [
                ("settings", "Configuración"),
            ]),
        ]

        for group_idx, (group_title, items) in enumerate(nav_groups):
            # Título de Sección
            group_lbl = ctk.CTkLabel(
                nav_scroll,
                text=group_title,
                font=ctk.CTkFont(family=Theme.FONT_TEXT, size=10, weight="bold"),
                text_color=Theme.TEXT_MUTED
            )
            top_pad = 4 if group_idx == 0 else 12
            group_lbl.pack(anchor="w", padx=Theme.SPACING_MD, pady=(top_pad, 2))

            for view_key, label in items:
                item_row = ctk.CTkFrame(nav_scroll, fg_color="transparent")
                item_row.pack(fill="x", padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)

                # Píldora indicadora lateral de selección activa
                pill = ctk.CTkFrame(
                    item_row,
                    width=3,
                    height=20,
                    corner_radius=Theme.SPACING_XS,
                    fg_color="transparent"
                )
                pill.pack(side="left", padx=(0, Theme.SPACING_XS))
                self.nav_pills[view_key] = pill

                btn = ctk.CTkButton(
                    item_row,
                    text=label,
                    anchor="w",
                    height=32,
                    corner_radius=Theme.SPACING_SM,
                    font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
                    fg_color="transparent",
                    text_color=Theme.TEXT_SECONDARY,
                    hover_color=Theme.BG_CARD,
                    command=lambda key=view_key: self.show_view(key)
                )
                btn.pack(side="left", fill="x", expand=True)
                self.nav_buttons[view_key] = btn

        # Botón Importar CSV
        btn_csv = ctk.CTkButton(
            nav_scroll,
            text="Importador CSV",
            anchor="w",
            height=32,
            corner_radius=Theme.SPACING_SM,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12, weight="bold"),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT,
            command=self._open_csv_importer
        )
        btn_csv.pack(fill="x", padx=(Theme.SPACING_SM, Theme.SPACING_XS), pady=(Theme.SPACING_SM, Theme.SPACING_XS))

        # 3. Sección Inferior del Sidebar
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=Theme.SPACING_MD, pady=Theme.SPACING_MD)

        # Widget de Balance Rápido
        self.quick_balance_box = ctk.CTkFrame(footer_frame, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        self.quick_balance_box.pack(fill="x", pady=(0, Theme.SPACING_SM))

        quick_inner = ctk.CTkFrame(self.quick_balance_box, fg_color="transparent")
        quick_inner.pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_SM)

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
            text_color=Theme.ACCENT_USD
        )
        self.lbl_sidebar_usd.pack(anchor="w", pady=(Theme.SPACING_XS, 0))

        self.lbl_sidebar_cop = ctk.CTkLabel(
            quick_inner,
            text="COP: $0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.ACCENT_COP
        )
        self.lbl_sidebar_cop.pack(anchor="w")

        # Selector de Modo Oscuro / Claro
        theme_row = ctk.CTkFrame(footer_frame, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, Theme.SPACING_SM))

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
            progress_color=Theme.ACCENT,
            button_color=Theme.TEXT_PRIMARY,
            button_hover_color=Theme.TEXT_SECONDARY,
            command=self._toggle_theme
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="right")

        # Indicador de Backup
        backup_info = self.db.get_last_backup_info()
        backup_text = f"Backup: {backup_info}" if backup_info else "Backup: Activo"
        self.lbl_backup_status = ctk.CTkLabel(
            footer_frame,
            text=backup_text,
            font=ctk.CTkFont(size=10),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_backup_status.pack(anchor="w")

        # Firma de Autoría Sutil
        self.lbl_author_signature = ctk.CTkLabel(
            footer_frame,
            text="Creado por Laura Moreno",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=10),
            text_color=Theme.TEXT_MUTED,
            cursor="hand2"
        )
        self.lbl_author_signature.pack(anchor="w", pady=(2, 0))
        self.lbl_author_signature.bind("<Button-1>", lambda e: self._open_about_modal())

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
            view = IncomesView(self.content_container, self.db)
        elif view_key == "expenses":
            view = ExpensesView(self.content_container, self.db)
        elif view_key == "budget":
            view = BudgetView(self.content_container, self.db)
        elif view_key == "debts":
            view = DebtView(self.content_container, self.db)
        elif view_key == "conversion":
            view = ConversionView(self.content_container, self.db)
        elif view_key == "investments":
            view = InvestmentsView(self.content_container, self.db)
        elif view_key == "ledger":
            view = LedgerView(self.content_container, self.db)
        elif view_key == "analytics":
            view = AnalyticsView(self.content_container, self.db)
        elif view_key == "settings":
            view = SettingsView(self.content_container, self.db)

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

        if self.current_view_key == view_key:
            return

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
            pill = self.nav_pills.get(key)
            if key == view_key:
                btn.configure(
                    fg_color=Theme.BG_CARD,
                    text_color=Theme.ACCENT,
                    font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12, weight="bold")
                )
                if pill:
                    pill.configure(fg_color=Theme.ACCENT)
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Theme.TEXT_SECONDARY,
                    font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12, weight="normal")
                )
                if pill:
                    pill.configure(fg_color="transparent")

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
            on_success=lambda: EventBus.publish("DATA_UPDATED")
        )

    def _toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def _setup_system_menus(self):
        """Configura los menús nativos del sistema operativo (macOS y Windows)."""
        import tkinter as tk
        import platform

        try:
            # 1. En macOS: Conectar con el diálogo nativo de Apple About
            if platform.system() == "Darwin":
                try:
                    self.createcommand("tkAboutDialog", self._open_about_modal)
                except Exception:
                    pass

            # 2. Barra de menú superior (Ayuda ➔ Buscar Actualizaciones... y Acerca de...)
            menubar = tk.Menu(self)
            help_menu = tk.Menu(menubar, tearoff=0)
            help_menu.add_command(
                label="Buscar Actualizaciones...",
                command=self.check_for_updates_manual
            )
            help_menu.add_separator()
            help_menu.add_command(
                label=f"Acerca de {APP_NAME_VISIBLE}",
                command=self._open_about_modal,
                accelerator="F1" if platform.system() != "Darwin" else ""
            )
            menubar.add_cascade(label="Ayuda", menu=help_menu)
            self.config(menu=menubar)
        except Exception:
            pass

    def _open_about_modal(self):
        """Abre la ventana modal 'Acerca de...' con los créditos de autoría."""
        AboutModal(self)

    def _check_updates_background(self):
        """Inicia la comprobación asíncrona de nuevas versiones en segundo plano."""
        UpdateService.check_for_updates_async(
            APP_VERSION,
            callback=self._on_update_check_finished
        )

    def _on_update_check_finished(self, info: Dict[str, Any]):
        """Procesa el resultado del chequeo silencioso en el hilo de la UI."""
        if info.get("update_available"):
            self.after(0, lambda: self._show_update_modal(info))

    def _show_update_modal(self, info: Dict[str, Any]):
        """Muestra el diálogo emergente con los detalles de la nueva versión."""
        UpdateModal(self, info)

    def check_for_updates_manual(self):
        """Verificación manual invocada por el usuario (muestra feedback si no hay actualizaciones)."""
        def _manual_callback(info: Dict[str, Any]):
            if info.get("update_available"):
                self.after(0, lambda: self._show_update_modal(info))
            else:
                from tkinter import messagebox
                if info.get("error"):
                    self.after(0, lambda: messagebox.showinfo(
                        "Actualizaciones",
                        "No fue posible conectar con el servidor de actualizaciones en este momento.\nVerifica tu conexión a internet."
                    ))
                else:
                    self.after(0, lambda: messagebox.showinfo(
                        f"{APP_NAME_VISIBLE} al día",
                        f"¡Tienes la versión más reciente instalada! (v{APP_VERSION})"
                    ))

        UpdateService.check_for_updates_async(APP_VERSION, callback=_manual_callback)

    def destroy(self):
        try:
            EventBus.unsubscribe("DATA_UPDATED", self.on_data_updated)
        except Exception:
            pass
        super().destroy()

