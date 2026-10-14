"""
Mixin para Gestión del Puente de Conversión (USD ➔ COP).
"""

from typing import List, Dict, Any, Optional, Tuple


class ConversionMixin:
    def execute_conversion(self, date: str, usd_amount: float, exchange_rate: float, notes: str = "") -> Tuple[bool, str]:
        if usd_amount <= 0:
            return False, "El monto en USD a retirar debe ser mayor a 0."
        if exchange_rate <= 0:
            return False, "La tasa de cambio debe ser mayor a 0."

        cop_amount = round(usd_amount * exchange_rate, 2)
        desc_notes = notes.strip() if notes else f"Retiro de ${usd_amount:,.2f} USD a tasa ${exchange_rate:,.2f} COP"

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN IMMEDIATE;")
                    
                    cursor.execute("""
                        SELECT 
                            COALESCE(SUM(CASE WHEN type IN ('DEPOSIT', 'TRANSFER_FROM_INVESTMENT') THEN amount ELSE 0 END), 0) -
                            COALESCE(SUM(CASE WHEN type IN ('TRANSFER_OUT', 'TRANSFER_TO_INVESTMENT', 'EXPENSE') THEN amount ELSE 0 END), 0) AS balance
                        FROM usd_transactions;
                    """)
                    row = cursor.fetchone()
                    current_usd_balance = float(row["balance"]) if row else 0.0

                    if usd_amount > current_usd_balance:
                        conn.rollback()
                        return False, f"Saldo insuficiente en Bóveda USD. Saldo disponible: ${current_usd_balance:,.2f} USD."

                    # 1. Registrar salida en Bóveda USD
                    cursor.execute("""
                        INSERT INTO usd_transactions (date, platform, type, amount, notes)
                        VALUES (?, 'Conversión a COP', 'TRANSFER_OUT', ?, ?);
                    """, (date, usd_amount, desc_notes))
                    usd_tx_id = cursor.lastrowid

                    # 2. Registrar entrada en Presupuesto COP
                    cursor.execute("""
                        INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                        VALUES (?, 'Conversión USD', 'TRANSFER_IN', ?, 0, 'DEBIT', ?);
                    """, (date, cop_amount, desc_notes))
                    cop_tx_id = cursor.lastrowid

                    # 3. Registrar en conversiones vinculando los IDs de transacciones generadas
                    cursor.execute("""
                        INSERT INTO conversions (date, usd_amount, exchange_rate, cop_amount, notes, usd_tx_id, cop_tx_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                    """, (date, usd_amount, exchange_rate, cop_amount, desc_notes, usd_tx_id, cop_tx_id))

                    conn.commit()
                    return True, f"¡Conversión exitosa! Se transfirieron ${cop_amount:,.0f} COP al presupuesto."
                except Exception as e:
                    conn.rollback()
                    return False, f"Error al procesar la transacción: {str(e)}"

    def update_conversion(
        self,
        conv_id: int,
        date: str,
        usd_amount: float,
        exchange_rate: float,
        notes: str = ""
    ) -> Tuple[bool, str]:
        if usd_amount <= 0 or exchange_rate <= 0:
            return False, "Monto en USD y tasa de cambio deben ser mayores a 0."

        cop_amount = round(usd_amount * exchange_rate, 2)
        desc_notes = notes.strip() if notes else f"Retiro de ${usd_amount:,.2f} USD a tasa ${exchange_rate:,.2f} COP"

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN IMMEDIATE;")

                    cursor.execute("SELECT id, usd_amount, cop_amount, notes, usd_tx_id, cop_tx_id FROM conversions WHERE id = ?;", (conv_id,))
                    old_conv = cursor.fetchone()
                    if not old_conv:
                        conn.rollback()
                        return False, "La conversión no existe."

                    old_notes = old_conv["notes"]
                    usd_tx_id = old_conv["usd_tx_id"] if "usd_tx_id" in old_conv.keys() else None
                    cop_tx_id = old_conv["cop_tx_id"] if "cop_tx_id" in old_conv.keys() else None

                    cursor.execute("""
                        UPDATE conversions
                        SET date = ?, usd_amount = ?, exchange_rate = ?, cop_amount = ?, notes = ?
                        WHERE id = ?;
                    """, (date, usd_amount, exchange_rate, cop_amount, desc_notes, conv_id))

                    if usd_tx_id:
                        cursor.execute("""
                            UPDATE usd_transactions
                            SET date = ?, amount = ?, notes = ?
                            WHERE id = ?;
                        """, (date, usd_amount, desc_notes, usd_tx_id))
                    else:
                        cursor.execute("""
                            UPDATE usd_transactions
                            SET date = ?, amount = ?, notes = ?
                            WHERE type = 'TRANSFER_OUT' AND notes = ?;
                        """, (date, usd_amount, desc_notes, old_notes))

                    if cop_tx_id:
                        cursor.execute("""
                            UPDATE cop_transactions
                            SET date = ?, amount = ?, notes = ?
                            WHERE id = ?;
                        """, (date, cop_amount, desc_notes, cop_tx_id))
                    else:
                        cursor.execute("""
                            UPDATE cop_transactions
                            SET date = ?, amount = ?, notes = ?
                            WHERE type = 'TRANSFER_IN' AND notes = ?;
                        """, (date, cop_amount, desc_notes, old_notes))

                    conn.commit()
                    return True, "Conversión y transacciones asociadas actualizadas con éxito."
                except Exception as e:
                    conn.rollback()
                    return False, f"Error al actualizar conversión: {str(e)}"

    def delete_conversion(self, conv_id: int, force: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN IMMEDIATE;")

                    cursor.execute("SELECT id, date, usd_amount, exchange_rate, cop_amount, notes, usd_tx_id, cop_tx_id FROM conversions WHERE id = ?;", (conv_id,))
                    conv = cursor.fetchone()
                    if not conv:
                        conn.rollback()
                        return False, "La conversión no existe.", None

                    cop_amt = float(conv["cop_amount"])
                    usd_amt = float(conv["usd_amount"])
                    current_cop_bal = self.get_cop_balance(conn=conn)
                    resulting_cop_bal = current_cop_bal - cop_amt

                    if resulting_cop_bal < -0.001 and not force:
                        conn.rollback()
                        warning_data = {
                            "type": "CONVERSION_COP_NEGATIVE",
                            "current_balance": current_cop_bal,
                            "amount_to_deduct": cop_amt,
                            "resulting_balance": resulting_cop_bal,
                            "currency": "COP",
                            "usd_refunded": usd_amt,
                            "description": f"Eliminar conversión del {conv['date']} (-${usd_amt:,.2f} USD ➔ +${cop_amt:,.0f} COP)"
                        }
                        return False, "WARNING_NEGATIVE_BALANCE", warning_data

                    usd_tx_id = conv["usd_tx_id"] if "usd_tx_id" in conv.keys() else None
                    cop_tx_id = conv["cop_tx_id"] if "cop_tx_id" in conv.keys() else None

                    cursor.execute("DELETE FROM conversions WHERE id = ?;", (conv_id,))

                    if usd_tx_id:
                        cursor.execute("DELETE FROM usd_transactions WHERE id = ?;", (usd_tx_id,))
                        cursor.execute("DELETE FROM transaction_tags WHERE source_table = 'usd_transactions' AND record_id = ?;", (usd_tx_id,))
                    else:
                        cursor.execute("""
                            DELETE FROM usd_transactions 
                            WHERE type = 'TRANSFER_OUT' AND (notes = ? OR (date = ? AND amount = ?));
                        """, (conv["notes"], conv["date"], usd_amt))

                    if cop_tx_id:
                        cursor.execute("DELETE FROM cop_transactions WHERE id = ?;", (cop_tx_id,))
                        cursor.execute("DELETE FROM transaction_tags WHERE source_table = 'cop_transactions' AND record_id = ?;", (cop_tx_id,))
                    else:
                        cursor.execute("""
                            DELETE FROM cop_transactions 
                            WHERE type = 'TRANSFER_IN' AND (notes = ? OR (date = ? AND amount = ?));
                        """, (conv["notes"], conv["date"], cop_amt))

                    conn.commit()
                    return True, f"Conversión eliminada. Se devolvieron +${usd_amt:,.2f} USD a la Bóveda y se descontaron -${cop_amt:,.0f} COP de tu presupuesto.", None
                except Exception as e:
                    conn.rollback()
                    return False, f"Error al eliminar conversión: {str(e)}", None

    def get_conversions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, usd_amount, exchange_rate, cop_amount, notes, usd_tx_id, cop_tx_id, created_at
                FROM conversions
                ORDER BY date DESC, id DESC
                LIMIT ?;
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_conversions_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM conversions;")
            row = cursor.fetchone()
            return int(row["total"]) if row else 0

    def get_conversions_summary(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(usd_amount), 0) AS total_usd,
                    COALESCE(SUM(cop_amount), 0) AS total_cop,
                    COALESCE(AVG(exchange_rate), 0) AS avg_rate,
                    COUNT(*) AS count
                FROM conversions;
            """)
            row = cursor.fetchone()
            return {
                "total_usd_converted": float(row["total_usd"]),
                "total_cop_injected": float(row["total_cop"]),
                "average_exchange_rate": float(row["avg_rate"]),
                "conversions_count": int(row["count"])
            }
