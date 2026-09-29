# Arquitectura de EmbedCraft RAG Studio

## 1. Patrones Arquitectónicos
EmbedCraft RAG Studio está fundamentado en una **arquitectura hexagonal** (puertos y adaptadores). El núcleo de dominio es completamente agnóstico de la infraestructura y bibliotecas externas.

La persistencia estructurada utiliza **SQLite en modo WAL** (Write-Ahead Logging) para garantizar concurrencia libre de bloqueos y transacciones ACID. El motor vectorial primario es **LanceDB**, el cual almacena representaciones densas directamente en disco con formato Apache Arrow sin requerir servidores externos en ejecución.

## 2. Política Estricta Anti-Alucinaciones
El motor de chat RAG implementa una política de **grounding cerrado**:
- Las respuestas se derivan exclusivamente del contexto recuperado.
- Si no existe evidencia suficiente en los fragmentos devueltos, el sistema responde explícitamente: *"No dispongo de evidencia suficiente en las fuentes indexadas para responder a esta pregunta."*
- Toda afirmación relevante está respaldada por una cita verificable con número de documento, ruta y extracto original.

## 3. Portabilidad y Formato .ecraft
La distribución y migración de proyectos se realiza a través de paquetes con extensión `.ecraft`.
Cada archivo `.ecraft` es un archivo ZIP autocontenido que contiene:
- `manifest.json`: metadatos del proyecto, modelo y dimensiones.
- `project.yaml`: configuración del proyecto libre de secretos o credenciales.
- `data/*.parquet`: tablas de documentos, chunks y colecciones en formato Parquet comprimido con Snappy.
- `checksums.sha256`: hashes criptográficos de cada componente para validación y defensa activa contra ataques de path traversal (Zip Slip).
