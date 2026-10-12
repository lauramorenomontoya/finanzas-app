"""
tests/test_ui_smoke.py - Prueba de humo permanente para la UI de Montu.
Abre secuencialmente las 10 vistas principales y verifica que ninguna
lance excepciones directas ni en callbacks de Tkinter.
Ejercita de forma real formularios, modales, botones segmentados y CRUD
en las vistas Expenses, Debts y Settings usando una base de datos temporal.
Salta con skip si el entorno carece de display gráfico (ej. CI headless sin Xvfb).
"""

import os
import sys
import shutil
import tempfile
import traceback
import unittest
import tkinter as tk

# Asegurar path raíz del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from core.constants import PaymentMethods, SettingsTabs, FilterOptions


class TestUISmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ui.utils.icon_helper import IconHelper
        IconHelper.clear_cache()
        # Verificar si hay display disponible
        try:
            root_test = tk.Tk()
            root_test.withdraw()
            root_test.destroy()
        except (tk.TclError, Exception) as e:
            raise unittest.SkipTest(f"No hay display disponible para pruebas de UI de Tkinter: {e}")
        IconHelper.clear_cache()

    def setUp(self):
        from ui.utils.icon_helper import IconHelper
        from core.event_bus import EventBus
        IconHelper.clear_cache()
        EventBus.clear()
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_ui_smoke.db")
        self.db = DatabaseManager(self.test_db_path)

    def tearDown(self):
        from ui.utils.icon_helper import IconHelper
        from core.event_bus import EventBus
        IconHelper.clear_cache()
        EventBus.clear()
        shutil.rmtree(self.temp_dir, ignore_errors=True)



    def _setup_app_with_error_capture(self):
        from ui.app import FinancialApp

        app = FinancialApp(db_manager=self.db)
        app.withdraw()

        captured_errors = []

        def custom_report_callback_exception(exc, val, tb):
            captured_errors.append((exc, val, tb))

        app.report_callback_exception = custom_report_callback_exception
        return app, captured_errors

    def test_open_all_views_without_exceptions(self):
        app, captured_errors = self._setup_app_with_error_capture()

        views_to_test = [
            "dashboard",
            "incomes",
            "expenses",
            "budget",
            "debts",
            "conversion",
            "investments",
            "ledger",
            "analytics",
            "settings"
        ]

        failed_views = {}

        try:
            for view_name in views_to_test:
                captured_errors.clear()
                try:
                    app.show_view(view_name)
                    app.update()

                    if captured_errors:
                        tb_msgs = []
                        for exc, val, tb in captured_errors:
                            tb_msgs.append("".join(traceback.format_exception(exc, val, tb)))
                        failed_views[view_name] = f"Callback error:\n{''.join(tb_msgs)}"
                except Exception as e:
                    failed_views[view_name] = f"Direct error:\n{traceback.format_exc()}"

            if failed_views:
                err_summary = "\n" + "=" * 60 + "\n"
                for v_name, err in failed_views.items():
                    err_summary += f"[VISTA FALLIDA: {v_name}]\n{err}\n" + "-" * 60 + "\n"
                self.fail(f"Se encontraron errores de UI en {len(failed_views)} vista(s):{err_summary}")
        finally:
            app.destroy()

    def test_expenses_view_crud_and_modals(self):
        """
        Ejercita la UI real de ExpensesView:
        - Rellenar formulario y pulsar botón guardar
        - Comprobar que el gasto se registró
        - Abrir modales (Edit, Duplicate, ApplyRecurring)
        - Eliminar el gasto y actualizar
        """
        from ui.components.edit_transaction_modal import EditTransactionModal
        from ui.components.duplicate_modal import DuplicateModal
        from ui.components.apply_recurring_modal import ApplyRecurringModal

        # Fondos iniciales para verificación de saldo en COP
        self.db.add_cop_income(date="2026-10-12", category="Salario", amount=1000000.0, notes="Bancolombia")

        app, captured_errors = self._setup_app_with_error_capture()

        try:
            app.show_view("expenses")
            app.update()
            expenses_view = app.views["expenses"]

            # 1. Rellenar formulario
            expenses_view.amount_entry.delete(0, "end")
            expenses_view.amount_entry.insert(0, "35000")
            expenses_view.category_combo.set("Alimentación / Mercado")
            expenses_view.payment_combo.set(PaymentMethods.DEBIT)
            expenses_view.notes_entry.delete(0, "end")
            expenses_view.notes_entry.insert(0, "Gasto Smoke UI")
            app.update()

            # 2. Pulsar botón guardar
            expenses_view.btn_submit.invoke()
            app.update()
            self.assertEqual(len(captured_errors), 0, f"Error al guardar gasto: {captured_errors}")

            # 3. Comprobar que el gasto existe en la base de datos
            expenses = self.db.get_cop_expenses()
            saved_expense = next((e for e in expenses if e["notes"] == "Gasto Smoke UI"), None)
            self.assertIsNotNone(saved_expense, "El gasto guardado no apareció en la base de datos")
            self.assertEqual(float(saved_expense["amount"]), 35000.0)

            # 4. Probar modales asociados a la vista
            edit_modal = EditTransactionModal(app, self.db, "cop_transactions", saved_expense)
            app.update()
            edit_modal.destroy()
            app.update()

            dup_modal = DuplicateModal(app, self.db, "cop_transactions", saved_expense)
            app.update()
            dup_modal.destroy()
            app.update()


            rec_modal = ApplyRecurringModal(app, self.db)
            app.update()
            rec_modal.destroy()
            app.update()

            # 5. Probar cambio de pestañas con el StyledSegmentedButton
            for tab in FilterOptions.TAB_EXPENSES:
                expenses_view.right_view_seg.set(tab)
                app.update()

            # 6. Eliminar el gasto
            success, _, _ = self.db.delete_cop_transaction(saved_expense["id"], force=True)
            self.assertTrue(success)
            expenses_view.refresh_data()
            app.update()
            self.assertEqual(len(captured_errors), 0, "Excepciones en ExpensesView tras eliminación")

        finally:
            app.destroy()

    def test_debts_view_crud_and_modals(self):
        """
        Ejercita la UI real de DebtView:
        - Crear deuda
        - Renderizar tarjetas de deudas
        - Abrir modales (AddDebtModal, DebtPaymentModal, DebtHistoryModal, CCPaymentModal)
        - Eliminar deuda y refrescar
        """
        from ui.components.add_debt_modal import AddDebtModal
        from ui.components.debt_payment_modal import DebtPaymentModal
        from ui.components.debt_history_modal import DebtHistoryModal
        from ui.components.cc_payment_modal import CCPaymentModal

        app, captured_errors = self._setup_app_with_error_capture()

        try:
            app.show_view("debts")
            app.update()
            debt_view = app.views["debts"]

            # 1. Crear deuda en base temporal
            debt_id = self.db.add_debt(
                creditor="Acreedor Test UI",
                total_amount=150000.0,
                currency="COP",
                due_date="2026-11-30",
                notes="Deuda Smoke Test"
            )
            self.assertGreater(debt_id, 0)
            debt_view.refresh_data()
            app.update()

            debts = self.db.get_debts()
            debt_data = next((d for d in debts if d["id"] == debt_id), None)
            self.assertIsNotNone(debt_data)

            # 2. Probar modales de deudas
            add_modal = AddDebtModal(app, self.db, debt=debt_data)
            app.update()
            add_modal.destroy()
            app.update()

            pay_modal = DebtPaymentModal(app, self.db, debt=debt_data)
            app.update()
            pay_modal.destroy()
            app.update()

            hist_modal = DebtHistoryModal(app, self.db, debt_id=debt_id)
            app.update()
            hist_modal.destroy()
            app.update()

            cc_modal = CCPaymentModal(app, self.db)
            app.update()
            cc_modal.destroy()
            app.update()

            # 3. Probar navegación con StyledSegmentedButton
            debt_view.seg_view_mode.set("Dinero que me deben (Por Cobrar)")
            app.update()
            debt_view.seg_view_mode.set("Mis Deudas (Pasivos)")
            app.update()

            # 4. Eliminar deuda y refrescar
            del_ok = self.db.delete_debt(debt_id)
            self.assertTrue(del_ok)
            debt_view.refresh_data()
            app.update()
            self.assertEqual(len(captured_errors), 0, "Excepciones en DebtView tras operaciones")

        finally:
            app.destroy()

    def test_settings_view_navigation_and_modals(self):
        """
        Ejercita la UI real de SettingsView:
        - Cambiar entre las 4 pestañas de configuración
        - Abrir CSVImporterModal
        - CRUD en CategoriesTab
        - CRUD en RecurringTab
        """
        from ui.components.csv_importer_modal import CSVImporterModal

        app, captured_errors = self._setup_app_with_error_capture()

        try:
            app.show_view("settings")
            app.update()
            settings_view = app.views["settings"]

            # 1. Cambiar entre todas las pestañas de SettingsTabs
            for tab_name in SettingsTabs.OPTIONS:
                settings_view.section_seg.set(tab_name)
                app.update()

            # 2. Abrir CSVImporterModal
            importer = CSVImporterModal(app, self.db)
            app.update()
            importer.destroy()
            app.update()

            # 3. CRUD en CategoriesTab
            settings_view.section_seg.set(SettingsTabs.CATEGORIES)
            app.update()
            cat_id = self.db.add_category("Test Smoke Cat", "EXPENSE_COP", "🏷️", "#10b981")
            self.assertGreater(cat_id, 0)
            settings_view.categories_tab.refresh_data()
            app.update()

            updated = self.db.update_category(cat_id, "Test Smoke Cat Updated", "💼", "#75D9A5")
            self.assertTrue(updated)
            settings_view.categories_tab.refresh_data()
            app.update()

            deleted, _ = self.db.delete_category(cat_id)
            self.assertTrue(deleted)
            settings_view.categories_tab.refresh_data()
            app.update()

            # 4. CRUD en RecurringTab
            settings_view.section_seg.set(SettingsTabs.RECURRING)
            app.update()
            rec_id = self.db.add_recurring_expense("Alimentación / Mercado", "Mercado Semanal Test", 80000.0, 5)
            self.assertGreater(rec_id, 0)
            settings_view.recurring_tab.refresh_data()
            app.update()

            del_rec = self.db.delete_recurring_expense(rec_id)
            self.assertTrue(del_rec)
            settings_view.recurring_tab.refresh_data()
            app.update()

            self.assertEqual(len(captured_errors), 0, "Excepciones en SettingsView")

        finally:
            app.destroy()

    def test_styled_segmented_buttons_real_click_simulation(self):
        """
        Simula el clic real (invocando seg._buttons_dict[valor].invoke())
        en TODOS los StyledSegmentedButton de la aplicación.
        Garantiza que CustomTkinter no falle con argumentos como from_button_callback.
        """
        from ui.components.segmented_button import StyledSegmentedButton

        app, captured_errors = self._setup_app_with_error_capture()

        def _find_segmented_buttons(widget):
            found = []
            if isinstance(widget, StyledSegmentedButton):
                found.append(widget)
            for child in widget.winfo_children():
                found.extend(_find_segmented_buttons(child))
            return found

        views_to_test = [
            "dashboard",
            "incomes",
            "expenses",
            "budget",
            "debts",
            "conversion",
            "investments",
            "ledger",
            "analytics",
            "settings"
        ]

        total_buttons_clicked = 0

        try:
            for view_name in views_to_test:
                app.show_view(view_name)
                app.update()
                view_widget = app.views[view_name]

                seg_buttons = _find_segmented_buttons(view_widget)
                for seg in seg_buttons:
                    for val, btn in list(seg._buttons_dict.items()):
                        captured_errors.clear()
                        # Simulación del clic nativo de CustomTkinter
                        btn.invoke()
                        app.update()

                        if captured_errors:
                            err_msg = "".join(traceback.format_exception(*captured_errors[0]))
                            self.fail(
                                f"Error en clic real de StyledSegmentedButton '{val}' en vista '{view_name}':\n{err_msg}"
                            )

                        self.assertEqual(
                            seg.get(), val,
                            f"El valor activo de segmented button no coincidió tras clic en '{val}' en '{view_name}'"
                        )
                        total_buttons_clicked += 1

            self.assertGreater(total_buttons_clicked, 0, "No se encontró ningún StyledSegmentedButton para probar")
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()

