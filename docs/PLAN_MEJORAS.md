# 🔍 Diagnóstico & Plan de Mejoras — Montu

> **Evaluado el:** 28 de septiembre de 2026  
> **Stack:** Python · CustomTkinter · SQLite · Matplotlib  
> **Estado general:** ✅ Funcional y bien estructurado, con oportunidades claras de refinamiento

---

## 📐 Arquitectura — Diagnóstico

### ✅ Lo que está bien hecho

| Área | Detalle |
|---|---|
| **Modularidad** | Separación clara `ui/` → `views/`, `components/`, `utils/`. Patrón MVC implícito. |
| **Mixin-pattern** | La DB está dividida en 13+ mixins (`budget_mixin`, `debt_mixin`, etc.) — excelente mantenibilidad. |
| **Lazy loading** | Las vistas se instancian solo cuando el usuario las visita por primera vez. |
| **Backup automático** | Se llama `db.create_backup()` al iniciar. |
| **Reactividad** | Callback `on_data_changed` propaga cambios entre vistas activas. |
| **Theming** | Clase `Theme` centralizada con soporte dark/light en tuplas CTK. |
| **Atajos de teclado** | `Cmd+K` / `Ctrl+K` para búsqueda global. |
| **TRM en tiempo real** | Fetch asíncrono de tasa de cambio al arrancar. |

---

### ⚠️ Problemas detectados

#### 1. `Any` importado pero no declarado en `app.py`
```python
# app.py línea 222 — usa `Any` pero no está en los imports
self.views: Dict[str, Any] = {}
```
**Fix:** agregar `Any` al import de `typing`.

#### 2. `_center_window` duplicado en ~15 modales
Cada modal (`AddDebtModal`, `EditTransactionModal`, etc.) repite el mismo bloque de 10 líneas para centrarse. Debería estar en un mixin o utilidad compartida.

#### 3. No hay logging estructurado
Los errores se imprimen con `print()`. En producción es difícil rastrear fallos. Se debería usar el módulo `logging` de Python.

#### 4. Archivos de test dispersos en la raíz
`test_debts.py`, `test_db.py`, `test_budget.py` etc. están en la raíz. Deberían estar en una carpeta `tests/`.

#### 5. Archivos temporales de SQLite en la raíz
`temp_test.db-shm`, `temp_test.db-wal`, `test_features.db-*` — deberían estar en `.gitignore` y limpiarse.

#### 6. Sincronización parcial de vistas
Solo la vista *activa* se refresca en `on_data_updated()`. Si el usuario vuelve al dashboard después de agregar un gasto, los datos se actualizan, pero si hay vistas cacheadas con datos stale, podrían verse desactualizadas en ciertos flujos de edge-case.

#### 7. `requirements.txt` sin versiones fijadas para matplotlib y pillow
Solo `>=`, lo que puede causar incompatibilidades futuras. Mejor fijar versiones exactas tras pruebas.

---

## 🎨 Interfaz (UI/UX) — Diagnóstico

### ✅ Base sólida
- Paleta de colores coherente y well-defined en `Theme`
- Cards con `corner_radius=14` y bordes sutiles dan sensación premium
- Uso de emojis como iconos da personalidad
- Sidebar funcional con balances visibles siempre

### 🔴 Problemas estéticos principales (priorizados)

#### P1 — **Sidebar plana y sin jerarquía visual**
Los 10 ítems de navegación tienen exactamente el mismo estilo, peso y tamaño. No hay grupos, separadores ni categorías. La navegación se siente como una lista genérica.

#### P2 — **El StatCard no tiene acento superior de color**
Las tarjetas del dashboard son blancas/grises sin distinguirse visualmente entre sí. No tienen la "barra de color" superior característica de los dashboards financieros premium (Linear, Notion, Stripe).

#### P3 — **Formularios sin estructura visual clara**
Los campos de los formularios (`ExpensesView`, `IncomesView`, etc.) van uno debajo del otro con etiquetas pequeñas. No hay secciones, separadores ni agrupación que guíe al usuario.

