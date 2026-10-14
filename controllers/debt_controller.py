from typing import Dict, Any, List

class DebtController:
    """
    Controlador para la vista de Deudas y Préstamos (MVC).
    """
    def __init__(self, db_manager):
        self.db = db_manager

    def get_debts_summary(self) -> Dict[str, Any]:
        return self.db.get_debts_summary()

    def get_debts(self, status: str = "ACTIVE", debt_type: str = "PAYABLE") -> List[Dict[str, Any]]:
        status_norm = status.upper() if status else None
        if status_norm in ("ACTIVO", "ACTIVE"):
            status_norm = "ACTIVE"
        elif status_norm in ("PAGADA", "PAID"):
            status_norm = "PAID"

        type_norm = debt_type.upper() if debt_type else None
        if type_norm in ("PAGAR", "PAYABLE", "DEUDA", "DEBT"):
            type_norm = "PAYABLE"
        elif type_norm in ("COBRAR", "RECEIVABLE"):
            type_norm = "RECEIVABLE"

        return self.db.get_debts(status=status_norm, debt_type=type_norm)

    def delete_debt(self, debt_id: int) -> bool:
        return self.db.delete_debt(debt_id)
