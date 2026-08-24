"""
Mixin para el Libro Mayor Unificado, Duplicación de Registros y Actividades Recientes.
"""

from typing import List, Dict, Any, Optional, Tuple


class LedgerMixin:
    def get_unified_ledger(
        self,
        limit: int = 200,
        module_filter: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search_query: Optional[str] = None,
        tag_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        ledger_entries: List[Dict[str, Any]] = []

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Movimientos USD
            if not module_filter or module_filter in ("Todos", "USD", "Ingresos USD", "Egresos USD"):
                cursor.execute("""
                    SELECT id, date, platform, type, amount, notes, created_at
                    FROM usd_transactions;
                """)
                for r in cursor.fetchall():
                    t = r["type"]
                    inflow = r["amount"] if t in ("DEPOSIT", "TRANSFER_FROM_INVESTMENT") else 0.0
                    outflow = r["amount"] if t in ("TRANSFER_OUT", "TRANSFER_TO_INVESTMENT", "EXPENSE") else 0.0
                    
                    if t == "DEPOSIT":
                        mod_name = "Ingresos USD"
                        extra = "Depósito"
                    elif t == "EXPENSE":
                        mod_name = "Egresos USD"
                        extra = "Gasto Directo"
                    elif t == "TRANSFER_OUT":
                        mod_name = "Conversión"
                        extra = "Retiro a COP"
                    else:
                        mod_name = "Inversión USD"
                        extra = "Transferencia Inv"

                    ledger_entries.append({
                        "id": r["id"],
                        "source_table": "usd_transactions",
                        "date": r["date"],
                        "module": mod_name,
                        "concept": r["platform"],
                        "currency": "USD",
                        "inflow": inflow,
                        "outflow": outflow,
                        "type_tag": t,
                        "extra_info": extra,
                        "notes": r["notes"] or "",
                        "created_at": r["created_at"]
                    })

            # 2. Movimientos COP
            if not module_filter or module_filter in ("Todos", "COP", "Ingresos COP", "Egresos COP"):
                cursor.execute("""
                    SELECT id, date, category, type, amount, is_fixed, payment_method, notes, created_at
                    FROM cop_transactions;
                """)
                for r in cursor.fetchall():
                    t = r["type"]
                    inflow = r["amount"] if t in ("MANUAL_INCOME", "TRANSFER_IN", "TRANSFER_FROM_INVESTMENT") else 0.0
                    outflow = r["amount"] if t in ("EXPENSE", "CC_PAYMENT", "TRANSFER_TO_INVESTMENT") else 0.0
                    
                    pm_str = "TC" if r["payment_method"] == "CREDIT_CARD" else "Débito"
                    if t == "CC_PAYMENT":
                        pm_str = "Pago Tarjeta"

                    if t == "TRANSFER_IN":
                        mod_name = "Conversión"
                    elif t in ("TRANSFER_TO_INVESTMENT", "TRANSFER_FROM_INVESTMENT"):
                        mod_name = "Inversión COP"
                    elif t in ("EXPENSE", "CC_PAYMENT"):
                        mod_name = "Egresos COP"
                    else:
                        mod_name = "Ingresos COP"

                    ledger_entries.append({
                        "id": r["id"],
                        "source_table": "cop_transactions",
                        "date": r["date"],
                        "module": mod_name,
                        "concept": r["category"],
                        "currency": "COP",
                        "inflow": inflow,
                        "outflow": outflow,
                        "type_tag": t,
                        "extra_info": pm_str,
                        "notes": r["notes"] or "",
                        "created_at": r["created_at"]
                    })

            # 3. Rendimientos en Cuentas
            if not module_filter or module_filter in ("Todos", "Inversiones", "Rendimientos"):
                cursor.execute("""
                    SELECT t.id, t.date, a.name as account_name, a.currency, t.type, t.amount, t.notes, t.created_at
                    FROM account_transactions t
                    JOIN accounts a ON t.account_id = a.id
                    WHERE t.type = 'YIELD';
                """)
                for r in cursor.fetchall():
                    ledger_entries.append({
                        "id": r["id"],
                        "source_table": "account_transactions",
                        "date": r["date"],
                        "module": "Rendimientos",
                        "concept": f"Intereses: {r['account_name']}",
                        "currency": r["currency"],
                        "inflow": r["amount"],
                        "outflow": 0.0,
                        "type_tag": "YIELD",
                        "extra_info": "Rendimiento",
                        "notes": r["notes"] or "",
                        "created_at": r["created_at"]
                    })

        # Adjuntar tags a los registros
        for entry in ledger_entries:
            entry["tags"] = self.get_tags_for_record(entry["source_table"], entry["id"]) if hasattr(self, "get_tags_for_record") else []

        filtered = []
        q = search_query.lower().strip() if search_query else None

        for item in ledger_entries:
            if date_from and item["date"] < date_from:
                continue
            if date_to and item["date"] > date_to:
                continue

            if tag_id:
                has_tag = any(t["id"] == tag_id for t in item.get("tags", []))
                if not has_tag:
                    continue

            if q:
                tag_names = " ".join([t["name"] for t in item.get("tags", [])])
                match_text = f"{item['date']} {item['module']} {item['concept']} {item['currency']} {item['notes']} {item['extra_info']} {tag_names}".lower()
                if q not in match_text:
                    continue

            filtered.append(item)

        filtered.sort(key=lambda x: (x["date"], x.get("created_at", "")), reverse=True)
        return filtered[:limit]

    def duplicate_record(
        self,
        source_table: str,
        record_id: int,
        new_date: str,
        new_amount: Optional[float] = None,
        new_notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()

                    if source_table == "usd_transactions":
                        cursor.execute("SELECT platform, type, amount, notes FROM usd_transactions WHERE id = ?;", (record_id,))
                        row = cursor.fetchone()
                        if not row:
                            return False, "Registro original no encontrado."

                        amt = new_amount if new_amount is not None else row["amount"]
                        nts = new_notes if new_notes is not None else row["notes"]

                        cursor.execute("""
                            INSERT INTO usd_transactions (date, platform, type, amount, notes)
                            VALUES (?, ?, ?, ?, ?);
                        """, (new_date, row["platform"], row["type"], amt, nts))
                        conn.commit()
                        return True, "Registro en USD duplicado exitosamente."

                    elif source_table == "cop_transactions":
                        cursor.execute("SELECT category, type, amount, is_fixed, payment_method, notes FROM cop_transactions WHERE id = ?;", (record_id,))
                        row = cursor.fetchone()
                        if not row:
                            return False, "Registro original no encontrado."

                        amt = new_amount if new_amount is not None else row["amount"]
                        nts = new_notes if new_notes is not None else row["notes"]

                        cursor.execute("""
                            INSERT INTO cop_transactions (date, category, type, amount, is_fixed, payment_method, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?);
                        """, (new_date, row["category"], row["type"], amt, row["is_fixed"], row["payment_method"], nts))
                        conn.commit()
                        return True, "Registro en COP duplicado exitosamente."

                    elif source_table == "account_transactions":
                        cursor.execute("SELECT account_id, type, amount, notes FROM account_transactions WHERE id = ?;", (record_id,))
                        row = cursor.fetchone()
                        if not row:
                            return False, "Registro original no encontrado."

                        amt = new_amount if new_amount is not None else row["amount"]
                        nts = new_notes if new_notes is not None else row["notes"]

                        cursor.execute("""
                            INSERT INTO account_transactions (account_id, date, type, amount, notes)
                            VALUES (?, ?, ?, ?, ?);
                        """, (row["account_id"], new_date, row["type"], amt, nts))
                        conn.commit()
                        return True, "Rendimiento/Movimiento duplicado exitosamente."

                    else:
                        return False, "Tabla no compatible para duplicación directa."
                except Exception as e:
                    return False, f"Error al duplicar: {str(e)}"

    def get_recent_activities(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Obtiene una lista cronológica de las últimas actividades para el dashboard."""
        activities = []
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Ingresos USD
            cursor.execute("""
                SELECT id, date, platform, type, amount, notes, created_at
                FROM usd_transactions
                ORDER BY date DESC, id DESC
                LIMIT ?;
            """, (limit,))
            for r in cursor.fetchall():
                t = r["type"]
                if t == "DEPOSIT":
                    activities.append({
                        "id": f"usd_{r['id']}",
                        "title": f"Depósito: {r['platform']}",
                        "amount_str": f"+${r['amount']:,.2f} USD",
                        "source": "Bóveda USD",
                        "date": r["date"],
                        "notes": r["notes"],
                        "color_type": "income_usd",
                        "created_at": r["created_at"]
                    })
                elif t == "EXPENSE":
                    activities.append({
                        "id": f"usd_{r['id']}",
                        "title": f"Gasto USD: {r['platform']}",
                        "amount_str": f"-${r['amount']:,.2f} USD",
                        "source": "Bóveda USD",
                        "date": r["date"],
                        "notes": r["notes"],
                        "color_type": "expense_cop",
                        "created_at": r["created_at"]
                    })
                elif t == "TRANSFER_OUT":
                    activities.append({
                        "id": f"usd_{r['id']}",
                        "title": f"Retiro (Conversión a COP)",
                        "amount_str": f"-${r['amount']:,.2f} USD",
                        "source": "Bóveda USD",
                        "date": r["date"],
                        "notes": r["notes"],
                        "color_type": "transfer_usd",
                        "created_at": r["created_at"]
                    })
                elif t == "TRANSFER_TO_INVESTMENT":
                    activities.append({
                        "id": f"usd_{r['id']}",
                        "title": f"Aporte a Inversión USD",
                        "amount_str": f"-${r['amount']:,.2f} USD",
                        "source": "Bóveda USD",
                        "date": r["date"],
                        "notes": r["notes"],
                        "color_type": "investment_out",
                        "created_at": r["created_at"]
                    })

            # 2. Movimientos COP
            cursor.execute("""
                SELECT id, date, category, type, amount, is_fixed, payment_method, notes, created_at
                FROM cop_transactions
                ORDER BY date DESC, id DESC
                LIMIT ?;
            """, (limit,))
            for r in cursor.fetchall():
                t = r["type"]
                pm = r["payment_method"]
                if t == "EXPENSE":
                    pm_badge = " (TC)" if pm == "CREDIT_CARD" else ""
                    activities.append({
                        "id": f"cop_{r['id']}",
                        "title": f"Gasto: {r['category']}{pm_badge}",
                        "amount_str": f"-${r['amount']:,.0f} COP",
                        "source": "Presupuesto COP",
                        "date": r["date"],
                        "notes": r["notes"],
                        "color_type": "expense_cop",
                        "created_at": r["created_at"]
                    })
                elif t == "MANUAL_INCOME":
                    activities.append({
                        "id": f"cop_{r['id']}",
                        "title": f"Ingreso: {r['category']}",
                        "amount_str": f"+${r['amount']:,.0f} COP",
                        "source": "Presupuesto COP",
                        "date": r["date"],
                        "notes": r["notes"],
                        "color_type": "transfer_cop",
                        "created_at": r["created_at"]
                    })
                elif t == "TRANSFER_IN":
                    activities.append({
                        "id": f"cop_{r['id']}",
                        "title": f"Inyección de Fondos (Conversión)",
                        "amount_str": f"+${r['amount']:,.0f} COP",
                        "source": "Presupuesto COP",
                        "date": r["date"],
                        "notes": r["notes"],
                        "color_type": "transfer_cop",
                        "created_at": r["created_at"]
                    })
                elif t == "CC_PAYMENT":
                    activities.append({
                        "id": f"cop_{r['id']}",
                        "title": f"Pago Tarjeta de Crédito",
                        "amount_str": f"-${r['amount']:,.0f} COP",
                        "source": "Presupuesto COP",
                        "date": r["date"],
                        "notes": r["notes"],
                        "color_type": "cc_payment",
                        "created_at": r["created_at"]
                    })

            # 3. Rendimientos en cuentas
            cursor.execute("""
                SELECT t.id, t.date, a.name as account_name, a.currency, t.type, t.amount, t.notes, t.created_at
                FROM account_transactions t
                JOIN accounts a ON t.account_id = a.id
                WHERE t.type = 'YIELD'
                ORDER BY t.date DESC, t.id DESC
                LIMIT ?;
            """, (limit,))
            for r in cursor.fetchall():
                curr = r["currency"]
                amt_str = f"+${r['amount']:,.2f} USD" if curr == "USD" else f"+${r['amount']:,.0f} COP"
                activities.append({
                    "id": f"acc_{r['id']}",
                    "title": f"Rendimiento: {r['account_name']}",
                    "amount_str": amt_str,
                    "source": "Inversión",
                    "date": r["date"],
                    "notes": r["notes"],
                    "color_type": "yield_income",
                    "created_at": r["created_at"]
                })

        activities.sort(key=lambda x: (x["date"], x.get("created_at", "")), reverse=True)
        return activities[:limit]
