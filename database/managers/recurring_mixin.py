"""
Mixin para Gestión de Gastos Fijos Multimoneda y Checklist (Agenda).
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class RecurringMixin:
    def get_recurring_expenses(self, only_active: bool = True) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if only_active:
                cursor.execute("""
                    SELECT id, category, description, amount, currency, due_day, is_active, created_at
                    FROM recurring_expenses
                    WHERE is_active = 1
                    ORDER BY currency ASC, due_day ASC;
                """)
            else:
                cursor.execute("""
                    SELECT id, category, description, amount, currency, due_day, is_active, created_at
                    FROM recurring_expenses
                    ORDER BY currency ASC, due_day ASC;
                """)
            return [dict(row) for row in cursor.fetchall()]

    def add_recurring_expense(
        self,
        category: str,
        description: str,
        amount: float,
        currency: str = "COP",
        due_day: int = 1
    ) -> Optional[int]:
        category = category.strip()
        description = description.strip()
        if not category or not description or amount <= 0:
            return None
        if currency not in ("COP", "USD"):
            currency = "COP"

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO recurring_expenses (category, description, amount, currency, due_day, is_active)
                    VALUES (?, ?, ?, ?, ?, 1);
                """, (category, description, float(amount), currency, int(due_day)))
                conn.commit()
                return cursor.lastrowid

    def update_recurring_expense(
        self,
        rec_id: int,
        category: str,
        description: str,
        amount: float,
        currency: str = "COP",
        due_day: int = 1,
        is_active: int = 1
    ) -> bool:
        category = category.strip()
        description = description.strip()
        if not category or not description or amount <= 0:
            return False
        if currency not in ("COP", "USD"):
            currency = "COP"

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE recurring_expenses
                    SET category = ?, description = ?, amount = ?, currency = ?, due_day = ?, is_active = ?
                    WHERE id = ?;
                """, (category, description, float(amount), currency, int(due_day), int(is_active), rec_id))
                conn.commit()
                return cursor.rowcount > 0

    def delete_recurring_expense(self, rec_id: int) -> bool:
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM recurring_expenses WHERE id = ?;", (rec_id,))
                conn.commit()
                return cursor.rowcount > 0

    def get_recurring_checklist_status(self, year_month: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Devuelve la lista de gastos fijos de la plantilla con su estado de pago
        en el mes indicado, soportando tanto COP como USD.
        """
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        recurring_items = self.get_recurring_expenses(only_active=True)
        checklist: List[Dict[str, Any]] = []

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for rec in recurring_items:
                desc = rec["description"]
                cat = rec["category"]
                curr = rec.get("currency", "COP")

                if curr == "USD":
                    cursor.execute("""
                        SELECT id, date, amount, notes
                        FROM usd_transactions
                        WHERE type = 'EXPENSE' 
                          AND strftime('%Y-%m', date) = ?
                          AND (notes LIKE ? OR platform LIKE ?)
                        ORDER BY date DESC LIMIT 1;
                    """, (year_month, f"%{desc}%", f"%{cat}%"))
                else:
                    cursor.execute("""
                        SELECT id, date, amount, payment_method, notes
                        FROM cop_transactions
                        WHERE type = 'EXPENSE' 
                          AND strftime('%Y-%m', date) = ?
                          AND (notes LIKE ? OR (category = ? AND is_fixed = 1))
                        ORDER BY date DESC LIMIT 1;
                    """, (year_month, f"%{desc}%", cat))

                tx = cursor.fetchone()
                is_paid = tx is not None
                tx_id = tx["id"] if tx else None
                paid_date = tx["date"] if tx else None

                checklist.append({
                    "id": rec["id"],
                    "category": rec["category"],
                    "description": rec["description"],
                    "amount": rec["amount"],
                    "currency": curr,
                    "due_day": rec["due_day"],
                    "is_paid": is_paid,
                    "tx_id": tx_id,
                    "paid_date": paid_date,
                    "year_month": year_month
                })

        checklist.sort(key=lambda x: (x["currency"] != "COP", x["due_day"]))
        return checklist

    def pay_recurring_item(self, recurring_id: int, date_str: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
        """Registra el pago de un gasto fijo (COP o USD) desde el checklist."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT category, description, amount, currency FROM recurring_expenses WHERE id = ?;", (recurring_id,))
                rec = cursor.fetchone()
                if not rec:
                    return False, "Gasto fijo no encontrado en la plantilla.", None

                curr = rec["currency"] or "COP"
                amt = float(rec["amount"])

                if curr == "USD":
                    cursor.execute("""
                        INSERT INTO usd_transactions (date, platform, type, amount, notes)
                        VALUES (?, ?, 'EXPENSE', ?, ?);
                    """, (date_str, rec["category"], amt, f"Gasto fijo USD: {rec['description']}"))
                    tx_id = cursor.lastrowid
                    conn.commit()
                    return True, f"¡{rec['description']} marcado como PAGADO (${amt:,.2f} USD)!", tx_id
                else:
                    cursor.execute("""
                        INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                        VALUES (?, ?, 'EXPENSE', ?, 1, 'DEBIT', ?);
                    """, (date_str, rec["category"], amt, f"Gasto fijo COP: {rec['description']}"))
                    tx_id = cursor.lastrowid
                    conn.commit()
                    return True, f"¡{rec['description']} marcado como PAGADO (${amt:,.0f} COP)!", tx_id

    def unpay_recurring_item(self, tx_id: int, currency: str = "COP") -> Tuple[bool, str]:
        """Revierte el pago de un gasto fijo eliminando su registro de transacción."""
        if currency == "USD":
            success, msg, _ = self.delete_usd_transaction(tx_id, force=True)
        else:
            success, msg, _ = self.delete_cop_transaction(tx_id, force=True)
        return success, "Pago de gasto fijo revertido a PENDIENTE." if success else msg

    def apply_recurring_batch(self, recurring_ids: List[int], date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Aplica múltiples gastos fijos en una sola transacción atómica.
        Retorna resumen con total aplicado, omitido y errores.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        applied_count = 0
        skipped_count = 0
        errors = []

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN IMMEDIATE;")

                    for r_id in recurring_ids:
                        cursor.execute("SELECT category, description, amount, currency FROM recurring_expenses WHERE id = ? AND is_active = 1;", (r_id,))
                        rec = cursor.fetchone()
                        if not rec:
                            skipped_count += 1
                            continue

                        curr = rec["currency"] or "COP"
                        amt = float(rec["amount"])

                        if curr == "USD":
                            cursor.execute("""
                                INSERT INTO usd_transactions (date, platform, type, amount, notes)
                                VALUES (?, ?, 'EXPENSE', ?, ?);
                            """, (date_str, rec["category"], amt, f"Gasto fijo USD: {rec['description']}"))
                        else:
                            cursor.execute("""
                                INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                                VALUES (?, ?, 'EXPENSE', ?, 1, 'DEBIT', ?);
                            """, (date_str, rec["category"], amt, f"Gasto fijo COP: {rec['description']}"))

                        applied_count += 1

                    conn.commit()
                    return {
                        "success": True,
                        "applied": applied_count,
                        "skipped": skipped_count,
                        "errors": errors
                    }
                except Exception as e:
                    conn.rollback()
                    return {
                        "success": False,
                        "applied": 0,
                        "skipped": len(recurring_ids),
                        "errors": [str(e)]
                    }

    def apply_recurring_expenses(self, date_str: Optional[str] = None, expense_ids: Optional[List[int]] = None) -> Tuple[int, float]:
        """Aplica gastos fijos especificados y retorna (count, total_amount)."""
        if expense_ids is None:
            items = self.get_recurring_expenses(only_active=True)
            expense_ids = [i["id"] for i in items]

        total_amt = 0.0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for r_id in expense_ids:
                cursor.execute("SELECT amount FROM recurring_expenses WHERE id = ?;", (r_id,))
                r = cursor.fetchone()
                if r:
                    total_amt += float(r["amount"])

        res = self.apply_recurring_batch(expense_ids, date_str)
        return res.get("applied", 0), total_amt

