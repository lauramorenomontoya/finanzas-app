from typing import Dict, Any, List

class DebtController:
    """
    Controlador para la vista de Deudas y Préstamos (MVC).
    """
    def __init__(self, db_manager):
        self.db = db_manager

    def get_debts_summary(self) -> Dict[str, Any]:
        return self.db.get_debts_summary()

    def get_debts(self, status: str = "Active", debt_type: str = "Pagar") -> List[Dict[str, Any]]:
        return self.db.get_debts(status=status, debt_type=debt_type)

    def delete_debt(self, debt_id: int) -> bool:
        return self.db.delete_debt(debt_id)
