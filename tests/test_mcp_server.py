"""
Pruebas Unitarias para el Servidor MCP (Model Context Protocol) de Montu.
Verifica:
- get_financial_summary
- add_expense (COP y USD, validación de montos y fechas)
- add_income (COP y USD)
- get_recent_transactions
- get_budget_status
- query_database (consultas SELECT permitidas, bloqueo de sentencias destructivas: DROP, DELETE, INSERT, etc.)
- add_debt_payment (abonos a pasivos y cuentas por cobrar)
"""

import unittest
import tempfile
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
import mcp_server


class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(db_path=self.temp_db.name)
        # Inyectar la base de datos de pruebas en el servidor MCP
        self.original_db = mcp_server.db
        mcp_server.db = self.db

    def tearDown(self):
        mcp_server.db = self.original_db
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_get_financial_summary(self):
        self.db.add_usd_deposit("2026-10-01", "Wenia", 1500.0)
        self.db.add_cop_income("2026-10-01", "Nómina", 4000000.0)

        res_str = mcp_server.get_financial_summary()
        data = json.loads(res_str)

        self.assertIn("liquidez", data)
        self.assertEqual(data["liquidez"]["boveda_usd"], 1500.0)
        self.assertEqual(data["liquidez"]["saldo_operativo_cop"], 4000000.0)

    def test_add_expense_cop_and_usd(self):
        # 1. Monto inválido
        err_res = json.loads(mcp_server.add_expense(amount=-10.0, category="Comida"))
        self.assertIn("error", err_res)

        # 2. Gasto COP
        cop_res = json.loads(mcp_server.add_expense(
            amount=50000.0,
            category="Alimentación / Mercado",
            currency="COP",
            date="2026-10-15",
            notes="Mercado semanal",
            payment_method="DEBIT"
        ))
        self.assertTrue(cop_res.get("exito"))
        self.assertEqual(cop_res["detalles"]["categoria"], "Alimentación / Mercado")

        # 3. Gasto USD
        usd_res = json.loads(mcp_server.add_expense(
            amount=20.0,
            category="Software / IA",
            currency="USD",
            date="2026-10-15",
            notes="Suscripción ChatGPT"
        ))
        self.assertTrue(usd_res.get("exito"))
        self.assertIn("USD", usd_res["detalles"]["monto"])

    def test_add_income_cop_and_usd(self):
        # 1. Ingreso COP
        cop_res = json.loads(mcp_server.add_income(
            amount=3000000.0,
            platform_or_category="Nómina / Salario",
            currency="COP",
            date="2026-10-10",
            notes="Sueldo"
        ))
        self.assertTrue(cop_res.get("exito"))
        self.assertIn("Nómina", cop_res["detalles"]["categoria"])

        # 2. Ingreso USD
        usd_res = json.loads(mcp_server.add_income(
            amount=800.0,
            platform_or_category="Wenia",
            currency="USD",
            date="2026-10-10",
            notes="Pago proyecto"
        ))
        self.assertTrue(usd_res.get("exito"))
        self.assertIn("Wenia", usd_res["detalles"]["plataforma"])

    def test_get_recent_transactions(self):
        self.db.add_cop_expense("2026-10-15", "Transporte", 12000.0)
        self.db.add_usd_deposit("2026-10-15", "Wenia", 500.0)

        res = json.loads(mcp_server.get_recent_transactions(limit=5))
        self.assertIsInstance(res, list)
        self.assertGreaterEqual(len(res), 2)

    def test_get_budget_status(self):
        from datetime import datetime
        now_ym = datetime.now().strftime("%Y-%m")
        self.db.set_category_budget(now_ym, "Alimentación / Mercado", 800000.0)
        self.db.add_cop_expense(f"{now_ym}-15", "Alimentación / Mercado", 200000.0)

        res = json.loads(mcp_server.get_budget_status())
        self.assertIn("categorias", res)
        cat = next((c for c in res["categorias"] if c["categoria"] == "Alimentación / Mercado"), None)
        self.assertIsNotNone(cat)
        self.assertEqual(cat["gastado_cop"], 200000.0)
        self.assertEqual(cat["presupuesto_cop"], 800000.0)

    def test_query_database_read_only_and_security(self):
        self.db.add_cop_income("2026-10-01", "Honorarios", 1000000.0)

        # 1. Consulta SELECT válida
        valid_res = json.loads(mcp_server.query_database("SELECT category, amount FROM cop_transactions;"))
        self.assertIn("resultados", valid_res)
        self.assertGreater(valid_res["filas_retornadas"], 0)

        # 2. Bloqueo de sentencias destructivas: DROP
        drop_res = json.loads(mcp_server.query_database("DROP TABLE cop_transactions;"))
        self.assertIn("error", drop_res)

        # 3. Bloqueo de DELETE
        del_res = json.loads(mcp_server.query_database("DELETE FROM cop_transactions WHERE id = 1;"))
        self.assertIn("error", del_res)

        # 4. Bloqueo de INSERT
        ins_res = json.loads(mcp_server.query_database("INSERT INTO cop_transactions VALUES (1, '2026-10-01', 'Test', 'EXPENSE', 10, 0, 'DEBIT', '', '');"))
        self.assertIn("error", ins_res)

        # 5. Bloqueo de UPDATE
        upd_res = json.loads(mcp_server.query_database("UPDATE cop_transactions SET amount = 999;"))
        self.assertIn("error", upd_res)

    def test_add_debt_payment(self):
        d_id = self.db.add_debt("Banco de Occidente", 1000000.0, "COP", "2026-10-01", "2027-10-01")
        self.db.add_cop_income("2026-10-01", "Fondo inicial", 500000.0)

        # Abono
        res = json.loads(mcp_server.add_debt_payment(debt_id=d_id, amount=200000.0, notes="Abono extraordinario"))
        self.assertTrue(res.get("exito"))

        # Verificar saldo restante en base de datos
        debts = self.db.get_debts()
        debt = next((d for d in debts if d["id"] == d_id), None)
        self.assertIsNotNone(debt)
        self.assertEqual(debt["remaining_amount"], 800000.0)


if __name__ == "__main__":
    unittest.main()
