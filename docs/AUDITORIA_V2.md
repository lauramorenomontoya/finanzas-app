# 📋 Informe de Auditoría de Arquitectura y Diseño UI/UX

## 1. Resumen Ejecutivo
La aplicación ha alcanzado un estado de madurez funcional (v1.0.0 publicada), logrando aislar correctamente la base de datos por usuario (Application Support / APPDATA) y automatizar el despliegue con GitHub Actions. No obstante, el código actual sufre de fugas de lógica de negocio hacia la capa de presentación (UI), creación de God Components (ej. settings.py de +850 líneas) y una ausencia de un sistema estricto de Design Tokens. Esto genera inconsistencias visuales y dificulta la reutilización de código. El objetivo principal de las próximas iteraciones debe ser el desacoplamiento total (Separation of Concerns) y la unificación del Design System.

---

## 2. Hallazgos Estructurales (Arquitectura y Código)

### 🔴 2.1. Fuga de Lógica de Negocio y "God Components"
- **Modularidad y SoC (Separation of Concerns)**: Actualmente, las vistas (UI) no son "tontas". Archivos como `expenses.py` y `settings.py` contienen validaciones de negocio e información "hardcodeada" (como listas estáticas de categorías o flujos de inserción directa a base de datos).
- **God Components**: El archivo `settings.py` se ha convertido en un componente monolítico de más de 850 líneas. Al manejar múltiples flujos CRUD simultáneamente, viola el principio de responsabilidad única (SRP).

### 🟡 2.2. Flujo de Datos y Concurrencia
- **Gestión Asíncrona**: Es excelente el uso de threading y `.after()` en las vistas para interactuar con servicios pesados como CurrencyService sin congelar la UI de CustomTkinter.
- **Prop Drilling y Estado**: La base de datos (`db_manager`) se pasa continuamente hacia abajo ("prop drilling") por todas las vistas. Sería mucho más escalable utilizar un patrón de Inyección de Dependencias o una capa de repositorios/controladores intermedia, de modo que las vistas solo llamen a métodos como `ExpensesController.add_expense(...)`.

### 🟡 2.3. Deuda Técnica en la Capa de Datos
- **Mixins sobrecargados**: La lógica de la base de datos está dispersa en varios archivos `_mixin.py`. Si la aplicación sigue creciendo, esta estructura puede volverse frágil. Se recomienda transicionar de mixins de SQLite puro a un patrón Repository o utilizar un ORM ligero si la estructura relacional se vuelve más compleja.

---

## 3. Hallazgos Estéticos (Diseño UI/UX)

### 🔴 3.1. Ausencia de un Sistema Estricto de "Design Tokens"
- **Uso del Color**: Aunque existe el archivo `theme.py` con paletas adaptables para Modo Claro/Oscuro, he detectado múltiples valores Hexadecimales estáticos dispersos a lo largo de los componentes de UI. Esto rompe la consistencia y hace casi imposible implementar un re-skinning de la app con seguridad.

### 🟡 3.2. Espaciado, Alineación y Consistencia (Grid System)
- **Márgenes y Paddings inconsistentes**: Hay una mezcla de paddings fijos calculados "al ojo" componente por componente. Un diseño premium requiere una escala de espaciado matemática (por ejemplo, escala de 4px u 8px: xs=4, sm=8, md=16, lg=24, xl=32).
- **Jerarquía Visual**: El Dashboard muestra demasiados pesos visuales similares. Es necesario generar mayor contraste entre las métricas clave (Hero metrics) y los controles secundarios.

### 🟢 3.3. Feedback y Microinteracciones
- **Puntos fuertes**: Componentes como `ToastNotification`, `ConfirmDialog`, `BalanceWarningDialog` y `EmptyState` aportan un excelente feedback al usuario y previenen errores destructivos. Son componentes que aportan ese nivel "Premium" que buscamos.

---

## 4. Plan de Acción en 2 Fases

### 🚀 Fase 1: Quick Wins (Alto impacto, bajo esfuerzo) -> ✅ (Completado)
Estas tareas buscan estabilizar la consistencia visual y limpiar la "suciedad" superficial del código.
- [x] **Unificación de Tokens de Diseño**: Eliminar todos los valores hexadecimales hardcodeados en las vistas y usar `Theme.*`.
- [x] **Escala de espaciado estándar**: Aplicar `SPACING_SM`, `SPACING_MD`, etc., en toda la UI.
- [x] **Extracción de Constantes**: Mover las listas estáticas a un archivo de configuración puro `core/constants.py`.
- [x] **Estandarización de Modales**: Unificar el código repetitivo de creación de las ventanas secundarias (`BaseModal`).

### 🛠 Fase 2: Refactoring Profundo (Arquitectura Limpia) -> 🔄 (En progreso)
Estas tareas implican reestructurar la lógica de negocio para hacer la app altamente escalable.
- [x] **Desacoplar la Base de Datos de las Vistas (Patrón MVC / Repository)**: Eliminar llamados directos de sentencias SQL en las vistas UI y usar Controladores (Ej. `ExpenseController`).
- [x] **Descomposición del Monolito `settings.py`**: Dividir este archivo gigante en sub-componentes independientes: `SettingsProfileView`, `SettingsDataView`, `SettingsPreferencesView`, etc.
- [x] **Jerarquía Visual del Dashboard**: Generar mayor contraste entre métricas clave y controles.
- [x] **Gestor de Estado Centralizado (Opcional)**: Implementar un patrón de Pub/Sub simple (Event Bus) para evitar el prop drilling con `on_data_changed`.
