"""
Pruebas automatizadas para las nuevas funcionalidades:
Categorías dinámicas, Plantilla de Gastos Fijos y Balance Anual.
"""

import unittest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DatabaseManager


class TestNewFeatures(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "test_features.db"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = DatabaseManager(self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_default_categories_initialized(self):
        usd_cats = self.db.get_categories("INCOME_USD")
        cop_income_cats = self.db.get_categories("INCOME_COP")
        cop_expense_cats = self.db.get_categories("EXPENSE_COP")
        self.assertTrue(any("USD" in c["name"] or "Clientes" in c["name"] for c in usd_cats))
        self.assertTrue(any("COP" in c["name"] or "Nómina" in c["name"] for c in cop_income_cats))
        self.assertTrue(any(c["name"] == "Hogar & Servicios" for c in cop_expense_cats))


    def test_category_crud(self):
        # Crear categoría personalizada
        cat_id = self.db.add_category("Cliente X", "INCOME_COP", "💼", "#10b981")
        self.assertGreater(cat_id, 0)

        # Actualizar categoría
        updated = self.db.update_category(cat_id, "Cliente X Modificado", "🚀", "#38bdf8")
        self.assertTrue(updated)

        cats = [c["name"] for c in self.db.get_categories("INCOME_COP")]
        self.assertIn("Cliente X Modificado", cats)

        # Eliminar categoría sin transacciones
        success, msg = self.db.delete_category(cat_id)
        self.assertTrue(success)

    def test_recurring_expenses_crud_and_apply(self):
        # Añadir gasto recurrente
        rec_id = self.db.add_recurring_expense("Educación / Cursos", "Curso inglés", 200000.0, 15)
        self.assertGreater(rec_id, 0)

        items = self.db.get_recurring_expenses()
        self.assertTrue(any(r["description"] == "Curso inglés" for r in items))

        # Aplicar gastos recurrentes
        count, total = self.db.apply_recurring_expenses("2026-08-20", expense_ids=[rec_id])
        self.assertEqual(count, 1)
        self.assertEqual(total, 200000.0)

        # Verificar que se creó la transacción en COP
        txs = self.db.get_cop_transactions(limit=10)
        self.assertTrue(any(t["category"] == "Educación / Cursos" and t["amount"] == 200000.0 for t in txs))

    def test_annual_overview(self):
        # Registrar movimientos
        self.db.add_usd_deposit("2026-08-01", "Wenia (SIC)", 1500.0, "Pago quincenal SIC")
        self.db.add_usd_deposit("2026-08-15", "Wenia (SIC)", 1500.0, "Pago quincenal SIC")
        self.db.execute_conversion("2026-08-16", 1000.0, 4000.0, "Retiro a Bancolombia")
        self.db.add_cop_manual_income("2026-08-10", "Invisible Work (IW)", 3500000.0, "Proyecto IW")
        self.db.add_cop_expense("2026-08-05", "Arriendo / Hipoteca", 1800000.0, is_fixed=True, notes="Arriendo")

        overview = self.db.get_annual_overview(2026)
        self.assertEqual(overview["year"], 2026)
        totals = overview["totals"]

        self.assertEqual(totals["usd_earned"], 3000.0)
        self.assertEqual(totals["usd_converted"], 1000.0)
        self.assertEqual(totals["usd_saved"], 2000.0)
        self.assertEqual(totals["cop_manual_income"], 3500000.0)
        self.assertEqual(totals["cop_from_conversions"], 4000000.0)
        self.assertEqual(totals["cop_expenses"], 1800000.0)
        self.assertEqual(totals["cop_net"], 5700000.0)


if __name__ == "__main__":
    unittest.main()
