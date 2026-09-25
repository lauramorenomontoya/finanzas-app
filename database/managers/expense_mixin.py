"""
Mixin para Gestión de Egresos y Gastos (COP y USD).
"""

from datetime import datetime
from typing import List, Dict, Any, Optional


class ExpenseMixin:
    def add_cop_expense(
        self,
        date: str,
        category: str,
        amount: float,
        is_fixed: bool = False,
        payment_method: str = "DEBIT",
        notes: str = ""
    ) -> int:
        """Registra un nuevo gasto en COP."""
        if amount <= 0:
            raise ValueError("El monto del gasto debe ser mayor a 0.")
        
        if payment_method not in ("DEBIT", "CREDIT_CARD", "CASH"):
            payment_method = "DEBIT"

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                    VALUES (?, ?, 'EXPENSE', ?, ?, ?, ?);
                """, (date, category.strip(), float(amount), 1 if is_fixed else 0, payment_method, notes.strip()))
                conn.commit()
                return cursor.lastrowid

    def add_usd_expense(self, date: str, category_or_service: str, amount: float, notes: str = "") -> int:
        """Registra un gasto directo en USD."""
        if amount <= 0:
            raise ValueError("El monto del gasto debe ser mayor a 0.")

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO usd_transactions (date, platform, type, amount, notes)
                    VALUES (?, ?, 'EXPENSE', ?, ?);
                """, (date, category_or_service.strip(), float(amount), notes.strip()))
                conn.commit()
                return cursor.lastrowid

    def get_expenses_summary(self, year_month: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene un resumen de egresos en COP y USD."""
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 
                    COALESCE(SUM(amount), 0) AS total_exp,
                    COALESCE(SUM(CASE WHEN is_fixed = 1 THEN amount ELSE 0 END), 0) AS fixed_exp,
                    COALESCE(SUM(CASE WHEN payment_method = 'CREDIT_CARD' THEN amount ELSE 0 END), 0) AS cc_exp
                FROM cop_transactions
                WHERE type = 'EXPENSE' AND strftime('%Y-%m', date) = ?;
            """, (year_month,))
            cop_r = cursor.fetchone()

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total_usd_exp
                FROM usd_transactions
                WHERE type = 'EXPENSE' AND strftime('%Y-%m', date) = ?;
            """, (year_month,))
            usd_r = cursor.fetchone()

            return {
                "month_cop_expenses": float(cop_r["total_exp"]),
                "month_cop_fixed": float(cop_r["fixed_exp"]),
                "month_cop_cc": float(cop_r["cc_exp"]),
                "month_usd_expenses": float(usd_r["total_usd_exp"]),
                "credit_card_debt": self.get_credit_card_debt(),
                "cop_balance": self.get_cop_balance(),
                "usd_balance": self.get_usd_balance()
            }

    def get_all_expenses(
        self,
        limit: int = 50,
        currency_filter: Optional[str] = None,
        category: Optional[str] = None,
        payment_method: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene historial unificado de egresos en COP y USD."""
        expenses = []
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if not currency_filter or currency_filter in ("Todas", "USD"):
                cursor.execute("""
                    SELECT id, date, platform as category, amount, 'USD' as currency, 0 as is_fixed, 'N/A' as payment_method, notes, 'EXPENSE' as type, created_at
                    FROM usd_transactions
                    WHERE type = 'EXPENSE';
                """)
                for r in cursor.fetchall():
                    expenses.append(dict(r))

            if not currency_filter or currency_filter in ("Todas", "COP"):
                conditions = ["type IN ('EXPENSE', 'CC_PAYMENT')"]
                params = []
                if category and category != "Todas":
                    conditions.append("category = ?")
                    params.append(category)
                if payment_method and payment_method != "Todos":
                    conditions.append("payment_method = ?")
                    params.append(payment_method)

                cursor.execute(f"""
                    SELECT id, date, category, amount, 'COP' as currency, is_fixed, payment_method, notes, type, created_at
                    FROM cop_transactions
                    WHERE {' AND '.join(conditions)};
                """, params)
                for r in cursor.fetchall():
                    expenses.append(dict(r))

        expenses.sort(key=lambda x: (x["date"], x.get("created_at", "")), reverse=True)
        return expenses[:limit]

    def get_cop_expenses(
        self,
        limit: int = 50,
        category: Optional[str] = None,
        payment_method: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene lista de gastos en COP con filtros opcionales."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = ["type IN ('EXPENSE', 'CC_PAYMENT')"]
            params = []

            if category and category != "Todas":
                conditions.append("category = ?")
                params.append(category)
            if payment_method and payment_method != "Todos":
                conditions.append("payment_method = ?")
                params.append(payment_method)

            where_clause = f"WHERE {' AND '.join(conditions)}"
            params.append(limit)

            cursor.execute(f"""
                SELECT id, date, category, type, amount, is_fixed, payment_method, notes, created_at
                FROM cop_transactions
                {where_clause}
                ORDER BY date DESC, id DESC
                LIMIT ?;
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_cop_expenses_summary(self, year_month: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene totales y estadísticas de gastos para el mes en curso en COP."""
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(amount), 0) AS total_expenses,
                    COALESCE(SUM(CASE WHEN is_fixed = 1 THEN amount ELSE 0 END), 0) AS fixed_expenses,
                    COALESCE(SUM(CASE WHEN is_fixed = 0 AND type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS variable_expenses,
                    COALESCE(SUM(CASE WHEN payment_method = 'CREDIT_CARD' AND type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS credit_card_expenses,
                    COALESCE(SUM(CASE WHEN payment_method = 'DEBIT' AND type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS debit_expenses,
                    COALESCE(SUM(CASE WHEN type = 'CC_PAYMENT' THEN amount ELSE 0 END), 0) AS cc_payments
                FROM cop_transactions
                WHERE type IN ('EXPENSE', 'CC_PAYMENT') AND strftime('%Y-%m', date) = ?;
            """, (year_month,))
            row = cursor.fetchone()

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total_income
                FROM cop_transactions
                WHERE type IN ('TRANSFER_IN', 'MANUAL_INCOME', 'TRANSFER_FROM_INVESTMENT') AND strftime('%Y-%m', date) = ?;
            """, (year_month,))
            income_row = cursor.fetchone()

            total_expenses = float(row["total_expenses"])
            total_income = float(income_row["total_income"])
            fixed_expenses = float(row["fixed_expenses"])
            variable_expenses = float(row["variable_expenses"])
            cc_expenses = float(row["credit_card_expenses"])
            debit_expenses = float(row["debit_expenses"])

            fixed_ratio = (fixed_expenses / total_expenses * 100) if total_expenses > 0 else 0
            variable_ratio = (variable_expenses / total_expenses * 100) if total_expenses > 0 else 0
            burn_rate = (total_expenses / total_income * 100) if total_income > 0 else 0

            return {
                "month": year_month,
                "total_expenses": total_expenses,
                "total_income": total_income,
                "fixed_expenses": fixed_expenses,
                "variable_expenses": variable_expenses,
                "credit_card_expenses": cc_expenses,
                "debit_expenses": debit_expenses,
                "net_balance_month": total_income - total_expenses,
                "fixed_ratio": fixed_ratio,
                "variable_ratio": variable_ratio,
                "burn_rate": burn_rate
            }

    def get_expenses_by_category(self, year_month: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene desglose de gastos agrupados por categoría para un mes."""
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    category,
                    COALESCE(SUM(amount), 0) AS total,
                    COUNT(*) AS count
                FROM cop_transactions
                WHERE type = 'EXPENSE' AND category NOT LIKE 'Ajuste%' AND strftime('%Y-%m', date) = ?
                GROUP BY category
                ORDER BY total DESC;
            """, (year_month,))
            return [dict(row) for row in cursor.fetchall()]

    def get_expenses_by_category_all_time(self) -> List[Dict[str, Any]]:
        """Obtiene desglose de gastos agrupados por categoría histórico."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    category,
                    COALESCE(SUM(amount), 0) AS total,
                    COUNT(*) AS count
                FROM cop_transactions
                WHERE type = 'EXPENSE'
                GROUP BY category
                ORDER BY total DESC;
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_monthly_expenses_history(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtiene resumen de gastos mes a mes para un año determinado."""
        if not year:
            year = datetime.now().year

        year_str = str(year)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', date) AS month,
                    COALESCE(SUM(CASE WHEN is_fixed = 1 THEN amount ELSE 0 END), 0) AS fixed,
                    COALESCE(SUM(CASE WHEN is_fixed = 0 THEN amount ELSE 0 END), 0) AS variable,
                    COALESCE(SUM(amount), 0) AS total
                FROM cop_transactions
                WHERE type = 'EXPENSE' AND strftime('%Y', date) = ?
                GROUP BY strftime('%Y-%m', date)
                ORDER BY month ASC;
            """, (year_str,))
            return [dict(row) for row in cursor.fetchall()]
