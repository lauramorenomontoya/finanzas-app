"""
Mixin para Cálculos de Analítica, Balance General y Patrimonio Neto Global.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional


class AnalyticsMixin:
    def get_global_net_worth(self, exchange_rate: float = 3100.0) -> Dict[str, Any]:
        """
        Calcula el Patrimonio Neto Global Consolidado:
        Activos COP + (Activos USD convertidos a TRM) - Pasivos (Deuda TC).
        """
        cop_liquid = self.get_cop_balance()
        usd_vault = self.get_usd_balance()
        inv_summary = self.get_investments_summary()
        
        cop_invested = inv_summary["total_cop_invested"]
        usd_invested = inv_summary["total_usd_invested"]
        cc_debt = self.get_credit_card_debt()

        total_cop_assets = cop_liquid + cop_invested
        total_usd_assets = usd_vault + usd_invested
        total_usd_in_cop = total_usd_assets * exchange_rate

        total_gross_assets_cop = total_cop_assets + total_usd_in_cop
        net_worth_cop = total_gross_assets_cop - cc_debt
        net_worth_usd = net_worth_cop / exchange_rate if exchange_rate > 0 else 0.0

        return {
            "exchange_rate": exchange_rate,
            "cop_liquid": cop_liquid,
            "cop_invested": cop_invested,
            "total_cop_assets": total_cop_assets,
            "usd_vault": usd_vault,
            "usd_invested": usd_invested,
            "total_usd_assets": total_usd_assets,
            "total_usd_in_cop": total_usd_in_cop,
            "total_liabilities_cop": cc_debt,
            "net_worth_cop": net_worth_cop,
            "net_worth_usd": net_worth_usd
        }

    def get_monthly_metrics(self, year_month: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene métricas clave consolidadas para el dashboard."""
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # USD Ingresos y Egresos del mes
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'DEPOSIT' THEN amount ELSE 0 END), 0) as deposits,
                    COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) as expenses,
                    COALESCE(SUM(CASE WHEN type = 'TRANSFER_OUT' THEN amount ELSE 0 END), 0) as conversions
                FROM usd_transactions
                WHERE strftime('%Y-%m', date) = ?;
            """, (year_month,))
            usd_row = cursor.fetchone()

            # COP Ingresos y Gastos del mes
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) as total_expenses,
                    COALESCE(SUM(CASE WHEN type = 'EXPENSE' AND payment_method IN ('DEBIT', 'CASH') THEN amount ELSE 0 END), 0) as cash_debit_expenses,
                    COALESCE(SUM(CASE WHEN type = 'EXPENSE' AND payment_method = 'CREDIT_CARD' THEN amount ELSE 0 END), 0) as cc_expenses,
                    COALESCE(SUM(CASE WHEN type IN ('MANUAL_INCOME', 'TRANSFER_IN') THEN amount ELSE 0 END), 0) as total_income
                FROM cop_transactions
                WHERE strftime('%Y-%m', date) = ?;
            """, (year_month,))
            cop_row = cursor.fetchone()

            return {
                "usd_deposits": float(usd_row["deposits"]),
                "usd_expenses": float(usd_row["expenses"]),
                "usd_conversions": float(usd_row["conversions"]),
                "cop_total_expenses": float(cop_row["total_expenses"]),
                "cop_cash_debit_expenses": float(cop_row["cash_debit_expenses"]),
                "cop_cc_expenses": float(cop_row["cc_expenses"]),
                "cop_total_income": float(cop_row["total_income"])
            }

    def get_latest_exchange_rate(self) -> float:
        """
        Obtiene la TRM oficial de referencia más reciente:
        1. Consulta la TRM oficial guardada en caché (app_settings).
        2. Si no hay, consulta la tasa de la última conversión registrada.
        3. Si ninguna existe, retorna 3350.0 como valor base de mercado.
        """
        try:
            cached = self.get_setting("official_trm")
            if cached:
                val = float(cached)
                if val > 0:
                    return val
        except Exception:
            pass

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT exchange_rate FROM conversions ORDER BY date DESC, id DESC LIMIT 1;")
            row = cursor.fetchone()
            if row and row["exchange_rate"]:
                return float(row["exchange_rate"])
        return 3350.0

    def get_consolidated_monthly_summary(
        self,
        year_month: Optional[str] = None,
        exchange_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula el resumen financiero consolidado multimoneda del mes:
        - Ingresos reales totales generados (COP directos + USD a tasa de cambio/TRM)
        - Egresos totales reales (COP + USD)
        - Resultado neto del mes (Superávit / Déficit) y % de ahorro
        - Liquidez inmediata real (Saldo COP + Saldo líquido USD valorizado en COP)
        - Detección de compras extraordinarias de activos
        """
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        if not exchange_rate or exchange_rate <= 0:
            exchange_rate = self.get_latest_exchange_rate()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. USD en el mes
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'DEPOSIT' THEN amount ELSE 0 END), 0) AS deposits,
                    COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS expenses,
                    COALESCE(SUM(CASE WHEN type = 'TRANSFER_OUT' THEN amount ELSE 0 END), 0) AS conversions_out,
                    COALESCE(SUM(CASE WHEN type = 'TRANSFER_TO_INVESTMENT' THEN amount ELSE 0 END), 0) AS invested_out
                FROM usd_transactions
                WHERE strftime('%Y-%m', date) = ?;
            """, (year_month,))
            usd_row = cursor.fetchone()
            usd_income = float(usd_row["deposits"])
            usd_expenses = float(usd_row["expenses"])
            usd_converted = float(usd_row["conversions_out"])
            usd_invested = float(usd_row["invested_out"])

            # 2. COP en el mes (Ingresos directos vs conversiones)
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'MANUAL_INCOME' THEN amount ELSE 0 END), 0) AS manual_income,
                    COALESCE(SUM(CASE WHEN type = 'TRANSFER_IN' THEN amount ELSE 0 END), 0) AS from_conversion
                FROM cop_transactions
                WHERE strftime('%Y-%m', date) = ?;
            """, (year_month,))
            cop_inc_row = cursor.fetchone()
            cop_direct_income = float(cop_inc_row["manual_income"])
            cop_from_conversion = float(cop_inc_row["from_conversion"])

            # 3. Egresos COP del mes
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS total_expenses,
                    COALESCE(SUM(CASE WHEN is_fixed = 1 AND type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS fixed_expenses,
                    COALESCE(SUM(CASE WHEN is_fixed = 0 AND type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS var_expenses,
                    COALESCE(SUM(CASE WHEN payment_method = 'CREDIT_CARD' AND type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS cc_expenses,
                    COALESCE(SUM(CASE WHEN payment_method IN ('DEBIT', 'CASH') AND type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS debit_expenses
                FROM cop_transactions
                WHERE strftime('%Y-%m', date) = ?;
            """, (year_month,))
            cop_exp_row = cursor.fetchone()
            cop_expenses = float(cop_exp_row["total_expenses"])
            cop_fixed = float(cop_exp_row["fixed_expenses"])
            cop_var = float(cop_exp_row["var_expenses"])
            cop_cc = float(cop_exp_row["cc_expenses"])
            cop_debit = float(cop_exp_row["debit_expenses"])

            # 4. Saldos líquidos actuales
            cop_liquid = self.get_cop_balance()
            usd_liquid = self.get_usd_balance()
            usd_liquid_in_cop = usd_liquid * exchange_rate
            net_immediate_liquidity = cop_liquid + usd_liquid_in_cop

            # 5. Consolidación de ingresos y egresos
            usd_income_in_cop = usd_income * exchange_rate
            total_consolidated_income = cop_direct_income + usd_income_in_cop
            total_consolidated_expenses = cop_expenses + (usd_expenses * exchange_rate)
            net_monthly_result = total_consolidated_income - total_consolidated_expenses
            is_positive = net_monthly_result >= 0

            # 6. Detección de compras extraordinarias mayores a $1.500.000 COP
            cursor.execute("""
                SELECT category, amount, notes
                FROM cop_transactions
                WHERE type = 'EXPENSE' AND amount >= 1500000 AND strftime('%Y-%m', date) = ?
                ORDER BY amount DESC;
            """, (year_month,))
            extraordinary_purchases = [dict(r) for r in cursor.fetchall()]
            extraordinary_sum = sum(p["amount"] for p in extraordinary_purchases)
            routine_expenses = max(0.0, total_consolidated_expenses - extraordinary_sum)

            return {
                "year_month": year_month,
                "exchange_rate": exchange_rate,
                "cop_direct_income": cop_direct_income,
                "cop_from_conversion": cop_from_conversion,
                "usd_income": usd_income,
                "usd_income_in_cop": usd_income_in_cop,
                "total_consolidated_income": total_consolidated_income,
                "cop_expenses": cop_expenses,
                "cop_fixed": cop_fixed,
                "cop_var": cop_var,
                "cop_cc": cop_cc,
                "cop_debit": cop_debit,
                "usd_expenses": usd_expenses,
                "total_consolidated_expenses": total_consolidated_expenses,
                "net_monthly_result": net_monthly_result,
                "is_positive": is_positive,
                "cop_liquid": cop_liquid,
                "usd_liquid": usd_liquid,
                "usd_liquid_in_cop": usd_liquid_in_cop,
                "net_immediate_liquidity": net_immediate_liquidity,
                "extraordinary_purchases": extraordinary_purchases,
                "extraordinary_sum": extraordinary_sum,
                "routine_expenses": routine_expenses
            }

    def get_annual_overview(self, year: Optional[int] = None) -> Dict[str, Any]:
        """Obtiene resumen de flujo mensual y anualizado para analítica."""
        if not year:
            year = datetime.now().year

        months_data = []
        month_names = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

        total_usd_earned = 0.0
        total_usd_spent = 0.0
        total_usd_converted = 0.0
        total_cop_manual_income = 0.0
        total_cop_from_conversions = 0.0
        total_cop_expenses = 0.0
        total_cop_fixed_expenses = 0.0
        total_cop_var_expenses = 0.0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            for m in range(1, 13):
                ym = f"{year:04d}-{m:02d}"

                # USD Data
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type = 'DEPOSIT' THEN amount ELSE 0 END), 0) AS deposits,
                        COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS expenses,
                        COALESCE(SUM(CASE WHEN type = 'TRANSFER_OUT' THEN amount ELSE 0 END), 0) AS conversions
                    FROM usd_transactions
                    WHERE strftime('%Y-%m', date) = ?;
                """, (ym,))
                usd_row = cursor.fetchone()
                m_usd_income = float(usd_row["deposits"])
                m_usd_spent = float(usd_row["expenses"])
                m_usd_converted = float(usd_row["conversions"])

                # COP Data
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type = 'MANUAL_INCOME' THEN amount ELSE 0 END), 0) AS manual_income,
                        COALESCE(SUM(CASE WHEN type = 'TRANSFER_IN' THEN amount ELSE 0 END), 0) AS from_conversion
                    FROM cop_transactions
                    WHERE strftime('%Y-%m', date) = ?;
                """, (ym,))
                inc_row = cursor.fetchone()
                m_cop_manual = float(inc_row["manual_income"])
                m_cop_from_conversion = float(inc_row["from_conversion"])

                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN is_fixed = 1 THEN amount ELSE 0 END), 0) AS fixed_tot,
                        COALESCE(SUM(CASE WHEN is_fixed = 0 AND type = 'EXPENSE' THEN amount ELSE 0 END), 0) AS var_tot,
                        COALESCE(SUM(amount), 0) AS total_exp
                    FROM cop_transactions
                    WHERE type = 'EXPENSE' AND strftime('%Y-%m', date) = ?;
                """, (ym,))
                exp_row = cursor.fetchone()
                m_cop_fixed = float(exp_row["fixed_tot"])
                m_cop_var = float(exp_row["var_tot"])
                m_cop_exp = float(exp_row["total_exp"])

                m_cop_total_inflow = m_cop_manual + m_cop_from_conversion
                m_cop_net = m_cop_total_inflow - m_cop_exp
                m_usd_saved = m_usd_income - (m_usd_converted + m_usd_spent)

                total_usd_earned += m_usd_income
                total_usd_spent += m_usd_spent
                total_usd_converted += m_usd_converted
                total_cop_manual_income += m_cop_manual
                total_cop_from_conversions += m_cop_from_conversion
                total_cop_expenses += m_cop_exp
                total_cop_fixed_expenses += m_cop_fixed
                total_cop_var_expenses += m_cop_var

                months_data.append({
                    "month": m,
                    "month_name": month_names[m - 1],
                    "usd_income": m_usd_income,
                    "usd_spent": m_usd_spent,
                    "usd_converted": m_usd_converted,
                    "usd_saved": m_usd_saved,
                    "cop_manual_income": m_cop_manual,
                    "cop_from_conversion": m_cop_from_conversion,
                    "cop_total_income": m_cop_total_inflow,
                    "cop_fixed_expenses": m_cop_fixed,
                    "cop_var_expenses": m_cop_var,
                    "cop_expenses": m_cop_exp,
                    "cop_net": m_cop_net
                })

        total_cop_inflow = total_cop_manual_income + total_cop_from_conversions
        total_cop_net = total_cop_inflow - total_cop_expenses
        total_usd_saved_annual = total_usd_earned - (total_usd_converted + total_usd_spent)
        savings_rate_usd = (total_usd_saved_annual / total_usd_earned * 100) if total_usd_earned > 0 else 0.0

        return {
            "year": year,
            "months": months_data,
            "totals": {
                "usd_earned": total_usd_earned,
                "usd_spent": total_usd_spent,
                "usd_converted": total_usd_converted,
                "usd_saved": total_usd_saved_annual,
                "usd_savings_rate": savings_rate_usd,
                "cop_manual_income": total_cop_manual_income,
                "cop_from_conversions": total_cop_from_conversions,
                "cop_total_inflow": total_cop_inflow,
                "cop_fixed_expenses": total_cop_fixed_expenses,
                "cop_var_expenses": total_cop_var_expenses,
                "cop_expenses": total_cop_expenses,
                "cop_net": total_cop_net
            }
        }

    def get_monthly_net_worth_history(self, year: Optional[int] = None, exchange_rate: float = 3100.0) -> List[Dict[str, Any]]:
        """Calcula la evolución del patrimonio neto mes a mes para graficar tendencias."""
        if not year:
            year = datetime.now().year

        month_names = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        history = []

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for m in range(1, 13):
                cutoff_date = f"{year:04d}-{m:02d}-31"

                # Balance acumulado USD hasta ese mes
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type IN ('DEPOSIT', 'TRANSFER_FROM_INVESTMENT') THEN amount ELSE 0 END), 0) -
                        COALESCE(SUM(CASE WHEN type IN ('TRANSFER_OUT', 'TRANSFER_TO_INVESTMENT', 'EXPENSE') THEN amount ELSE 0 END), 0) AS bal
                    FROM usd_transactions
                    WHERE date <= ?;
                """, (cutoff_date,))
                usd_bal = float(cursor.fetchone()["bal"])

                # Balance acumulado COP hasta ese mes
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type IN ('TRANSFER_IN', 'MANUAL_INCOME', 'TRANSFER_FROM_INVESTMENT') THEN amount ELSE 0 END), 0) -
                        COALESCE(SUM(CASE 
                            WHEN type = 'EXPENSE' AND payment_method IN ('DEBIT', 'CASH') THEN amount 
                            WHEN type IN ('CC_PAYMENT', 'TRANSFER_TO_INVESTMENT') THEN amount
                            ELSE 0 
                        END), 0) AS bal
                    FROM cop_transactions
                    WHERE date <= ?;
                """, (cutoff_date,))
                cop_bal = float(cursor.fetchone()["bal"])

                # Deuda TC hasta ese mes
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type = 'EXPENSE' AND payment_method = 'CREDIT_CARD' THEN amount ELSE 0 END), 0) -
                        COALESCE(SUM(CASE WHEN type = 'CC_PAYMENT' THEN amount ELSE 0 END), 0) AS debt
                    FROM cop_transactions
                    WHERE date <= ?;
                """, (cutoff_date,))
                debt = max(0.0, float(cursor.fetchone()["debt"]))

                # Inversiones hasta ese mes
                cursor.execute("""
                    SELECT 
                        a.currency,
                        a.initial_balance,
                        COALESCE(SUM(CASE WHEN t.type IN ('DEPOSIT', 'TRANSFER_IN', 'YIELD') THEN t.amount ELSE 0 END), 0) -
                        COALESCE(SUM(CASE WHEN t.type IN ('WITHDRAWAL', 'TRANSFER_OUT') THEN t.amount ELSE 0 END), 0) AS tx_bal
                    FROM accounts a
                    LEFT JOIN account_transactions t ON a.id = t.account_id AND t.date <= ?
                    GROUP BY a.id;
                """, (cutoff_date,))
                
                inv_cop = 0.0
                inv_usd = 0.0
                for r in cursor.fetchall():
                    acc_bal = float(r["initial_balance"] or 0) + float(r["tx_bal"] or 0)
                    if r["currency"] == "COP":
                        inv_cop += acc_bal
                    else:
                        inv_usd += acc_bal

                total_cop = cop_bal + inv_cop
                total_usd = usd_bal + inv_usd
                net_worth_cop = total_cop + (total_usd * exchange_rate) - debt

                history.append({
                    "month": m,
                    "month_name": month_names[m - 1],
                    "cop_balance": cop_bal,
                    "usd_balance": usd_bal,
                    "net_worth_cop": net_worth_cop,
                    "net_worth_usd": net_worth_cop / exchange_rate if exchange_rate > 0 else 0
                })

        return history
