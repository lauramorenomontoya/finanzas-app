"""
Mixin para Gestión de Cuentas, Fiducias e Inversiones.
"""

from typing import List, Dict, Any, Optional, Tuple


class AccountMixin:
    def create_account(
        self,
        name: str,
        currency: str,
        account_type: str = "INVERSION_FIDUCIA",
        institution: str = "",
        initial_balance: float = 0.0,
        color: str = "#10b981",
        icon: str = "📈"
    ) -> int:
        name = name.strip()
        if not name:
            raise ValueError("El nombre de la cuenta no puede estar vacío.")
        if currency not in ("COP", "USD"):
            raise ValueError("La moneda debe ser 'COP' o 'USD'.")
        if account_type not in ("INVERSION_FIDUCIA", "AHORRO", "BILLETERA", "OPERATIVA"):
            account_type = "INVERSION_FIDUCIA"

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO accounts (name, currency, account_type, institution, initial_balance, color, icon, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1);
                """, (name, currency, account_type, institution.strip(), float(initial_balance), color, icon))
                conn.commit()
                return cursor.lastrowid

    def get_accounts(self, currency: Optional[str] = None, only_active: bool = True) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if only_active:
                conditions.append("a.is_active = 1")
            if currency:
                conditions.append("a.currency = ?")
                params.append(currency)

            where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT 
                    a.id, a.name, a.currency, a.account_type, a.institution, 
                    a.initial_balance, a.color, a.icon, a.is_active, a.created_at,
                    COALESCE(SUM(CASE WHEN t.type IN ('DEPOSIT', 'TRANSFER_IN', 'YIELD') THEN t.amount ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN t.type IN ('WITHDRAWAL', 'TRANSFER_OUT') THEN t.amount ELSE 0 END), 0) AS tx_balance,
                    COALESCE(SUM(CASE WHEN t.type = 'YIELD' THEN t.amount ELSE 0 END), 0) AS total_yields
                FROM accounts a
                LEFT JOIN account_transactions t ON a.id = t.account_id
                {where_clause}
                GROUP BY a.id
                ORDER BY a.currency ASC, a.name ASC;
            """

            cursor.execute(query, params)
            accounts = []
            for row in cursor.fetchall():
                acc = dict(row)
                tx_balance = float(acc.pop("tx_balance", 0.0) or 0.0)
                total_yields = float(acc.get("total_yields", 0.0) or 0.0)
                acc["total_yields"] = total_yields
                acc["current_balance"] = acc["initial_balance"] + tx_balance
                accounts.append(acc)

            return accounts

    def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        accounts = self.get_accounts(only_active=False)
        for a in accounts:
            if a["id"] == account_id:
                return a
        return None

    def update_account(
        self,
        account_id: int,
        name: str,
        account_type: str,
        institution: str,
        color: str,
        icon: str,
        is_active: int = 1
    ) -> bool:
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE accounts
                    SET name = ?, account_type = ?, institution = ?, color = ?, icon = ?, is_active = ?
                    WHERE id = ?;
                """, (name.strip(), account_type, institution.strip(), color, icon, int(is_active), account_id))
                conn.commit()
                return cursor.rowcount > 0

    def delete_account(self, account_id: int) -> Tuple[bool, str]:
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM accounts WHERE id = ?;", (account_id,))
                acc = cursor.fetchone()
                if not acc:
                    return False, "La cuenta no existe."

                cursor.execute("SELECT COUNT(*) as count FROM account_transactions WHERE account_id = ?;", (account_id,))
                if cursor.fetchone()["count"] > 0:
                    cursor.execute("UPDATE accounts SET is_active = 0 WHERE id = ?;", (account_id,))
                    conn.commit()
                    return True, f"La cuenta '{acc['name']}' tiene historial y fue archivada/desactivada."

                cursor.execute("DELETE FROM accounts WHERE id = ?;", (account_id,))
                conn.commit()
                return True, f"Cuenta '{acc['name']}' eliminada exitosamente."

    def transfer_to_investment(
        self,
        account_id: int,
        amount: float,
        date: str,
        notes: str = ""
    ) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "El monto a transferir debe ser mayor a 0."

        acc = self.get_account_by_id(account_id)
        if not acc:
            return False, "Cuenta de inversión no encontrada."

        currency = acc["currency"]
        desc_notes = notes.strip() if notes else f"Aporte a {acc['name']}"

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN IMMEDIATE;")

                    if currency == "COP":
                        cop_bal = self.get_cop_balance(conn=conn)
                        if amount > cop_bal:
                            conn.rollback()
                            return False, f"Saldo insuficiente en cuenta COP (${cop_bal:,.0f} COP)."

                        cursor.execute("""
                            INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                            VALUES (?, ?, 'TRANSFER_TO_INVESTMENT', ?, 0, 'DEBIT', ?);
                        """, (date, f"Inversión: {acc['name']}", amount, desc_notes))
                        linked_tx_id = cursor.lastrowid
                        linked_table = "cop_transactions"
                    else:
                        usd_bal = self.get_usd_balance(conn=conn)
                        if amount > usd_bal:
                            conn.rollback()
                            return False, f"Saldo insuficiente en Bóveda USD (${usd_bal:,.2f} USD)."

                        cursor.execute("""
                            INSERT INTO usd_transactions (date, platform, type, amount, notes)
                            VALUES (?, ?, 'TRANSFER_TO_INVESTMENT', ?, ?);
                        """, (date, f"Inversión: {acc['name']}", amount, desc_notes))
                        linked_tx_id = cursor.lastrowid
                        linked_table = "usd_transactions"

                    cursor.execute("""
                        INSERT INTO account_transactions (account_id, date, type, amount, notes, linked_tx_id, linked_table)
                        VALUES (?, ?, 'TRANSFER_IN', ?, ?, ?, ?);
                    """, (account_id, date, amount, desc_notes, linked_tx_id, linked_table))

                    formatted_amount = f"${amount:,.2f}" if currency == "USD" else f"${amount:,.0f}"
                    conn.commit()
                    return True, f"¡Transferencia de {formatted_amount} {currency} a '{acc['name']}' completada con éxito!"
                except Exception as e:
                    conn.rollback()
                    return False, f"Error al transferir: {str(e)}"

    def transfer_from_investment(
        self,
        account_id: int,
        amount: float,
        date: str,
        notes: str = ""
    ) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "El monto a retirar debe ser mayor a 0."

        acc = self.get_account_by_id(account_id)
        if not acc:
            return False, "Cuenta de inversión no encontrada."

        if amount > acc["current_balance"]:
            formatted_bal = f"${acc['current_balance']:,.2f}" if acc["currency"] == "USD" else f"${acc['current_balance']:,.0f}"
            return False, f"Saldo insuficiente en '{acc['name']}' ({formatted_bal} {acc['currency']})."

        currency = acc["currency"]
        desc_notes = notes.strip() if notes else f"Retiro de {acc['name']}"

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN IMMEDIATE;")

                    if currency == "COP":
                        cursor.execute("""
                            INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                            VALUES (?, ?, 'TRANSFER_FROM_INVESTMENT', ?, 0, 'DEBIT', ?);
                        """, (date, f"Retiro Inversión: {acc['name']}", amount, desc_notes))
                        linked_tx_id = cursor.lastrowid
                        linked_table = "cop_transactions"
                    else:
                        cursor.execute("""
                            INSERT INTO usd_transactions (date, platform, type, amount, notes)
                            VALUES (?, ?, 'TRANSFER_FROM_INVESTMENT', ?, ?);
                        """, (date, f"Retiro Inversión: {acc['name']}", amount, desc_notes))
                        linked_tx_id = cursor.lastrowid
                        linked_table = "usd_transactions"

                    cursor.execute("""
                        INSERT INTO account_transactions (account_id, date, type, amount, notes, linked_tx_id, linked_table)
                        VALUES (?, ?, 'TRANSFER_OUT', ?, ?, ?, ?);
                    """, (account_id, date, amount, desc_notes, linked_tx_id, linked_table))

                    formatted_amount = f"${amount:,.2f}" if currency == "USD" else f"${amount:,.0f}"
                    conn.commit()
                    return True, f"¡Retiro de {formatted_amount} {currency} completado! Fondos acreditados en tu presupuesto."
                except Exception as e:
                    conn.rollback()
                    return False, f"Error al retirar: {str(e)}"

    def add_account_yield(
        self,
        account_id: int,
        amount: float,
        date: str,
        notes: str = ""
    ) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "El monto del rendimiento debe ser mayor a 0."

        acc = self.get_account_by_id(account_id)
        if not acc:
            return False, "Cuenta no encontrada."

        currency = acc["currency"]
        desc_notes = notes.strip() if notes else f"Rendimientos / Intereses en {acc['name']}"

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO account_transactions (account_id, date, type, amount, notes)
                    VALUES (?, ?, 'YIELD', ?, ?);
                """, (account_id, date, float(amount), desc_notes))
                conn.commit()
                formatted_amount = f"${amount:,.2f}" if currency == "USD" else f"${amount:,.0f}"
                return True, f"¡Rendimiento de +{formatted_amount} {currency} registrado en '{acc['name']}'!"

    def update_account_transaction(self, tx_id: int, date: str, amount: float, notes: str = "") -> Tuple[bool, str]:
        if amount <= 0:
            return False, "El monto debe ser mayor a 0."

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE account_transactions
                        SET date = ?, amount = ?, notes = ?
                        WHERE id = ?;
                    """, (date, float(amount), notes.strip(), tx_id))
                    conn.commit()
                    return True, "Movimiento de inversión actualizado exitosamente."
                except Exception as e:
                    return False, f"Error al actualizar: {str(e)}"

    def delete_account_transaction(self, tx_id: int, force: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, account_id, date, type, amount, notes, linked_tx_id, linked_table FROM account_transactions WHERE id = ?;", (tx_id,))
                    tx = cursor.fetchone()
                    if not tx:
                        return False, "Movimiento de inversión no encontrado.", None

                    linked_id = tx["linked_tx_id"] if "linked_tx_id" in tx.keys() else None
                    linked_tbl = tx["linked_table"] if "linked_table" in tx.keys() else None

                    cursor.execute("DELETE FROM account_transactions WHERE id = ?;", (tx_id,))
                    cursor.execute("DELETE FROM transaction_tags WHERE source_table = 'account_transactions' AND record_id = ?;", (tx_id,))

                    if linked_id and linked_tbl in ("cop_transactions", "usd_transactions"):
                        cursor.execute(f"DELETE FROM {linked_tbl} WHERE id = ?;", (linked_id,))
                        cursor.execute("DELETE FROM transaction_tags WHERE source_table = ? AND record_id = ?;", (linked_tbl, linked_id))

                    conn.commit()
                    return True, "Movimiento de inversión eliminado.", None
                except Exception as e:
                    conn.rollback()
                    return False, f"Error al eliminar: {str(e)}", None

    def get_account_transactions(self, account_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if account_id:
                cursor.execute("""
                    SELECT t.id, t.account_id, a.name as account_name, a.currency, t.date, t.type, t.amount, t.notes, t.created_at
                    FROM account_transactions t
                    JOIN accounts a ON t.account_id = a.id
                    WHERE t.account_id = ?
                    ORDER BY t.date DESC, t.id DESC
                    LIMIT ?;
                """, (account_id, limit))
            else:
                cursor.execute("""
                    SELECT t.id, t.account_id, a.name as account_name, a.currency, t.date, t.type, t.amount, t.notes, t.created_at
                    FROM account_transactions t
                    JOIN accounts a ON t.account_id = a.id
                    ORDER BY t.date DESC, t.id DESC
                    LIMIT ?;
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_investments_summary(self) -> Dict[str, Any]:
        accounts = self.get_accounts(only_active=True)
        total_cop_invested = sum(a["current_balance"] for a in accounts if a["currency"] == "COP")
        total_usd_invested = sum(a["current_balance"] for a in accounts if a["currency"] == "USD")
        total_cop_yields = sum(a["total_yields"] for a in accounts if a["currency"] == "COP")
        total_usd_yields = sum(a["total_yields"] for a in accounts if a["currency"] == "USD")

        return {
            "total_cop_invested": total_cop_invested,
            "total_usd_invested": total_usd_invested,
            "total_cop_yields": total_cop_yields,
            "total_usd_yields": total_usd_yields,
            "accounts_count": len(accounts),
            "accounts": accounts
        }
