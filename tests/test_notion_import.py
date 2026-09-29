"""
Pruebas Automatizadas de Importación de Datos de Notion a SQLite.
Verifica que las fechas en formato día/mes/año (DD/MM/YYYY), montos en COP,
categorías y transacciones de Notion se procesen con 100% de exactitud y sin errores.
"""

import os
import sys
import unittest
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from services.notion_importer import NotionImporter


class TestNotionImport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_finanzas.db")
        self.db = DatabaseManager(self.db_path)
        self.notion_dir = os.path.abspath("csv_notion/ExportBlock-150b2efb-d26c-44ee-b97d-e7a84a227521-Part-1/2026")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_spanish_date(self):
        """Prueba que el parser de fechas día/mes/año soporte todos los formatos de Notion."""
        # Formato texto español
        self.assertEqual(NotionImporter.parse_spanish_date("14 de agosto de 2026"), "2026-08-14")
        self.assertEqual(NotionImporter.parse_spanish_date("1 de diciembre de 2025"), "2025-12-01")
        self.assertEqual(NotionImporter.parse_spanish_date("28 de mayo de 2026"), "2026-05-28")

        # Formato día/mes/año DD/MM/YYYY
        self.assertEqual(NotionImporter.parse_spanish_date("14/08/2026"), "2026-08-14")
        self.assertEqual(NotionImporter.parse_spanish_date("01/12/2025"), "2025-12-01")

        # Formato fallback de mes
        self.assertEqual(NotionImporter.parse_spanish_date("", "Marzo 2026 (link)"), "2026-03-01")
        self.assertEqual(NotionImporter.parse_spanish_date(None, "Agosto 2026"), "2026-08-01")

        # Display format
        self.assertEqual(NotionImporter.format_display_date("2026-08-14"), "14/08/2026")

    def test_parse_currency_amount(self):
        """Prueba que el parser de montos maneje formato COP, decimales y miles latinos."""
        self.assertEqual(NotionImporter.parse_currency_amount("1.240.922,00 COP"), 1240922.0)
        self.assertEqual(NotionImporter.parse_currency_amount("71.445,00 COP"), 71445.0)
        self.assertEqual(NotionImporter.parse_currency_amount("193627.33"), 193627.33)
        self.assertEqual(NotionImporter.parse_currency_amount("-530.000,00 COP"), -530000.0)
        self.assertEqual(NotionImporter.parse_currency_amount("$ 45.000"), 45000.0)

    def test_extract_relation_name(self):
        """Prueba que los enlaces y relaciones markdown de Notion se limpien correctamente."""
        self.assertEqual(
            NotionImporter.extract_relation_name("Cuidado (2026/Categorías/Cuidado 2bcacd5f78e381e7a058c7802b661834.md)"),
            "Cuidado"
        )
        self.assertEqual(
            NotionImporter.extract_relation_name("Nómina (https://app.notion.com/p/N-mina-2bcacd5f)"),
            "Nómina"
        )

    def test_preview_import(self):
        """Prueba la vista previa sobre la carpeta real exportada de Notion."""
        if not os.path.exists(self.notion_dir):
            self.skipTest("Carpeta csv_notion no encontrada")

        preview = NotionImporter.preview_import(self.notion_dir)
        self.assertTrue(preview["success"])
        self.assertGreater(preview["total_expenses_count"], 300)
        self.assertGreater(preview["total_incomes_count"], 20)
        self.assertIn("Salud & Cuidado Personal", preview["categories_detected"])
        self.assertIn("Mercado & Supermercado", preview["categories_detected"])
        self.assertIn("Restaurantes / Salidas", preview["categories_detected"])
        self.assertIsNotNone(preview["date_min"])
        self.assertIsNotNone(preview["date_max"])

    def test_full_folder_import(self):
        """Prueba la importación real completa de todos los módulos de Notion."""
        if not os.path.exists(self.notion_dir):
            self.skipTest("Carpeta csv_notion no encontrada")

        result = NotionImporter.execute_import(self.db, self.notion_dir)
        self.assertTrue(result["success"], f"Falló importación: {result.get('error')}")
        self.assertGreaterEqual(result["imported_expenses"], 370)
        self.assertGreaterEqual(result["imported_incomes"], 25)
        self.assertGreaterEqual(result["imported_investments"], 10)

        # Validar en base de datos
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Total Gastos en cop_transactions
            cursor.execute("SELECT COUNT(*) as cnt, SUM(amount) as total FROM cop_transactions WHERE type = 'EXPENSE';")
            exp = cursor.fetchone()
            self.assertGreaterEqual(exp["cnt"], 370)
            self.assertGreater(exp["total"], 10000000)

            # 2. Total Ingresos en cop_transactions
            cursor.execute("SELECT COUNT(*) as cnt, SUM(amount) as total FROM cop_transactions WHERE type = 'MANUAL_INCOME';")
            inc = cursor.fetchone()
            self.assertGreaterEqual(inc["cnt"], 25)
            self.assertGreater(inc["total"], 5000000)

            # 3. Inversiones en account_transactions y balances de Fiducuenta
            cursor.execute("SELECT COUNT(*) as cnt FROM account_transactions;")
            inv = cursor.fetchone()
            self.assertGreaterEqual(inv["cnt"], 10)

            accounts = self.db.get_accounts(currency="COP")
            fidu_acc = next((a for a in accounts if "Fiducuenta" in a["name"]), None)
            self.assertIsNotNone(fidu_acc)
            self.assertEqual(fidu_acc["total_yields"], 208313.0)
            self.assertEqual(fidu_acc["current_balance"], 752440.0)

            # 4. Categorías canónicas auto-creadas
            cursor.execute("SELECT name FROM categories;")
            cats = [r["name"] for r in cursor.fetchall()]
            self.assertIn("Salud & Cuidado Personal", cats)
            self.assertIn("Mercado & Supermercado", cats)
            self.assertIn("Moto & Mantenimiento", cats)
            self.assertIn("Restaurantes / Salidas", cats)

    def test_deduplication_prevention(self):
        """Prueba que ejecutar la importación dos veces consecutivas no genere registros duplicados."""
        if not os.path.exists(self.notion_dir):
            self.skipTest("Carpeta csv_notion no encontrada")

        res1 = NotionImporter.execute_import(self.db, self.notion_dir)
        total1 = res1["imported_total"]

        # Segunda ejecución inmediata
        res2 = NotionImporter.execute_import(self.db, self.notion_dir)
        # La segunda ejecución debe omitir (skip) todos los registros ya existentes
        self.assertEqual(res2["imported_total"], 0)
        self.assertGreater(res2["skipped"], 300)


if __name__ == "__main__":
    unittest.main()
