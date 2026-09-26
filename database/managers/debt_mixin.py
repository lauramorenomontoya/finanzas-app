"""
Módulo de Gestión de Deudas y Préstamos (DebtMixin).
Permite administrar deudas personales o institucionales, registro de abonos parciales,
seguimiento del saldo pendiente, amortización y consolidación con la deuda de tarjeta de crédito.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class DebtMixin:
    """Mixin que encapsula la lógica de negocio y persistencia de Deudas y Abonos."""

    def add_debt(
        self,
        creditor: str,
        total_amount: float,
        currency: str = "COP",
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        notes: str = "",
        debt_type: str = "PAYABLE"
    ) -> int:
        """Registra una nueva deuda (PAYABLE = lo que debo, RECEIVABLE = lo que me deben)."""
        creditor = creditor.strip()
        if not creditor:
            raise ValueError("El nombre de la persona o entidad no puede estar vacío.")
        if total_amount <= 0:
            raise ValueError("El monto total debe ser mayor a 0.")
        if currency not in ("COP", "USD"):
            currency = "COP"
        if debt_type not in ("PAYABLE", "RECEIVABLE"):
            debt_type = "PAYABLE"

        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO debts (creditor, total_amount, currency, start_date, due_date, notes, status, debt_type)
                    VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?);
                """, (creditor, float(total_amount), currency, start_date, due_date, notes.strip(), debt_type))
                conn.commit()
                return cursor.lastrowid

    def get_debts(self, status: Optional[str] = None, debt_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene la lista de deudas o cuentas por cobrar con abonos, saldo restante y porcentaje pagado."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    d.id,
                    d.creditor,
                    d.total_amount,
                    d.currency,
                    d.start_date,
                    d.due_date,
                    d.notes,
                    d.status,
                    d.debt_type,
                    d.created_at,
                    COALESCE(SUM(p.amount), 0.0) AS total_paid,
                    COUNT(p.id) AS payments_count,
                    MAX(p.date) AS last_payment_date
                FROM debts d
                LEFT JOIN debt_payments p ON d.id = p.debt_id
            """
            conditions = []
            params = []
            if status:
                conditions.append("d.status = ?")
                params.append(status)
            if debt_type:
                conditions.append("d.debt_type = ?")
                params.append(debt_type)

            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"

            query += " GROUP BY d.id ORDER BY (d.total_amount - COALESCE(SUM(p.amount), 0.0)) DESC, d.start_date DESC;"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for r in rows:
                total_amount = float(r["total_amount"])
                total_paid = float(r["total_paid"])
                remaining = max(0.0, total_amount - total_paid)
                pct_paid = min(100.0, (total_paid / total_amount * 100.0)) if total_amount > 0 else 100.0
                
                results.append({
                    "id": r["id"],
                    "creditor": r["creditor"],
                    "total_amount": total_amount,
                    "currency": r["currency"],
                    "start_date": r["start_date"],
                    "due_date": r["due_date"],
                    "notes": r["notes"] or "",
                    "status": r["status"],
                    "debt_type": r["debt_type"] or "PAYABLE",
                    "created_at": r["created_at"],
                    "total_paid": total_paid,
                    "remaining_amount": remaining,
                    "percent_paid": round(pct_paid, 1),
                    "payments_count": int(r["payments_count"]),
                    "last_payment_date": r["last_payment_date"]
                })
            return results

    def get_debt_by_id(self, debt_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene una deuda específica por su identificador."""
        debts = self.get_debts()
        for d in debts:
            if d["id"] == debt_id:
                return d
        return None

    def update_debt(
        self,
        debt_id: int,
        creditor: str,
        total_amount: float,
        start_date: str,
        due_date: Optional[str] = None,
        notes: str = "",
        debt_type: str = "PAYABLE"
    ) -> bool:
        """Actualiza los datos básicos de una deuda o cuenta por cobrar existente."""
        creditor = creditor.strip()
        if not creditor:
            return False
        if total_amount <= 0:
            return False
        if debt_type not in ("PAYABLE", "RECEIVABLE"):
            debt_type = "PAYABLE"

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE debts 
                    SET creditor = ?, total_amount = ?, start_date = ?, due_date = ?, notes = ?, debt_type = ?
                    WHERE id = ?;
                """, (creditor, float(total_amount), start_date, due_date, notes.strip(), debt_type, debt_id))
                conn.commit()

                # Reevaluar si con el nuevo monto total cambia su estado a PAGADA o ACTIVA
                self._sync_debt_status(conn, debt_id)
                return cursor.rowcount > 0

    def delete_debt(self, debt_id: int) -> bool:
        """Elimina una deuda y sus abonos registrados."""
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM debts WHERE id = ?;", (debt_id,))
                conn.commit()
                return cursor.rowcount > 0

    def add_debt_payment(
        self,
        debt_id: int,
        amount: float,
        date: Optional[str] = None,
        notes: str = "",
        deduct_from_balance: bool = True
    ) -> Tuple[bool, str]:
        """
        Registra un abono a una deuda o un cobro/pago recibido de una cuenta por cobrar.
        - Para PAYABLE (Debo): descuenta del saldo COP como egreso si deduct_from_balance=True.
        - Para RECEIVABLE (Me deben): suma al saldo COP como ingreso si deduct_from_balance=True.
        """
        if amount <= 0:
            return False, "El monto del abono o pago debe ser mayor a 0."

        debt = self.get_debt_by_id(debt_id)
        if not debt:
            return False, "No se encontró el registro especificado."

        is_payable = debt.get("debt_type", "PAYABLE") == "PAYABLE"
        remaining = debt["remaining_amount"]
        if remaining <= 0:
            msg_done = f"La deuda con {debt['creditor']} ya está completamente pagada." if is_payable else f"{debt['creditor']} ya pagó la totalidad de lo adeudado."
            return False, msg_done

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # Validación de saldo disponible solo para pagos que realizo yo (PAYABLE)
        if is_payable and deduct_from_balance and debt["currency"] == "COP":
            cop_balance = self.get_cop_balance()
            if amount > cop_balance:
                return False, f"Saldo insuficiente en cuenta COP (${cop_balance:,.0f} COP) para realizar el abono de ${amount:,.0f} COP."

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                tx_id = None

                # Registrar movimiento en cop_transactions si aplica
                if deduct_from_balance and debt["currency"] == "COP":
                    if is_payable:
                        cat_name = "Abono a Deudas"
                        cursor.execute("SELECT id FROM categories WHERE name = ?;", (cat_name,))
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT OR IGNORE INTO categories (name, type, icon, color, is_system)
                                VALUES ('Abono a Deudas', 'EXPENSE_COP', '🤝', '#f59e0b', 0);
                            """)

                        expense_note = f"Abono a deuda con {debt['creditor']}"
                        if notes.strip():
                            expense_note += f": {notes.strip()}"

                        cursor.execute("""
                            INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                            VALUES (?, ?, 'EXPENSE', ?, 0, 'DEBIT', ?);
                        """, (date, cat_name, float(amount), expense_note))
                        tx_id = cursor.lastrowid
                    else:
                        cat_name = "Cobro de Préstamos"
                        cursor.execute("SELECT id FROM categories WHERE name = ?;", (cat_name,))
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT OR IGNORE INTO categories (name, type, icon, color, is_system)
                                VALUES ('Cobro de Préstamos', 'INCOME_COP', '📥', '#10b981', 0);
                            """)

                        income_note = f"Pago recibido de {debt['creditor']}"
                        if notes.strip():
                            income_note += f": {notes.strip()}"

                        cursor.execute("""
                            INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                            VALUES (?, ?, 'MANUAL_INCOME', ?, 0, 'DEBIT', ?);
                        """, (date, cat_name, float(amount), income_note))
                        tx_id = cursor.lastrowid

                # Registrar el abono en debt_payments
                cursor.execute("""
                    INSERT INTO debt_payments (debt_id, date, amount, notes, transaction_id)
                    VALUES (?, ?, ?, ?, ?);
                """, (debt_id, date, float(amount), notes.strip(), tx_id))

                conn.commit()

                new_status = self._sync_debt_status(conn, debt_id)
                new_remaining = max(0.0, remaining - amount)
                
                action_word = "Abono registrado" if is_payable else "Pago recibido registrado"
                msg = f"¡{action_word} de ${amount:,.0f} {debt['currency']} con éxito! Saldo restante: ${new_remaining:,.0f} {debt['currency']}."
                if new_status == "PAID":
                    msg += " 🎉 ¡La obligación ha sido completamente liquidada!" if is_payable else f" 🎉 ¡{debt['creditor']} te ha pagado la totalidad!"

                return True, msg

    def get_debt_payments(self, debt_id: int) -> List[Dict[str, Any]]:
        """Obtiene el historial detallado de abonos o pagos registrados a una deuda."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, debt_id, date, amount, notes, transaction_id, created_at
                FROM debt_payments
                WHERE debt_id = ?
                ORDER BY date DESC, id DESC;
            """, (debt_id,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "debt_id": r["debt_id"],
                    "date": r["date"],
                    "amount": float(r["amount"]),
                    "notes": r["notes"] or "",
                    "transaction_id": r["transaction_id"],
                    "created_at": r["created_at"]
                }
                for r in rows
            ]

    def delete_debt_payment(self, payment_id: int) -> Tuple[bool, str]:
        """Elimina un abono y revierte su movimiento de saldo si estaba vinculado a cop_transactions."""
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT debt_id, amount, transaction_id FROM debt_payments WHERE id = ?;", (payment_id,))
                payment = cursor.fetchone()
                if not payment:
                    return False, "No se encontró el abono a eliminar."

                debt_id = payment["debt_id"]
                tx_id = payment["transaction_id"]

                # Si estaba vinculado a cop_transactions, eliminar para restaurar el saldo
                if tx_id:
                    cursor.execute("DELETE FROM cop_transactions WHERE id = ?;", (tx_id,))

                cursor.execute("DELETE FROM debt_payments WHERE id = ?;", (payment_id,))
                conn.commit()

                # Reajustar estado de la deuda
                self._sync_debt_status(conn, debt_id)
                return True, "Abono eliminado y saldo restituido correctamente."

    def _sync_debt_status(self, conn, debt_id: int) -> str:
        """Verifica los abonos y actualiza el estado de la deuda a ACTIVE o PAID."""
        cursor = conn.cursor()
        cursor.execute("SELECT total_amount FROM debts WHERE id = ?;", (debt_id,))
        row = cursor.fetchone()
        if not row:
            return "ACTIVE"
        total_amount = float(row["total_amount"])

        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) AS paid FROM debt_payments WHERE debt_id = ?;", (debt_id,))
        paid_row = cursor.fetchone()
        paid = float(paid_row["paid"]) if paid_row else 0.0

        new_status = "PAID" if paid >= total_amount else "ACTIVE"
        cursor.execute("UPDATE debts SET status = ? WHERE id = ?;", (new_status, debt_id))
        conn.commit()
        return new_status

    def get_debts_summary(self) -> Dict[str, Any]:
        """
        Retorna un resumen global consolidado:
        - Deudas que debo (PAYABLE: total, abonado, restante)
        - Dinero que me deben (RECEIVABLE: total, cobrado, restante)
        - Deuda de Tarjeta de Crédito
        - Deuda Total Pasiva (Consolidada: TC + Mis Deudas)
        """
        debts = self.get_debts()
        
        # Mis Deudas (PAYABLE)
        payable = [d for d in debts if d.get("debt_type") in ("PAYABLE", "OWED_BY_ME", None) and d["currency"] == "COP"]
        payable_total = sum(d["total_amount"] for d in payable)
        payable_paid = sum(d["total_paid"] for d in payable)
        payable_remaining = sum(d["remaining_amount"] for d in payable if d["status"] == "ACTIVE")

        # Dinero que me deben (RECEIVABLE)
        receivable = [d for d in debts if d.get("debt_type") in ("RECEIVABLE", "OWED_TO_ME") and d["currency"] == "COP"]
        receivable_total = sum(d["total_amount"] for d in receivable)
        receivable_paid = sum(d["total_paid"] for d in receivable)
        receivable_remaining = sum(d["remaining_amount"] for d in receivable if d["status"] == "ACTIVE")

        cc_debt = self.get_credit_card_debt()
        grand_total_debt = payable_remaining + cc_debt
        net_debt = grand_total_debt - receivable_remaining

        return {
            "personal_payable_total": payable_total,
            "personal_payable_paid": payable_paid,
            "personal_payable_remaining": payable_remaining,
            "personal_receivable_total": receivable_total,
            "personal_receivable_paid": receivable_paid,
            "personal_receivable_remaining": receivable_remaining,
            # Compatibilidad hacia atrás
            "personal_total": payable_total,
            "personal_paid": payable_paid,
            "personal_remaining": payable_remaining,
            "credit_card_debt": cc_debt,
            "grand_total_debt": grand_total_debt,
            "net_debt": net_debt,
            "active_debts_count": len([d for d in payable if d["status"] == "ACTIVE"]),
            "active_receivables_count": len([d for d in receivable if d["status"] == "ACTIVE"]),
            "paid_debts_count": len([d for d in payable if d["status"] == "PAID"])
        }
