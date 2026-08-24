"""
Mixin para Importación y Descarga de Plantillas CSV.
"""

import csv
import os
from datetime import datetime
from typing import Dict, Any, Optional


class CSVMixin:
    def generate_csv_template(self, save_path: Optional[str] = None) -> str:
        """
        Genera la plantilla CSV estándar con encabezados y filas de ejemplo.
        Si se especifica save_path, escribe el archivo en disco. Retorna el contenido en texto.
        """
        template_content = (
            "tipo,fecha,concepto,monto,moneda,metodo_pago,es_fijo,notas\n"
            "INGRESO_USD,2026-08-01,Clientes Internacionales,1500.00,USD,,,Honorarios proyecto\n"
            "GASTO_USD,2026-08-02,Software / IA,20.00,USD,,,Suscripción ChatGPT Plus\n"
            "INGRESO_COP,2026-08-05,Clientes Locales,3500000,COP,,,Consultoría\n"
            "GASTO_COP,2026-08-10,Arriendo / Hipoteca,1500000,COP,DEBIT,1,Pago arriendo mensual\n"
            "GASTO_COP,2026-08-12,Alimentación / Mercado,250000,COP,CREDIT_CARD,0,Mercado semanal\n"
            "CONVERSION,2026-08-15,Retiro USD a Cuenta Bancaria,500.00,USD,,,3100\n"
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8-sig") as f:
                f.write(template_content)
        return template_content

    def import_csv_data(self, file_path: str) -> Dict[str, Any]:
        """
        Importa movimientos masivos desde un archivo CSV delimitado por comas o punto y coma.
        Procesa de forma inteligente ingresos, egresos, conversiones y gastos con TC.
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": f"El archivo no existe: {file_path}", "imported": 0, "skipped": 0}

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

                for row_idx, raw_row in enumerate(rows, start=2):
                    row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k and v is not None}

                    tx_type = (row.get("tipo") or row.get("type") or row.get("modulo") or "").upper()
                    date_val = row.get("fecha") or row.get("date") or datetime.now().strftime("%Y-%m-%d")
                    concept = row.get("concepto") or row.get("categoria") or row.get("description") or row.get("concept") or "Movimiento Importado"
                    amount_str = row.get("monto") or row.get("amount") or row.get("valor") or "0"
                    currency = (row.get("moneda") or row.get("currency") or "COP").upper()
                    pm = (row.get("metodo_pago") or row.get("payment_method") or "DEBIT").upper()
                    fixed_str = (row.get("es_fijo") or row.get("is_fixed") or "0").lower()
                    notes = row.get("notas") or row.get("notes") or row.get("detalle") or "Importado desde CSV"

                    try:
                        cleaned_amt = amount_str.replace("$", "").replace(" ", "")
                        if "," in cleaned_amt and "." in cleaned_amt:
                            cleaned_amt = cleaned_amt.replace(".", "").replace(",", ".")
                        elif "," in cleaned_amt:
                            cleaned_amt = cleaned_amt.replace(",", ".")
                        amount = float(cleaned_amt)
                        if amount <= 0:
                            skipped_count += 1
                            continue
                    except ValueError:
                        skipped_count += 1
                        errors.append(f"Fila {row_idx}: monto inválido '{amount_str}'")
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
                                if notes and any(c.isdigit() for c in notes):
                                    rate_digits = "".join([c for c in notes if c.isdigit() or c in ".,"])
                                    if rate_digits:
                                        rate = float(rate_digits.replace(",", "."))
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