#### P4 — **Botones de acción sin consistencia de estilo**
En el dashboard hay botones con ~8 colores de fondo hardcodeados distintos (`#0284c7`, `#6366f1`, `#e11d48`, `#059669`, `#0f766e`, `#334155`…). Esto crea ruido visual.

#### P5 — **Banner de salud financiera sobreargado**
El banner principal tiene título, 2 KPIs grandes, descripción, badge de estado y una franja inferior con 2 líneas de texto densas. Compite visualmente consigo mismo.

#### P6 — **Feed de actividades reciente sin separación de fechas**
La lista de movimientos recientes muestra todos los items con el mismo peso visual, sin agrupar por fecha (Hoy / Ayer / Esta semana).

#### P7 — **Ausencia de estados vacíos elegantes**
El mensaje de "No hay movimientos" es un label de texto plano. Los dashboards modernos usan ilustraciones o iconos grandes con call-to-action.

#### P8 — **Tipografía depende de "SF Pro" (fuente del sistema Apple)**
Si se corre en Windows/Linux, `SF Pro Display` y `SF Pro Text` no existen y CustomTkinter cae al fallback. Debería usarse una fuente disponible multiplataforma.

---

## 🗺️ Plan de Mejoras — Priorizado

Las mejoras están organizadas en **3 fases** de menor a mayor impacto visual.

---

### 🔵 Fase 1 — Bugs & Deuda Técnica ✅ *(Completada)*

| # | Tarea | Archivo | Estado |
|---|---|---|:---:|
| 1.1 | Agregar `Any` al import de `typing` | `ui/app.py` | ✅ Completado |
| 1.2 | Crear `ui/utils/modal_helper.py` con `center_window()` y refactorizar todos los modales | `ui/utils/` | ✅ Completado |
| 1.3 | Mover archivos de test a `tests/` | Raíz del proyecto | ✅ Completado |
| 1.4 | Actualizar `.gitignore` para excluir `*.db-shm`, `*.db-wal`, `temp_*` | `.gitignore` | ✅ Completado |
| 1.5 | Agregar `logging` básico en lugar de `print()` en `main.py` | `main.py` | ✅ Completado |

---

### 🟡 Fase 2 — Mejoras de UI de Alto Impacto ✅ *(Completada)*

#### 2.1 · Sidebar rediseñada con grupos y jerarquía ✅ *(Completada)*

**Propuesta:**
```
💎 Finanzas Pro
─────────────────────
  FINANZAS
  📊 Panel Principal        ← Activo: highlight azul con pill lateral
  📥 Ingresos
  💸 Egresos & Gastos

  PLANIFICACIÓN
  🎯 Presupuesto & Metas
  💳 Control de Deudas
  🔄 Puente USD → COP

  PATRIMONIO
  📈 Cuentas & Inversiones
  📖 Libro Mayor
  📊 Balance General

  SISTEMA
  ⚙️  Configuración
─────────────────────
  [balances + switch]
```

**Cambios concretos:**
- Agregar labels de grupo en mayúscula (`FINANZAS`, `PLANIFICACIÓN`, etc.)
- Cuando un botón está activo, mostrar una "píldora" lateral izquierda de 3px de color acento
- Reducir la fuente de los botones a `size=12` (peso `normal`, no bold)

#### 2.2 · StatCard con barra de acento superior ✅ *(Completada)*

Agregar un `CTkFrame` de altura 4px al tope de cada tarjeta con el `accent_color`. Esto da identidad visual instantánea.

```
┌──────────────────────────┐
█████ (barra azul 4px) ████│
│ 🏦 BÓVEDA USD             │
│ $2,450.00 USD            │
│ ≈ $9,800,000 COP líquidos│
└──────────────────────────┘
```

#### 2.3 · Banner de salud financiera simplificado ✅ *(Completada)*

Reducir a **2 métricas core** visibles y mover el detalle a un acordeón expandible o tooltip:
- Métrica 1: Resultado Neto del Mes (grande, con color semáforo)
- Métrica 2: Liquidez Total
- Botón "Ver detalle ▼" que expande la franja inferior

