"""
tests/test_ui_smoke.py - Prueba de humo permanente para la UI de Montu.
Abre secuencialmente las 10 vistas principales y verifica que ninguna
lance excepciones directas ni en callbacks de Tkinter.
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


class TestUISmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Verificar si hay display disponible
        try:
            root_test = tk.Tk()
            root_test.withdraw()
            root_test.destroy()
        except (tk.TclError, Exception) as e:
            raise unittest.SkipTest(f"No hay display disponible para pruebas de UI de Tkinter: {e}")

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_ui_smoke.db")
        # Sembrar con un DatabaseManager limpio
        self.db = DatabaseManager(self.test_db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_open_all_views_without_exceptions(self):
        from ui.app import FinancialApp

        app = FinancialApp(db_manager=self.db)
        app.withdraw()  # Ocultar ventana para no parpadear en pantalla

        captured_errors = []

        def custom_report_callback_exception(exc, val, tb):
            captured_errors.append((exc, val, tb))

        app.report_callback_exception = custom_report_callback_exception

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


if __name__ == "__main__":
    unittest.main()
