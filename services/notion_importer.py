"""
Servicio Especializado para Importación y Normalización de Datos de Notion.
Soporta archivos individuales y carpetas completas exportadas de Notion (Gastos Diarios,
Ingresos, Fiducuenta, Gastos Fijos de Hogar/Moto), con parser inteligente de fechas (día/mes/año),
montos en COP y aprovisionamiento automático de categorías.
"""

import os
import csv
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from services.category_service import CategoryService


class NotionImporter:
    # Mapeo de meses en español a número de mes
    MONTHS_ES = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }

    # Presets recomendados de iconos y colores canónicos
    CATEGORY_PRESETS = {
        c[0].lower(): (c[2], c[3], c[1]) for c in CategoryService.CANONICAL_CATEGORIES
    }


    @classmethod
    def parse_spanish_date(cls, date_str: Optional[str], fallback_month_str: Optional[str] = None) -> Optional[str]:
        """
        Normaliza fechas en formato día/mes/año a formato ISO 'YYYY-MM-DD'.
        Soporta:
          - '14 de agosto de 2026' -> '2026-08-14'
          - '14/08/2026' o '14-08-2026' -> '2026-08-14'
          - '2026-08-14' -> '2026-08-14'
          - Fallback de columna 'Mes' (ej. 'Agosto 2026' -> '2026-08-01')
        """
        if date_str:
            d_clean = str(date_str).strip().lower()

            # 1. Formato 'DD de [mes] de YYYY' (ej. '14 de agosto de 2026' o '1 de diciembre de 2025')
            m_text = re.search(r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})", d_clean)
            if m_text:
                day = int(m_text.group(1))
                m_name = m_text.group(2)
                year = int(m_text.group(3))
                month = cls.MONTHS_ES.get(m_name)
                if month and 1 <= day <= 31:
                    return f"{year:04d}-{month:02d}-{day:02d}"

            # 2. Formato día/mes/año 'DD/MM/YYYY' o 'DD-MM-YYYY'
            m_dmy = re.search(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$", d_clean)
            if m_dmy:
                day = int(m_dmy.group(1))
                month = int(m_dmy.group(2))
                year = int(m_dmy.group(3))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return f"{year:04d}-{month:02d}-{day:02d}"

            # 3. Formato ISO 'YYYY-MM-DD'
            m_iso = re.search(r"^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})$", d_clean)
            if m_iso:
                year = int(m_iso.group(1))
                month = int(m_iso.group(2))
                day = int(m_iso.group(3))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return f"{year:04d}-{month:02d}-{day:02d}"

        # 4. Fallback: extraer mes y año del campo 'Mes' (ej. 'Agosto 2026' o 'Enero 2026')
        if fallback_month_str:
            f_clean = str(fallback_month_str).strip().lower()
            for m_name, m_num in cls.MONTHS_ES.items():
                if m_name in f_clean:
                    y_match = re.search(r"\b(\d{4})\b", f_clean)
                    year = int(y_match.group(1)) if y_match else datetime.now().year
                    return f"{year:04d}-{m_num:02d}-01"

        return None

    @classmethod
    def format_display_date(cls, iso_date: str) -> str:
        """Convierte una fecha 'YYYY-MM-DD' a formato legible día/mes/año 'DD/MM/YYYY'."""
        try:
            dt = datetime.strptime(iso_date, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except Exception:
            return iso_date

    @classmethod
    def parse_currency_amount(cls, val_str: Any) -> float:
        """
        Limpia y convierte montos numéricos en formato COP / USD / Latino:
          - '1.240.922,00 COP' -> 1240922.0
          - '193627.33' -> 193627.33
          - '-530.000,00 COP' -> -530000.0
          - '$ 45.000' -> 45000.0
        """
        if val_str is None:
            return 0.0
        s = str(val_str).replace("COP", "").replace("USD", "").replace("$", "").replace("\xa0", "").replace(" ", "").strip()
        if not s:
            return 0.0

        is_negative = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
        s = s.replace("-", "").replace("(", "").replace(")", "").strip()

        if "," in s and "." in s:
            # Notación latina: 1.240.922,00
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            # Solo coma: 71445,00
            s = s.replace(",", ".")
        elif "." in s:
            parts = s.split(".")
            if len(parts) > 2:
                # Múltiples puntos de miles: 1.500.000
                s = "".join(parts)
            elif len(parts) == 2 and len(parts[1]) == 3 and not any(c.isalpha() for c in parts[1]):
                # Punto de miles en COP: 45.000
                s = "".join(parts)

        try:
            amt = float(s)
            return -amt if is_negative else amt
        except Exception:
            return 0.0

    @classmethod
    def extract_relation_name(cls, raw_relation: Any, default: str = "Otros") -> str:
        """
        Limpia enlaces y relaciones Markdown de Notion:
          - 'Cuidado (2026/Categorías/Cuidado 2bcacd5f...).md' -> 'Cuidado'
          - 'Nómina (https://app.notion.com/...)' -> 'Nómina'
        """
        if not raw_relation:
            return default
        s = str(raw_relation).strip()
        # Regex para remover enlaces entre paréntesis '( ... )'
        m = re.match(r"^(.*?)\s*\(.*?\)$", s)
        clean = m.group(1).strip() if m else s
        # Remover sufijos .md si quedaron
        clean = re.sub(r"\.md$", "", clean, flags=re.IGNORECASE).strip()
        return clean if clean else default

    @classmethod
    def detect_file_type(cls, file_path: str) -> str:
        """Detecta el tipo de archivo o exportación de Notion analizando encabezados y nombre de archivo."""
        if not os.path.exists(file_path):
            return "UNKNOWN"

        if os.path.isdir(file_path):
            return "NOTION_FOLDER"

        filename = os.path.basename(file_path).lower()

        # Detección por nombre de archivo prioritario
        if ("ingreso" in filename or "➕ingresos" in filename) and "anual" not in filename and "categori" not in filename:
            return "NOTION_INGRESOS"
        if ("gastos diarios" in filename or "➖gastos diarios" in filename or "gasto" in filename) and "anual" not in filename and "categori" not in filename and "hogar" not in filename and "moto" not in filename:
            return "NOTION_GASTOS"
        if "fiducuenta" in filename:
            return "NOTION_FIDUCUENTA"
        if "hogar" in filename:
            return "NOTION_GASTOS_HOGAR"
        if "moto" in filename:
            return "NOTION_GASTOS_MOTO"
        if "transferencia" in filename:
            return "NOTION_TRANSFERENCIAS"

        try:
            with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                sample = f.read(2048)
                f.seek(0)
                delimiter = ";" if ";" in sample and sample.count(";") > sample.count(",") else ","
                reader = csv.reader(f, delimiter=delimiter)
                headers = [h.strip().lower() for h in next(reader, [])]

            # 1. Plantilla Estándar App
            if "tipo" in headers and "monto" in headers:
                return "STANDARD_CSV"

            # 2. Gastos Diarios Notion
            if any("fecha gasto" in h for h in headers) or (any("gasto" in h for h in headers) and any("categorías" in h for h in headers)):
                return "NOTION_GASTOS"

            # 3. Ingresos Notion
            if any("categorías de ingreso" in h for h in headers) or (any("ingreso" in h for h in headers) and any("cantidad" in h for h in headers)):
                return "NOTION_INGRESOS"

            # 4. Fiducuenta Notion
            if "rendimientos" in headers or ("ahorro" in headers and "saldo total" in headers):
                return "NOTION_FIDUCUENTA"

            # 5. Gastos Hogar / Gastos Fijos
            if "etiquetas" in headers and "número" in headers:
                return "NOTION_GASTOS_HOGAR"

            # 6. Gastos Moto
            if "año" in headers or ("date" in headers and "number" in headers):
                return "NOTION_GASTOS_MOTO"

            # 7. Si contiene columnas genéricas de Notion
            if "concepto" in headers or "nombre" in headers:
                return "NOTION_GENERIC"

            return "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    @classmethod
    def find_all_notion_files(cls, base_dir: str) -> Dict[str, str]:
        """
        Escanea recursivamente una carpeta en busca de los archivos CSV clave de Notion.
        Prioriza los archivos '_all.csv' cuando existan.
        """
        found_files = {}
        for root, _, files in os.walk(base_dir):
            for f in files:
                if not f.endswith(".csv"):
                    continue
                full_path = os.path.join(root, f)
                f_type = cls.detect_file_type(full_path)

                if f_type in ("NOTION_GASTOS", "NOTION_INGRESOS", "NOTION_FIDUCUENTA", "NOTION_GASTOS_HOGAR", "NOTION_GASTOS_MOTO", "NOTION_TRANSFERENCIAS"):
                    # Si ya teníamos uno, preferir el que termine en _all.csv
                    if f_type in found_files:
                        if "_all.csv" in f:
                            found_files[f_type] = full_path
                    else:
                        found_files[f_type] = full_path

        return found_files

    @classmethod
    def parse_fiducuenta_snapshots(cls, fidu_path: str) -> List[Dict[str, Any]]:
        """
        Procesa el archivo histórico de Fiducuenta interpretando cada fila como un snapshot de balance
        y calculando los deltas reales de capital (DEPOSIT/WITHDRAWAL) y rendimientos (YIELD) del periodo.
        """
        if not fidu_path or not os.path.exists(fidu_path):
            return []

        with open(fidu_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            raw_rows = list(reader)

        parsed = []
        for r in raw_rows:
            name = r.get("Name", "").strip()
            d = cls.parse_spanish_date(r.get("Fecha"))
            ahorro = cls.parse_currency_amount(r.get("Ahorro"))
            rend = cls.parse_currency_amount(r.get("Rendimientos"))
            saldo = cls.parse_currency_amount(r.get("Saldo Total"))
            if d and (ahorro > 0 or rend != 0 or saldo > 0):
                parsed.append({"name": name, "date": d, "ahorro": ahorro, "rend": rend, "saldo": saldo})

        parsed.sort(key=lambda x: x["date"])

        unique = []
        for p in parsed:
            if unique and unique[-1]["date"] == p["date"] and unique[-1]["saldo"] == p["saldo"]:
                continue
            unique.append(p)

        transactions = []
        prev_ahorro = 0.0
        max_rend_previo = 0.0

        for idx, p in enumerate(unique):
            d = p["date"]
            a = p["ahorro"]
            r = p["rend"]
            name = p["name"]

            if idx == 0:
                if a > 0:
                    transactions.append({"date": d, "type": "DEPOSIT", "amount": a, "notes": f"Aporte inicial Fiducuenta ({name})"})
                if r > 0:
                    transactions.append({"date": d, "type": "YIELD", "amount": r, "notes": f"Rendimiento inicial Fiducuenta ({name})"})
                    max_rend_previo = r
                prev_ahorro = a
            else:
                d_ahorro = a - prev_ahorro
                if d_ahorro > 0:
                    transactions.append({"date": d, "type": "DEPOSIT", "amount": d_ahorro, "notes": f"Aporte Fiducuenta ({name})"})
                elif d_ahorro < 0:
                    transactions.append({"date": d, "type": "WITHDRAWAL", "amount": abs(d_ahorro), "notes": f"Retiro Fiducuenta ({name})"})

                if r > 0:
                    if max_rend_previo > 0:
                        d_rend = r - max_rend_previo
                        if d_rend > 0:
                            transactions.append({"date": d, "type": "YIELD", "amount": d_rend, "notes": f"Rendimiento Fiducuenta ({name})"})
                    else:
                        transactions.append({"date": d, "type": "YIELD", "amount": r, "notes": f"Rendimiento Fiducuenta ({name})"})

                    if r > max_rend_previo:
                        max_rend_previo = r

                prev_ahorro = a

        return transactions

    @classmethod
    def preview_import(cls, target_path: str) -> Dict[str, Any]:
        """
        Genera una vista previa detallada y estadísticas de los datos a importar sin modificar la base de datos.
        """
        if not os.path.exists(target_path):
            return {"success": False, "error": f"La ruta no existe: {target_path}"}

        is_folder = os.path.isdir(target_path)
        files_to_process = cls.find_all_notion_files(target_path) if is_folder else {cls.detect_file_type(target_path): target_path}

        summary = {
            "success": True,
            "is_folder": is_folder,
            "total_expenses_count": 0,
            "total_expenses_amount": 0.0,
            "total_incomes_count": 0,
            "total_incomes_amount": 0.0,
            "total_investment_tx_count": 0,
            "total_recurring_count": 0,
            "categories_detected": set(),
            "date_min": None,
            "date_max": None,
            "sample_rows": [],
            "files_found": list(files_to_process.keys())
        }

        dates_found = []

        # Procesar Gastos
        gastos_path = files_to_process.get("NOTION_GASTOS")
        if gastos_path and os.path.exists(gastos_path):
            with open(gastos_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    concept = r.get("Concepto", "").strip()
                    amt = cls.parse_currency_amount(r.get("Gasto") or r.get("Amount") or r.get("Valor"))
                    cat_raw = cls.extract_relation_name(r.get("Categorías") or r.get("Categoria"))
                    cat = CategoryService.normalize_category_name(cat_raw, "EXPENSE_COP")
                    d = cls.parse_spanish_date(r.get("Fecha Gasto") or r.get("Fecha") or r.get("Date"), r.get("Mes"))
                    desc = r.get("Descripción", "").strip()

                    if amt > 0:
                        summary["total_expenses_count"] += 1
                        summary["total_expenses_amount"] += amt
                        summary["categories_detected"].add(cat)
                        if d:
                            dates_found.append(d)
                        if len(summary["sample_rows"]) < 6:
                            summary["sample_rows"].append({
                                "tipo": "GASTO_COP",
                                "fecha": cls.format_display_date(d) if d else "N/A",
                                "concepto": concept,
                                "categoria": cat,
                                "monto": amt,
                                "es_fijo": 1 if "FIJO" in desc.upper() else 0
                            })

        # Procesar Ingresos
        ingresos_path = files_to_process.get("NOTION_INGRESOS")
        if ingresos_path and os.path.exists(ingresos_path):
            with open(ingresos_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    concept = r.get("Concepto", "").strip()
                    amt = cls.parse_currency_amount(r.get("Cantidad") or r.get("Monto") or r.get("Amount"))
                    cat_raw = cls.extract_relation_name(r.get("Categorías de Ingreso") or r.get("Categoria"))
                    cat = CategoryService.normalize_category_name(cat_raw, "INCOME_COP")
                    d = cls.parse_spanish_date(r.get("Fecha") or r.get("Date"), r.get("Mes"))

                    if amt > 0:
                        summary["total_incomes_count"] += 1
                        summary["total_incomes_amount"] += amt
                        summary["categories_detected"].add(cat)
                        if d:
                            dates_found.append(d)
                        if len(summary["sample_rows"]) < 10:
                            summary["sample_rows"].append({
                                "tipo": "INGRESO_COP",
                                "fecha": cls.format_display_date(d) if d else "N/A",
                                "concepto": concept,
                                "categoria": cat,
                                "monto": amt,
                                "es_fijo": 0
                            })

        # Procesar Fiducuenta
        fidu_path = files_to_process.get("NOTION_FIDUCUENTA")
        if fidu_path and os.path.exists(fidu_path):
            fidu_txs = cls.parse_fiducuenta_snapshots(fidu_path)
            summary["total_investment_tx_count"] = len(fidu_txs)
            for t in fidu_txs:
                dates_found.append(t["date"])
                if len(summary["sample_rows"]) < 12 and t["type"] == "YIELD":
                    summary["sample_rows"].append({
                        "tipo": "RENDIMIENTO",
                        "fecha": cls.format_display_date(t["date"]),
                        "concepto": t["notes"],
                        "categoria": "Fiducuenta Bancolombia",
                        "monto": t["amount"],
                        "es_fijo": 0
                    })

        # Procesar Gastos Fijos Hogar
        hogar_path = files_to_process.get("NOTION_GASTOS_HOGAR")
        if hogar_path and os.path.exists(hogar_path):
            with open(hogar_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    amt = cls.parse_currency_amount(r.get("Número") or r.get("Numero"))
                    if amt > 0:
                        summary["total_recurring_count"] += 1

        if dates_found:
            dates_found.sort()
            summary["date_min"] = cls.format_display_date(dates_found[0])
            summary["date_max"] = cls.format_display_date(dates_found[-1])

        summary["categories_detected"] = sorted(list(summary["categories_detected"]))
        return summary

    @classmethod
    def execute_import(cls, db_manager, target_path: str) -> Dict[str, Any]:
        """
        Ejecuta la importación completa de los datos de Notion en SQLite dentro de una transacción segura.
        Crea respaldo automático previo, aprovisiona categorías faltantes y evita duplicados.
        """
        if not os.path.exists(target_path):
            return {"success": False, "error": f"La ruta no existe: {target_path}", "imported": 0, "skipped": 0}

        # 1. Crear respaldo preventivo de la base de datos
        backup_file = db_manager.create_backup()

        is_folder = os.path.isdir(target_path)
        files_to_process = cls.find_all_notion_files(target_path) if is_folder else {cls.detect_file_type(target_path): target_path}

        imported_expenses = 0
        imported_incomes = 0
        imported_investments = 0
        imported_recurring = 0
        skipped_count = 0
        errors = []

        try:
            # 2. Cargar categorías existentes para comparar
            existing_cats = {c["name"].lower(): c for c in db_manager.get_categories()}

            # 3. Procesar e insertar en SQLite con Write Lock
            with db_manager._write_lock:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()

                    # Función helper para asegurar que la categoría exista
                    def ensure_category(cat_name: str, cat_type: str = "EXPENSE_COP"):
                        normalized_name = CategoryService.normalize_category_name(cat_name, cat_type)
                        cat_key = normalized_name.strip().lower()
                        if cat_key in existing_cats:
                            return existing_cats[cat_key]["name"]

                        preset = cls.CATEGORY_PRESETS.get(cat_key, ("🏷️", "#38bdf8", cat_type))
                        icon, color, t = preset
                        cursor.execute("""
                            INSERT OR IGNORE INTO categories (name, type, icon, color, is_system)
                            VALUES (?, ?, ?, ?, 0);
                        """, (normalized_name.strip(), t, icon, color))
                        existing_cats[cat_key] = {"name": normalized_name.strip(), "type": t}
                        return normalized_name.strip()

                    # ----------------------------------------------------
                    # A. IMPORTAR GASTOS DIARIOS
                    # ----------------------------------------------------
                    gastos_path = files_to_process.get("NOTION_GASTOS")
                    if gastos_path and os.path.exists(gastos_path):
                        with open(gastos_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                            reader = csv.DictReader(f)
                            for row_idx, r in enumerate(reader, start=2):
                                try:
                                    concept = r.get("Concepto", "").strip() or "Gasto Importado"
                                    amt = cls.parse_currency_amount(r.get("Gasto") or r.get("Amount") or r.get("Valor"))
                                    raw_cat = r.get("Categorías") or r.get("Categoria")
                                    cat = cls.extract_relation_name(raw_cat, default="Otros Gastos")
                                    d = cls.parse_spanish_date(r.get("Fecha Gasto") or r.get("Fecha") or r.get("Date"), r.get("Mes"))
                                    desc = r.get("Descripción", "").strip()
                                    chk = r.get("Checkbox", "").strip()

                                    if amt <= 0:
                                        skipped_count += 1
                                        continue

                                    date_val = d if d else datetime.now().strftime("%Y-%m-%d")
                                    is_fixed = 1 if "FIJO" in desc.upper() else 0
                                    cat_name = ensure_category(cat, "EXPENSE_COP")

                                    # Armar nota descriptiva
                                    notes_parts = []
                                    if desc and "FIJO" not in desc.upper():
                                        notes_parts.append(desc)
                                    if chk and chk.lower() != "pagado":
                                        notes_parts.append(f"Estado: {chk}")
                                    notes_str = " | ".join(notes_parts) if notes_parts else f"Importado Notion ({concept})"

                                    # Chequeo de duplicados
                                    cursor.execute("""
                                        SELECT id FROM cop_transactions
                                        WHERE date = ? AND category = ? AND type = 'EXPENSE' AND ABS(amount - ?) < 0.01 AND notes = ?;
                                    """, (date_val, cat_name, amt, notes_str))
                                    if cursor.fetchone():
                                        skipped_count += 1
                                        continue

                                    cursor.execute("""
                                        INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                                        VALUES (?, ?, 'EXPENSE', ?, ?, 'DEBIT', ?);
                                    """, (date_val, cat_name, amt, is_fixed, notes_str))
                                    imported_expenses += 1

                                except Exception as e_row:
                                    skipped_count += 1
                                    errors.append(f"Gastos Fila {row_idx}: {str(e_row)}")

                    # ----------------------------------------------------
                    # B. IMPORTAR INGRESOS
                    # ----------------------------------------------------
                    ingresos_path = files_to_process.get("NOTION_INGRESOS")
                    if ingresos_path and os.path.exists(ingresos_path):
                        with open(ingresos_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                            reader = csv.DictReader(f)
                            for row_idx, r in enumerate(reader, start=2):
                                try:
                                    concept = r.get("Concepto", "").strip() or "Ingreso Importado"
                                    amt = cls.parse_currency_amount(r.get("Cantidad") or r.get("Monto") or r.get("Amount"))
                                    raw_cat = r.get("Categorías de Ingreso") or r.get("Categoria")
                                    cat = cls.extract_relation_name(raw_cat, default="Otros Ingresos COP")
                                    d = cls.parse_spanish_date(r.get("Fecha") or r.get("Date"), r.get("Mes"))

                                    if amt <= 0:
                                        skipped_count += 1
                                        continue

                                    date_val = d if d else datetime.now().strftime("%Y-%m-%d")
                                    cat_name = ensure_category(cat, "INCOME_COP")
                                    notes_str = f"Importado Notion ({concept})"

                                    # Chequeo de duplicados
                                    cursor.execute("""
                                        SELECT id FROM cop_transactions
                                        WHERE date = ? AND category = ? AND type = 'MANUAL_INCOME' AND ABS(amount - ?) < 0.01;
                                    """, (date_val, cat_name, amt))
                                    if cursor.fetchone():
                                        skipped_count += 1
                                        continue

                                    cursor.execute("""
                                        INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                                        VALUES (?, ?, 'MANUAL_INCOME', ?, 0, 'DEBIT', ?);
                                    """, (date_val, cat_name, amt, notes_str))
                                    imported_incomes += 1

                                except Exception as e_row:
                                    skipped_count += 1
                                    errors.append(f"Ingresos Fila {row_idx}: {str(e_row)}")

                    # ----------------------------------------------------
                    # C. IMPORTAR FIDUCUENTA (CUENTA DE INVERSIÓN CON DELTAS)
                    # ----------------------------------------------------
                    fidu_path = files_to_process.get("NOTION_FIDUCUENTA")
                    if fidu_path and os.path.exists(fidu_path):
                        cursor.execute("SELECT id FROM accounts WHERE name LIKE '%Fiducuenta%' OR currency = 'COP' LIMIT 1;")
                        acc_row = cursor.fetchone()
                        acc_id = acc_row["id"] if acc_row else 1

                        fidu_txs = cls.parse_fiducuenta_snapshots(fidu_path)
                        for t in fidu_txs:
                            try:
                                cursor.execute("""
                                    SELECT id FROM account_transactions
                                    WHERE account_id = ? AND date = ? AND type = ? AND ABS(amount - ?) < 0.01;
                                """, (acc_id, t["date"], t["type"], t["amount"]))
                                if not cursor.fetchone():
                                    cursor.execute("""
                                        INSERT INTO account_transactions (account_id, date, type, amount, notes)
                                        VALUES (?, ?, ?, ?, ?);
                                    """, (acc_id, t["date"], t["type"], t["amount"], t["notes"]))
                                    imported_investments += 1
                                else:
                                    skipped_count += 1
                            except Exception as e_tx:
                                errors.append(f"Fiducuenta Tx {t['date']}: {str(e_tx)}")

                    # ----------------------------------------------------
                    # D. IMPORTAR PLANTILLA GASTOS FIJOS (HOGAR)
                    # ----------------------------------------------------
                    hogar_path = files_to_process.get("NOTION_GASTOS_HOGAR")
                    if hogar_path and os.path.exists(hogar_path):
                        with open(hogar_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                            reader = csv.DictReader(f)
                            for r in reader:
                                nombre = r.get("Nombre", "").strip()
                                amt = cls.parse_currency_amount(r.get("Número") or r.get("Numero"))
                                if amt > 0 and nombre:
                                    cat_name = ensure_category("Hogar", "EXPENSE_COP")
                                    cursor.execute("""
                                        SELECT id FROM recurring_expenses
                                        WHERE description = ? AND currency = 'COP';
                                    """, (nombre,))
                                    if not cursor.fetchone():
                                        cursor.execute("""
                                            INSERT INTO recurring_expenses (category, description, amount, currency, due_day, is_active)
                                            VALUES (?, ?, ?, 'COP', 1, 1);
                                        """, (cat_name, nombre, amt))
                                        imported_recurring += 1

                    conn.commit()

            total_imported = imported_expenses + imported_incomes + imported_investments + imported_recurring

            return {
                "success": total_imported > 0 or skipped_count == 0,
                "imported_total": total_imported,
                "imported_expenses": imported_expenses,
                "imported_incomes": imported_incomes,
                "imported_investments": imported_investments,
                "imported_recurring": imported_recurring,
                "skipped": skipped_count,
                "backup_file": backup_file,
                "errors": errors
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error crítico durante la importación: {str(e)}",
                "imported_total": 0,
                "skipped": skipped_count,
                "backup_file": backup_file,
                "errors": errors
            }
