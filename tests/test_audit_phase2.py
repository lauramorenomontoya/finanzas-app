import unittest
import os
import tempfile
import shutil
from database.db_manager import DatabaseManager
from controllers.settings_controller import SettingsController
from core.event_bus import EventBus

class TestAuditPhase2(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_phase2.db")
        self.db = DatabaseManager(self.db_path)
        EventBus.clear()

    def tearDown(self):
        EventBus.clear()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_linked_conversions_lifecycle(self):
        # Depositar en USD
        self.db.add_usd_deposit("2026-10-01", "Wenia", 500.0, "Fondeo inicial")
        usd_bal = self.db.get_usd_balance()
        self.assertEqual(usd_bal, 500.0)

        # Ejecutar conversión
        ok, msg = self.db.execute_conversion("2026-10-02", 200.0, 4000.0, "Conversión de prueba")
        self.assertTrue(ok)

        # Verificar enlace
        conversions = self.db.get_conversions()
        self.assertEqual(len(conversions), 1)
        conv = conversions[0]
        self.assertIsNotNone(conv.get("usd_tx_id"))
        self.assertIsNotNone(conv.get("cop_tx_id"))
        self.assertEqual(self.db.get_usd_balance(), 300.0)
        self.assertEqual(self.db.get_cop_balance(), 800000.0)

        # Actualizar conversión
        ok, msg = self.db.update_conversion(conv["id"], "2026-10-02", 250.0, 4000.0, "Conversión actualizada")
        self.assertTrue(ok)
        self.assertEqual(self.db.get_usd_balance(), 250.0)
        self.assertEqual(self.db.get_cop_balance(), 1000000.0)

        # Eliminar conversión
        ok, msg, warn = self.db.delete_conversion(conv["id"])
        self.assertTrue(ok)
        self.assertEqual(self.db.get_usd_balance(), 500.0)
        self.assertEqual(self.db.get_cop_balance(), 0.0)

    def test_linked_investment_transfers_lifecycle(self):
        # Crear cuenta de inversión en COP
        accounts = self.db.get_accounts()
        fidu = next(a for a in accounts if a["name"] == "Fiducuenta Bancolombia")

        # Cargar saldo en COP
        self.db.add_cop_income("2026-10-01", "Salario", 5000000.0, "Ingreso")
        self.assertEqual(self.db.get_cop_balance(), 5000000.0)

        # Transferir a inversión
        ok, msg = self.db.transfer_to_investment(fidu["id"], 1500000.0, "2026-10-02", "Aporte mensual")
        self.assertTrue(ok)
        self.assertEqual(self.db.get_cop_balance(), 3500000.0)

        # Verificar linked_tx_id y linked_table
        txs = self.db.get_account_transactions(fidu["id"])
        self.assertEqual(len(txs), 1)
        inv_tx = txs[0]
        self.assertEqual(inv_tx["amount"], 1500000.0)

        # Eliminar transacción de inversión y comprobar reversión en cop_transactions
        ok, msg, warn = self.db.delete_account_transaction(inv_tx["id"])
        self.assertTrue(ok)
        self.assertEqual(self.db.get_cop_balance(), 5000000.0)

    def test_usd_debt_lifecycle(self):
        # Crear deuda en USD
        debt_id = self.db.add_debt("Lender USA", 1000.0, currency="USD", notes="Préstamo en dólares")
        summary = self.db.get_debts_summary()
        self.assertEqual(summary["usd_payable_total"], 1000.0)
        self.assertEqual(summary["usd_payable_remaining"], 1000.0)

        # Cargar saldo en USD
        self.db.add_usd_deposit("2026-10-01", "Payoneer", 1500.0, "Fondeo")
        self.assertEqual(self.db.get_usd_balance(), 1500.0)

        # Abonar a la deuda en USD
        ok, msg = self.db.add_debt_payment(debt_id, 400.0, "2026-10-03", notes="Abono 1 USD", deduct_from_balance=True)
        self.assertTrue(ok)
        self.assertEqual(self.db.get_usd_balance(), 1100.0)

        summary = self.db.get_debts_summary()
        self.assertEqual(summary["usd_payable_paid"], 400.0)
        self.assertEqual(summary["usd_payable_remaining"], 600.0)

        # Eliminar abono y restaurar saldo USD
        payments = self.db.get_debt_payments(debt_id)
        self.assertEqual(len(payments), 1)
        ok, msg = self.db.delete_debt_payment(payments[0]["id"])
        self.assertTrue(ok)
        self.assertEqual(self.db.get_usd_balance(), 1500.0)

    def test_event_bus_resilience(self):
        executed = []

        def failing_subscriber():
            raise RuntimeError("Fallo deliberado en suscriptor")

        def successful_subscriber():
            executed.append(True)

        EventBus.subscribe("TEST_EVENT", failing_subscriber)
        EventBus.subscribe("TEST_EVENT", successful_subscriber)

        # publish no debe lanzar excepción y debe ejecutar el segundo suscriptor
        EventBus.publish("TEST_EVENT")
        self.assertEqual(len(executed), 1)
        self.assertTrue(executed[0])

    def test_settings_controller_backup_export(self):
        settings_ctrl = SettingsController(self.db)
        backup_path = os.path.join(self.test_dir, "exported_backup.db")
        ok, msg = settings_ctrl.export_database_backup(backup_path)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(backup_path))
        self.assertGreater(os.path.getsize(backup_path), 0)

if __name__ == "__main__":
    unittest.main()
