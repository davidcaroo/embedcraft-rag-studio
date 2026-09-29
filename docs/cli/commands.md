# Referencia de Comandos CLI de EmbedCraft

El comando ejecutable de consola es `embedcraft`. Permite automatizar todas las operaciones del estudio con soporte para `--json` y formateo enriquecido mediante Rich.

## Resumen de Comandos

```bash
# Ayuda y Versión
embedcraft --help
embedcraft version
embedcraft doctor [--json]

# Gestión de Proyectos
embedcraft project create NAME [--description "..."]
embedcraft project list [--json]
embedcraft project show PROJECT [--json]
embedcraft project delete PROJECT [--yes]

# Gestión de Fuentes
embedcraft source add PROJECT PATH [--name NAME]
embedcraft source list PROJECT [--json]
embedcraft source remove PROJECT SOURCE_ID

# Pipeline de Ingestión
embedcraft ingest scan PROJECT [--json]
embedcraft ingest run PROJECT [--json]
embedcraft ingest status PROJECT [--json]

# Previsualización
embedcraft preview doc PROJECT PATH
embedcraft preview chunks PROJECT PATH

# Colecciones e Índices
embedcraft collection list PROJECT [--json]
embedcraft collection create PROJECT NAME
embedcraft index publish PROJECT [--collection default]
embedcraft index list PROJECT [--json]
embedcraft index rollback PROJECT REVISION_NUMBER

# Búsqueda y Chat RAG
embedcraft search PROJECT QUERY [--mode hybrid|vector|lexical] [--top-k 10]
embedcraft chat PROJECT [--query "..."] [--mode hybrid] [--retrieval-only] [--json]

# Portabilidad y Formato .ecraft
embedcraft export PROJECT OUTPUT [--include-vectors/--no-vectors] [--json]
embedcraft import PACKAGE [--name NEW_NAME] [--overwrite] [--json]
embedcraft package verify PACKAGE [--json]

# Evaluación Técnica
embedcraft evaluate PROJECT DATASET [--k 10] [--mode hybrid] [--json]

# Interfaz Gráfica
embedcraft gui
```
