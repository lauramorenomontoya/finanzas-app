# core/constants.py

# Variables de Marca
APP_NAME = "Montu"
APP_NAME_VISIBLE = "Montu"
APP_NAME_TECHNICAL = "montu"
APP_BUNDLE_ID = "com.lauramoreno.montu"

APP_VERSION = "1.2.1"
APP_AUTHOR = "Laura Moreno Montoya"
APP_COPYRIGHT = "© 2026 Laura Moreno Montoya. Todos los derechos reservados."



class Currencies:
    COP = "COP"
    USD = "USD"
    ALL = "Todas"


class CurrencyLabels:
    COP = "COP (Pesos)"
    USD = "USD (Dólares)"
    INCOME_COP = "Ingreso COP"
    INCOME_USD = "Ingreso USD"
    EXPENSE_COP = "Gasto COP"
    EXPENSE_USD = "Gasto Directo USD"


class Platforms:
    USD = ["Wenia", "ARQ", "Deel", "Binance", "Transferencia Bancaria", "Otro"]
    COP = ["Bancolombia", "Nu Colombia", "Davivienda", "Efectivo", "Otro"]
    ALL = [
        "Wenia",
        "ARQ",
        "Deel",
        "Binance",
        "Bancolombia",
        "Nu Colombia",
        "Davivienda",
        "Efectivo",
        "Transferencia Bancaria",
        "Otro",
    ]


class Categories:
    INCOME_USD = [
        "Clientes Internacionales USD",
        "Consultoría / Freelance USD",
        "Otros Ingresos USD",
    ]
    INCOME_COP = ["Salario", "Honorarios", "Rendimientos", "Otros Ingresos COP"]
    EXPENSE_DEFAULT = [
        "Arriendo / Hipoteca",
        "Servicios Públicos",
        "Alimentación / Mercado",
        "Transporte",
        "Otros Gastos",
    ]
    EXPENSE_DEFAULT_COP = [
        "Arriendo / Hipoteca",
        "Servicios Públicos (Luz, Agua, Gas)",
        "Alimentación / Mercado",
        "Otros Gastos COP",
    ]


class PaymentMethods:
    DEBIT = "Débito / Cuenta Operativa"
    CREDIT_CARD = "Tarjeta de Crédito"
    CASH = "Efectivo"
    DEFAULT = "Débito / Cuenta Operativa"
    OPTIONS = [DEBIT, CREDIT_CARD, CASH]
    FILTER = ["Todos", "Débito", "TC"]


class FilterOptions:
    CURRENCY = ["Todas", "COP", "USD"]
    CURRENCY_INCOMES = ["Todas", "USD", "COP"]
    TAB_EXPENSES = ["Checklist Gastos Fijos", "Movimientos de Egresos"]


class SettingsTabs:
    CATEGORIES = "Categorías"
    ACCOUNTS = "Cuentas & Inversiones"
    RECURRING = "Gastos Fijos"
    AI = "Asistente IA"
    OPTIONS = [
        CATEGORIES,
        ACCOUNTS,
        RECURRING,
        AI,
    ]
    CATEGORY_TYPES = [
        "Ingresos USD",
        "Gastos Directos USD",
        "Ingresos COP",
        "Gastos COP",
    ]


MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


def format_month_year_es(dt=None) -> str:
    from datetime import datetime
    if dt is None:
        dt = datetime.now()
    return f"{MESES_ES[dt.month]} {dt.year}"
