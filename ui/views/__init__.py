# views package
from .dashboard import DashboardView
from .incomes import IncomesView
from .expenses import ExpensesView
from .conversion import ConversionView
from .investments import InvestmentsView
from .ledger import LedgerView
from .analytics import AnalyticsView
from .settings import SettingsView
from .budget_view import BudgetView
from .debt_view import DebtView

# Compatibilidad para referencias anteriores si fueran necesarias
USDVaultView = IncomesView
COPBudgetView = ExpensesView

__all__ = [
    "DashboardView",
    "IncomesView",
    "ExpensesView",
    "ConversionView",
    "InvestmentsView",
    "LedgerView",
    "AnalyticsView",
    "SettingsView",
    "BudgetView",
    "DebtView",
    "USDVaultView",
    "COPBudgetView"
]
