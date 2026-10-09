#!/usr/bin/env python3
"""
Servidor MCP (Model Context Protocol) para Montu.
Permite a modelos de inteligencia artificial interactuar con la base de datos
financiera personal: consultar balances, registrar ingresos/gastos y realizar análisis.
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Asegurar importación de módulos locales
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIRS = [
    CURRENT_DIR,
    os.path.expanduser("~/Desktop/Scripts/ControlFinanciero"),
    os.path.expanduser("~/Desktop/Scripts/Montu"),
]
for d in BASE_DIRS:
    if os.path.exists(d) and d not in sys.path:
        sys.path.insert(0, d)

from database.db_manager import DatabaseManager
from mcp.server.mcpserver import MCPServer

# Resolver ruta de la base de datos preferida (Montu con fallback seguro a ControlFinanciero o local)
if sys.platform == "darwin":
    NEW_PROD_DB = os.path.expanduser("~/Library/Application Support/Montu/finanzas.db")
    OLD_PROD_DB = os.path.expanduser("~/Library/Application Support/ControlFinanciero/finanzas.db")
elif sys.platform == "win32":
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    NEW_PROD_DB = os.path.join(appdata, "Montu", "finanzas.db")
    OLD_PROD_DB = os.path.join(appdata, "ControlFinanciero", "finanzas.db")
else:
    NEW_PROD_DB = os.path.expanduser("~/.local/share/Montu/finanzas.db")
    OLD_PROD_DB = os.path.expanduser("~/.local/share/ControlFinanciero/finanzas.db")

if os.path.exists(NEW_PROD_DB):
    DB_PATH = NEW_PROD_DB
elif os.path.exists(OLD_PROD_DB):
    DB_PATH = OLD_PROD_DB
else:
    DB_PATH = os.path.join(CURRENT_DIR, "finanzas.db")

db = DatabaseManager(db_path=DB_PATH)
mcp = MCPServer("montu")


@mcp.tool()
def get_financial_summary() -> str:
    """
    Obtiene el estado y balance financiero consolidado actual:
    - Bóveda de dólares (USD)
    - Saldo operativo en pesos (COP)
    - Tasa de cambio oficial (TRM)
    - Resumen de ingresos y egresos del mes en curso
    - Resumen de deudas activas (tarjetas de crédito y préstamos)
    """
    try:
        usd_balance = db.get_usd_balance()
        cop_balance = db.get_cop_balance()
        
        try:
            trm = float(db.get_latest_exchange_rate())
        except Exception:
            trm = 4000.0

        current_month = datetime.now().strftime("%Y-%m")
        inc_summary = db.get_incomes_summary(current_month)
        exp_summary = db.get_expenses_summary(current_month)
        debts = db.get_debts_summary()

        summary = {
            "fecha_consulta": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "base_de_datos": DB_PATH,
            "liquidez": {
                "boveda_usd": round(usd_balance, 2),
                "saldo_operativo_cop": round(cop_balance, 2),
                "trm_actual": round(trm, 2),
                "usd_en_cop": round(usd_balance * trm, 2),
                "liquidez_total_cop": round(cop_balance + (usd_balance * trm), 2)
            },
            "mes_en_curso": current_month,
            "ingresos_mes": {
                "cop": inc_summary.get("total_cop_month", 0),
                "usd": inc_summary.get("total_usd_month", 0)
            },
            "egresos_mes": {
                "cop": exp_summary.get("total_cop_month", 0),
                "usd": exp_summary.get("total_usd_month", 0)
            },
            "deudas_activas": {
                "tarjetas_credito_cop": debts.get("total_credit_card_cop", 0),
                "prestamos_personales_cop": debts.get("total_personal_loans_cop", 0),
                "total_deuda_cop": debts.get("total_debt_cop", 0)
            }
        }
        return json.dumps(summary, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error al obtener resumen: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
def add_expense(
    amount: float,
    category: str = "Otros Gastos",
    currency: str = "COP",
    date: str = "",
    payment_method: str = "DEBIT",
    notes: str = "",
    is_fixed: bool = False
) -> str:
    """
    Registra un nuevo egreso o gasto en la base de datos financiera.
    
    Parámetros:
    - amount: Monto numérico del gasto (ej: 45000 o 12.50).
    - category: Nombre de la categoría (ej: 'Alimentación / Mercado', 'Transporte', 'Restaurantes', 'Servicios Públicos').
    - currency: 'COP' o 'USD'.
    - date: Fecha en formato YYYY-MM-DD. Si está vacío o es 'hoy', se usa la fecha actual.
    - payment_method: 'DEBIT' (Débito/Cuenta), 'CREDIT_CARD' (Tarjeta de Crédito) o 'CASH' (Efectivo).
    - notes: Descripción o detalle adicional del gasto.
    - is_fixed: True si es un gasto recurrente/fijo, False si es variable.
    """
    try:
        if amount <= 0:
            return json.dumps({"error": "El monto debe ser mayor a 0."}, ensure_ascii=False)

        clean_date = date.strip() if date and date.lower() != "hoy" else datetime.now().strftime("%Y-%m-%d")
        curr = currency.strip().upper()
        
        # Mapeo de método de pago
        pm = payment_method.strip().upper()
        if "CREDIT" in pm or "TC" in pm or "TARJETA" in pm:
            pm = "CREDIT_CARD"
        elif "CASH" in pm or "EFECTIVO" in pm:
            pm = "CASH"
        else:
            pm = "DEBIT"

        if curr == "USD":
            tx_id = db.add_usd_expense(
                date=clean_date,
                category_or_service=category.strip(),
                amount=float(amount),
                notes=notes.strip()
            )
            new_bal = db.get_usd_balance()
            return json.dumps({
                "exito": True,
                "mensaje": f"Gasto registrado exitosamente en USD (ID #{tx_id}).",
                "detalles": {
                    "id": tx_id,
                    "fecha": clean_date,
                    "monto": f"${amount:,.2f} USD",
                    "categoria": category,
                    "nuevo_saldo_usd": f"${new_bal:,.2f} USD"
                }
            }, indent=2, ensure_ascii=False)
        else:
            tx_id = db.add_cop_expense(
                date=clean_date,
                category=category.strip(),
                amount=float(amount),
                is_fixed=is_fixed,
                payment_method=pm,
                notes=notes.strip()
            )
            new_bal = db.get_cop_balance()
            return json.dumps({
                "exito": True,
                "mensaje": f"Gasto registrado exitosamente en COP (ID #{tx_id}).",
                "detalles": {
                    "id": tx_id,
                    "fecha": clean_date,
                    "monto": f"${amount:,.0f} COP",
                    "categoria": category,
                    "metodo_pago": pm,
                    "nuevo_saldo_cop": f"${new_bal:,.0f} COP"
                }
            }, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error al registrar gasto: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
def add_income(
    amount: float,
    platform_or_category: str = "Otros Ingresos",
    currency: str = "COP",
    date: str = "",
    notes: str = ""
) -> str:
    """
    Registra un nuevo ingreso o depósito.
    
    Parámetros:
    - amount: Monto recibido.
    - platform_or_category: Plataforma (ej: 'Wenia', 'ARQ', 'Deel') si es USD, o Categoría (ej: 'Salario', 'Honorarios') si es COP.
    - currency: 'COP' o 'USD'.
    - date: Fecha en formato YYYY-MM-DD (deja vacío para 'hoy').
    - notes: Notas o concepto del ingreso.
    """
    try:
        if amount <= 0:
            return json.dumps({"error": "El monto debe ser mayor a 0."}, ensure_ascii=False)

        clean_date = date.strip() if date and date.lower() != "hoy" else datetime.now().strftime("%Y-%m-%d")
        curr = currency.strip().upper()

        if curr == "USD":
            tx_id = db.add_usd_deposit(
                date=clean_date,
                platform=platform_or_category.strip(),
                amount=float(amount),
                notes=notes.strip()
            )
            new_bal = db.get_usd_balance()
            return json.dumps({
                "exito": True,
                "mensaje": f"Depósito USD registrado (ID #{tx_id}).",
                "detalles": {
                    "id": tx_id,
                    "fecha": clean_date,
                    "monto": f"${amount:,.2f} USD",
                    "plataforma": platform_or_category,
                    "nuevo_saldo_usd": f"${new_bal:,.2f} USD"
                }
            }, indent=2, ensure_ascii=False)
        else:
            tx_id = db.add_cop_income(
                date=clean_date,
                category=platform_or_category.strip(),
                amount=float(amount),
                notes=notes.strip()
            )
            new_bal = db.get_cop_balance()
            return json.dumps({
                "exito": True,
                "mensaje": f"Ingreso COP registrado (ID #{tx_id}).",
                "detalles": {
                    "id": tx_id,
                    "fecha": clean_date,
                    "monto": f"${amount:,.0f} COP",
                    "categoria": platform_or_category,
                    "nuevo_saldo_cop": f"${new_bal:,.0f} COP"
                }
            }, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error al registrar ingreso: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
def get_recent_transactions(limit: int = 15) -> str:
    """
    Obtiene las transacciones y movimientos financieros más recientes registrados.
    """
    try:
        activities = db.get_recent_activities(limit=max(1, min(limit, 50)))
        return json.dumps(activities, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error al obtener transacciones: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
def get_budget_status(year_month: str = "") -> str:
    """
    Obtiene el estado de cumplimiento del presupuesto del mes:
    - Gastos ejecutados por categoría vs presupuesto asignado
    - Porcentaje gastado y saldo restante
    """
    try:
        ym = year_month.strip() if year_month else datetime.now().strftime("%Y-%m")
        expenses_by_cat = db.get_expenses_by_category()
        budgets_raw = db.get_category_budgets()
        budgets_map = {b["category"]: b["budget"] for b in budgets_raw}

        breakdown = []
        for cat in expenses_by_cat:
            c_name = cat.get("category", "")
            spent = float(cat.get("total", 0))
            budget = float(budgets_map.get(c_name, 0))
            pct = round((spent / budget * 100), 1) if budget > 0 else 0
            breakdown.append({
                "categoria": c_name,
                "gastado_cop": spent,
                "presupuesto_cop": budget,
                "porcentaje_ejecutado": f"{pct}%",
                "disponible_cop": budget - spent
            })

        return json.dumps({
            "mes": ym,
            "categorias": breakdown
        }, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error al obtener presupuesto: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
def query_database(sql_query: str) -> str:
    """
    Ejecuta una consulta SQL personalizada de SOLO LECTURA (SELECT) sobre la base de datos.
    Permite responder preguntas analíticas complejas o agrupaciones personalizadas.
    
    Protección de seguridad: Rechaza cualquier sentencia destructiva o de modificación.
    """
    cleaned = sql_query.strip().strip(";")
    upper = cleaned.upper()

    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        return json.dumps({"error": "Solo se permiten consultas de lectura (SELECT / WITH)."}, ensure_ascii=False)

    for forbidden in ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "ATTACH", "DETACH"]:
        if forbidden in upper.split():
            return json.dumps({"error": f"Operación '{forbidden}' no permitida por seguridad."}, ensure_ascii=False)

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(cleaned)
            rows = cursor.fetchmany(50)
            results = [dict(row) for row in rows]
            return json.dumps({
                "filas_retornadas": len(results),
                "resultados": results
            }, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error SQL: {str(e)}"}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
