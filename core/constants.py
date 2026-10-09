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
    COP = "🇨🇴 Pesos (COP)"
    USD = "💵 Dólares (USD)"
    INCOME_COP = "🇨🇴 Ingreso COP"
    INCOME_USD = "💵 Ingreso USD"
    EXPENSE_COP = "🇨🇴 Gasto en COP"
    EXPENSE_USD = "💵 Gasto Directo USD"


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
    OPTIONS = ["💳 Débito / Cuenta Operativa", "💳 Tarjeta de Crédito", "💵 Efectivo"]
    FILTER = ["Todos", "Débito", "TC"]


class FilterOptions:
    CURRENCY = ["Todas", "COP", "USD"]
    CURRENCY_INCOMES = ["Todas", "USD", "COP"]
    TAB_EXPENSES = ["📋 Checklist Gastos Fijos (Agenda)", "📑 Movimientos de Egresos"]


class SettingsTabs:
    OPTIONS = [
        "🏷️  Categorías",
        "🏦  Cuentas & Fiducias",
        "📋  Gastos Fijos Multimoneda",
        "🤖  Asistente IA (MCP)",
    ]
    CATEGORY_TYPES = [
        "Ingresos USD",
        "Gastos Directos USD",
        "Ingresos COP",
        "Gastos COP",
    ]
