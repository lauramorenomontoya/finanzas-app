"""
Modal para Importar Historial Financiero Masivo desde Archivos CSV.
Permite seleccionar archivo local, ver previsualización, descargar plantilla e importar a SQLite.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import csv
from typing import Callable, Optional
from ui.theme import Theme


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
        self.selected_file_path = None

        self.title("Importador de Historial CSV")
        self.geometry("780x600")
        self.minsize(720, 520)
        self.configure(fg_color=Theme.BG_WINDOW)

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
            x = parent_x + (parent_w - 780) // 2
            y = parent_y + (parent_h - 600) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. Encabezado con Botón Descargar Plantilla
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 12))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_box,
            text="📄 Importador Masivo de Datos CSV",
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Carga tu historial previo de ingresos, gastos y conversiones directamente a SQLite.",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        btn_template = ctk.CTkButton(
            header,
            text="📥 Descargar Plantilla CSV",
            height=34,
            corner_radius=8,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_BLUE,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._handle_download_template
        )
        btn_template.pack(side="right", padx=(12, 0))

        # 2. Barra de Selección de Archivo
        picker_box = ctk.CTkFrame(main_frame, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        picker_box.pack(fill="x", padx=20, pady=(0, 14))

        picker_inner = ctk.CTkFrame(picker_box, fg_color="transparent")
        picker_inner.pack(fill="x", padx=14, pady=12)

        self.lbl_filepath = ctk.CTkLabel(
            picker_inner,
            text="Ningún archivo .csv seleccionado",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_filepath.pack(side="left", fill="x", expand=True, padx=(0, 12))

        btn_select = ctk.CTkButton(
            picker_inner,
            text="📁 Seleccionar CSV...",
            height=36,
            corner_radius=8,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._handle_select_file
        )
        btn_select.pack(side="right")

        # 3. Área de Previsualización
        preview_header = ctk.CTkFrame(main_frame, fg_color="transparent")
        preview_header.pack(fill="x", padx=20, pady=(0, 6))

        ctk.CTkLabel(
            preview_header,
            text="👁️ Vista Previa del Archivo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.lbl_row_count = ctk.CTkLabel(
            preview_header,
            text="0 filas detectadas",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_row_count.pack(side="right")

        self.preview_scroll = ctk.CTkScrollableFrame(main_frame, fg_color=Theme.BG_INPUT, corner_radius=8, height=190)
        self.preview_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        self.lbl_placeholder = ctk.CTkLabel(
            self.preview_scroll,
            text="Selecciona un archivo .csv para ver la previsualización de datos antes de importar.",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_placeholder.pack(pady=40)

        # 4. Barra de Estado y Botón de Importación
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(0, 14))

        self.lbl_status = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_status.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.btn_import = ctk.CTkButton(
            footer,
            text="🚀 Importar Datos a la Base de Datos",
            height=40,
            corner_radius=8,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled",
            command=self._handle_import
        )
        self.btn_import.pack(side="right")

    def _handle_download_template(self):
        dest_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")],
            initialfile="plantilla_control_financiero.csv",
            title="Guardar Plantilla CSV de Ejemplo"
        )
        if dest_path:
            try:
                self.db.generate_csv_template(save_path=dest_path)
                messagebox.showinfo("Plantilla Guardada", f"La plantilla CSV de ejemplo ha sido guardada exitosamente en:\n{dest_path}")
            except Exception as e:
                messagebox.showerror("Error al Guardar", f"No se pudo guardar la plantilla: {str(e)}")

    def _handle_select_file(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo CSV para importar",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if not filepath:
            return

        self.selected_file_path = filepath
        filename = os.path.basename(filepath)
        self.lbl_filepath.configure(text=f"📄 {filename}", text_color=Theme.TEXT_PRIMARY)
        self._preview_csv(filepath)

    def _preview_csv(self, filepath: str):
        for widget in self.preview_scroll.winfo_children():
            widget.destroy()

        try:
            with open(filepath, mode="r", encoding="utf-8-sig") as f:
                sample = f.read(2048)
                f.seek(0)
                delimiter = ";" if ";" in sample and sample.count(";") > sample.count(",") else ","
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)

            if not rows:
                ctk.CTkLabel(self.preview_scroll, text="El archivo CSV está vacío.", text_color=Theme.ACCENT_ROSE).pack(pady=20)
                self.btn_import.configure(state="disabled")
                return

            headers = rows[0]
            data_rows = rows[1:]
            self.lbl_row_count.configure(text=f"{len(data_rows)} filas detectadas")

            # Encabezados en la vista previa
            header_card = ctk.CTkFrame(self.preview_scroll, fg_color=Theme.BG_CARD, corner_radius=6)
            header_card.pack(fill="x", pady=2, padx=2)
            header_text = " │ ".join(headers[:7])
            ctk.CTkLabel(
                header_card,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=Theme.ACCENT_BLUE
            ).pack(anchor="w", padx=8, pady=4)

            # Primeras 15 filas de ejemplo
            for idx, r in enumerate(data_rows[:15]):
                card = ctk.CTkFrame(self.preview_scroll, fg_color=Theme.BG_CARD_SUBTLE if idx % 2 == 0 else "transparent", corner_radius=4)
                card.pack(fill="x", pady=1, padx=2)
                row_str = f"#{idx+1}: " + " │ ".join(r[:7])
                ctk.CTkLabel(
                    card,
                    text=row_str,
                    font=ctk.CTkFont(size=11),
                    text_color=Theme.TEXT_SECONDARY
                ).pack(anchor="w", padx=8, pady=3)

            if len(data_rows) > 15:
                ctk.CTkLabel(
                    self.preview_scroll,
                    text=f"... y {len(data_rows) - 15} filas adicionales.",
                    font=ctk.CTkFont(size=10, slant="italic"),
                    text_color=Theme.TEXT_MUTED
                ).pack(pady=6)

            self.btn_import.configure(state="normal", fg_color="#10b981")
            self.lbl_status.configure(text="✅ Archivo listo para importar", text_color=Theme.ACCENT_GREEN)

        except Exception as e:
            ctk.CTkLabel(self.preview_scroll, text=f"Error al leer archivo: {str(e)}", text_color=Theme.ACCENT_ROSE).pack(pady=20)
            self.btn_import.configure(state="disabled")

    def _handle_import(self):
        if not self.selected_file_path:
            return

        self.btn_import.configure(state="disabled", text="⏳ Importando...")
        self.lbl_status.configure(text="⏳ Procesando e insertando registros...", text_color=Theme.ACCENT_BLUE)
        self.update_idletasks()

        res = self.db.import_csv_data(self.selected_file_path)

        if res.get("success"):
            imp = res.get("imported", 0)
            skp = res.get("skipped", 0)
            msg = f"¡Importación exitosa!\n\nSe insertaron {imp} registros a SQLite ({skp} omitidos)."
            messagebox.showinfo("Importación Completada", msg)
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            err = res.get("error", "Error desconocido al importar.")
            self.lbl_status.configure(text=f"⚠️ {err}", text_color=Theme.ACCENT_ROSE)
            self.btn_import.configure(state="normal", text="🚀 Reintentar Importación")
