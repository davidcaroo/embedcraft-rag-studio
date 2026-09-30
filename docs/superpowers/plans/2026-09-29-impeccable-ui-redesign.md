# Rediseño Impeccable de UI: Iconografía Vectorial, Tema Claro/Oscuro y Adaptabilidad

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar por completo el uso de emojis en toda la interfaz gráfica de EmbedCraft RAG Studio, reemplazándolos con un sistema de iconografía vectorial profesional basado en SVG, implementando soporte fluido para Modo Claro y Modo Oscuro con selector interactivo en la cabecera, y garantizando una adaptabilidad de pantalla responsiva y fluida ante cualquier tamaño de ventana.

**Architecture:** Se implementa un motor desacoplado de iconos vectoriales en `embedcraft.gui.icons` que renderiza SVG de precisión geométrica teñidos dinámicamente según el tema activo. Se refactoriza `theme.py` y `styles.py` para introducir un `ThemeManager` con paletas completas `DARK` y `LIGHT` conformes con WCAG 2.1 AA. Todos los componentes y vistas se adaptan mediante `QScrollArea`, políticas de tamaño elásticas (`QSizePolicy.Expanding`), `QSplitter` elásticos y estados semánticos sin texto emoji.

**Tech Stack:** Python 3.11+, PySide6 (Qt6: `QIcon`, `QPixmap`, `QSvgRenderer`, `QPainter`, `QScrollArea`, `QSplitter`, `QPropertyAnimation`), pytest, pytest-qt.

**Spec:** Directiva de usuario de rediseño frontend bajo la metodología `/impeccable`, eliminando emojis, introduciendo iconos SVG dedicados, selector claro/oscuro y diseño responsivo adaptativo.

---

## Global Constraints

- **Cero Emojis:** Queda estrictamente prohibido el uso de caracteres emoji (ej. 📊, 📁, ⚡, 🔍, 📚, 💬, 🩺, ✔, ⚠, ✖, 🚀, 💾, ⏳) en cualquier elemento visual, botón, etiqueta, encabezado, tooltip, chip de estado o diálogo.
- **Iconografía Vectorial:** Todos los iconos deben ser generados a partir de paths vectoriales limpios (estilo Lucide / Feather / Heroicons), sin dependencias de fuentes de iconos externas ni archivos binarios no rastreados.
- **Contraste y Accesibilidad:** Tanto el Modo Oscuro como el Modo Claro deben cumplir una relación de contraste mínima de 4.5:1 para texto normal (WCAG AA).
- **Inmutabilidad de Lógica de Dominio:** Ningún cambio en la UI debe alterar las firmas de casos de uso ni la lógica de la arquitectura hexagonal.
- **Retrocompatibilidad de Tests:** La suite completa de 69 tests existentes debe seguir pasando al 100% tras cada tarea.

---

## File Structure & Responsibilities

| Archivo | Responsabilidad |
| :--- | :--- |
| `src/embedcraft/gui/icons.py` | Motor de generación y caché de iconos SVG vectoriales tintados dinámicamente (`get_icon`, `get_pixmap`). |
| `src/embedcraft/gui/theme.py` | Definición de tokens de diseño para `LIGHT` y `DARK`, gestión de estado (`ThemeManager`) y señales de cambio de tema. |
| `src/embedcraft/gui/styles.py` | Generador QSS modular reactivo a tokens de tema (soporte dual para Modo Claro y Modo Oscuro). |
| `src/embedcraft/gui/components/header.py` | Cabecera superior con selector de proyecto limpio y botón de alternancia Claro/Oscuro con icono dinámico Sol/Luna. |
| `src/embedcraft/gui/components/sidebar.py` | Barra lateral con iconografía vectorial en cada sección y navegación con retroalimentación visual refinada. |
| `src/embedcraft/gui/components/card.py` | Tarjetas y StatBoxes elásticos, sin colores de texto cableados y con soporte de iconos vectoriales. |
| `src/embedcraft/gui/main_window.py` | Ventana principal con orquestación del cambio de tema en vivo y responsividad ante redimensionado. |
| `src/embedcraft/gui/views/*.py` | Vistas de la aplicación adaptadas con `QScrollArea`, splitters flexibles y chips de estado tipográficos. |
| `tests/unit/test_gui_icons.py` | Pruebas unitarias del motor de iconos y tintado dinámico. |
| `tests/unit/test_gui_theme.py` | Pruebas unitarias del `ThemeManager` y generación de estilos claros/oscuros. |

