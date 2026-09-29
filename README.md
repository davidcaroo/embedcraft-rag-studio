# EmbedCraft RAG Studio

EmbedCraft RAG Studio es una aplicación profesional de escritorio (PySide6) y consola (Typer) diseñada para crear, gestionar, probar y exportar sistemas de Recuperación Aumentada por Generación (RAG) de grado empresarial en Windows.

## Características Principales
- **Arquitectura Hexagonal:** Desacoplamiento estricto entre núcleo de dominio, puertos, adaptadores, CLI y GUI.
- **RAG Multi-Colección & Vista Unificada:** Búsqueda vectorial, búsqueda léxica (SQLite FTS5) e indexación híbrida con trazabilidad de citas.
- **Gestión Incremental e Idempotente:** Ingestión de lotes de hasta 100k documentos con detección de cambios por hash (Blake3/SHA-256).
- **Publicación Atómica por Revisiones:** Transición de estados `draft` -> `staging` -> `active` con soporte de rollback sin tiempo de inactividad.
- **Seguridad Integrada:** Gestión de credenciales mediante Windows Credential Manager (`keyring`), redacción de secretos y prevención de path traversal.
- **Portabilidad Total:** Empaquetado y distribución en formato abierto `.ecraft` (ZIP + Parquet + Schemas).

## Instalación y Desarrollo
```bash
# Activar entorno virtual
.venv\Scripts\activate

# Instalar dependencias en modo editable
pip install -e ".[dev]"
```
