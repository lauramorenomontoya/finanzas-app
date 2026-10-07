---
name: control-financiero
description: >-
  Asistente y gestor de finanzas personales multimoneda (COP/USD) para Control Financiero.
  Úsalo cuando el usuario pida registrar un gasto, egreso, ingreso, depósito, consultar
  sus balances, revisar el estado de su presupuesto, ver movimientos recientes o pedir
  análisis de su base de datos financiera en SQLite.
---

# Skill: Control Financiero

Esta habilidad permite al asistente gestionar la base de datos financiera personal del usuario en `finanzas.db` (ubicada en `~/Library/Application Support/ControlFinanciero/finanzas.db`).

## Herramientas Disponibles (MCP Server: ControlFinanciero)

1. `get_financial_summary`:
   - Devuelve la liquidez en USD, saldo operativo COP, TRM, ingresos/egresos del mes y deudas activas.

2. `add_expense`:
   - Registra un gasto en COP o USD.
   - Parámetros: `amount`, `category`, `currency` ('COP' o 'USD'), `date` (YYYY-MM-DD o 'hoy'), `payment_method` ('DEBIT', 'CREDIT_CARD', 'CASH'), `notes`, `is_fixed`.
   - Si no se especifica moneda y el monto es > 1000, inferir 'COP'. Si es un monto menor como $15 o $50, inferir 'USD'.

3. `add_income`:
   - Registra un ingreso o depósito en COP o USD.
   - Parámetros: `amount`, `platform_or_category`, `currency`, `date`, `notes`.

4. `get_recent_transactions`:
   - Consulta las últimas transacciones registradas.
   - Parámetro: `limit` (por defecto 15).

5. `get_budget_status`:
   - Consulta el avance del presupuesto del mes por categoría.

6. `query_database`:
   - Ejecuta consultas SQL de solo lectura (`SELECT ...`) para reportes o análisis analíticos avanzados.

## Reglas de Interacción con el Usuario
- Formatea siempre los valores en pesos colombianos como `$XX,XXX COP` (sin decimales) y en dólares como `$XX.XX USD`.
- Al registrar un gasto o ingreso, confirma siempre el monto, la categoría inferida y el nuevo saldo resultante.
- Si el usuario dice "gasté 40 mil en uber con débito", traduce automáticamente a: `amount=40000`, `category="Transporte"`, `currency="COP"`, `payment_method="DEBIT"`.
