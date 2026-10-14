"""
Mixin para Gestión de Saldos, Transacciones Base y Tarjetas de Crédito.
"""

from typing import List, Dict, Any, Optional, Tuple


class BalanceMixin:
    def get_usd_balance(self, conn: Optional[Any] = None) -> float:
        query = """
            SELECT 
                COALESCE(SUM(CASE WHEN type IN ('DEPOSIT', 'TRANSFER_FROM_INVESTMENT') THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN type IN ('TRANSFER_OUT', 'TRANSFER_TO_INVESTMENT', 'EXPENSE') THEN amount ELSE 0 END), 0) AS balance
            FROM usd_transactions;
        """
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            return float(row["balance"]) if row else 0.0

        with self.get_connection() as c:
            cursor = c.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            return float(row["balance"]) if row else 0.0

    def get_usd_total_saved_all_time(self) -> float:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM usd_transactions
                WHERE type = 'DEPOSIT';
            """)
            row = cursor.fetchone()
            return float(row["total"]) if row else 0.0

    def get_usd_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, platform, type, amount, notes, created_at
                FROM usd_transactions
                ORDER BY date DESC, id DESC
                LIMIT ?;
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_usd_transactions_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM usd_transactions;")
            row = cursor.fetchone()
            return int(row["total"]) if row else 0

    def update_usd_transaction(self, tx_id: int, date: str, platform: str, amount: float, notes: str = "") -> Tuple[bool, str]:
        if amount <= 0:
            return False, "El monto debe ser mayor a 0."

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE usd_transactions
                        SET date = ?, platform = ?, amount = ?, notes = ?
                        WHERE id = ?;
                    """, (date, platform.strip(), float(amount), notes.strip(), tx_id))
                    conn.commit()
                    return True, "Transacción en USD actualizada correctamente."
                except Exception as e:
                    return False, f"Error al actualizar: {str(e)}"

    def delete_usd_transaction(self, tx_id: int, force: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN IMMEDIATE;")
                    cursor.execute("SELECT id, type, amount, platform FROM usd_transactions WHERE id = ?;", (tx_id,))
                    tx = cursor.fetchone()
                    if not tx:
                        conn.rollback()
                        return False, "La transacción no existe.", None

                    if tx["type"] == "TRANSFER_OUT" and not force:
                        conn.rollback()
                        return False, "Esta transacción es el reflejo de una conversión. Debes eliminarla desde 'Puente Conversión'.", None

                    if tx["type"] == "DEPOSIT":
                        current_balance = self.get_usd_balance(conn=conn)
                        resulting_balance = current_balance - float(tx["amount"])

                        if resulting_balance < -0.001 and not force:
                            conn.rollback()
                            warning_data = {
                                "type": "USD_BALANCE_NEGATIVE",
                                "current_balance": current_balance,
                                "amount_to_deduct": float(tx["amount"]),
                                "resulting_balance": resulting_balance,
                                "currency": "USD",
                                "description": f"Eliminar el depósito de ${tx['amount']:,.2f} USD en {tx['platform']}"
                            }
                            return False, "WARNING_NEGATIVE_BALANCE", warning_data

                    if tx["type"] in ("TRANSFER_TO_INVESTMENT", "TRANSFER_FROM_INVESTMENT"):
                        cursor.execute("SELECT id FROM account_transactions WHERE linked_table = 'usd_transactions' AND linked_tx_id = ?;", (tx_id,))
                        acc_tx = cursor.fetchone()
                        if acc_tx:
                            cursor.execute("DELETE FROM account_transactions WHERE id = ?;", (acc_tx["id"],))
                            cursor.execute("DELETE FROM transaction_tags WHERE source_table = 'account_transactions' AND record_id = ?;", (acc_tx["id"],))

                    cursor.execute("DELETE FROM usd_transactions WHERE id = ?;", (tx_id,))
                    cursor.execute("DELETE FROM transaction_tags WHERE source_table = 'usd_transactions' AND record_id = ?;", (tx_id,))
                    conn.commit()
                    return True, "Transacción en USD eliminada exitosamente.", None
                except Exception as e:
                    conn.rollback()
                    return False, f"Error al eliminar: {str(e)}", None

    def get_cop_balance(self, conn: Optional[Any] = None) -> float:
        query = """
            SELECT 
                COALESCE(SUM(CASE WHEN type IN ('TRANSFER_IN', 'MANUAL_INCOME', 'TRANSFER_FROM_INVESTMENT') THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE 
                    WHEN type = 'EXPENSE' AND payment_method IN ('DEBIT', 'CASH') THEN amount 
                    WHEN type IN ('CC_PAYMENT', 'TRANSFER_TO_INVESTMENT') THEN amount
                    ELSE 0 
                END), 0) AS balance
            FROM cop_transactions;
        """
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            return float(row["balance"]) if row else 0.0

        with self.get_connection() as c:
            cursor = c.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            return float(row["balance"]) if row else 0.0

    def get_credit_card_debt(self, conn: Optional[Any] = None) -> float:
        query = """
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'EXPENSE' AND payment_method = 'CREDIT_CARD' THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN type = 'CC_PAYMENT' THEN amount ELSE 0 END), 0) AS debt
            FROM cop_transactions;
        """
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            debt = float(row["debt"]) if row else 0.0
            return max(0.0, debt)

        with self.get_connection() as c:
            cursor = c.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            debt = float(row["debt"]) if row else 0.0
            return max(0.0, debt)

    def pay_credit_card(self, date: str, amount: float, notes: str = "") -> Tuple[bool, str]:
        # Soporte por si por error se invocó con argumentos invertidos (amount, date)
        if isinstance(date, (int, float)) and isinstance(amount, str):
            date, amount = str(amount), float(date)

        if amount <= 0:
            return False, "El monto del pago debe ser mayor a 0."

        current_debt = self.get_credit_card_debt()
        if current_debt <= 0:
            return False, "No tienes deuda pendiente en tarjeta de crédito por pagar."

        cop_balance = self.get_cop_balance()
        if amount > cop_balance:
            return False, f"Saldo insuficiente en cuenta COP (${cop_balance:,.0f} COP) para realizar el pago de ${amount:,.0f} COP."

        is_partial = amount < current_debt
        default_label = f"Abono parcial Tarjeta de Crédito (${amount:,.0f} COP)" if is_partial else f"Pago total Tarjeta de Crédito (${amount:,.0f} COP)"
        desc_notes = notes.strip() if notes else default_label

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                    VALUES (?, 'Pago Tarjeta de Crédito', 'CC_PAYMENT', ?, 0, 'DEBIT', ?);
                """, (date, float(amount), desc_notes))
                conn.commit()
                tipo_pago = "Abono parcial" if is_partial else "Pago"
                remaining_debt = max(0.0, current_debt - amount)
                return True, f"¡{tipo_pago} de ${amount:,.0f} COP registrado con éxito! Deuda restante: ${remaining_debt:,.0f} COP."

    def pay_credit_card_debt(self, amount: float, date: Optional[str] = None, notes: str = "") -> Tuple[bool, str]:
        """Alias para registrar abono o pago de tarjeta recibiendo el monto primero."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        return self.pay_credit_card(date=date, amount=amount, notes=notes)

    def get_cop_transactions(self, limit: int = 50, category: Optional[str] = None, payment_method: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if category and category != "Todas":
                conditions.append("category = ?")
                params.append(category)
            if payment_method and payment_method != "Todos":
                conditions.append("payment_method = ?")
                params.append(payment_method)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            params.append(limit)

            cursor.execute(f"""
                SELECT id, date, category, type, amount, is_fixed, payment_method, notes, created_at
                FROM cop_transactions
                {where_clause}
                ORDER BY date DESC, id DESC
                LIMIT ?;
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_cop_transactions_count(self, category: Optional[str] = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if category and category != "Todas":
                cursor.execute("SELECT COUNT(*) AS total FROM cop_transactions WHERE category = ?;", (category,))
            else:
                cursor.execute("SELECT COUNT(*) AS total FROM cop_transactions;")
            row = cursor.fetchone()
            return int(row["total"]) if row else 0

    def update_cop_transaction(
        self,
        tx_id: int,
        date: str,
        category: str,
        amount: float,
        is_fixed: bool = False,
        payment_method: str = "DEBIT",
        notes: str = ""
    ) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "El monto debe ser mayor a 0."

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE cop_transactions
                        SET date = ?, category = ?, amount = ?, is_fixed = ?, payment_method = ?, notes = ?
                        WHERE id = ?;
                    """, (date, category.strip(), float(amount), 1 if is_fixed else 0, payment_method, notes.strip(), tx_id))
                    conn.commit()
                    return True, "Movimiento en COP actualizado correctamente."
                except Exception as e:
                    return False, f"Error al actualizar: {str(e)}"

    def delete_cop_transaction(self, tx_id: int, force: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN IMMEDIATE;")
                    cursor.execute("SELECT id, type, amount, category FROM cop_transactions WHERE id = ?;", (tx_id,))
                    tx = cursor.fetchone()
                    if not tx:
                        conn.rollback()
                        return False, "El movimiento no existe.", None

                    if tx["type"] == "TRANSFER_IN" and not force:
                        conn.rollback()
                        return False, "Este ingreso proviene de una conversión USD. Debes gestionarlo desde 'Puente Conversión'.", None

                    if tx["type"] in ("MANUAL_INCOME", "TRANSFER_FROM_INVESTMENT"):
                        current_bal = self.get_cop_balance(conn=conn)
                        resulting_bal = current_bal - float(tx["amount"])
                        if resulting_bal < -0.001 and not force:
                            conn.rollback()
                            warning_data = {
                                "type": "COP_BALANCE_NEGATIVE",
                                "current_balance": current_bal,
                                "amount_to_deduct": float(tx["amount"]),
                                "resulting_balance": resulting_bal,
                                "currency": "COP",
                                "description": f"Eliminar el ingreso de ${tx['amount']:,.0f} COP ({tx['category']})"
                            }
                            return False, "WARNING_NEGATIVE_BALANCE", warning_data

                    if tx["type"] in ("TRANSFER_TO_INVESTMENT", "TRANSFER_FROM_INVESTMENT"):
                        cursor.execute("SELECT id FROM account_transactions WHERE linked_table = 'cop_transactions' AND linked_tx_id = ?;", (tx_id,))
                        acc_tx = cursor.fetchone()
                        if acc_tx:
                            cursor.execute("DELETE FROM account_transactions WHERE id = ?;", (acc_tx["id"],))
                            cursor.execute("DELETE FROM transaction_tags WHERE source_table = 'account_transactions' AND record_id = ?;", (acc_tx["id"],))

                    cursor.execute("DELETE FROM cop_transactions WHERE id = ?;", (tx_id,))
                    cursor.execute("DELETE FROM transaction_tags WHERE source_table = 'cop_transactions' AND record_id = ?;", (tx_id,))
                    conn.commit()
                    return True, "Movimiento eliminado exitosamente.", None
                except Exception as e:
                    conn.rollback()
                    return False, f"Error al eliminar: {str(e)}", None
