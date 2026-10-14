from typing import List, Dict, Any, Tuple

class SettingsController:
    """
    Controlador para la configuración y personalización del sistema (MVC).
    Maneja categorías, cuentas/fiducias y la plantilla de gastos fijos.
    """
    def __init__(self, db_manager):
        self.db = db_manager

    def export_database_backup(self, dest_path: str) -> Tuple[bool, str]:
        """Realiza un backup en caliente seguro usando el SQLite Online Backup API."""
        try:
            result = self.db.create_backup(dest_path)
            if result:
                return True, "¡Backup exportado correctamente!"
            return False, "No se pudo generar el archivo de backup."
        except Exception as e:
            return False, f"Error al exportar backup: {str(e)}"

    # ==========================================
    # CATEGORÍAS
    # ==========================================
    def get_categories(self, cat_type: str) -> List[Dict[str, Any]]:
        return self.db.get_categories(cat_type)

    def add_category(self, name: str, cat_type: str, emoji: str, color: str) -> Tuple[bool, str]:
        if not name or not name.strip():
            return False, "Por favor ingresa un nombre para la categoría."
        try:
            self.db.add_category(name.strip(), cat_type, emoji, color)
            return True, f"¡Categoría '{name.strip()}' agregada con éxito!"
        except Exception as e:
            return False, f"Error al guardar: {str(e)}"

    def delete_category(self, cat_id: int) -> Tuple[bool, str]:
        return self.db.delete_category(cat_id)

    # ==========================================
    # CUENTAS Y FIDUCIAS
    # ==========================================
    def get_accounts(self, only_active: bool = False) -> List[Dict[str, Any]]:
        return self.db.get_accounts(only_active)

    def delete_account(self, acc_id: int) -> Tuple[bool, str]:
        return self.db.delete_account(acc_id)

    # ==========================================
    # GASTOS FIJOS (RECURRING)
    # ==========================================
    def get_recurring_expenses(self) -> List[Dict[str, Any]]:
        return self.db.get_recurring_expenses()

    def add_recurring_expense(self, category: str, description: str, amount_raw: str, currency: str, day_raw: str) -> Tuple[bool, str]:
        if not description or not description.strip():
            return False, "Por favor ingresa una descripción para el gasto fijo."
            
        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            return False, "Ingresa un monto válido mayor a 0."

        try:
            due_day = int(day_raw)
            if not (1 <= due_day <= 31):
                due_day = 1
        except ValueError:
            due_day = 1

        try:
            self.db.add_recurring_expense(category, description.strip(), amount, currency=currency, due_day=due_day)
            return True, f"¡Gasto fijo '{description.strip()}' agregado a la plantilla!"
        except Exception as e:
            return False, f"Error al guardar: {str(e)}"

    def delete_recurring_expense(self, rec_id: int) -> Tuple[bool, str]:
        try:
            self.db.delete_recurring_expense(rec_id)
            return True, "Gasto fijo eliminado de la plantilla."
        except Exception as e:
            return False, f"Error al eliminar: {str(e)}"