---

### Task 1: Motor de Iconografía Vectorial SVG (`src/embedcraft/gui/icons.py`)

**Files:**
- Create: `src/embedcraft/gui/icons.py`
- Create: `tests/unit/test_gui_icons.py`

**Interfaces:**
- Produces: `get_icon(name: str, color: str | None = None, size: int = 18) -> QIcon`
- Produces: `get_pixmap(name: str, color: str | None = None, size: int = 18) -> QPixmap`
- Produces: Catálogo semántico de iconos: `dashboard`, `projects`, `monitor`, `preview`, `collections`, `chat`, `doctor`, `sun`, `moon`, `plus`, `download`, `upload`, `play`, `stop`, `refresh`, `check`, `alert`, `close`, `folder`, `file`.

- [ ] **Step 1: Escribir el test unitario para el motor de iconos**

```python
# tests/unit/test_gui_icons.py
import pytest
from PySide6.QtGui import QIcon, QPixmap
from embedcraft.gui.icons import get_icon, get_pixmap, list_available_icons


def test_list_available_icons_contains_core_keys():
    icons = list_available_icons()
    expected = {"dashboard", "projects", "monitor", "preview", "collections", "chat", "doctor", "sun", "moon"}
    assert expected.issubset(icons)


def test_get_icon_returns_valid_qicon(qapp):
    icon = get_icon("dashboard", color="#6366F1", size=24)
    assert isinstance(icon, QIcon)
    assert not icon.isNull()


def test_get_pixmap_dimensions(qapp):
    pixmap = get_pixmap("sun", color="#F59E0B", size=32)
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    assert pixmap.width() == 32
    assert pixmap.height() == 32


def test_get_icon_unknown_name_fallback(qapp):
    icon = get_icon("non_existent_icon_name")
    assert isinstance(icon, QIcon)
```

- [ ] **Step 2: Ejecutar el test para verificar que falla**

Run: `.venv\Scripts\pytest tests/unit/test_gui_icons.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'embedcraft.gui.icons'`

- [ ] **Step 3: Implementar el módulo `icons.py` con SVGs puros**

Crear `src/embedcraft/gui/icons.py` conteniendo paths SVG vectoriales geométricos (24x24 viewBox, stroke-width 2, round joins) y el renderizador mediante `QSvgRenderer` y `QPainter`.

- [ ] **Step 4: Ejecutar el test para verificar que pasa**

Run: `.venv\Scripts\pytest tests/unit/test_gui_icons.py -v`
Expected: PASS

- [ ] **Step 5: Commit de la tarea**

```bash
git add src/embedcraft/gui/icons.py tests/unit/test_gui_icons.py
git commit -m "feat(gui): implement vector SVG icon engine for crisp resolution-independent UI"
```

---

### Task 2: Arquitectura Dual de Temas y Estilos QSS (`theme.py` & `styles.py`)

**Files:**
- Modify: `src/embedcraft/gui/theme.py`
- Modify: `src/embedcraft/gui/styles.py`
- Create: `tests/unit/test_gui_theme.py`

**Interfaces:**
- Consumes: Tokens de color y estados de tema.
- Produces: `ThemeMode(Enum)` con `LIGHT` y `DARK`.
- Produces: `ThemeManager` con `current_mode`, `toggle_theme()`, y señal `theme_changed = Signal(str)`.
- Produces: `get_application_stylesheet(mode: ThemeMode = ThemeMode.DARK) -> str`.

- [ ] **Step 1: Escribir el test unitario para el `ThemeManager` y generación QSS**

```python
# tests/unit/test_gui_theme.py
import pytest
from embedcraft.gui.theme import ThemeManager, ThemeMode, get_palette
from embedcraft.gui.styles import get_application_stylesheet


def test_theme_manager_toggle():
    manager = ThemeManager()
    manager.set_mode(ThemeMode.DARK)
    assert manager.mode == ThemeMode.DARK

    manager.toggle_theme()
    assert manager.mode == ThemeMode.LIGHT

    manager.toggle_theme()
    assert manager.mode == ThemeMode.DARK


def test_stylesheet_generation_both_modes():
    dark_qss = get_application_stylesheet(ThemeMode.DARK)
    light_qss = get_application_stylesheet(ThemeMode.LIGHT)

    assert dark_qss != light_qss
    assert "QMainWindow" in dark_qss
    assert "QMainWindow" in light_qss
```