#### 2.4 · Feed de actividades agrupado por fecha ✅ *(Completada)*

```
HOY — 28 sep
├── 💵 Salario USD        +$1,200.00 USD
└── 📉 Netflix (USD)       -$17.99 USD

AYER — 27 sep
└── 💳 Mercado Éxito   -$145,000 COP
```

Agregar separadores de grupo con fecha en `TEXT_MUTED`, tamaño pequeño.

#### 2.5 · Sistema de botones unificado en Quick Actions ✅ *(Completada)*

En lugar de 6 colores distintos, usar **3 variantes semánticas**:
- **Primario** (azul `#0284c7`): acción principal → + Ingreso
- **Destructivo** (rojo `#e11d48`): eliminación o gasto → - Egreso
- **Neutro** (gris `#334155`): navegación → Libro Mayor, Inversiones

Y estandarizar: todos 32px de altura, `corner_radius=8`, misma fuente `size=12`.

---

### 🟢 Fase 3 — Refinamiento Premium *(En curso)*

#### 3.1 · Fuente multiplataforma ✅ *(Completada)*
- Creado `ui/utils/font_helper.py` con detección automática de SO (macOS: `SF Pro`, Windows: `Segoe UI`, Linux: `Ubuntu`).
- Definidos `Theme.FONT_DISPLAY` y `Theme.FONT_TEXT` en `ui/theme.py`.
- Migradas todas las vistas (Dashboard, Incomes, Expenses, Budget, Debts, Investments, Conversion, Ledger, Settings) y los 18 modales/componentes a las fuentes de `Theme`.

#### 3.2 · Estados vacíos elegantes (`EmptyState`) ✅ *(Completada)*
- Creado componente reutilizable `ui/components/empty_state.py` con badge de icono grande, título contrastado en `FONT_DISPLAY`, descripción explicativa en `FONT_TEXT` y botón de llamada a la acción (CTA) opcional.
- Integrado en Dashboard (categorías y feed de movimientos), Ingresos, Egresos (agenda fija e historial), Control de Deudas (préstamos y obligaciones), Inversiones (cuentas e historial), Conversión y Libro Mayor.

#### 3.3 · Micro-animaciones en vistas y sidebar
Al activar una vista o expandir acordeones, añadir transiciones y animaciones sutiles.

#### 3.4 · Estructura e indicadores de sección en formularios extensos ✅ *(Completada)*
- Añadidos divisores y encabezados numéricos de sección (`1. DATOS PRINCIPALES & MONTO`, `2. CALENDARIO & PLAZOS`, `3. OBSERVACIONES ADICIONALES`) para organizar visualmente los campos en modales extensos como `AddDebtModal`.

#### 3.5 · Toast notifications mejoradas ✅ *(Completada)*
- Modernizado `ui/components/toast.py` con soporte para variantes semánticas: éxito (✅), error (❌), advertencia (⚠️) e información (ℹ️).
- Paletas armónicas adaptadas a modo claro y oscuro, bordes coloreados y descarte automático seguro con temporizador.

---

## 📊 Resumen de Prioridades

```
IMPACTO
  │
  │  [Fase 2.1 Sidebar]    [Fase 2.2 StatCards]
  │
  │                    [Fase 2.3 Banner]   [Fase 3.2 Empty States]
  │
  │  [Fase 1.x Bugs]    [Fase 2.4 Feed]    [Fase 3.1 Fuentes]
  │
  └─────────────────────────────────────────────── ESFUERZO
     Bajo              Medio              Alto
```

---

## 🚀 Sugerencia de Orden de Implementación

1. **Empezar hoy:** Fase 1 completa (bugs/técnico) — son cambios seguros y preparatorios
2. **Siguiente sesión:** Fase 2.1 (sidebar) + 2.2 (StatCard acento) — mayor impacto visual por esfuerzo
3. **Después:** Fase 2.3 + 2.4 (banner y feed) — refinamiento del dashboard
4. **Opcional/largo plazo:** Fase 3 completa — pulido premium
