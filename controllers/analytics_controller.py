from typing import Dict, Any, List, Optional

class AnalyticsController:
    """
    Controlador para el Dashboard de Análisis y Estadísticas (MVC).
    """
    def __init__(self, db_manager):
        self.db = db_manager

    def get_latest_exchange_rate(self) -> float:
        return self.db.get_latest_exchange_rate()

    def set_official_trm(self, rate: float):
        self.db.set_setting("official_trm", str(rate))

    def get_global_net_worth(self, exchange_rate: float) -> float:
        return self.db.get_global_net_worth(exchange_rate=exchange_rate)

    def get_annual_overview(self, year: int) -> Dict[str, Any]:
        return self.db.get_annual_overview(year)

    def get_accounts(self, only_active: bool = True) -> List[Dict[str, Any]]:
        return self.db.get_accounts(only_active=only_active)

    def get_expenses_by_category(self) -> List[Dict[str, Any]]:
        return self.db.get_expenses_by_category()

    def get_monthly_net_worth_history(self, year: int, exchange_rate: float) -> Dict[str, float]:
        return self.db.get_monthly_net_worth_history(year, exchange_rate=exchange_rate)
