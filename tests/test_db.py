"""
Pruebas Unitarias Automatizadas para Montu (Multimoneda USD/COP).
Valida Ingresos, Egresos, Gastos Fijos Multimoneda en Checklist, Edición de Gastos Fijos (update_recurring_expense),
TRM en vivo desde APIs gratuitas (open.er-api.com / exchangerate-api.com), CRUD de Categorías y Patrimonio Neto.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import tempfile
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DatabaseManager
from services.currency_service import CurrencyService


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = DatabaseManager(db_path=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_incomes_multicurrency(self):
        # 1. Registrar Ingreso USD
        self.db.add_usd_deposit("2026-08-01", "Clientes Internacionales", 1200.0, "Honorarios")
        self.assertEqual(self.db.get_usd_balance(), 1200.0)

        # 2. Registrar Ingreso COP
        self.db.add_cop_income("2026-08-01", "Clientes Locales", 4500000.0, "Consultoría")
        self.assertEqual(self.db.get_cop_balance(), 4500000.0)

        # 3. Resumen de Ingresos
        summary = self.db.get_incomes_summary("2026-08")
        self.assertEqual(summary["total_usd"], 1200.0)
        self.assertEqual(summary["total_cop"], 4500000.0)

    def test_expenses_and_credit_card(self):
        # Inyectar saldo COP
        self.db.add_cop_income("2026-08-01", "Clientes Locales", 5000000.0)
        self.db.add_usd_deposit("2026-08-01", "Clientes Internacionales", 1000.0)

        # Gasto Débito COP
        self.db.add_cop_expense("2026-08-02", "Arriendo / Hipoteca", 1500000.0, is_fixed=True, payment_method="DEBIT")
        self.assertEqual(self.db.get_cop_balance(), 3500000.0)

        # Gasto Directo USD
        self.db.add_usd_expense("2026-08-02", "Software / IA (ChatGPT, Claude)", 20.0, "ChatGPT Plus")
        self.assertEqual(self.db.get_usd_balance(), 980.0)

        # Gasto con TC
        self.db.add_cop_expense("2026-08-03", "Alimentación / Mercado", 300000.0, payment_method="CREDIT_CARD")
        self.assertEqual(self.db.get_credit_card_debt(), 300000.0)

        # Pago de TC
        success, _ = self.db.pay_credit_card("2026-08-05", 300000.0)
        self.assertTrue(success)
        self.assertEqual(self.db.get_credit_card_debt(), 0.0)
        self.assertEqual(self.db.get_cop_balance(), 3200000.0)

    def test_recurring_expenses_multicurrency_checklist(self):
        # 1. Crear gasto fijo recurrente en USD
        rec_usd_id = self.db.add_recurring_expense("Software / IA", "Claude Pro", 20.0, currency="USD", due_day=5)
        self.assertIsNotNone(rec_usd_id)

        # 2. Consultar checklist del mes
        checklist = self.db.get_recurring_checklist_status("2026-08")
        usd_items = [i for i in checklist if i["currency"] == "USD"]
        self.assertTrue(len(usd_items) >= 1)

        # 3. Pagar el ítem en USD
        claude_item = [i for i in checklist if i["id"] == rec_usd_id][0]
        self.assertFalse(claude_item["is_paid"])

        success, msg, tx_id = self.db.pay_recurring_item(rec_usd_id, "2026-08-05")
        self.assertTrue(success)
        self.assertIsNotNone(tx_id)

        # 4. Verificar que se registre en usd_transactions y marque el checklist como pagado
        checklist_updated = self.db.get_recurring_checklist_status("2026-08")
        updated_item = [i for i in checklist_updated if i["id"] == rec_usd_id][0]
        self.assertTrue(updated_item["is_paid"])
        self.assertEqual(updated_item["tx_id"], tx_id)

        # 5. Desmarcar el pago en USD
        success, msg = self.db.unpay_recurring_item(tx_id, currency="USD")
        self.assertTrue(success)

    def test_recurring_expenses_same_category_individual_selection(self):
        # 1. Crear múltiples gastos fijos en la misma categoría (COP)
        id_agua = self.db.add_recurring_expense("Hogar", "Agua", 50000.0, currency="COP", due_day=5)
        id_luz = self.db.add_recurring_expense("Hogar", "Luz", 100000.0, currency="COP", due_day=10)
        id_gas = self.db.add_recurring_expense("Hogar", "Gas", 30000.0, currency="COP", due_day=15)

        ym = "2026-09"
        # 2. Inicialmente todos deben estar pendientes
        checklist = {i["id"]: i for i in self.db.get_recurring_checklist_status(ym)}
        self.assertFalse(checklist[id_agua]["is_paid"])
        self.assertFalse(checklist[id_luz]["is_paid"])
        self.assertFalse(checklist[id_gas]["is_paid"])

        # 3. Pagar únicamente 'Agua'
        success, _, tx_agua = self.db.pay_recurring_item(id_agua, f"{ym}-05")
        self.assertTrue(success)

        # 4. Verificar que SOLO 'Agua' está marcado como pagado
        checklist = {i["id"]: i for i in self.db.get_recurring_checklist_status(ym)}
        self.assertTrue(checklist[id_agua]["is_paid"])
        self.assertEqual(checklist[id_agua]["tx_id"], tx_agua)
        self.assertFalse(checklist[id_luz]["is_paid"], "Luz no debería marcarse pagada al pagar Agua")
        self.assertIsNone(checklist[id_luz]["tx_id"])
        self.assertFalse(checklist[id_gas]["is_paid"], "Gas no debería marcarse pagada al pagar Agua")
        self.assertIsNone(checklist[id_gas]["tx_id"])

        # 5. Pagar 'Luz'
        success, _, tx_luz = self.db.pay_recurring_item(id_luz, f"{ym}-10")
        self.assertTrue(success)
        self.assertNotEqual(tx_agua, tx_luz)

        checklist = {i["id"]: i for i in self.db.get_recurring_checklist_status(ym)}
        self.assertTrue(checklist[id_agua]["is_paid"])
        self.assertTrue(checklist[id_luz]["is_paid"])
        self.assertFalse(checklist[id_gas]["is_paid"])
        self.assertEqual(checklist[id_luz]["tx_id"], tx_luz)

        # 6. Desmarcar 'Agua' individualmente
        success, _ = self.db.unpay_recurring_item(tx_agua, currency="COP")
        self.assertTrue(success)

        # 7. Verificar que SOLO 'Agua' volvió a pendiente, y 'Luz' permanece pagada
        checklist = {i["id"]: i for i in self.db.get_recurring_checklist_status(ym)}
        self.assertFalse(checklist[id_agua]["is_paid"], "Agua debe volver a pendiente")
        self.assertTrue(checklist[id_luz]["is_paid"], "Luz debe seguir pagada después de desmarcar Agua")
        self.assertFalse(checklist[id_gas]["is_paid"])

    def test_edit_recurring_expense(self):
        # 1. Crear gasto fijo
        rec_id = self.db.add_recurring_expense("Servicios Públicos", "Internet Fibra", 120000.0, currency="COP", due_day=10)
        self.assertIsNotNone(rec_id)

        # 2. Modificarlo
        updated = self.db.update_recurring_expense(
            rec_id=rec_id,
            category="Servicios Públicos",
            description="Internet Fibra Óptica 500MB",
            amount=135000.0,
            currency="COP",
            due_day=15
        )
        self.assertTrue(updated)

        # 3. Validar cambios
        items = self.db.get_recurring_expenses()
        item = [i for i in items if i["id"] == rec_id][0]
        self.assertEqual(item["description"], "Internet Fibra Óptica 500MB")
        self.assertEqual(item["amount"], 135000.0)
        self.assertEqual(item["due_day"], 15)

    @patch("urllib.request.urlopen")
    def test_currency_service_live_rate(self, mock_urlopen):
        # Desacoplado de red externa mediante mock de respuesta JSON
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps([{"valor": "4150.50"}]).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        rate = CurrencyService.get_live_usd_to_cop_rate(timeout=1.0)
        self.assertIsNotNone(rate)
        self.assertEqual(rate, 4150.50)

    def test_categories_crud(self):
        # 1. Crear categoría
        cat_id = self.db.add_category("Diseño UI/UX", "INCOME_USD", "🎨", "#ec4899")
        self.assertIsNotNone(cat_id)

        # 2. Editar categoría
        success = self.db.update_category(cat_id, "Diseño de Producto UI/UX", "✨", "#a855f7")
        self.assertTrue(success)

        # 3. Consultar y verificar
        cats = self.db.get_categories("INCOME_USD")
        d_cat = [c for c in cats if c["id"] == cat_id][0]
        self.assertEqual(d_cat["name"], "Diseño de Producto UI/UX")
        self.assertEqual(d_cat["icon"], "✨")
        self.assertEqual(d_cat["color"], "#a855f7")

        # 4. Eliminar categoría
        success, msg = self.db.delete_category(cat_id)
        self.assertTrue(success)

    def test_global_net_worth_with_default_trm_3100(self):
        self.db.add_cop_income("2026-08-01", "Honorarios", 3100000.0)
        self.db.add_usd_deposit("2026-08-01", "Clientes", 1000.0)

        # Default TRM = 3100.0
        nw = self.db.get_global_net_worth(exchange_rate=3100.0)
        self.assertEqual(nw["net_worth_cop"], 6200000.0)
        self.assertEqual(nw["net_worth_usd"], 2000.0)

    def test_apply_recurring_batch(self):
        # 1. Crear dos gastos fijos
        id1 = self.db.add_recurring_expense("Hogar", "Internet", 100000.0, currency="COP", due_day=5)
        id2 = self.db.add_recurring_expense("Software", "ChatGPT", 20.0, currency="USD", due_day=1)

        # 2. Aplicar en batch
        res = self.db.apply_recurring_batch([id1, id2], date_str="2026-08-01")
        self.assertTrue(res["success"])
        self.assertEqual(res["applied"], 2)
        self.assertEqual(res["skipped"], 0)

        # 3. Verificar estado en checklist
        status = self.db.get_recurring_checklist_status("2026-08")
        status_dict = {i["id"]: i["is_paid"] for i in status}
        self.assertTrue(status_dict.get(id1))
        self.assertTrue(status_dict.get(id2))

    def test_tags_crud_and_association(self):
        # 1. Crear tag
        tag_id = self.db.add_tag("Freelance Proyecto Alpha", "#8b5cf6")
        self.assertIsNotNone(tag_id)

        # 2. Crear transacción y asignar tag
        tx_id = self.db.add_cop_income("2026-08-10", "Honorarios Alpha", 5000000.0)
        self.assertTrue(self.db.set_tags_for_record("cop_transactions", tx_id, [tag_id]))

        # 3. Consultar tags para el registro
        tags = self.db.get_tags_for_record("cop_transactions", tx_id)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["name"], "Freelance Proyecto Alpha")

        # 4. Filtrar libro mayor por tag
        ledger = self.db.get_unified_ledger(tag_id=tag_id)
        self.assertGreaterEqual(len(ledger), 1)
        self.assertEqual(ledger[0]["id"], tx_id)

    def test_get_unified_ledger_filters(self):
        # Insertar registros en diferentes fechas y módulos
        self.db.add_usd_deposit("2026-07-15", "Cliente Julio", 500.0)
        self.db.add_usd_deposit("2026-08-15", "Cliente Agosto", 800.0)
        self.db.add_cop_expense("2026-08-20", "Restaurantes / Salidas", 60000.0)
        self.db.add_cop_income("2026-08-25", "Nómina / Salario", 2500000.0)

        # 1. Filtro por fecha (Mes actual: 2026-08)
        aug_rows = self.db.get_unified_ledger(date_from="2026-08-01", date_to="2026-08-31")
        self.assertEqual(len(aug_rows), 3)
        concepts = [r["concept"] for r in aug_rows]
        self.assertIn("Cliente Agosto", concepts)
        self.assertNotIn("Cliente Julio", concepts)

        # 2. Filtro por módulo (Egresos COP)
        exp_rows = self.db.get_unified_ledger(module_filter="Egresos COP", date_from="2026-08-01")
        self.assertEqual(len(exp_rows), 1)
        self.assertEqual(exp_rows[0]["concept"], "Restaurantes / Salidas")

        # 3. Filtro por búsqueda
        search_rows = self.db.get_unified_ledger(search_query="Nómina")
        self.assertEqual(len(search_rows), 1)
        self.assertEqual(search_rows[0]["concept"], "Nómina / Salario")

    def test_monthly_net_worth_history(self):
        self.db.add_cop_income("2026-01-15", "Salario Enero", 4000000.0)
        self.db.add_usd_deposit("2026-02-10", "Cliente USD", 1000.0)


        history = self.db.get_monthly_net_worth_history(year=2026, exchange_rate=3100.0)
        self.assertEqual(len(history), 12)
        # Enero debe tener al menos 4M COP
        self.assertGreaterEqual(history[0]["net_worth_cop"], 4000000.0)
        # Febrero debe sumar el equivalente USD
        self.assertGreaterEqual(history[1]["net_worth_cop"], 7100000.0)


    def test_generate_csv_template_and_import(self):
        # 1. Generar plantilla
        temp_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        temp_csv.close()

        try:
            content = self.db.generate_csv_template(save_path=temp_csv.name)
            self.assertIn("tipo,fecha,concepto,monto,moneda", content)
            self.assertTrue(os.path.exists(temp_csv.name))

            # 2. Importar datos desde la plantilla
            result = self.db.import_csv_data(temp_csv.name)
            self.assertTrue(result["success"])
            self.assertGreater(result["imported"], 0)
            self.assertEqual(result["skipped"], 0)
        finally:
            if os.path.exists(temp_csv.name):
                os.remove(temp_csv.name)

    def test_category_service_consolidation(self):
        from services.category_service import CategoryService


        # 1. Registrar transacciones con nombres antiguos / duplicados
        self.db.add_cop_expense("2026-08-01", "Resto/Tienda", 45000.0)
        self.db.add_cop_expense("2026-08-02", "Cuidado", 30000.0)
        self.db.add_cop_expense("2026-08-03", "Peluquería", 25000.0)
        self.db.add_cop_income("2026-08-04", "Nómina", 2000000.0)
        rec_id = self.db.add_recurring_expense("Suscripciones", "Netflix", 35000.0, currency="COP", due_day=10)

        # 2. Ejecutar consolidación
        stats = CategoryService.consolidate_database_categories(self.db)
        self.assertTrue(stats["success"])
        self.assertGreaterEqual(stats["cop_transactions_updated"], 4)

        # 3. Verificar que las categorías se actualizaron canónicamente
        expenses = self.db.get_cop_expenses(limit=10)
        exp_cats = {e["category"] for e in expenses}
        self.assertIn("Restaurantes / Salidas", exp_cats)
        self.assertIn("Salud & Cuidado Personal", exp_cats)
        self.assertNotIn("Resto/Tienda", exp_cats)
        self.assertNotIn("Cuidado", exp_cats)

        # 4. Verificar gasto fijo actualizado
        recs = self.db.get_recurring_expenses()
        rec_item = [r for r in recs if r["id"] == rec_id][0]
        self.assertEqual(rec_item["category"], "Suscripciones & Apps")

    def test_credit_card_partial_payments_and_aliases(self):
        # 1. Cargar saldo COP y generar deuda con TC
        self.db.add_cop_income("2026-09-01", "Honorarios", 2000000.0)
        self.db.add_cop_expense("2026-09-02", "Compras Varias", 1000000.0, payment_method="CREDIT_CARD")
        self.assertEqual(self.db.get_credit_card_debt(), 1000000.0)
        self.assertEqual(self.db.get_cop_balance(), 2000000.0)

        # 2. Registrar primer abono parcial ($400,000 COP) con pay_credit_card
        success, msg = self.db.pay_credit_card("2026-09-05", 400000.0)
        self.assertTrue(success)
        self.assertIn("Abono parcial", msg)
        self.assertEqual(self.db.get_credit_card_debt(), 600000.0)
        self.assertEqual(self.db.get_cop_balance(), 1600000.0)

        # 3. Registrar segundo abono parcial ($300,000 COP) con pay_credit_card_debt alias
        success2, msg2 = self.db.pay_credit_card_debt(amount=300000.0, date="2026-09-10")
        self.assertTrue(success2)
        self.assertIn("Abono parcial", msg2)
        self.assertEqual(self.db.get_credit_card_debt(), 300000.0)
        self.assertEqual(self.db.get_cop_balance(), 1300000.0)

        # 4. Probar seguridad con argumentos invertidos (amount, date)
        success3, msg3 = self.db.pay_credit_card(300000.0, "2026-09-15")  # type: ignore
        self.assertTrue(success3)
        self.assertEqual(self.db.get_credit_card_debt(), 0.0)
        self.assertEqual(self.db.get_cop_balance(), 1000000.0)

        # 5. Verificar transacciones generadas en la base de datos
        txs = self.db.get_cop_transactions(limit=10)
        cc_payments = [t for t in txs if t["type"] == "CC_PAYMENT"]
        self.assertEqual(len(cc_payments), 3)


if __name__ == "__main__":
    unittest.main()