- [ ] **Step 2: Ejecutar el test para verificar que falla**

Run: `.venv\Scripts\pytest tests/unit/test_gui_theme.py -v`
Expected: FAIL con `ImportError: cannot import name 'ThemeMode'`

- [ ] **Step 3: Implementar la arquitectura dual de temas en `theme.py` y `styles.py`**

1. Definir `DARK_PALETTE` (fondo grafito oscuro `#0B0F19`, superficies `#111827`, tarjetas `#1F2937`, bordes `#374151`, texto `#F9FAFB` y `#9CA3AF`).
2. Definir `LIGHT_PALETTE` (fondo blanco/pizarra `#F8FAFC`, superficies `#FFFFFF`, tarjetas `#FFFFFF`, bordes `#E2E8F0`, texto `#0F172A` y `#64748B`).
3. Crear clase `ThemeManager(QObject)` con señal `theme_changed`.
4. Refactorizar `get_application_stylesheet(mode: ThemeMode)` en `styles.py` para usar dinámicamente los tokens de la paleta activa, asegurando soporte para inputs, botones, tablas, splitters y tarjetas en ambos modos.

- [ ] **Step 4: Ejecutar el test para verificar que pasa**

Run: `.venv\Scripts\pytest tests/unit/test_gui_theme.py -v`
Expected: PASS

- [ ] **Step 5: Commit de la tarea**

```bash
git add src/embedcraft/gui/theme.py src/embedcraft/gui/styles.py tests/unit/test_gui_theme.py
git commit -m "feat(gui): introduce ThemeManager with dark and light mode stylesheet generation"
```

---

### Task 3: Rediseño del Shell Principal (`Sidebar`, `HeaderBar`, `MainWindow`)

**Files:**
- Modify: `src/embedcraft/gui/components/sidebar.py`
- Modify: `src/embedcraft/gui/components/header.py`
- Modify: `src/embedcraft/gui/main_window.py`
- Modify: `tests/gui/test_gui.py`

**Interfaces:**
- Consumes: `get_icon` desde `embedcraft.gui.icons`, `theme_manager` desde `embedcraft.gui.theme`.
- Produces: Barra lateral con navegación por iconos vectoriales SVG sin emojis.
- Produces: Cabecera con botón de alternancia Claro/Oscuro (icono Sol / Luna) y combo limpio de proyectos.
- Produces: `MainWindow` que re-aplica el stylesheet global en tiempo real ante la señal `theme_changed`.

- [ ] **Step 1: Escribir tests para la navegación con iconos y alternancia de tema**

Actualizar `tests/gui/test_gui.py` verificando:
1. Ningún botón de la barra lateral contiene caracteres fuera de ASCII/Latin estándar (cero emojis).
2. El botón de cambio de tema en `HeaderBar` invoca `theme_manager.toggle_theme()` y emite la señal.
3. La ventana principal responde al cambio de tema actualizando su apariencia.

- [ ] **Step 2: Ejecutar el test para verificar el fallo**

Run: `.venv\Scripts\pytest tests/gui/test_gui.py -v`
Expected: FAIL por aserciones de emojis existentes en `sidebar.py`.

- [ ] **Step 3: Implementar el rediseño en `sidebar.py`, `header.py` y `main_window.py`**

1. En `sidebar.py`: eliminar emojis (`📊`, `📁`, etc.), asociar `setIcon(get_icon(key))` a cada item con tamaño estándar (18x18), espaciado limpio y tipografía refinada.
2. En `header.py`: eliminar `📁` del combo de proyectos. Añadir botón `btn_theme` con icono vectorial `moon` (en modo claro) o `sun` (en modo oscuro), conectado a `theme_manager.toggle_theme()`.
3. En `main_window.py`: conectar `theme_manager.theme_changed` para actualizar `QApplication.instance().setStyleSheet(...)` y refrescar los iconos de navegación con el color correspondiente.

