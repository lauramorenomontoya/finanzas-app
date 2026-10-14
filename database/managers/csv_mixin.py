"""
Mixin para Importación y Descarga de Plantillas CSV y Datos de Notion.
"""

import csv
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional

from services.notion_importer import NotionImporter


class CSVMixin:
    def generate_csv_template(self, save_path: Optional[str] = None) -> str:
        """
        Genera la plantilla CSV estándar con encabezados y filas de ejemplo.
        Si se especifica save_path, escribe el archivo en disco. Retorna el contenido en texto.
        """
        template_content = (
            "tipo,fecha,concepto,monto,moneda,metodo_pago,es_fijo,notas\n"
            "INGRESO_USD,01/08/2026,Clientes Internacionales,1500.00,USD,,,Honorarios proyecto\n"
            "GASTO_USD,02/08/2026,Software / IA,20.00,USD,,,Suscripción ChatGPT Plus\n"
            "INGRESO_COP,05/08/2026,Clientes Locales,3500000,COP,,,Consultoría\n"
            "GASTO_COP,10/08/2026,Arriendo / Hipoteca,1500000,COP,DEBIT,1,Pago arriendo mensual\n"
            "GASTO_COP,12/08/2026,Alimentación / Mercado,250000,COP,CREDIT_CARD,0,Mercado semanal\n"
            "CONVERSION,15/08/2026,Retiro USD a Cuenta Bancaria,500.00,USD,,,3100\n"
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8-sig") as f:
                f.write(template_content)
        return template_content

    def detect_import_format(self, path: str) -> str:
        """Detecta si la ruta seleccionada es una carpeta de Notion, un CSV de Notion o plantilla estándar."""
        return NotionImporter.detect_file_type(path)

    def preview_import_data(self, path: str) -> Dict[str, Any]:
        """Obtiene vista previa y estadísticas de cualquier archivo o carpeta antes de importar."""
        f_type = self.detect_import_format(path)
        if f_type.startswith("NOTION_") or f_type == "NOTION_FOLDER":
            return NotionImporter.preview_import(path)

        # Si es CSV Estándar
        if not os.path.exists(path):
            return {"success": False, "error": f"El archivo no existe: {path}"}

        try:
            with open(path, mode="r", encoding="utf-8-sig") as f:
                sample = f.read(2048)
                f.seek(0)
                delimiter = ";" if ";" in sample and sample.count(";") > sample.count(",") else ","
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)

            sample_rows = []
            for r in rows[:8]:
                raw_d = r.get("fecha") or r.get("date")
                parsed_d = NotionImporter.parse_spanish_date(raw_d)
                sample_rows.append({
                    "tipo": (r.get("tipo") or r.get("type") or "GASTO_COP").upper(),
                    "fecha": NotionImporter.format_display_date(parsed_d) if parsed_d else (raw_d or "N/A"),
                    "concepto": r.get("concepto") or r.get("categoria") or "Movimiento",
                    "categoria": r.get("categoria") or r.get("concepto") or "General",
                    "monto": NotionImporter.parse_currency_amount(r.get("monto") or r.get("amount")),
                    "es_fijo": 1 if str(r.get("es_fijo", "")).lower() in ("1", "true", "si") else 0
                })

            return {
                "success": True,
                "is_folder": False,
                "file_type": "STANDARD_CSV",
                "total_rows": len(rows),
                "sample_rows": sample_rows
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_notion_data(self, target_path: str) -> Dict[str, Any]:
        """Importa datos desde una carpeta completa o archivo individual exportado de Notion."""
        return NotionImporter.execute_import(self, target_path)

    def import_csv_data(self, file_path: str) -> Dict[str, Any]:
        """
        Importa movimientos masivos desde un archivo CSV o carpeta.
        Auto-detecta si se trata de una exportación de Notion o la plantilla estándar.
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": f"El archivo no existe: {file_path}", "imported": 0, "skipped": 0}

        # Auto-detectar formato
        f_type = NotionImporter.detect_file_type(file_path)
        if f_type.startswith("NOTION_") or f_type == "NOTION_FOLDER":
            res = NotionImporter.execute_import(self, file_path)
            # Adaptar respuesta para compatibilidad
            res["imported"] = res.get("imported_total", 0)
            return res

        imported_count = 0
        skipped_count = 0
        errors = []

        try:
            with open(file_path, mode="r", encoding="utf-8-sig") as f:
                sample = f.read(2048)
                f.seek(0)
                delimiter = ";" if ";" in sample and sample.count(";") > sample.count(",") else ","
                reader = csv.DictReader(f, delimiter=delimiter)

                rows = list(reader)
                if not rows:
                    return {"success": False, "error": "El archivo CSV está vacío.", "imported": 0, "skipped": 0}

                # Crear respaldo preventivo
                self.create_backup()

                # Batching seguro con Write Lock para prevenir contención de bloqueos WAL
                with self._write_lock:
                    for row_idx, raw_row in enumerate(rows, start=2):
                        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k and v is not None}

                        tx_type = (row.get("tipo") or row.get("type") or row.get("modulo") or "").upper()
                        raw_date = row.get("fecha") or row.get("date")
                        parsed_d = NotionImporter.parse_spanish_date(raw_date)
                        date_val = parsed_d if parsed_d else (raw_date or datetime.now().strftime("%Y-%m-%d"))

                        concept = row.get("concepto") or row.get("categoria") or row.get("description") or row.get("concept") or "Movimiento Importado"
                        amount_str = row.get("monto") or row.get("amount") or row.get("valor") or "0"
                        currency = (row.get("moneda") or row.get("currency") or "COP").upper()
                        pm = (row.get("metodo_pago") or row.get("payment_method") or "DEBIT").upper()
                        fixed_str = (row.get("es_fijo") or row.get("is_fixed") or "0").lower()
                        notes = row.get("notas") or row.get("notes") or row.get("detalle") or "Importado desde CSV"

                        amount = NotionImporter.parse_currency_amount(amount_str)
                        if amount <= 0:
                            skipped_count += 1
                            continue

                        pm_code = "DEBIT"
                        if "TC" in pm or "CREDIT" in pm or "TARJETA" in pm:
                            pm_code = "CREDIT_CARD"
                        elif "CASH" in pm or "EFECTIVO" in pm:
                            pm_code = "CASH"

                        is_fixed = fixed_str in ("1", "true", "si", "sí", "yes", "fijo")

                        try:
                            if "CONVERSION" in tx_type:
                                rate = 3100.0
                                try:
                                    if notes:
                                        m_rate = re.search(r"(\d{3,5}(?:[.,]\d+)?)", notes)
                                        if m_rate:
                                            rate = float(m_rate.group(1).replace(",", "."))
                                except Exception:
                                    rate = 3100.0
                                self.execute_conversion(date_val, amount, rate, notes=notes)
                                imported_count += 1

                            elif "USD" in tx_type or currency == "USD":
                                if "GASTO" in tx_type or "EGRESO" in tx_type or "EXPENSE" in tx_type:
                                    self.add_usd_expense(date_val, concept, amount, notes=notes)
                                else:
                                    self.add_usd_deposit(date_val, concept, amount, notes=notes)
                                imported_count += 1

                            else:
                                if "GASTO" in tx_type or "EGRESO" in tx_type or "EXPENSE" in tx_type:
                                    self.add_cop_expense(date_val, concept, amount, is_fixed=is_fixed, payment_method=pm_code, notes=notes)
                                else:
                                    self.add_cop_income(date_val, concept, amount, notes=notes)
                                imported_count += 1

                        except Exception as row_err:
                            skipped_count += 1
                            errors.append(f"Fila {row_idx}: {str(row_err)}")

            return {
                "success": imported_count > 0 or skipped_count == 0,
                "imported": imported_count,
                "skipped": skipped_count,
                "errors": errors
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error general al procesar el archivo CSV: {str(e)}",
                "imported": imported_count,
                "skipped": skipped_count,
                "errors": errors
            }

