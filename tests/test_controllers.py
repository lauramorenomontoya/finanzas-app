"""
Pruebas Unitarias para los Controladores de Montu (Patrón MVC).
Verifica validaciones de entrada, lógica de negocio y persistencia en:
- ExpenseController
- IncomeController
- DebtController
- LedgerController
- SettingsController
- DashboardController
- InvestmentController
"""

import unittest
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from controllers.expense_controller import ExpenseController
from controllers.income_controller import IncomeController
from controllers.debt_controller import DebtController
from controllers.ledger_controller import LedgerController
from controllers.settings_controller import SettingsController
from controllers.dashboard_controller import DashboardController
from controllers.investment_controller import InvestmentController


class TestControllers(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    # ==========================================
    # ExpenseController Tests
    # ==========================================
    def test_expense_controller_validations(self):
        ctrl = ExpenseController(self.db)

        # 1. Monto vacío
        ok, msg = ctrl.add_expense("", "Alimentación", "2026-10-15", "", False, False, "Débito", [])
        self.assertFalse(ok)
        self.assertIn("vacío", msg.lower())

        # 2. Monto inválido <= 0
        ok, msg = ctrl.add_expense("-5000", "Alimentación", "2026-10-15", "", False, False, "Débito", [])
        self.assertFalse(ok)
        self.assertIn("mayor a cero", msg.lower())

        # 3. Gasto COP válido con tag
        tag_id = self.db.add_tag("Familia", "#10b981")
        ok, msg = ctrl.add_expense("45000", "Alimentación / Mercado", "2026-10-15", "Mercado test", False, False, "Débito", [tag_id])
        self.assertTrue(ok)
        self.assertIn("éxito", msg.lower())

        # 4. Gasto USD válido
        ok, msg = ctrl.add_expense("25.50", "Software / IA", "2026-10-15", "API credit", False, True, "N/A", [])
        self.assertTrue(ok)
        self.assertIn("USD", msg)

        # 5. Balances y Categorías
        balances = ctrl.get_balances()
        self.assertIn("cop", balances)
        self.assertIn("usd", balances)

        cats_cop = ctrl.get_categories(is_usd_or_type=False)
        self.assertGreater(len(cats_cop), 0)

        cats_usd = ctrl.get_categories(is_usd_or_type=True)
        self.assertGreater(len(cats_usd), 0)

    # ==========================================
    # IncomeController Tests
    # ==========================================
    def test_income_controller_validations_and_records(self):
        ctrl = IncomeController(self.db)

        # 1. Monto vacío
        ok, msg = ctrl.add_income("", False, "Bancolombia", "Nómina", "2026-10-15", "")
        self.assertFalse(ok)
        self.assertIn("vacío", msg.lower())

        # 2. Fecha inválida
        ok, msg = ctrl.add_income("2000000", False, "Bancolombia", "Nómina", "15-10-2026", "")
        self.assertFalse(ok)
        self.assertIn("fecha inválida", msg.lower())

        # 3. Ingreso COP exitoso con plataforma en notas
        ok, msg = ctrl.add_income("3500000", False, "Bancolombia", "Nómina / Salario", "2026-10-15", "Pago quincenal")
        self.assertTrue(ok)
        self.assertIn("3,500,000", msg)

        # 4. Ingreso USD exitoso
        ok, msg = ctrl.add_income("1200.00", True, "Wenia", "Clientes Internacionales", "2026-10-15", "Factura #102")
        self.assertTrue(ok)
        self.assertIn("1,200.00", msg)
        self.assertEqual(self.db.get_usd_balance(), 1200.00)

    # ==========================================
    # DebtController Tests
    # ==========================================
    def test_debt_controller_defaults_and_normalization(self):
        ctrl = DebtController(self.db)

        # Crear deuda de prueba
        d_id = self.db.add_debt("Banco Popular", 1500000.0, "COP", "2026-10-01", "2027-10-01", debt_type="PAYABLE")
        self.assertGreater(d_id, 0)

        # 1. Llamada con defaults corregidos ("ACTIVE", "PAYABLE")
        debts = ctrl.get_debts()
        self.assertEqual(len(debts), 1)
        self.assertEqual(debts[0]["creditor"], "Banco Popular")

        # 2. Normalización de variantes en español / minúsculas
        debts_norm = ctrl.get_debts(status="activo", debt_type="pagar")
        self.assertEqual(len(debts_norm), 1)

        # 3. Summary
        summary = ctrl.get_debts_summary()
        self.assertIn("grand_total_debt", summary)
        self.assertIn("personal_payable_total", summary)

        # 4. Delete
        del_ok = ctrl.delete_debt(d_id)
        self.assertTrue(del_ok)
        self.assertEqual(len(ctrl.get_debts()), 0)

    # ==========================================
    # LedgerController Tests
    # ==========================================
    def test_ledger_controller_crud_and_security(self):
        ctrl = LedgerController(self.db)

        # 1. Registro de transacción de prueba
        tx_id = self.db.add_cop_expense("2026-10-15", "Alimentación", 50000.0)

        # 2. Fetch full record con tabla permitida
        rec = ctrl.fetch_full_record("cop_transactions", tx_id)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["amount"], 50000.0)

        # 3. Fetch con tabla no permitida (prevención de inyección)
        malicious = ctrl.fetch_full_record("sqlite_master", 1)
        self.assertIsNone(malicious)

        # 4. Unified ledger
        ledger = ctrl.get_unified_ledger(limit=10)
        self.assertGreater(len(ledger), 0)

        # 5. Delete transaction
        ok, msg, _ = ctrl.delete_transaction("cop_transactions", tx_id, force=True)
        self.assertTrue(ok)
        self.assertIsNone(ctrl.fetch_full_record("cop_transactions", tx_id))

    # ==========================================
    # SettingsController Tests
    # ==========================================
    def test_settings_controller_operations(self):
        ctrl = SettingsController(self.db)

        # 1. Export backup seguro
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as bkp:
            bkp_path = bkp.name
        try:
            ok, msg = ctrl.export_database_backup(bkp_path)
            self.assertTrue(ok)
            self.assertTrue(os.path.exists(bkp_path))
            self.assertGreater(os.path.getsize(bkp_path), 0)
        finally:
            if os.path.exists(bkp_path):
                os.remove(bkp_path)

        # 2. Categorías
        ok, msg = ctrl.add_category("Gimnasio", "EXPENSE_COP", "🏋️", "#f59e0b")
        self.assertTrue(ok)
        cats = ctrl.get_categories("EXPENSE_COP")
        gym_cat = next((c for c in cats if c["name"] == "Gimnasio"), None)
        self.assertIsNotNone(gym_cat)

        del_ok, _ = ctrl.delete_category(gym_cat["id"])
        self.assertTrue(del_ok)

        # 3. Gastos fijos (Recurring)
        ok, msg = ctrl.add_recurring_expense("Hogar", "Internet Fibra", "120000", "COP", "15")
        self.assertTrue(ok)
        recs = ctrl.get_recurring_expenses()
        self.assertTrue(any(r["description"] == "Internet Fibra" for r in recs))

    # ==========================================
    # DashboardController Tests
    # ==========================================
    def test_dashboard_controller_metrics(self):
        ctrl = DashboardController(self.db)

        # 1. TRM
        saved = ctrl.save_exchange_rate(4150.0)
        self.assertTrue(saved)
        trm = ctrl.get_latest_exchange_rate()
        self.assertEqual(trm, 4150.0)

        # 2. Resumen consolidado y deudas
        summary = ctrl.get_consolidated_summary(exchange_rate=4150.0)
        self.assertIn("cop_liquid", summary)
        self.assertIn("usd_liquid", summary)

        debts_sum = ctrl.get_debts_summary()
        self.assertIn("grand_total_debt", debts_sum)

        # 3. Categorías y presupuestos
        cats, b_map = ctrl.get_categories_breakdown_data()
        self.assertIsInstance(cats, list)
        self.assertIsInstance(b_map, dict)

        # 4. Actividades recientes
        self.db.add_cop_expense("2026-10-15", "Transporte", 15000.0)
        acts = ctrl.get_recent_activities(limit=5)
        self.assertGreater(len(acts), 0)

    # ==========================================
    # InvestmentController Tests
    # ==========================================
    def test_investment_controller_accounts(self):
        ctrl = InvestmentController(self.db)

        # 1. Crear cuenta de inversión con nombre único
        acc_id = self.db.create_account("Fiducuenta Test Controller", "COP", "INVERSION_FIDUCIA", "Bancolombia", 500000.0)
        self.assertGreater(acc_id, 0)

        # 2. Get accounts & summary
        accs = ctrl.get_accounts(currency="COP", only_active=True)
        self.assertTrue(any(a["id"] == acc_id for a in accs))

        inv_sum = ctrl.get_investments_summary()
        self.assertIn("total_cop_invested", inv_sum)


if __name__ == "__main__":
    unittest.main()
