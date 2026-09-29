# 🔍 Diagnóstico & Plan de Mejoras — Control Financiero

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

### 🔵 Fase 1 — Bugs & Deuda Técnica *(~2-3 horas)*

| # | Tarea | Archivo |
|---|---|---|
| 1.1 | Agregar `Any` al import de `typing` | `ui/app.py` |
| 1.2 | Crear `ui/utils/modal_helper.py` con `center_window()` y refactorizar todos los modales | `ui/utils/` |
| 1.3 | Mover archivos de test a `tests/` | Raíz del proyecto |
| 1.4 | Actualizar `.gitignore` para excluir `*.db-shm`, `*.db-wal`, `temp_*` | `.gitignore` |
| 1.5 | Agregar `logging` básico en lugar de `print()` en `main.py` | `main.py` |

---

### 🟡 Fase 2 — Mejoras de UI de Alto Impacto *(~4-6 horas)*

#### 2.1 · Sidebar rediseñada con grupos y jerarquía

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

#### 2.2 · StatCard con barra de acento superior

Agregar un `CTkFrame` de altura 4px al tope de cada tarjeta con el `accent_color`. Esto da identidad visual instantánea.

```
┌──────────────────────────┐
█████ (barra azul 4px) ████│
│ 🏦 BÓVEDA USD             │
│ $2,450.00 USD            │
│ ≈ $9,800,000 COP líquidos│
└──────────────────────────┘
```

#### 2.3 · Banner de salud financiera simplificado

Reducir a **2 métricas core** visibles y mover el detalle a un acordeón expandible o tooltip:
- Métrica 1: Resultado Neto del Mes (grande, con color semáforo)
- Métrica 2: Liquidez Total
- Botón "Ver detalle ▼" que expande la franja inferior

#### 2.4 · Feed de actividades agrupado por fecha

```
HOY — 28 sep
├── 💵 Salario USD        +$1,200.00 USD
└── 📉 Netflix (USD)       -$17.99 USD

AYER — 27 sep
└── 💳 Mercado Éxito   -$145,000 COP
```

Agregar separadores de grupo con fecha en `TEXT_MUTED`, tamaño pequeño.

#### 2.5 · Sistema de botones unificado en Quick Actions

En lugar de 6 colores distintos, usar **3 variantes semánticas**:
- **Primario** (azul `#0284c7`): acción principal → + Ingreso
- **Destructivo** (rojo `#e11d48`): eliminación o gasto → - Egreso
- **Neutro** (gris `#334155`): navegación → Libro Mayor, Inversiones

Y estandarizar: todos 32px de altura, `corner_radius=8`, misma fuente `size=12`.

---

### 🟢 Fase 3 — Refinamiento Premium *(~3-5 horas)*

#### 3.1 · Fuente multiplataforma

Reemplazar `"SF Pro Display"` / `"SF Pro Text"` por una fuente disponible multiplataforma:
- **Opción A (sin instalación):** `"Segoe UI"` en Windows, `"Helvetica Neue"` en macOS, `"Ubuntu"` en Linux — con detección automática
- **Opción B (recomendada):** Empaquetar `Inter` o `DM Sans` como TTF dentro del proyecto y cargarla con `tkfont`

```python
# ui/utils/fonts.py
import platform
def get_system_font():
    sys = platform.system()
    if sys == "Darwin": return "SF Pro Display"
    if sys == "Windows": return "Segoe UI"
    return "Ubuntu"
```

#### 3.2 · Estados vacíos elegantes

Para pantallas sin datos, reemplazar el label de texto plano por un componente visual:

```
        📭
   Sin movimientos aún
   Registra tu primer ingreso
   para empezar a ver tus métricas.

   [📥 + Agregar Ingreso]
```

Crear `ui/components/empty_state.py` reutilizable.

#### 3.3 · Micro-animaciones en el sidebar

Al activar una vista, hacer un fade suave del contenido en lugar de un swap abrupto:

```python
def _fade_in(self, widget, steps=6, delay=16):
    """Incrementa opacity simulando un fade-in."""
    # ... implementar con .after() y alpha
```

> En CTK/Tkinter en macOS se puede usar `self.attributes("-alpha", value)` a nivel de toplevel; para frames internos se simula con color interpolation.

#### 3.4 · Indicadores de progreso en formularios multi-paso

Para modales largos como `AddDebtModal` o `EditBudgetModal`, agregar un stepper simple en el header:

```
● Datos básicos  ——  ○ Calendario  ——  ○ Confirmar
```

#### 3.5 · Toast notifications mejoradas

El sistema de toasts actual (`toast.py`) es un label simple. Mejorar con:
- Icono de tipo (✅ éxito, ❌ error, ⚠️ advertencia)
- Barra de progreso de duración visible
- Animación de entrada desde abajo

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
