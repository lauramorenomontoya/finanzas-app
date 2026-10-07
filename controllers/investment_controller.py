from typing import Dict, Any, List, Tuple

class InvestmentController:
    """
    Controlador para la vista de Cuentas, Ahorro e Inversión (MVC).
    """
    def __init__(self, db_manager):
        self.db = db_manager

    def get_investments_summary(self) -> Dict[str, Any]:
        return self.db.get_investments_summary()

    def get_accounts(self, currency: str = None, only_active: bool = True) -> List[Dict[str, Any]]:
        return self.db.get_accounts(currency=currency, only_active=only_active)

    def get_account_transactions(self, limit: int = 25) -> List[Dict[str, Any]]:
        return self.db.get_account_transactions(limit=limit)

    def delete_account_transaction(self, tx_id: int) -> Tuple[bool, str, Any]:
        return self.db.delete_account_transaction(tx_id)