- [ ] **Step 4: Ejecutar los tests de GUI para verificar que pasan**

Run: `.venv\Scripts\pytest tests/gui/test_gui.py -v`
Expected: PASS

- [ ] **Step 5: Commit de la tarea**

```bash
git add src/embedcraft/gui/components/sidebar.py src/embedcraft/gui/components/header.py src/embedcraft/gui/main_window.py tests/gui/test_gui.py
git commit -m "feat(gui): integrate vector icons in sidebar and live theme toggle in header"
```

---

### Task 4: Rediseño Responsivo de Vistas Base (`Card`, `StatBox`, `DashboardView`, `ProjectsView`, `DoctorView`)

**Files:**
- Modify: `src/embedcraft/gui/components/card.py`
- Modify: `src/embedcraft/gui/views/dashboard_view.py`
- Modify: `src/embedcraft/gui/views/projects_view.py`
- Modify: `src/embedcraft/gui/views/doctor_view.py`

**Interfaces:**
- Consumes: `get_icon`, clases CSS semánticas de `styles.py`.
- Produces: `StatBox` con soporte para `icon_name: str` vectorial.
- Produces: Layouts envueltos en `QScrollArea(widgetResizable=True)` para adaptabilidad completa en resoluciones desde 960x640 hasta 4K.
- Produces: Chips de estado tipográficos (`[OK]`, `[ADVERTENCIA]`, `[ERROR]`, `[ACTIVO]`, `[BORRADOR]`) con estilos semánticos y cero emojis.

- [ ] **Step 1: Escribir el test de adaptabilidad y ausencia de emojis en vistas base**

Añadir test en `tests/gui/test_gui.py` que recorra todas las vistas base e inspeccione recursivamente los textos de `QPushButton`, `QLabel` y `QTableWidgetItem`, verificando que no existan emojis.

- [ ] **Step 2: Ejecutar el test para verificar que falla**

Run: `.venv\Scripts\pytest tests/gui/test_gui.py -k "test_no_emojis_in_base_views" -v`
Expected: FAIL detectando emojis en botones y stat cards de Dashboard, Proyectos y Doctor.

- [ ] **Step 3: Implementar la refactorización en `card.py`, `dashboard_view.py`, `projects_view.py` y `doctor_view.py`**

1. `card.py`: eliminar colores `#0F172A` cableados; adaptar `StatBox` para recibir `icon_name` vectorial y pintarlo con `QLabel.setPixmap(get_pixmap(...))`.
2. `dashboard_view.py`: sustituir emojis en StatBoxes (`projects`, `file`, `layers`, `activity`); sustituir texto de acciones rápidas por texto limpio con iconos vectoriales (`plus`, `play`, `search`, `doctor`). Envolver la vista en `QScrollArea` para fluidez responsiva.
3. `projects_view.py`: limpiar botones de importación/exportación (`📥` $\rightarrow$ `get_icon('download')`, `📤` $\rightarrow$ `get_icon('upload')`, `📁` $\rightarrow$ `get_icon('folder')`, `📄` $\rightarrow$ `get_icon('file')`). Configurar splitters elásticos.
4. `doctor_view.py`: sustituir `🔄` por `get_icon('refresh')`. En la tabla de diagnósticos, usar `QLabel` con clases semánticas `badgeSuccess`, `badgeWarning`, `badgeError` sin caracteres emoji.

- [ ] **Step 4: Ejecutar el test para verificar que pasa**

Run: `.venv\Scripts\pytest tests/gui/test_gui.py -v`
Expected: PASS

- [ ] **Step 5: Commit de la tarea**

```bash
git add src/embedcraft/gui/components/card.py src/embedcraft/gui/views/dashboard_view.py src/embedcraft/gui/views/projects_view.py src/embedcraft/gui/views/doctor_view.py
git commit -m "refactor(gui): remove emojis from dashboard, projects and doctor views with responsive scroll areas"
```

---

### Task 5: Rediseño Responsivo de Vistas Interactivas (`MonitorView`, `PreviewView`, `ChatView`, `CollectionsView`)

**Files:**
- Modify: `src/embedcraft/gui/views/monitor_view.py`
- Modify: `src/embedcraft/gui/views/preview_view.py`
- Modify: `src/embedcraft/gui/views/chat_view.py`
- Modify: `src/embedcraft/gui/views/collections_view.py`

