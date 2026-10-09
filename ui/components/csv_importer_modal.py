"""
Modal para Importar Historial Financiero Masivo desde Archivos CSV o Exportación de Notion.
Permite seleccionar archivo local o carpeta completa de Notion, ver previsualización enriquecida con
métricas (Gastos, Ingresos, Inversiones, Rango de Fechas DD/MM/YYYY y Categorías) e importar a SQLite.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from ui.utils.modal_helper import center_window
from services.notion_importer import NotionImporter


class CSVImporterModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.on_success = on_success
        self.selected_target_path = None
        self.current_preview_data = None

        self.title("Importador de Historial CSV & Notion")
        self.geometry("860x680")
        self.minsize(780, 580)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui()

    def _center_window(self, parent):
        center_window(self, parent, 860, 680)

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=Theme.SPACING_MD)

        # 1. Encabezado
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_box,
            text="📥 Importador Masivo: CSV & Notion",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=19, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Carga tus datos exportados de Notion o plantillas CSV estándar con fechas en formato día/mes/año.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        btn_template = ctk.CTkButton(
            header,
            text="📄 Descargar Plantilla",
            height=32,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_BLUE,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._handle_download_template
        )
        btn_template.pack(side="right", padx=(Theme.SPACING_SM, 0))

        # 2. Barra de Selección dual (Archivo o Carpeta Notion)
        picker_box = ctk.CTkFrame(main_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
        picker_box.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))

        picker_inner = ctk.CTkFrame(picker_box, fg_color="transparent")
        picker_inner.pack(fill="x", padx=Theme.SPACING_MD, pady=Theme.SPACING_SM)

        self.lbl_filepath = ctk.CTkLabel(
            picker_inner,
            text="Ningún archivo o carpeta seleccionada",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_filepath.pack(side="left", fill="x", expand=True, padx=(0, Theme.SPACING_SM))

        btn_select_file = ctk.CTkButton(
            picker_inner,
            text="📄 Archivo CSV...",
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._handle_select_file
        )
        btn_select_file.pack(side="right", padx=(Theme.SPACING_XS, 0))

        btn_select_folder = ctk.CTkButton(
            picker_inner,
            text="📦 Carpeta Notion...",
            height=34,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._handle_select_folder
        )
        btn_select_folder.pack(side="right")

        # 3. Resumen y Badge de Tipo Detectado
        self.summary_cards_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.summary_cards_frame.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))

        # 4. Área de Previsualización
        preview_header = ctk.CTkFrame(main_frame, fg_color="transparent")
        preview_header.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_XS))

        self.lbl_preview_title = ctk.CTkLabel(
            preview_header,
            text="👁️ Vista Previa de Datos Detectados",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_preview_title.pack(side="left")

        self.lbl_row_count = ctk.CTkLabel(
            preview_header,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_row_count.pack(side="right")

        self.preview_scroll = ctk.CTkScrollableFrame(main_frame, fg_color=Theme.BG_INPUT, corner_radius=Theme.SPACING_SM, height=220)
        self.preview_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))

        self.lbl_placeholder = ctk.CTkLabel(
            self.preview_scroll,
            text="Selecciona un archivo CSV o la carpeta 'csv_notion' para previsualizar los movimientos antes de importar.",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_placeholder.pack(pady=Theme.SPACING_XL)

        # 5. Footer con Estado y Botón de Importación
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))

        self.lbl_status = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_status.pack(side="left", fill="x", expand=True, padx=(0, Theme.SPACING_SM))

        self.btn_import = ctk.CTkButton(
            footer,
            text="🚀 Importar Datos a SQLite",
            height=40,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled",
            command=self._handle_import
        )
        self.btn_import.pack(side="right")

    def _handle_download_template(self):
        dest_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")],
            initialfile="plantilla_montu.csv",
            title="Guardar Plantilla CSV de Ejemplo"
        )
        if dest_path:
            try:
                self.db.generate_csv_template(save_path=dest_path)
                messagebox.showinfo("Plantilla Guardada", f"La plantilla CSV de ejemplo ha sido guardada en:\n{dest_path}")
            except Exception as e:
                messagebox.showerror("Error al Guardar", f"No se pudo guardar la plantilla: {str(e)}")

    def _handle_select_file(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo CSV para importar",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if not filepath:
            return

        self.selected_target_path = filepath
        filename = os.path.basename(filepath)
        self.lbl_filepath.configure(text=f"📄 {filename}", text_color=Theme.TEXT_PRIMARY)
        self._load_preview(filepath)

    def _handle_select_folder(self):
        folderpath = filedialog.askdirectory(
            title="Seleccionar Carpeta Exportada de Notion (ej. csv_notion)"
        )
        if not folderpath:
            return

        self.selected_target_path = folderpath
        foldername = os.path.basename(folderpath) or folderpath
        self.lbl_filepath.configure(text=f"📦 Carpeta Notion: {foldername}", text_color=Theme.TEXT_PRIMARY)
        self._load_preview(folderpath)

    def _load_preview(self, target_path: str):
        for widget in self.summary_cards_frame.winfo_children():
            widget.destroy()
        for widget in self.preview_scroll.winfo_children():
            widget.destroy()

        try:
            preview = self.db.preview_import_data(target_path)
            self.current_preview_data = preview

            if not preview.get("success"):
                err = preview.get("error", "No se pudo leer la información.")
                ctk.CTkLabel(self.preview_scroll, text=f"⚠️ {err}", text_color=Theme.ACCENT_ROSE).pack(pady=Theme.SPACING_XL)
                self.btn_import.configure(state="disabled")
                return

            f_type = self.db.detect_import_format(target_path)

            # 1. Renderizar Tarjetas de Resumen
            self._render_summary_cards(preview, f_type)

            # 2. Renderizar Tabla de Previsualización
            sample_rows = preview.get("sample_rows", [])
            if not sample_rows:
                ctk.CTkLabel(self.preview_scroll, text="No se detectaron transacciones válidas.", text_color=Theme.TEXT_MUTED).pack(pady=Theme.SPACING_XL)
                self.btn_import.configure(state="disabled")
                return

            # Cabecera de la tabla
            table_hdr = ctk.CTkFrame(self.preview_scroll, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_XS)
            table_hdr.pack(fill="x", pady=(0, Theme.SPACING_XS), padx=Theme.SPACING_XS)

            cols = [("TIPO", 110), ("FECHA (D/M/A)", 100), ("CATEGORÍA", 140), ("CONCEPTO", 240), ("MONTO", 120)]
            for name, w in cols:
                ctk.CTkLabel(table_hdr, text=name, width=w, anchor="w", font=ctk.CTkFont(size=10, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)

            # Filas de datos
            for idx, r in enumerate(sample_rows):
                row_card = ctk.CTkFrame(self.preview_scroll, fg_color=Theme.BG_CARD_SUBTLE if idx % 2 == 0 else "transparent", corner_radius=Theme.SPACING_XS)
                row_card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

                tipo = r.get("tipo", "GASTO_COP")
                t_color = Theme.ACCENT_ROSE if "GASTO" in tipo else Theme.ACCENT_GREEN
                fecha = r.get("fecha", "N/A")
                cat = r.get("categoria", "General")
                con = r.get("concepto", "")
                monto = float(r.get("monto", 0.0))
                m_str = f"${monto:,.0f} COP" if monto >= 1000 else f"${monto:,.2f}"

                ctk.CTkLabel(row_card, text=tipo, width=110, anchor="w", font=ctk.CTkFont(size=10, weight="bold"), text_color=t_color).pack(side="left", padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)
                ctk.CTkLabel(row_card, text=fecha, width=100, anchor="w", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_PRIMARY).pack(side="left", padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)
                ctk.CTkLabel(row_card, text=cat, width=140, anchor="w", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_BLUE).pack(side="left", padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)
                ctk.CTkLabel(row_card, text=con[:30], width=240, anchor="w", font=ctk.CTkFont(size=11), text_color=Theme.TEXT_SECONDARY).pack(side="left", padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)
                ctk.CTkLabel(row_card, text=m_str, width=120, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(side="left", padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)

            self.btn_import.configure(state="normal", fg_color=Theme.SUCCESS)
            self.lbl_status.configure(text="✅ Datos listos para importar a SQLite", text_color=Theme.ACCENT_GREEN)

        except Exception as e:
            ctk.CTkLabel(self.preview_scroll, text=f"Error al analizar datos: {str(e)}", text_color=Theme.ACCENT_ROSE).pack(pady=Theme.SPACING_XL)
            self.btn_import.configure(state="disabled")

    def _render_summary_cards(self, preview: Dict[str, Any], f_type: str):
        # Badge descriptivo
        badge_text = "📦 Exportación Completa de Notion" if f_type == "NOTION_FOLDER" else f"📄 Archivo Detectado: {f_type}"
        badge = ctk.CTkFrame(self.summary_cards_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_XS, border_width=1, border_color=Theme.BORDER_SUBTLE)
        badge.pack(side="top", anchor="w", pady=(0, Theme.SPACING_SM))
        ctk.CTkLabel(badge, text=badge_text, font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.ACCENT_BLUE).pack(padx=Theme.SPACING_SM, pady=Theme.SPACING_XS)

        # Fila de tarjetas de métricas
        row = ctk.CTkFrame(self.summary_cards_frame, fg_color="transparent")
        row.pack(fill="x")

        # Tarjeta 1: Gastos
        g_cnt = preview.get("total_expenses_count", 0)
        g_amt = preview.get("total_expenses_amount", 0.0)
        if g_cnt > 0:
            c1 = ctk.CTkFrame(row, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            c1.pack(side="left", padx=(0, Theme.SPACING_SM), fill="both", expand=True)
            ctk.CTkLabel(c1, text="💸 Total Gastos COP", font=ctk.CTkFont(size=10, weight="bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=Theme.SPACING_SM, pady=(Theme.SPACING_XS, 0))
            ctk.CTkLabel(c1, text=f"${g_amt:,.0f} COP ({g_cnt})", font=ctk.CTkFont(size=13, weight="bold"), text_color=Theme.ACCENT_ROSE).pack(anchor="w", padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_XS))

        # Tarjeta 2: Ingresos
        i_cnt = preview.get("total_incomes_count", 0)
        i_amt = preview.get("total_incomes_amount", 0.0)
        if i_cnt > 0:
            c2 = ctk.CTkFrame(row, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            c2.pack(side="left", padx=(0, Theme.SPACING_SM), fill="both", expand=True)
            ctk.CTkLabel(c2, text="💰 Total Ingresos COP", font=ctk.CTkFont(size=10, weight="bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=Theme.SPACING_SM, pady=(Theme.SPACING_XS, 0))
            ctk.CTkLabel(c2, text=f"${i_amt:,.0f} COP ({i_cnt})", font=ctk.CTkFont(size=13, weight="bold"), text_color=Theme.ACCENT_GREEN).pack(anchor="w", padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_XS))

        # Tarjeta 3: Rango de Fechas
        d_min = preview.get("date_min")
        d_max = preview.get("date_max")
        if d_min and d_max:
            c3 = ctk.CTkFrame(row, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            c3.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(c3, text="📅 Rango de Fechas (D/M/A)", font=ctk.CTkFont(size=10, weight="bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=Theme.SPACING_SM, pady=(Theme.SPACING_XS, 0))
            ctk.CTkLabel(c3, text=f"{d_min} ➔ {d_max}", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_XS))

    def _handle_import(self):
        if not self.selected_target_path:
            return

        self.btn_import.configure(state="disabled", text="⏳ Importando...")
        self.lbl_status.configure(text="⏳ Creando respaldo y procesando registros...", text_color=Theme.ACCENT_BLUE)
        self.update_idletasks()

        res = self.db.import_csv_data(self.selected_target_path)

        if res.get("success"):
            imp_total = res.get("imported_total", res.get("imported", 0))
            imp_exp = res.get("imported_expenses", 0)
            imp_inc = res.get("imported_incomes", 0)
            imp_inv = res.get("imported_investments", 0)
            skp = res.get("skipped", 0)

            msg = (
                f"🎉 ¡Importación Completada con Éxito!\n\n"
                f"• Total Registros Guardados: {imp_total}\n"
                f"  - Gastos Diarios COP: {imp_exp}\n"
                f"  - Ingresos COP: {imp_inc}\n"
                f"  - Inversiones / Fiducuenta: {imp_inv}\n"
                f"• Registros Omitidos / Duplicados: {skp}\n\n"
                f"Se creó un respaldo preventivo de la base de datos."
            )
            messagebox.showinfo("Importación Exitosa", msg)
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            err = res.get("error", "Error desconocido durante la importación.")
            self.lbl_status.configure(text=f"⚠️ {err}", text_color=Theme.ACCENT_ROSE)
            self.btn_import.configure(state="normal", text="🚀 Reintentar Importación")
