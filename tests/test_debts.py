"""
Pruebas Unitarias para el Módulo de Control de Deudas y Abonos.
Valida:
1. Creación, listado y edición de deudas personales.
2. Cálculo exacto de saldo restante y porcentaje pagado.
3. Registro de abonos con deducción automática del saldo disponible en COP.
4. Transición automática a estado PAID al liquidar la deuda.
5. Reversión / eliminación de abonos con restitución del saldo bancario.
6. Resumen consolidado con la Deuda de Tarjeta de Crédito.
"""

import unittest
import tempfile
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DatabaseManager


class TestDebtManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = DatabaseManager(db_path=self.temp_file.name)

        # Inyectar saldo inicial en COP para permitir abonos
        self.db.add_cop_income("2026-09-20", "Nómina", 10000000.0, "Salario")

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_add_and_get_debt(self):
        # Crear la deuda con Papá de 7,590,000 COP
        debt_id = self.db.add_debt(
            creditor="Papá",
            total_amount=7590000.0,
            currency="COP",
            start_date="2026-09-24",
            notes="Préstamo personal familiar"
        )
        self.assertGreater(debt_id, 0)

        debts = self.db.get_debts()
        self.assertEqual(len(debts), 1)
        debt = debts[0]
        self.assertEqual(debt["creditor"], "Papá")
        self.assertEqual(debt["total_amount"], 7590000.0)
        self.assertEqual(debt["total_paid"], 0.0)
        self.assertEqual(debt["remaining_amount"], 7590000.0)
        self.assertEqual(debt["percent_paid"], 0.0)
        self.assertEqual(debt["status"], "ACTIVE")

    def test_add_abono_deducts_from_cop_balance(self):
        debt_id = self.db.add_debt("Papá", 7590000.0, start_date="2026-09-24")
        initial_cop_balance = self.db.get_cop_balance()
        self.assertEqual(initial_cop_balance, 10000000.0)

        # Realizar abono de 1,000,000 COP
        success, msg = self.db.add_debt_payment(
            debt_id=debt_id,
            amount=1000000.0,
            date="2026-09-25",
            notes="Primer abono quincenal",
            deduct_from_balance=True
        )
        self.assertTrue(success)
        self.assertIn("1,000,000", msg)

        # Verificar que el saldo COP disminuyó exactamente en 1,000,000
        new_cop_balance = self.db.get_cop_balance()
        self.assertEqual(new_cop_balance, 9000000.0)

        # Verificar datos actualizados de la deuda
        debt = self.db.get_debt_by_id(debt_id)
        self.assertEqual(debt["total_paid"], 1000000.0)
        self.assertEqual(debt["remaining_amount"], 6590000.0)
        self.assertAlmostEqual(debt["percent_paid"], 13.2, places=1)
        self.assertEqual(debt["status"], "ACTIVE")
        self.assertEqual(debt["payments_count"], 1)

    def test_full_payment_settles_debt(self):
        debt_id = self.db.add_debt("Amigo Juan", 500000.0, start_date="2026-09-24")
        
        # Pagar la totalidad
        success, msg = self.db.add_debt_payment(debt_id, 500000.0, date="2026-09-25")
        self.assertTrue(success)
        self.assertIn("liquidada", msg)

        debt = self.db.get_debt_by_id(debt_id)
        self.assertEqual(debt["remaining_amount"], 0.0)
        self.assertEqual(debt["percent_paid"], 100.0)
        self.assertEqual(debt["status"], "PAID")

    def test_delete_payment_restores_balance(self):
        debt_id = self.db.add_debt("Papá", 7590000.0)
        self.db.add_debt_payment(debt_id, 2000000.0, date="2026-09-25", deduct_from_balance=True)
        self.assertEqual(self.db.get_cop_balance(), 8000000.0)

        payments = self.db.get_debt_payments(debt_id)
        self.assertEqual(len(payments), 1)
        payment_id = payments[0]["id"]

        # Eliminar el abono
        success, msg = self.db.delete_debt_payment(payment_id)
        self.assertTrue(success)

        # Saldo restituido a 10,000,000 COP
        self.assertEqual(self.db.get_cop_balance(), 10000000.0)
        debt = self.db.get_debt_by_id(debt_id)
        self.assertEqual(debt["total_paid"], 0.0)
        self.assertEqual(debt["remaining_amount"], 7590000.0)

    def test_debts_summary_consolidated_with_credit_card(self):
        # 1. Registrar deuda personal
        self.db.add_debt("Papá", 7590000.0)
        self.db.add_debt_payment(1, 590000.0)

        # 2. Registrar deuda en Tarjeta de Crédito (Gasto TC de 300,000 COP)
        self.db.add_cop_expense("2026-09-24", "Restaurantes", 300000.0, payment_method="CREDIT_CARD")
        self.assertEqual(self.db.get_credit_card_debt(), 300000.0)

        # 3. Resumen Consolidado
        summary = self.db.get_debts_summary()
        self.assertEqual(summary["personal_total"], 7590000.0)
        self.assertEqual(summary["personal_paid"], 590000.0)
        self.assertEqual(summary["personal_remaining"], 7000000.0)
        self.assertEqual(summary["credit_card_debt"], 300000.0)
        self.assertEqual(summary["grand_total_debt"], 7300000.0) # 7,000,000 + 300,000
        self.assertEqual(summary["active_debts_count"], 1)


    def test_receivable_debt_and_collection(self):
        # 1. Registrar préstamo a cobrar a Luisa
        rec_id = self.db.add_debt(
            creditor="Luisa",
            total_amount=464950.0,
            currency="COP",
            start_date="2026-09-24",
            debt_type="RECEIVABLE",
            notes="Compras con TC: Compra + Ropa deportiva"
        )
        self.assertGreater(rec_id, 0)

        # Verificar listado por debt_type
        receivables = self.db.get_debts(debt_type="RECEIVABLE")
        self.assertEqual(len(receivables), 1)
        self.assertEqual(receivables[0]["creditor"], "Luisa")
        self.assertEqual(receivables[0]["debt_type"], "RECEIVABLE")
        self.assertEqual(receivables[0]["remaining_amount"], 464950.0)

        # 2. Luisa me paga 200,000 COP
        initial_cop = self.db.get_cop_balance()
        success, msg = self.db.add_debt_payment(
            debt_id=rec_id,
            amount=200000.0,
            date="2026-09-25",
            notes="Abono recibido por transferencia",
            deduct_from_balance=True # Suma a cuenta de ahorros COP
        )
        self.assertTrue(success)
        self.assertIn("Pago recibido registrado", msg)

        # Verificar que el saldo COP aumentó en 200,000 COP
        new_cop = self.db.get_cop_balance()
        self.assertEqual(new_cop, initial_cop + 200000.0)

        # Verificar saldo restante por cobrar
        rec_debt = self.db.get_debt_by_id(rec_id)
        self.assertEqual(rec_debt["total_paid"], 200000.0)
        self.assertEqual(rec_debt["remaining_amount"], 264950.0)

        # 3. Eliminar el pago recibido revierte el ingreso
        payments = self.db.get_debt_payments(rec_id)
        self.assertEqual(len(payments), 1)
        self.db.delete_debt_payment(payments[0]["id"])
        self.assertEqual(self.db.get_cop_balance(), initial_cop)


if __name__ == "__main__":
    unittest.main()
