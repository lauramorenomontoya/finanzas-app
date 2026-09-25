"""
Mixin para Gestión de Presupuesto Mensual, Metas de Ahorro/Inversión y Porcentajes Financieros.
Soporta comparativa Presupuestado vs. Real por categoría y cálculo de Dinero Seguro para Gastar.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class BudgetMixin:
    def _init_budget_tables(self):
        """Inicializa las tablas necesarias para la presupuestación y metas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Configuración de Porcentajes Financieros (Pilares)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budget_settings (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    needs_pct REAL DEFAULT 50.0,
                    savings_pct REAL DEFAULT 15.0,
                    invest_pct REAL DEFAULT 10.0,
                    lifestyle_pct REAL DEFAULT 25.0,
                    default_moto_amount REAL DEFAULT 150000.0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO budget_settings (id, needs_pct, savings_pct, invest_pct, lifestyle_pct, default_moto_amount)
                VALUES (1, 50.0, 15.0, 10.0, 25.0, 150000.0);
            """)

            # 2. Límites de Presupuesto por Categoría por Mes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS category_budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year_month TEXT NOT NULL,
                    category TEXT NOT NULL,
                    currency TEXT DEFAULT 'COP' CHECK(currency IN ('COP', 'USD')),
                    budget_amount REAL NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(year_month, category, currency)
                );
            """)

            # 3. Metas y Proyecciones Mensuales (Ahorro, Inversión, Provisión Moto e Ingreso Estimado)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year_month TEXT NOT NULL UNIQUE,
                    estimated_income_cop REAL DEFAULT 0.0,
                    estimated_income_usd REAL DEFAULT 0.0,
                    moto_target_cop REAL DEFAULT 150000.0,
                    emergency_savings_target_cop REAL DEFAULT 0.0,
                    invest_target_cop REAL DEFAULT 0.0,
                    invest_target_usd REAL DEFAULT 0.0,
                    notes TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    # ==========================================
    # CONFIGURACIÓN DE REGLAS & PORCENTAJES
    # ==========================================

    def get_budget_settings(self) -> Dict[str, float]:
        """Obtiene la configuración actual de porcentajes de los 4 pilares."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT needs_pct, savings_pct, invest_pct, lifestyle_pct, default_moto_amount FROM budget_settings WHERE id = 1;")
            row = cursor.fetchone()
            if row:
                return {
                    "needs_pct": float(row["needs_pct"]),
                    "savings_pct": float(row["savings_pct"]),
                    "invest_pct": float(row["invest_pct"]),
                    "lifestyle_pct": float(row["lifestyle_pct"]),
                    "default_moto_amount": float(row["default_moto_amount"])
                }
            return {
                "needs_pct": 50.0,
                "savings_pct": 15.0,
                "invest_pct": 10.0,
                "lifestyle_pct": 25.0,
                "default_moto_amount": 150000.0
            }

    def update_budget_settings(
        self,
        needs_pct: float,
        savings_pct: float,
        invest_pct: float,
        lifestyle_pct: float,
        default_moto_amount: float = 150000.0
    ) -> Tuple[bool, str]:
        """Actualiza los porcentajes de los 4 pilares financieros."""
        total = round(needs_pct + savings_pct + invest_pct + lifestyle_pct, 2)
        if total != 100.0:
            return False, f"La suma de los porcentajes debe ser exactamente 100% (actualmente suma {total}%)."

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE budget_settings
                    SET needs_pct = ?, savings_pct = ?, invest_pct = ?, lifestyle_pct = ?, default_moto_amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1;
                """, (needs_pct, savings_pct, invest_pct, lifestyle_pct, default_moto_amount))
                conn.commit()
                return True, "¡Reglas de distribución presupuestaria actualizadas con éxito!"

    # ==========================================
    # METAS MENSUALES (MOTO, AHORRO, INVERSIÓN)
    # ==========================================

    def get_monthly_targets(self, year_month: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene las metas de ahorro e inversión para el mes especificado."""
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        settings = self.get_budget_settings()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT estimated_income_cop, estimated_income_usd, moto_target_cop, emergency_savings_target_cop, invest_target_cop, invest_target_usd, notes
                FROM monthly_targets
                WHERE year_month = ?;
            """, (year_month,))
            row = cursor.fetchone()

            if row:
                return {
                    "year_month": year_month,
                    "estimated_income_cop": float(row["estimated_income_cop"]),
                    "estimated_income_usd": float(row["estimated_income_usd"]),
                    "moto_target_cop": float(row["moto_target_cop"]),
                    "emergency_savings_target_cop": float(row["emergency_savings_target_cop"]),
                    "invest_target_cop": float(row["invest_target_cop"]),
                    "invest_target_usd": float(row["invest_target_usd"]),
                    "notes": row["notes"] or ""
                }
            
            # Si no existe configuración específica para este mes, calcular sugerencias
            # Tomar los ingresos reales de este mes como estimación base si existen
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS actual_inc
                FROM cop_transactions
                WHERE type IN ('MANUAL_INCOME', 'TRANSFER_IN') AND strftime('%Y-%m', date) = ?;
            """, (year_month,))
            actual_inc = float(cursor.fetchone()["actual_inc"])

            # Provisión por defecto de la moto en Fiducuenta
            moto_def = settings["default_moto_amount"]

            # Si hay ingresos, sugerir montos basados en porcentajes
            savings_pct = settings["savings_pct"] / 100.0
            invest_pct = settings["invest_pct"] / 100.0

            suggested_savings = max(0.0, (actual_inc * savings_pct) - moto_def) if actual_inc > 0 else 0.0
            suggested_invest = (actual_inc * invest_pct) if actual_inc > 0 else 0.0

            return {
                "year_month": year_month,
                "estimated_income_cop": actual_inc,
                "estimated_income_usd": 0.0,
                "moto_target_cop": moto_def,
                "emergency_savings_target_cop": suggested_savings,
                "invest_target_cop": suggested_invest,
                "invest_target_usd": 0.0,
                "notes": ""
            }

    def save_monthly_targets(
        self,
        year_month: str,
        estimated_income_cop: float,
        moto_target_cop: float,
        emergency_savings_target_cop: float,
        invest_target_cop: float,
        estimated_income_usd: float = 0.0,
        invest_target_usd: float = 0.0,
        notes: str = ""
    ) -> Tuple[bool, str]:
        """Guarda o actualiza las metas del mes."""
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO monthly_targets (
                        year_month, estimated_income_cop, estimated_income_usd, moto_target_cop,
                        emergency_savings_target_cop, invest_target_cop, invest_target_usd, notes, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(year_month) DO UPDATE SET
                        estimated_income_cop = excluded.estimated_income_cop,
                        estimated_income_usd = excluded.estimated_income_usd,
                        moto_target_cop = excluded.moto_target_cop,
                        emergency_savings_target_cop = excluded.emergency_savings_target_cop,
                        invest_target_cop = excluded.invest_target_cop,
                        invest_target_usd = excluded.invest_target_usd,
                        notes = excluded.notes,
                        updated_at = CURRENT_TIMESTAMP;
                """, (
                    year_month, float(estimated_income_cop), float(estimated_income_usd),
                    float(moto_target_cop), float(emergency_savings_target_cop),
                    float(invest_target_cop), float(invest_target_usd), notes.strip()
                ))
                conn.commit()
                return True, f"¡Metas para {year_month} guardadas con éxito!"

    # ==========================================
    # LÍMITES POR CATEGORÍA (PRESUPUESTADO VS REAL)
    # ==========================================

    def get_category_budgets(self, year_month: Optional[str] = None, currency: str = "COP") -> List[Dict[str, Any]]:
        """
        Retorna la lista de todas las categorías de gasto con su límite presupuestado,
        gasto real ejecutado en el mes, saldo restante y porcentaje de uso.
        """
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        cat_type = "EXPENSE_COP" if currency == "COP" else "EXPENSE_USD"

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Obtener todas las categorías de gasto registradas
            cursor.execute("SELECT id, name, icon, color FROM categories WHERE type = ? ORDER BY name ASC;", (cat_type,))
            cat_dict = {row["name"]: dict(row) for row in cursor.fetchall()}

            # 2. Obtener presupuestos asignados para este mes
            cursor.execute("""
                SELECT category, budget_amount, notes
                FROM category_budgets
                WHERE year_month = ? AND currency = ?;
            """, (year_month, currency))
            budgets_map = {row["category"]: (float(row["budget_amount"]), row["notes"] or "") for row in cursor.fetchall()}

            # 3. Obtener gastos reales ejecutados en el mes
            if currency == "COP":
                cursor.execute("""
                    SELECT category, COALESCE(SUM(amount), 0) AS spent, COUNT(id) AS tx_count
                    FROM cop_transactions
                    WHERE type = 'EXPENSE' AND category NOT LIKE 'Ajuste%' AND strftime('%Y-%m', date) = ?
                    GROUP BY category;
                """, (year_month,))
            else:
                cursor.execute("""
                    SELECT platform AS category, COALESCE(SUM(amount), 0) AS spent, COUNT(id) AS tx_count
                    FROM usd_transactions
                    WHERE type = 'EXPENSE' AND strftime('%Y-%m', date) = ?
                    GROUP BY platform;
                """, (year_month,))

            spent_map = {row["category"]: (float(row["spent"]), int(row["tx_count"])) for row in cursor.fetchall()}

            # Unir todas las categorías: registradas en catálogo, con presupuesto asignado o con gastos ejecutados
            all_cat_names = sorted(list(set(cat_dict.keys()) | set(budgets_map.keys()) | set(spent_map.keys())))

            results = []
            for name in all_cat_names:
                cat_info = cat_dict.get(name, {"icon": "🏷️", "color": "#38bdf8"})
                budget_amt, notes = budgets_map.get(name, (0.0, ""))
                spent_amt, tx_count = spent_map.get(name, (0.0, 0))

                remaining = budget_amt - spent_amt if budget_amt > 0 else -spent_amt
                pct = (spent_amt / budget_amt * 100.0) if budget_amt > 0 else (100.0 if spent_amt > 0 else 0.0)

                # Semáforo:
                # 'SAFE' (verde < 75%)
                # 'WARNING' (amarillo 75% - 99.9%)
                # 'OVER' (rojo >= 100%)
                # 'UNBUDGETED' (si no tiene presupuesto asignado pero se gastó)
                if budget_amt <= 0:
                    status = "UNBUDGETED" if spent_amt > 0 else "NO_BUDGET"
                elif spent_amt > budget_amt:
                    status = "OVER"
                elif pct >= 75.0:
                    status = "WARNING"
                else:
                    status = "SAFE"

                results.append({
                    "category": name,
                    "icon": cat_info.get("icon", "🏷️"),
                    "color": cat_info.get("color", "#38bdf8"),
                    "budget": budget_amt,
                    "spent": spent_amt,
                    "remaining": remaining,
                    "percentage": pct,
                    "tx_count": tx_count,
                    "status": status,
                    "notes": notes
                })

            # Ordenar: primero categorías con presupuesto asignado o gastos, luego las vacías
            results.sort(key=lambda x: (x["budget"] <= 0 and x["spent"] <= 0, -x["spent"]))
            return results

    def set_category_budget(
        self,
        year_month: str,
        category: str,
        amount: float,
        currency: str = "COP",
        notes: str = ""
    ) -> Tuple[bool, str]:
        """Establece o actualiza el límite de presupuesto para una categoría en un mes."""
        if amount < 0:
            return False, "El monto del presupuesto no puede ser negativo."

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if amount == 0:
                    cursor.execute("DELETE FROM category_budgets WHERE year_month = ? AND category = ? AND currency = ?;", (year_month, category, currency))
                    conn.commit()
                    return True, f"Límite de '{category}' eliminado para {year_month}."

                cursor.execute("""
                    INSERT INTO category_budgets (year_month, category, currency, budget_amount, notes)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(year_month, category, currency) DO UPDATE SET
                        budget_amount = excluded.budget_amount,
                        notes = excluded.notes;
                """, (year_month, category, currency, float(amount), notes.strip()))
                conn.commit()
                return True, f"Límite de ${amount:,.0f} {currency} asignado a '{category}' para {year_month}."

    def copy_budgets_from_previous_month(self, from_ym: str, to_ym: str) -> Tuple[bool, str, int]:
        """Copia todos los límites de categorías y metas del mes origen al mes destino."""
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Copiar presupuestos de categorías
                cursor.execute("""
                    SELECT category, currency, budget_amount, notes
                    FROM category_budgets
                    WHERE year_month = ?;
                """, (from_ym,))
                rows = cursor.fetchall()
                if not rows:
                    return False, f"No hay presupuestos registrados en {from_ym} para copiar.", 0

                copied_count = 0
                for r in rows:
                    cursor.execute("""
                        INSERT INTO category_budgets (year_month, category, currency, budget_amount, notes)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(year_month, category, currency) DO UPDATE SET
                            budget_amount = excluded.budget_amount,
                            notes = excluded.notes;
                    """, (to_ym, r["category"], r["currency"], r["budget_amount"], r["notes"]))
                    copied_count += 1

                # Copiar metas mensuales si existen
                cursor.execute("""
                    SELECT estimated_income_cop, estimated_income_usd, moto_target_cop, emergency_savings_target_cop, invest_target_cop, invest_target_usd, notes
                    FROM monthly_targets
                    WHERE year_month = ?;
                """, (from_ym,))
                t_row = cursor.fetchone()
                if t_row:
                    cursor.execute("""
                        INSERT INTO monthly_targets (
                            year_month, estimated_income_cop, estimated_income_usd, moto_target_cop,
                            emergency_savings_target_cop, invest_target_cop, invest_target_usd, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(year_month) DO UPDATE SET
                            estimated_income_cop = excluded.estimated_income_cop,
                            estimated_income_usd = excluded.estimated_income_usd,
                            moto_target_cop = excluded.moto_target_cop,
                            emergency_savings_target_cop = excluded.emergency_savings_target_cop,
                            invest_target_cop = excluded.invest_target_cop,
                            invest_target_usd = excluded.invest_target_usd,
                            notes = excluded.notes;
                    """, (
                        to_ym, t_row["estimated_income_cop"], t_row["estimated_income_usd"],
                        t_row["moto_target_cop"], t_row["emergency_savings_target_cop"],
                        t_row["invest_target_cop"], t_row["invest_target_usd"], t_row["notes"]
                    ))

                conn.commit()
                return True, f"¡Se copiaron {copied_count} categorías y metas de {from_ym} hacia {to_ym}!", copied_count

    # ==========================================
    # CÁLCULO MAESTRO: DINERO SEGURO PARA GASTAR
    # ==========================================

    def get_budget_overview(self, year_month: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcula la visión financiera global del mes:
        - Ingresos disponibles (Reales del mes + Conversiones o Ingreso Estimado)
        - Gastos Fijos obligatorios (de la plantilla o ya pagados)
        - Provisión Moto Fiducuenta ($150.000 COP)
        - Meta de Ahorro para Imprevistos
        - Meta de Inversión (Fidurenta / Trii)
        - Total Presupuestado en Categorías Variables
        - Total Gastado Real en el mes
        - Dinero Seguro para Gastar (Safe-to-Spend) restante
        """
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        settings = self.get_budget_settings()
        targets = self.get_monthly_targets(year_month)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Ingresos reales registrados en el mes
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'MANUAL_INCOME' THEN amount ELSE 0 END), 0) AS manual_inc,
                    COALESCE(SUM(CASE WHEN type = 'TRANSFER_IN' THEN amount ELSE 0 END), 0) AS conv_inc
                FROM cop_transactions
                WHERE strftime('%Y-%m', date) = ?;
            """, (year_month,))
            inc_row = cursor.fetchone()
            actual_income = float(inc_row["manual_inc"]) + float(inc_row["conv_inc"])

            # Ingreso base para el mes: el mayor entre el estimado y el real
            estimated_income = targets.get("estimated_income_cop", 0.0)
            base_income = max(actual_income, estimated_income)

            # Si ambos son cero, tomar el saldo COP en cuenta como referencia disponible
            cop_balance = self.get_cop_balance()
            if base_income <= 0:
                base_income = cop_balance

            # 2. Gastos Fijos Obligatorios del mes
            # Tomamos la suma de los gastos fijos de la plantilla de recurring_expenses
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS fixed_sum
                FROM recurring_expenses
                WHERE currency = 'COP';
            """)
            fixed_template_sum = float(cursor.fetchone()["fixed_sum"])

            # Gastos fijos ya pagados en el mes
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS fixed_paid
                FROM cop_transactions
                WHERE is_fixed = 1 AND type = 'EXPENSE' AND strftime('%Y-%m', date) = ?;
            """, (year_month,))
            fixed_paid = float(cursor.fetchone()["fixed_paid"])

            # Compromiso de fijos total: al menos lo que está en la plantilla
            total_fixed_obligations = max(fixed_template_sum, fixed_paid)
            pending_fixed = max(0.0, total_fixed_obligations - fixed_paid)

            # 3. Metas de Ahorro e Inversión
            moto_target = targets.get("moto_target_cop", 150000.0)
            savings_target = targets.get("emergency_savings_target_cop", 0.0)
            invest_target = targets.get("invest_target_cop", 0.0)
            total_savings_and_invest = moto_target + savings_target + invest_target

            # 4. Aportes ya realizados a cuentas en el mes (Fiducuenta, Fidurenta, etc.)
            cursor.execute("""
                SELECT 
                    a.name AS account_name,
                    COALESCE(SUM(t.amount), 0) AS transferred
                FROM accounts a
                JOIN account_transactions t ON a.id = t.account_id
                WHERE a.currency = 'COP' AND t.type IN ('TRANSFER_IN', 'DEPOSIT') AND strftime('%Y-%m', t.date) = ?
                GROUP BY a.id;
            """, (year_month,))
            contributions = {row["account_name"]: float(row["transferred"]) for row in cursor.fetchall()}

            # También considerar transferencias directas en cop_transactions si no estuvieran en accounts
            cursor.execute("""
                SELECT category, COALESCE(SUM(amount), 0) AS total
                FROM cop_transactions
                WHERE type = 'TRANSFER_TO_INVESTMENT' AND strftime('%Y-%m', date) = ?
                GROUP BY category;
            """, (year_month,))
            for row in cursor.fetchall():
                cat_name = row["category"]
                amt = float(row["total"])
                matched = any(acc_name in cat_name or cat_name in acc_name for acc_name in contributions)
                if not matched:
                    contributions[cat_name] = amt
            
            moto_contributed = 0.0
            for acc_name, val in contributions.items():
                if "Fiducuenta" in acc_name:
                    moto_contributed += val
            total_invested_actual = sum(contributions.values())

            # 5. Gastos Variables Totales Presupuestados vs. Gastados
            cursor.execute("""
                SELECT COALESCE(SUM(budget_amount), 0) AS total_var_budget
                FROM category_budgets
                WHERE year_month = ? AND currency = 'COP';
            """, (year_month,))
            total_budget_assigned = float(cursor.fetchone()["total_var_budget"])

            # Gastos variables reales en el mes (no fijos)
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS var_spent
                FROM cop_transactions
                WHERE is_fixed = 0 AND type = 'EXPENSE' AND category NOT LIKE 'Ajuste%' AND strftime('%Y-%m', date) = ?;
            """, (year_month,))
            actual_var_spent = float(cursor.fetchone()["var_spent"])

            # Total de egresos reales del mes (Fijos + Variables)
            total_actual_spent = fixed_paid + actual_var_spent

            # 6. CÁLCULO DEL "DINERO SEGURO PARA GASTAR" (Safe-to-Spend)
            # Fondos Totales Disponibles del mes - Gastos Fijos Pendientes - Metas de Ahorro/Inversión Pendientes - Gastos Variables ya realizados
            pending_moto = max(0.0, moto_target - moto_contributed)
            pending_invest = max(0.0, invest_target - max(0.0, total_invested_actual - moto_contributed))
            total_protected = pending_fixed + pending_moto + savings_target + pending_invest

            # Safe-to-spend teórico restante en el mes
            safe_to_spend = max(0.0, base_income - total_fixed_obligations - total_savings_and_invest - actual_var_spent)

            # Capacidad diaria sugerida (para el resto de días del mes)
            now = datetime.now()
            current_day = now.day if now.strftime("%Y-%m") == year_month else 1
            # Días en el mes
            import calendar
            try:
                y, m = map(int, year_month.split("-"))
                _, num_days = calendar.monthrange(y, m)
            except Exception:
                num_days = 30
            days_left = max(1, num_days - current_day + 1)
            daily_safe_budget = safe_to_spend / days_left if safe_to_spend > 0 else 0.0

            # Metas teóricas de los 4 pilares según porcentajes configurados
            p1_target = base_income * (settings["needs_pct"] / 100.0)
            p2_target = base_income * (settings["savings_pct"] / 100.0)
            p3_target = base_income * (settings["invest_pct"] / 100.0)
            p4_target = base_income * (settings["lifestyle_pct"] / 100.0)

            return {
                "year_month": year_month,
                "settings": settings,
                "base_income": base_income,
                "actual_income": actual_income,
                "cop_balance": cop_balance,
                "p1_target": p1_target,
                "p2_target": p2_target,
                "p3_target": p3_target,
                "p4_target": p4_target,
                "total_fixed_obligations": total_fixed_obligations,
                "fixed_paid": fixed_paid,
                "pending_fixed": pending_fixed,
                "moto_target": moto_target,
                "moto_contributed": moto_contributed,
                "pending_moto": pending_moto,
                "savings_target": savings_target,
                "invest_target": invest_target,
                "total_savings_and_invest": total_savings_and_invest,
                "total_invested_actual": total_invested_actual,
                "total_budget_assigned": total_budget_assigned,
                "actual_var_spent": actual_var_spent,
                "total_actual_spent": total_actual_spent,
                "safe_to_spend": safe_to_spend,
                "p_savings_invest_target": p2_target + p3_target,
                "current_day": current_day,
                "total_days": num_days,
                "days_left": days_left,
                "daily_safe_budget": daily_safe_budget
            }

    def get_category_expenses_detail(self, year_month: str, category: str, currency: str = "COP") -> List[Dict[str, Any]]:
        """
        Retorna la lista detallada de compras y transacciones de una categoría para un mes específico.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if currency == "COP":
                cursor.execute("""
                    SELECT id, date, category, amount, payment_method, notes, is_fixed
                    FROM cop_transactions
                    WHERE strftime('%Y-%m', date) = ? AND category = ? AND type = 'EXPENSE'
                    ORDER BY date DESC, id DESC;
                """, (year_month, category))
            else:
                cursor.execute("""
                    SELECT id, date, platform AS category, amount, 'USD' AS payment_method, notes, 0 AS is_fixed
                    FROM usd_transactions
                    WHERE strftime('%Y-%m', date) = ? AND platform = ? AND type = 'EXPENSE'
                    ORDER BY date DESC, id DESC;
                """, (year_month, category))
            return [dict(r) for r in cursor.fetchall()]

    def auto_suggest_budgets(self, year_month: str, currency: str = "COP") -> Tuple[bool, str, int]:
        """
        Calcula y asigna presupuestos iniciales sugeridos para las categorías variables
        basado en la capacidad del 25% de dinero libre para disfrutar.
        """
        overview = self.get_budget_overview(year_month)
        p4_budget = overview["p4_target"]
        if p4_budget <= 0:
            p4_budget = 800000.0

        weights = {
            "Mercado & Supermercado": 0.35,
            "Restaurantes / Salidas": 0.20,
            "Moto & Mantenimiento": 0.15,
            "Entretenimiento & Ocio": 0.10,
            "Moda & Vestuario": 0.10,
            "Otros Gastos": 0.10,
        }

        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                count = 0
                for cat_name, weight in weights.items():
                    amt = round((p4_budget * weight) / 10000) * 10000
                    if amt > 0:
                        cursor.execute("""
                            INSERT INTO category_budgets (year_month, category, currency, budget_amount, notes)
                            VALUES (?, ?, ?, ?, 'Sugerido por regla 25%')
                            ON CONFLICT(year_month, category, currency) DO UPDATE SET
                                budget_amount = excluded.budget_amount,
                                notes = excluded.notes;
                        """, (year_month, cat_name, currency, amt))
                        count += 1
                conn.commit()
                return True, f"¡Se asignaron límites automáticos sugeridos a {count} categorías para {year_month}!", count

