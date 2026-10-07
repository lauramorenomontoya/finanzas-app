"""
Vista Principal de Configuración.
Orquesta los submódulos: Categorías, Cuentas, y Gastos Fijos (MVC).
"""

import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
from typing import Callable, Optional
from ui.theme import Theme
from core.constants import SettingsTabs
from controllers.settings_controller import SettingsController
from ui.components import ToastNotification, CSVImporterModal
from ui.views.settings import CategoriesTab, AccountsTab, RecurringTab, AITab
from core.event_bus import EventBus

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, db_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.controller = SettingsController(db_manager)

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        self.toast = ToastNotification(self)

        # 1. Cabecera
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_LG, Theme.SPACING_MD))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_box,
            text="⚙️ Configuración & Personalización",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Administra categorías, cuentas de inversión y gastos fijos multimoneda.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        btn_import = ctk.CTkButton(
            header_frame,
            text="📥 Importar",
            height=36,
            width=100,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_importer
        )
        btn_import.pack(side="right")

        btn_export = ctk.CTkButton(
            header_frame,
            text="💾 Exportar Backup",
            height=36,
            width=130,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._export_backup
        )
        btn_export.pack(side="right", padx=(0, Theme.SPACING_SM))

        # 2. Selector de Sección
        self.section_seg = ctk.CTkSegmentedButton(
            self,
            values=SettingsTabs.OPTIONS,
            height=36,
            command=self._on_section_changed
        )
        self.section_seg.set("🏷️  Categorías")
        self.section_seg.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))

        # 3. Contenedor de contenido
        self.content_box = ctk.CTkFrame(self, fg_color="transparent")
        self.content_box.pack(fill="both", expand=True, padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_LG))

        # 4. Inicializar submódulos (Tabs)
        self.categories_tab = CategoriesTab(self.content_box, self.controller, self.toast)
        self.accounts_tab = AccountsTab(self.content_box, self.controller, self.toast)
        self.recurring_tab = RecurringTab(self.content_box, self.controller, self.toast)
        self.ai_tab = AITab(self.content_box, self.controller, self.toast)

        self._show_active_section()

    def _open_importer(self):
        CSVImporterModal(self.winfo_toplevel(), self.db, on_success=self._on_import_completed)

    def _export_backup(self):
        default_name = f"backup_finanzas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        dest_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            initialfile=default_name,
            title="Guardar Copia de Seguridad",
            filetypes=[("Base de Datos SQLite", "*.db"), ("Todos los archivos", "*.*")]
        )
        if dest_path:
            success, msg = self.controller.export_database_backup(dest_path)
            self.toast.show(msg, is_error=not success)

    def _on_import_completed(self):
        self.toast.show("¡Datos de CSV / Notion importados exitosamente!", is_error=False)
        self.refresh_data()
        EventBus.publish("DATA_UPDATED")

    def _on_section_changed(self, choice: str):
        self._show_active_section()

    def _show_active_section(self):
        choice = self.section_seg.get()
        self.categories_tab.pack_forget()
        self.accounts_tab.pack_forget()
        self.recurring_tab.pack_forget()
        self.ai_tab.pack_forget()

        if "Categorías" in choice:
            self.categories_tab.pack(fill="both", expand=True)
            self.categories_tab.refresh_data()
        elif "Cuentas" in choice:
            self.accounts_tab.pack(fill="both", expand=True)
            self.accounts_tab.refresh_data()
        elif "Gastos Fijos" in choice:
            self.recurring_tab.pack(fill="both", expand=True)
            self.recurring_tab.refresh_data()
        elif "Asistente" in choice or "IA" in choice:
            self.ai_tab.pack(fill="both", expand=True)
            self.ai_tab.refresh_data()

    def refresh_data(self):
        """Delega el refresh a cada una de las pestañas activas/inactivas."""
        self.categories_tab.refresh_data()
        self.accounts_tab.refresh_data()
        self.recurring_tab.refresh_data()
        self.ai_tab.refresh_data()
