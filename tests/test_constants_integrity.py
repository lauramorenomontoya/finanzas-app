"""
tests/test_constants_integrity.py - Verificación de integridad de constantes y AST.
Recorre ui/, controllers/ y services/ asegurando que cualquier acceso a atributos
de constantes (core/constants.py) o tema (core/theme.py) exista realmente.
Valida también la correspondencia exacta de SettingsTabs y PaymentMethods.
"""

import ast
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.constants as constants_mod
import core.theme as theme_mod


class TestConstantsIntegrity(unittest.TestCase):
    def test_settings_tabs_consistency(self):
        """Verifica que cada constante de SettingsTabs esté presente en SettingsTabs.OPTIONS con el mismo texto."""
        from core.constants import SettingsTabs

        self.assertIn(SettingsTabs.CATEGORIES, SettingsTabs.OPTIONS)
        self.assertIn(SettingsTabs.ACCOUNTS, SettingsTabs.OPTIONS)
        self.assertIn(SettingsTabs.RECURRING, SettingsTabs.OPTIONS)
        self.assertIn(SettingsTabs.AI, SettingsTabs.OPTIONS)

        expected = [
            SettingsTabs.CATEGORIES,
            SettingsTabs.ACCOUNTS,
            SettingsTabs.RECURRING,
            SettingsTabs.AI,
        ]
        self.assertEqual(SettingsTabs.OPTIONS, expected)

    def test_payment_methods_consistency(self):
        """Verifica que cada constante de PaymentMethods esté en OPTIONS."""
        from core.constants import PaymentMethods

        self.assertIn(PaymentMethods.DEBIT, PaymentMethods.OPTIONS)
        self.assertIn(PaymentMethods.CREDIT_CARD, PaymentMethods.OPTIONS)
        self.assertIn(PaymentMethods.CASH, PaymentMethods.OPTIONS)

    def test_ast_constants_and_theme_usage(self):
        """
        Recorre el AST de ui/, controllers/ y services/ y comprueba que
        cualquier acceso a atributos de clases de constantes o Theme sea válido.
        """
        constants_classes = {
            name: getattr(constants_mod, name)
            for name in dir(constants_mod)
            if isinstance(getattr(constants_mod, name), type)
        }
        theme_classes = {"Theme": theme_mod.Theme}

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dirs = [
            os.path.join(base_dir, "ui"),
            os.path.join(base_dir, "controllers"),
            os.path.join(base_dir, "services"),
        ]

        missing_references = []

        for t_dir in target_dirs:
            if not os.path.exists(t_dir):
                continue
            for root, _, files in os.walk(t_dir):
                for f in files:
                    if not f.endswith(".py"):
                        continue
                    file_path = os.path.join(root, f)
                    rel_path = os.path.relpath(file_path, base_dir)

                    with open(file_path, "r", encoding="utf-8") as fp:
                        try:
                            tree = ast.parse(fp.read(), filename=file_path)
                        except SyntaxError as e:
                            self.fail(f"Error de sintaxis en {rel_path}: {e}")

                    imported_classes = {}

                    # Registrar imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and ("constants" in node.module):
                                for alias in node.names:
                                    name = alias.name
                                    asname = alias.asname or name
                                    if name in constants_classes:
                                        imported_classes[asname] = constants_classes[name]
                            elif node.module and ("theme" in node.module):
                                for alias in node.names:
                                    name = alias.name
                                    asname = alias.asname or name
                                    if name in theme_classes:
                                        imported_classes[asname] = theme_classes[name]

                    # Revisar accesos a atributos
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                            obj_name = node.value.id
                            attr_name = node.attr
                            if obj_name in imported_classes:
                                target_class = imported_classes[obj_name]
                                if not hasattr(target_class, attr_name):
                                    missing_references.append(
                                        f"{rel_path}:{node.lineno} -> {obj_name}.{attr_name}"
                                    )

        if missing_references:
            formatted_errors = "\n".join(f"  - {err}" for err in missing_references)
            self.fail(
                f"Se encontraron {len(missing_references)} accesos a constantes o temas inexistentes:\n{formatted_errors}"
            )


if __name__ == "__main__":
    unittest.main()
