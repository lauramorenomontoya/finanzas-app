"""
Pruebas Unitarias para el Módulo de Presupuestos & Metas Financieras.
"""

import unittest
import os
import shutil
from database.db_manager import DatabaseManager


class TestBudgetModule(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_budget_env"
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, "test_finanzas.db")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_budget_settings_and_validation(self):
        # 1. Configuración por defecto
        settings = self.db.get_budget_settings()
        self.assertEqual(settings["needs_pct"], 50.0)
        self.assertEqual(settings["savings_pct"], 15.0)
        self.assertEqual(settings["invest_pct"], 10.0)
        self.assertEqual(settings["lifestyle_pct"], 25.0)
        self.assertEqual(settings["default_moto_amount"], 150000.0)

        # 2. Validación de suma = 100%
        success, err = self.db.update_budget_settings(50.0, 20.0, 10.0, 10.0)  # suma 90%
        self.assertFalse(success)
        self.assertIn("100%", err)

        # 3. Actualización exitosa
        success, msg = self.db.update_budget_settings(45.0, 15.0, 15.0, 25.0, 180000.0)
        self.assertTrue(success)
        updated = self.db.get_budget_settings()
        self.assertEqual(updated["needs_pct"], 45.0)
        self.assertEqual(updated["default_moto_amount"], 180000.0)

    def test_monthly_targets_and_moto_provision(self):
        ym = "2026-10"
        # 1. Guardar metas
        success, msg = self.db.save_monthly_targets(
            year_month=ym,
            estimated_income_cop=5000000.0,
            moto_target_cop=150000.0,
            emergency_savings_target_cop=600000.0,
            invest_target_cop=500000.0,
            notes="Mes de prueba"
        )
        self.assertTrue(success)

        # 2. Recuperar metas
        targets = self.db.get_monthly_targets(ym)
        self.assertEqual(targets["estimated_income_cop"], 5000000.0)
        self.assertEqual(targets["moto_target_cop"], 150000.0)
        self.assertEqual(targets["emergency_savings_target_cop"], 600000.0)
        self.assertEqual(targets["invest_target_cop"], 500000.0)
        self.assertEqual(targets["notes"], "Mes de prueba")

    def test_category_budgets_and_semaphores(self):
        ym = "2026-10"
        # 1. Asignar presupuestos
        self.db.set_category_budget(ym, "Alimentación / Mercado", 800000.0, "COP", "Mercado mensual")
        self.db.set_category_budget(ym, "Restaurantes / Salidas", 300000.0, "COP")

        # 2. Registrar gastos
        self.db.add_cop_income("2026-10-01", "Nómina", 4000000.0)
        self.db.add_cop_expense("2026-10-05", "Alimentación / Mercado", 400000.0)  # 50% -> SAFE (verde)
        self.db.add_cop_expense("2026-10-06", "Restaurantes / Salidas", 250000.0)  # 83% -> WARNING (amarillo)

        cats = self.db.get_category_budgets(ym, "COP")
        cat_map = {c["category"]: c for c in cats}

        # Verificar Alimentación
        ali = cat_map["Alimentación / Mercado"]
        self.assertEqual(ali["budget"], 800000.0)
        self.assertEqual(ali["spent"], 400000.0)
        self.assertEqual(ali["remaining"], 400000.0)
        self.assertEqual(ali["status"], "SAFE")

        # Verificar Restaurantes
        rest = cat_map["Restaurantes / Salidas"]
        self.assertEqual(rest["budget"], 300000.0)
        self.assertEqual(rest["spent"], 250000.0)
        self.assertEqual(rest["remaining"], 50000.0)
        self.assertEqual(rest["status"], "WARNING")

        # Sobrepasar límite
        self.db.add_cop_expense("2026-10-10", "Restaurantes / Salidas", 100000.0)  # 350.000 > 300.000 -> OVER (rojo)
        cats2 = self.db.get_category_budgets(ym, "COP")
        cat_map2 = {c["category"]: c for c in cats2}
        self.assertEqual(cat_map2["Restaurantes / Salidas"]["status"], "OVER")
        self.assertEqual(cat_map2["Restaurantes / Salidas"]["remaining"], -50000.0)

    def test_copy_budgets_between_months(self):
        from_ym = "2026-10"
        to_ym = "2026-11"

        self.db.set_category_budget(from_ym, "Alimentación / Mercado", 850000.0, "COP")
        self.db.set_category_budget(from_ym, "Moto & Mantenimiento", 120000.0, "COP")
        self.db.save_monthly_targets(from_ym, 4500000.0, 150000.0, 500000.0, 450000.0)

        success, msg, count = self.db.copy_budgets_from_previous_month(from_ym, to_ym)
        self.assertTrue(success)
        self.assertEqual(count, 2)

        nov_cats = self.db.get_category_budgets(to_ym, "COP")
        nov_map = {c["category"]: c for c in nov_cats}
        self.assertEqual(nov_map["Alimentación / Mercado"]["budget"], 850000.0)
        self.assertEqual(nov_map["Moto & Mantenimiento"]["budget"], 120000.0)

        nov_targets = self.db.get_monthly_targets(to_ym)
        self.assertEqual(nov_targets["moto_target_cop"], 150000.0)
        self.assertEqual(nov_targets["estimated_income_cop"], 4500000.0)

    def test_safe_to_spend_calculation(self):
        ym = "2026-10"
        # 1. Ingresos: $4.000.000 COP
        self.db.add_cop_income("2026-10-01", "Honorarios", 4000000.0)

        # 2. Metas: Moto $150k, Ahorro $400k, Inversión $400k ($950k total protegidos)
        self.db.save_monthly_targets(ym, 4000000.0, 150000.0, 400000.0, 400000.0)

        # 3. Gasto Fijo pagado: $1.000.000 COP
        self.db.add_cop_expense("2026-10-02", "Arriendo / Hipoteca", 1000000.0, is_fixed=True)

        # 4. Gasto Variable pagado: $300.000 COP
        self.db.add_cop_expense("2026-10-03", "Alimentación / Mercado", 300000.0, is_fixed=False)

        overview = self.db.get_budget_overview(ym)
        # Fijos totales comprometidos >= 1.5M (por la plantilla)
        self.assertGreaterEqual(overview["total_fixed_obligations"], 1000000.0)
        self.assertEqual(overview["moto_target"], 150000.0)
        self.assertGreaterEqual(overview["actual_income"], 4000000.0)
        self.assertIn("safe_to_spend", overview)
        self.assertIn("daily_safe_budget", overview)


if __name__ == "__main__":
    unittest.main()
