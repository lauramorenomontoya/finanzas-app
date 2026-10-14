# 📋 Plan Maestro de Implementación y Refactorización Técnica (Auditoría Integral 2026)

Este documento es la **hoja de ruta definitiva** para corregir, blindar y optimizar la aplicación **Montu (Control Financiero)** tras completar la auditoría técnica exhaustiva de los tres bloques del sistema.

---

## 🚦 Matriz de Severidad Global

```
┌────────────────────────────────────────────────────────────────────────┐
│ P0: BLOQUEANTE / CRÍTICO                                               │
│ - Modales que abren en blanco o crashean (CCPayment y ApplyRecurring)  │
│ - Fuga de conexiones SQLite (descriptores sin cerrar en with connect)  │
│ - Corrupción de decimales en USD (eliminar . multiplica montos x100)   │
│ - Split-Brain y llaves desfasadas en Servidor MCP                      │
│ - Crash por método inexistente en EmptyState de InvestmentsView        │
├────────────────────────────────────────────────────────────────────────┤
│ P1: ALTO (Seguridad, Concurrencia e Integridad Referencial)            │
│ - Transacciones huérfanas en Inversiones (falta linked_tx_id)          │
│ - Acoplamiento frágil por texto en Conversiones (usd/cop_tx_id)        │
│ - Modo solo lectura file:...?mode=ro e inyección en VACUUM INTO        │
│ - Deudas en USD omitidas en balances y resúmenes                       │
│ - Backups atómicos con WAL (conn.backup) y locks en set_setting        │
│ - Resiliencia de EventBus ante widgets destruidos                      │
│ - Limpieza de tags huérfanos y doble conteo de ahorro moto en Pilar 2  │
├────────────────────────────────────────────────────────────────────────┤
│ P2: MEDIO (Rendimiento y Experiencia de Usuario)                       │
│ - Eliminación de consultas N+1 en cuentas y batching en CSV            │
│ - Cache de balance en ConversionView (evitar SQLite en cada tecla)     │
│ - Reutilización de lienzos Matplotlib en AnalyticsView                 │
│ - Paginación SQL y Widget Pooling en LedgerView                        │
│ - Eliminación de doble/cuádruple refresh_data() en vistas              │
│ - Optimización de índices eliminando strftime() en WHERE               │
├────────────────────────────────────────────────────────────────────────┤
│ P3: BAJO (Robustez de Pruebas y Edge Cases)                            │
│ - Mocks de red en test_currency_service_live_rate                      │
│ - Corrección de argumentos posicionales en add_recurring_expense       │
│ - Validación estricta de fechas en NotionImporter                      │
│ - Alias .get() / .get_date() en DatePickerWidget                       │
│ - Tests automatizados para Controllers y MCP Server                    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 FASE 1: Prioridad P0 (Inmediata / Bugs Críticos)

- [x] **1.1. Reparación de Modales Rotos (`ui/components/cc_payment_modal.py` y `apply_recurring_modal.py`)**
  - **Problema:** No invocan la construcción de UI en `__init__` (abren en blanco) y usan firmas incompatibles con `BaseModal` (`create_standard_frame`, `subtitle` en `create_header`, tupla en `create_footer_buttons`).
  - **Acción:**
    1. Renombrar `build_ui` a `_build_ui()` y llamarlo al final de `__init__`.
    2. Adaptar llamadas a la firma real de `BaseModal`: `create_standard_frame()`, `create_header(parent, title, icon)` y `create_footer_buttons(parent, on_confirm, on_cancel)`.
    3. Asegurar emisión de `EventBus.publish("DATA_UPDATED")` en el callback de éxito.

- [x] **1.2. Función Centralizada de Parseo Numérico (`core/utils.py` o `core/constants.py`)**
  - **Problema:** En `expense_controller.py`, `edit_transaction_modal.py`, `edit_account_modal.py`, `add_debt_modal.py` y `debt_payment_modal.py`, el uso de `.replace(".", "")` elimina el punto decimal en USD (convirtiendo `$12.50` en `$1,250.00`).
  - **Acción:** Crear función central `parse_currency_amount(raw_value, currency="COP")`:
    - Para `USD`: normaliza comas como separador de miles, conserva el punto decimal y retorna `float` redondeado a 2 decimales.
    - Para `COP`: elimina comas y puntos de miles, retornando `float` o `int`.
    - Reemplazar las 9 implementaciones dispersas por esta función única.

- [x] **1.3. Corrección de Vacío de Conexiones SQLite (`database/db_manager.py`)**
  - **Problema:** `sqlite3.connect` no cierra la conexión al salir del bloque `with`.
  - **Acción:**
    1. Convertir `get_connection()` en un `@contextmanager` con bloque `finally: conn.close()` y `conn.commit()` post-yield para métodos simples.
    2. **Ajuste fino (Argon):** En métodos que ejecutan `BEGIN IMMEDIATE` (ej. `delete_usd_transaction`, `transfer_to_investment`, etc.), permitir recibir `conn: Optional[sqlite3.Connection] = None` opcional en `get_cop_balance(conn=None)` y `get_usd_balance(conn=None)`. De esta forma se reutiliza la conexión activa y se evita abrir una segunda conexión competidora durante una transacción inmediata.
  - **Archivos impactados:** `database/db_manager.py`, `database/managers/balance_mixin.py`.

- [x] **1.4. Unificación de Ruta y Claves en Servidor MCP (`mcp_server.py`)**
  - **Problema:** MCP lee `OLD_PROD_DB` antes que `NEW_PROD_DB` (split-brain) y busca claves desfasadas (`total_cop_month` en vez de `month_cop_expenses`).
  - **Acción:**
    1. Usar `os.path.join(DatabaseManager.get_app_data_dir(), "finanzas.db")`.
    2. Alinear diccionarios de respuesta con `expense_mixin.py` y `debt_mixin.py`.
    3. Configurar URI de conexión `file:{db_path}?mode=ro` en `query_database`.

- [x] **1.5. Corrección de Crash en EmptyState de Inversiones (`ui/views/investments.py`)**
  - **Problema:** Línea 249 apunta a `self._open_new_account_modal` inexistente.
  - **Acción:** Cambiar por `self._handle_create_account`.

---

## 📋 FASE 2: Prioridad P1 (Integridad Referencial, Seguridad y Concurrencia)

- [x] **2.1. Integridad de Categorías en Ingresos (`controllers/income_controller.py`)**
  - **Acción:** Guardar la categoría limpia en `category` y la plataforma en `notes` (para no romper `update_category` y consolidación).

- [x] **2.2. Enlaces Atómicos en Inversiones y Conversiones (`account_mixin.py`, `conversion_mixin.py`, `db_manager.py`)**
  - **Acción:**
    1. **Ajuste fino (Argon):** En `db_manager.py` (`init_db`), ejecutar migración defensiva con `PRAGMA table_info(...)` y `ALTER TABLE ... ADD COLUMN` para bases de datos existentes en producción:
       - `linked_tx_id INTEGER` y `linked_table TEXT` en `account_transactions`.
       - `usd_tx_id INTEGER` y `cop_tx_id INTEGER` en `conversions`.
    2. Mantener fallback a búsqueda histórica por fecha/monto/notas únicamente cuando `usd_tx_id IS NULL`, garantizando compatibilidad total con datos históricos.
    3. Borrar y editar pares atómicamente cuando el ID exista.

- [x] **2.3. Soporte Completo de Deudas en USD (`database/managers/debt_mixin.py`)**
  - **Acción:** Permitir deducción de saldo en USD (`add_usd_expense`) y contabilizar deudas en USD en `get_debts_summary()`.

- [x] **2.4. Doble Conteo de Moto en Presupuesto (`ui/views/budget_view.py`)**
  - **Acción:** Restar el ahorro de moto del total invertido antes de calcular el progreso del Pilar 2.

- [x] **2.5. Seguridad en Backups y WAL (`database/db_manager.py`, `settings_controller.py`)**
  - **Acción:** Usar `src_conn.backup(dst_conn)` nativo de SQLite tanto en `create_backup` como en `export_database_backup` (eliminando la interpolación insegura de `VACUUM INTO '{dest_path}'`).

- [x] **2.6. Resiliencia del EventBus (`core/event_bus.py`)**
  - **Acción:** Iterar sobre una copia `list(cls._subscribers[event_type])` y envolver cada callback en `try ... except Exception`.

- [x] **2.7. Limpieza de Tags Huérfanos (`database/managers/balance_mixin.py`, `account_mixin.py`)**
  - **Acción:** Ejecutar `DELETE FROM transaction_tags WHERE source_table = ? AND record_id = ?` al eliminar cualquier transacción.

- [x] **2.8. Limpieza de Método Duplicado en `ExpensesView` (`ui/views/expenses.py`)**
  - **Acción:** **Ajuste fino (Argon):** Unificar las dos definiciones de `_open_apply_recurring_modal` (líneas 346 y 406) conservando el parámetro de mes y el callback completo:
    ```python
    def _open_apply_recurring_modal(self):
        ApplyRecurringModal(
            self.winfo_toplevel(),
            self.db,
            target_ym=self.checklist_ym,
            on_success=self._on_recurring_applied
        )
    ```

---

## 📋 FASE 3: Prioridad P2 (Rendimiento de Consultas y UI)

- [x] **3.1. Eliminación de SQLite en KeyRelease de Conversiones (`ui/views/conversion.py`)**
  - **Acción:** Guardar `self.current_usd_balance` en memoria durante `refresh_data()` y consultarlo sin abrir la BD en cada tecla.

- [x] **3.2. Reutilización de Canvas Matplotlib en Analytics (`ui/views/analytics.py`)**
  - **Acción:** Instanciar las 3 figuras una sola vez en `_build_ui()` y solo limpiar ejes (`ax.clear()`) y redibujar (`draw_idle()`) en `refresh_data()`.

- [x] **3.3. Optimización de SettingsView (`ui/views/settings_view.py`)**
  - **Acción:** En `refresh_data()`, refrescar únicamente la pestaña actualmente visible (`_show_active_section()`), evitando 4 consultas masivas simultáneas.

- [x] **3.4. Eliminación de Refrescos Duplicados en Vistas**
  - **Acción:**
    1. Quitar `self.refresh_data()` antes de `EventBus.publish("DATA_UPDATED")` en los manejadores de éxito de `ExpensesView`, `IncomesView`, `DebtView` y `LedgerView`.
    2. **Ajuste fino (Argon):** Eliminar `self.refresh_data()` del final del `__init__()` de las 10 vistas principales (`DashboardView`, `ExpensesView`, `IncomesView`, `BudgetView`, `DebtView`, `ConversionView`, `InvestmentsView`, `LedgerView`, `AnalyticsView`, `SettingsView`), ya que `FinancialApp.show_view()` en `ui/app.py` (línea 346) siempre ejecuta `view.refresh_data()` al mostrar o empaquetar la vista. Esto previene el doble renderizado inicial.

- [x] **3.5. Eliminación de N+1 y Batching CSV (`account_mixin.py`, `csv_mixin.py`)**
  - **Acción:** Usar `LEFT JOIN` con `GROUP BY` en `get_accounts()`; envolver importaciones masivas CSV en una sola transacción atómica.

- [x] **3.6. Índices SQL y Widget Pooling en Ledger (`expense_mixin.py`, `ledger_mixin.py`, `ledger.py`)**
  - **Acción:**
    1. Reemplazar `strftime('%Y-%m', date) = ?` por rangos de fecha ISO para aprovechar `idx_cop_date_type`.
    2. Reciclar widgets de las 25 filas en `LedgerView` en lugar de destruir/crear 325 widgets por página.

---

## 📋 FASE 4: Prioridad P3 (Pruebas Automatizadas y Edge Cases)

- [x] **4.1. Desacoplar Tests de Conexión Externa (`tests/test_db.py`)**
  - **Acción:** Usar `unittest.mock.patch` en `test_currency_service_live_rate`.

- [x] **4.2. Corrección de Firma en Tests (`tests/test_features.py`, `tests/test_ui_smoke.py`)**
  - **Acción:** Especificar nombres de argumentos en `add_recurring_expense(..., currency="COP", due_day=15)`.

- [x] **4.3. Validación de Widgets Hijos en Smoke Tests (`tests/test_ui_smoke.py`)**
  - **Acción:** Verificar `self.assertGreater(len(modal.winfo_children()), 0)` en todos los modales para garantizar que ejecutan `_build_ui()`.

- [x] **4.4. Tests para Controladores y Servidor MCP**
  - **Acción:** Crear `tests/test_controllers.py` y `tests/test_mcp_server.py`.

- [x] **4.5. Casos Borde Menores**
  - **Acción:** Validación estricta de fechas de calendario en `NotionImporter`, regex en tasas de cambio CSV, corrección de defaults en `DebtController` y deselección del switch fijo en USD.

---

## 📈 Diagrama de Flujo de Implementación

```mermaid
graph TD
    subgraph Fase 1 [Fase 1: P0 Inmediata]
        M1[Reparar CCPayment y ApplyRecurring Modal]
        U1[parse_currency_amount Centralizado]
        D1[Context Manager conn.close en db_manager]
        MCP1[Unificar Rutas y Claves MCP Server]
        INV1[Corregir EmptyState en InvestmentsView]
    end

    subgraph Fase 2 [Fase 2: P1 Integridad y Seguridad]
        INC1[Categorías Limpias en IncomeController]
        LINK1[linked_tx_id en Inversiones y Conversiones]
        DEBT1[Deudas en USD y Descuento de Balance]
        BUD1[Corregir Doble Conteo Moto en Pilar 2]
        BAC1[conn.backup Atómico & Locks]
        EV1[Resiliencia EventBus y Limpieza Tags]
    end

    subgraph Fase 3 [Fase 3: P2 Rendimiento y UI]
        CONV1[Cache Balance en ConversionView]
        ANA1[Reutilizar Canvas Matplotlib]
        SET1[Refresco Lazy en SettingsView]
        REF1[Eliminar Doble refresh_data en Vistas]
        SQL1[SQL Índices ISO y Pooling Ledger]
    end

    subgraph Fase 4 [Fase 4: P3 Tests y Cierre]
        T1[Mock Tests Red & Corregir Firmas]
        T2[Validación Hijos en Smoke Tests]
        T3[Tests Controladores y MCP]
        E1[Edge Cases Fechas y Regex]
    end

    Fase 1 --> Fase 2 --> Fase 3 --> Fase 4
```

---

## 5. Estado de Ejecución y Entrega (Versión 1.3.1)

- [x] **Fase 1 (P0):** Integridad de datos y arquitectura base (100% completada).
- [x] **Fase 2 (P1):** Modales, eventos y flujos multimoneda (100% completada).
- [x] **Fase 3 (P2):** Optimización SQL, pooling de widgets en Ledger, lazy loading en Settings (100% completada).
- [x] **Fase 4 (P3):** Cobertura exhaustiva de tests (64 tests unitarios/smoke), mock de red y validación UI (100% completada).
- [x] **Integración de Marca & UI:** Logotipo horizontal oficial transparente (`montu_logo_sin_eslogan_alpha.png`), 8 íconos lineales limpios en `assets/icons/`, íconos para macOS (`montu_icon_1024.icns`) y Windows (`montu_icon_alpha_1024.ico`).
- [x] **Lanzamiento:** Preparada y etiquetada versión `v1.3.1`.

