# Especificación del Formato Portable `.ecraft`

El formato `.ecraft` es un contenedor seguro, autocontenido y determinista basado en ZIP para exportar, compartir y restaurar proyectos completos de EmbedCraft RAG Studio.

## 1. Estructura Interna del Archivo

```
package/
├── manifest.json                  # Metadatos del proyecto, modelo y dimensiones
├── project.yaml                   # Configuración del proyecto libre de secretos
├── profiles/
│   ├── processing.yaml            # Parámetros de fragmentación y OCR
│   └── retrieval.yaml             # Configuración de búsqueda y reranking
├── data/
│   ├── documents.parquet          # Metadatos de documentos ingeridos
│   ├── document_versions.parquet  # Historial de versiones y hashes
│   ├── chunks.parquet             # Fragmentos de texto con posiciones y tokens
│   └── collections.parquet        # Colecciones asociadas al proyecto
├── vectors/
│   ├── embeddings.parquet         # Tabla de vectores densos normalizados
│   └── index/                     # Índices invertidos o HNSW (opcional)
├── reports/
│   ├── processing.json            # Estadísticas de ingestión y tiempos
│   └── quality.json               # Métricas de cobertura y completitud
├── schemas/                       # Esquemas JSON de validación
└── checksums.sha256               # Hashes criptográficos SHA-256 de cada archivo
```

## 2. Reglas de Seguridad y Ciberdefensa
1. **Defensa contra Zip Slip**: Todo proceso de importación y verificación comprueba que ninguna entrada del archivo contenga rutas relativas padre (`..`), rutas absolutas (`/` o `C:\`) o intente escapar del directorio de extracción seguro.
2. **Cero Secretos**: Las claves API y contraseñas nunca se exportan al paquete; solo se conservan en el Keyring del sistema operativo local.
3. **Privacidad de Rutas**: Las rutas absolutas del sistema de archivos origen son saneadas a rutas relativas seguras.
4. **Verificación Criptográfica**: Cada componente se valida contra `checksums.sha256` antes de desempaquetar o insertar registros en la base de datos local.
