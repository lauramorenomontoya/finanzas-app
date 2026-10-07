"""
Controlador del Dashboard Principal (MVC):
Centraliza la obtención de métricas financieras consolidadas, KPIs,
tasas de cambio (TRM), estado de deudas y feed de actividades recientes.
"""

from typing import Dict, Any, List, Tuple


class DashboardController:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_latest_exchange_rate(self) -> float:
        """Obtiene la tasa de cambio TRM más reciente almacenada."""
        try:
            return float(self.db.get_latest_exchange_rate())
        except Exception:
            return 4000.0

    def save_exchange_rate(self, rate: float) -> bool:
        """Guarda la tasa de cambio oficial en la configuración del sistema."""
        try:
            self.db.set_setting("official_trm", str(rate))
            return True
        except Exception:
            return False

    def get_consolidated_summary(self, exchange_rate: float) -> Dict[str, Any]:
        """Calcula el resumen mensual consolidado multimoneda (COP + USD)."""
        return self.db.get_consolidated_monthly_summary(exchange_rate=exchange_rate)

    def get_debts_summary(self) -> Dict[str, Any]:
        """Obtiene el resumen de endeudamiento (Tarjeta de Crédito y Préstamos Personales)."""
        return self.db.get_debts_summary()

    def get_categories_breakdown_data(self) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Obtiene los egresos agrupados por categoría y el mapa de presupuestos asignados.
        Retorna (categories, budgets_map).
        """
        categories = self.db.get_expenses_by_category()
        budgets_map = {b["category"]: b["budget"] for b in self.db.get_category_budgets()}
        return categories, budgets_map

    def get_recent_activities(self, limit: int = 12) -> List[Dict[str, Any]]:
        """Obtiene la lista de los movimientos más recientes."""
        return self.db.get_recent_activities(limit=limit)