**Interfaces:**
- Consumes: `get_icon`, clases CSS semánticas.
- Produces: Vistas interactivas completamente adaptables, sin emojis y con diseño oscuro/claro balanceado.

- [ ] **Step 1: Escribir test de validación para las 4 vistas interactivas**

Añadir test en `tests/gui/test_gui.py` validando que `MonitorView`, `PreviewView`, `ChatView` y `CollectionsView` no posean emojis en sus controles y que sus splitters tengan factores de estiramiento elásticos configurados.

- [ ] **Step 2: Ejecutar el test para verificar que falla**

Run: `.venv\Scripts\pytest tests/gui/test_gui.py -k "test_interactive_views_clean" -v`
Expected: FAIL con mención de emojis en `chat_view` (`💾`), `monitor_view` (`⚡`, `🛑`), `collections_view` (`🚀`, `↩`).

- [ ] **Step 3: Implementar la refactorización de las vistas interactivas**

1. `monitor_view.py`: cambiar botones a iconos vectoriales (`play` para iniciar ingesta, `stop` para cancelar). Reemplazar flechas de texto con indicadores visuales de progreso limpios.
2. `preview_view.py`: ajustar el inspector tri-panel (`QSplitter`) con `setCollapsible(False)` y tamaños mínimos elásticos.
3. `chat_view.py`: botón exportar con icono vectorial `download`. Eliminar estilos de color hardcodeados en burbujas y paneles para heredar del stylesheet reactivo.
4. `collections_view.py`: botones de publicación y rollback con iconos vectoriales `upload` y `refresh`.

- [ ] **Step 4: Ejecutar el test para verificar que pasa**

Run: `.venv\Scripts\pytest tests/gui/test_gui.py -v`
Expected: PASS

- [ ] **Step 5: Commit de la tarea**

```bash
git add src/embedcraft/gui/views/monitor_view.py src/embedcraft/gui/views/preview_view.py src/embedcraft/gui/views/chat_view.py src/embedcraft/gui/views/collections_view.py
git commit -m "refactor(gui): polish interactive views with vector icons and adaptive splitters"
```

---

### Task 6: Actualización de Capturas Reales y Verificación End-to-End

**Files:**
- Modify: `scripts/capture_screenshots.py`
- Update: `docs/assets/screenshots/*.png`
- Modify: `README.md` (si requiere actualizar referencias de capturas o tema claro/oscuro)

**Interfaces:**
- Consumes: Aplicación PySide6 completa con las nuevas capacidades.
- Produces: Capturas de pantalla reales actualizadas en `docs/assets/screenshots/` reflejando la nueva UI limpia sin emojis, con iconos vectoriales y soporte de temas.

- [ ] **Step 1: Ejecutar la batería completa de tests del repositorio**

Run: `.venv\Scripts\pytest tests/ -v`
Expected: 69+ tests passing al 100%.

- [ ] **Step 2: Ejecutar el análisis estático y formateo con Ruff**

Run: `.venv\Scripts\ruff check .`
Expected: `All checks passed!`

- [ ] **Step 3: Actualizar el script de capturas y regenerar las imágenes oficiales**

Ejecutar `scripts/capture_screenshots.py` para generar las nuevas capturas de pantalla de alta resolución (1280x820) sin emojis y con la nueva iconografía vectorial.

- [ ] **Step 4: Confirmar la integridad visual y commitear**

```bash
git add docs/assets/screenshots README.md
git commit -m "docs: refresh real screenshots with clean vector icon UI and dual theme support"
git push origin main
```

---

## Self-Review Checklist

- [x] **Spec coverage:** El plan cubre específicamente: eliminación total de emojis, iconografía vectorial correcta, selector de modo claro / modo oscuro con iconos Sol/Luna, adaptabilidad responsiva ante cambios de tamaño y micro-interacciones.
- [x] **Placeholder scan:** No existen "TODO", "TBD", ni instrucciones vacías. Cada tarea contiene archivos exactos, tests concretos y comandos ejecutables.
- [x] **Type consistency:** Las funciones `get_icon`, `ThemeManager`, `ThemeMode` y las señales de navegación mantienen firmas coherentes a lo largo de todas las tareas.
