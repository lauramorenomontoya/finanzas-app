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

        where_usd: List[str] = []
        params_usd: List[Any] = []
        where_cop: List[str] = []
        params_cop: List[Any] = []
        where_acc: List[str] = ["t.type = 'YIELD'"]
        params_acc: List[Any] = []

        if date_from:
            where_usd.append("date >= ?")
            params_usd.append(date_from)
            where_cop.append("date >= ?")
            params_cop.append(date_from)
            where_acc.append("t.date >= ?")
            params_acc.append(date_from)

        if date_to:
            where_usd.append("date <= ?")
            params_usd.append(date_to)
            where_cop.append("date <= ?")
            params_cop.append(date_to)
            where_acc.append("t.date <= ?")
            params_acc.append(date_to)

        # Mapeo de módulos específicos
        include_usd = True
        include_cop = True
        include_yields = True

        if module_filter and module_filter != "Todos":
            if module_filter == "Ingresos USD":
                include_usd = True
                include_cop = False
                include_yields = False
                where_usd.append("type IN ('DEPOSIT', 'TRANSFER_FROM_INVESTMENT')")
            elif module_filter == "Egresos USD":
                include_usd = True
                include_cop = False
                include_yields = False
                where_usd.append("type = 'EXPENSE'")
            elif module_filter == "Ingresos COP":
                include_usd = False
                include_cop = True
                include_yields = False
                where_cop.append("type IN ('MANUAL_INCOME', 'TRANSFER_FROM_INVESTMENT')")
            elif module_filter == "Egresos COP":
                include_usd = False
                include_cop = True
                include_yields = False
                where_cop.append("type IN ('EXPENSE', 'CC_PAYMENT')")
            elif module_filter == "Conversión":
                include_usd = True
                include_cop = True
                include_yields = False
                where_usd.append("type = 'TRANSFER_OUT'")
                where_cop.append("type = 'TRANSFER_IN'")
            elif module_filter in ("Inversiones", "Rendimientos"):
                include_usd = False
                include_cop = False
                include_yields = True
            elif module_filter == "USD":
                include_usd = True
                include_cop = False
                include_yields = False
            elif module_filter == "COP":
                include_usd = False
                include_cop = True
                include_yields = False

        usd_sql_where = f"WHERE {' AND '.join(where_usd)}" if where_usd else ""
        cop_sql_where = f"WHERE {' AND '.join(where_cop)}" if where_cop else ""
        acc_sql_where = f"WHERE {' AND '.join(where_acc)}"

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Movimientos USD
            if include_usd:
                cursor.execute(f"""
                    SELECT id, date, platform, type, amount, notes, created_at
                    FROM usd_transactions
                    {usd_sql_where};
                """, params_usd)
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
            if include_cop:
                cursor.execute(f"""
                    SELECT id, date, category, type, amount, is_fixed, payment_method, notes, created_at
                    FROM cop_transactions
                    {cop_sql_where};
                """, params_cop)
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
            if include_yields:
                cursor.execute(f"""
                    SELECT t.id, t.date, a.name as account_name, a.currency, t.type, t.amount, t.notes, t.created_at
                    FROM account_transactions t
                    JOIN accounts a ON t.account_id = a.id
                    {acc_sql_where};
                """, params_acc)
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

            # Cargar tags de los registros obtenidos
            tags_map = {}
            if ledger_entries:
                cursor.execute("""
                    SELECT tt.source_table, tt.record_id, t.id, t.name, t.color
                    FROM transaction_tags tt
                    JOIN tags t ON tt.tag_id = t.id;
                """)
                for tr in cursor.fetchall():
                    key = (tr["source_table"], tr["record_id"])
                    if key not in tags_map:
                        tags_map[key] = []
                    tags_map[key].append({"id": tr["id"], "name": tr["name"], "color": tr["color"]})

        for entry in ledger_entries:
            entry["tags"] = tags_map.get((entry["source_table"], entry["id"]), [])

        filtered = []
        q = search_query.lower().strip() if search_query else None

        for item in ledger_entries:
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
