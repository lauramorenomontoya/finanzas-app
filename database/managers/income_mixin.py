"""
Mixin para Gestión de Ingresos (USD y COP).
"""

from datetime import datetime
from typing import List, Dict, Any, Optional


class IncomeMixin:
    def add_usd_deposit(self, date: str, platform: str, amount: float, notes: str = "") -> int:
        """Registra un nuevo ingreso en USD."""
        if amount <= 0:
            raise ValueError("El monto del depósito debe ser mayor a 0.")
        
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO usd_transactions (date, platform, type, amount, notes)
                    VALUES (?, ?, 'DEPOSIT', ?, ?);
                """, (date, platform.strip(), float(amount), notes.strip()))
                conn.commit()
                return cursor.lastrowid

    def add_cop_income(self, date: str, category: str, amount: float, notes: str = "") -> int:
        """Registra un ingreso en COP."""
        if amount <= 0:
            raise ValueError("El monto del ingreso debe ser mayor a 0.")
        
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                    VALUES (?, ?, 'MANUAL_INCOME', ?, 0, 'DEBIT', ?);
                """, (date, category.strip(), float(amount), notes.strip()))
                conn.commit()
                return cursor.lastrowid

    add_cop_manual_income = add_cop_income

    def get_incomes_summary(self, year_month: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene un resumen de ingresos en USD y COP para el mes y global."""
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM usd_transactions WHERE type = 'DEPOSIT';")
            total_usd = float(cursor.fetchone()["total"])

            cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM usd_transactions WHERE type = 'DEPOSIT' AND strftime('%Y-%m', date) = ?;", (year_month,))
            month_usd = float(cursor.fetchone()["total"])

            cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM cop_transactions WHERE type IN ('MANUAL_INCOME', 'TRANSFER_IN');")
            total_cop = float(cursor.fetchone()["total"])

            cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM cop_transactions WHERE type IN ('MANUAL_INCOME', 'TRANSFER_IN') AND strftime('%Y-%m', date) = ?;", (year_month,))
            month_cop = float(cursor.fetchone()["total"])

            return {
                "total_usd": total_usd,
                "month_usd": month_usd,
                "total_cop": total_cop,
                "month_cop": month_cop,
                "usd_balance": self.get_usd_balance(),
                "cop_balance": self.get_cop_balance()
            }

    def get_all_incomes(self, limit: int = 50, currency_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene lista unificada de ingresos ordenados por fecha."""
        incomes = []
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if not currency_filter or currency_filter in ("Todas", "USD"):
                cursor.execute("""
                    SELECT id, date, platform as concept, amount, 'USD' as currency, notes, 'DEPOSIT' as type_tag, created_at
                    FROM usd_transactions
                    WHERE type = 'DEPOSIT';
                """)
                for r in cursor.fetchall():
                    incomes.append(dict(r))

            if not currency_filter or currency_filter in ("Todas", "COP"):
                cursor.execute("""
                    SELECT id, date, category as concept, amount, 'COP' as currency, notes, type as type_tag, created_at
                    FROM cop_transactions
                    WHERE type IN ('MANUAL_INCOME', 'TRANSFER_IN');
                """)
                for r in cursor.fetchall():
                    incomes.append(dict(r))

        incomes.sort(key=lambda x: (x["date"], x.get("created_at", "")), reverse=True)
        return incomes[:limit]
