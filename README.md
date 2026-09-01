# 💰 Control Financiero | Gestor Multimoneda (USD / COP)

Una aplicación de escritorio moderna y nativa para **macOS** diseñada en Python con **CustomTkinter** y persistencia local en **SQLite**.

Permite gestionar tus finanzas dividiéndolas en dos mundos claros:
1. **🏦 Bóveda USD**: Ahorros intocables y recepción de ingresos en dólares (Wenia, ARQ, Deel, etc.).
2. **💳 Presupuesto COP**: Control de gastos fijos y variables mensuales en pesos colombianos.
3. **🔄 Puente de Conversión**: Módulo interactivo para transferir dólares a pesos con cálculo de tasa de cambio en vivo y actualización automática de saldos.

---

## 📸 Características Principales

- 🌙 **Modo Oscuro Elegante y Nativo**: Diseñado con bordes redondeados y estética minimalista para macOS.
- 🏦 **Bóveda USD**: Registro de ingresos por plataforma (Wenia, ARQ, Binance, Deel, etc.) con seguimiento de saldo intocable.
- 💳 **Presupuesto COP**: Registro y categorización de gastos fijos mensuales (arriendo, servicios, etc.) vs. variables (mercado, salidas).
- 🔄 **Puente de Conversión Inteligente**:
  - Ingreso de USD a retirar y tasa pactada (COP/USD).
  - Cálculo y previsualización en tiempo real.
  - Validación de saldo suficiente para evitar sobregiros.
  - Descuento atómico en USD e inyección automática en COP.
- 📊 **Panel Principal (Dashboard)**: Métricas globales, desglose porcentual de gastos y feed de movimientos recientes.
- 🗄️ **Base de Datos Local (SQLite)**: Tus datos nunca salen de tu computadora (`finanzas.db`).

---

## 🚀 Inicio Rápido (Ya configurado en tu Mac)

El entorno virtual ya ha sido creado e instalado con todas sus dependencias. Para ejecutar la aplicación en cualquier momento desde tu terminal:

```bash
cd /Users/lauramoreno/Desktop/Scripts/ControlFinanciero
./venv/bin/python3 main.py
```

O si activas el entorno virtual:
```bash
source venv/bin/activate
python3 main.py
```

---

## 🛠️ Estructura del Código

```text
ControlFinanciero/
├── main.py                # Punto de entrada principal
├── requirements.txt       # Dependencias (customtkinter, pillow)
├── test_db.py             # Pruebas unitarias de la base de datos
├── README.md              # Documentación de uso
├── database/
│   ├── __init__.py
│   └── db_manager.py      # Lógica de base de datos SQLite y transacciones
└── ui/
    ├── __init__.py
    ├── app.py             # Ventana principal y enrutador de vistas
    ├── components/
    │   ├── stat_card.py   # Tarjeta de métricas y saldos
    │   └── toast.py       # Notificaciones flotantes
    └── views/
        ├── dashboard.py   # Vista principal con métricas y feed
        ├── usd_vault.py   # Vista Bóveda de Ahorros USD
        ├── cop_budget.py  # Vista Presupuesto Operativo COP
        └── conversion.py  # Vista Puente de Conversión (USD -> COP)
```

---

## 💡 Cómo Usar la Aplicación

1. **Registrar un ingreso en USD**:
   - Ve a la pestaña **📥 Ingresos** (o **🏦 Bóveda USD**).
   - Selecciona tu plataforma (ej. *Wenia* o *ARQ*), ingresa el monto (ej. `800`) y haz clic en *Guardar Ingreso*.
   - Verás tu saldo actualizado en la Bóveda.


2. **Realizar una Conversión (USD ➔ COP)**:
   - Ve a la pestaña **🔄 Puente Conversión**.
   - Ingresa cuántos dólares deseas retirar (ej. `300`) y la tasa de cambio aplicada (ej. `4150`).
   - Revisa la vista previa en vivo (`$300 USD × $4,150 COP = $1,245,000 COP`).
   - Haz clic en *Ejecutar Conversión*. Automáticamente se descontarán $300 USD de tu Bóveda y tendrás $1,245,000 COP listos para gastar en tu presupuesto.

3. **Registrar tus Gastos en COP**:
   - Ve a la pestaña **💳 Presupuesto COP**.
   - Selecciona la categoría (ej. *Arriendo / Hipoteca* o *Servicios Públicos*), define si es un gasto fijo mensual e ingresa el monto en pesos.
   - Haz clic en *Registrar Gasto*.

4. **Monitorear en el Dashboard**:
   - Consulta el **📊 Panel Principal** para ver tus saldos globales, tus gastos categorizados con barras visuales y el feed de movimientos.
