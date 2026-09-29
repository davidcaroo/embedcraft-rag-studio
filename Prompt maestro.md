**Prompt maestro — EmbedCraft RAG Studio**

Actúa como arquitecto de software sénior e ingeniero Python especializado en aplicaciones de escritorio, sistemas RAG, procesamiento documental y empaquetado para Windows.

Debes diseñar e implementar **EmbedCraft RAG Studio**, una aplicación profesional para crear, administrar, probar y exportar sistemas RAG.

No entregues únicamente prototipos, pseudocódigo o pantallas estáticas. Construye una aplicación funcional, modular, probada y preparada para distribuirse como instalador de Windows.

**1. Objetivo del producto**

EmbedCraft RAG Studio debe permitir:

* Crear proyectos RAG.
* Importar documentos individualmente o por lotes.
* Procesar hasta 100.000 documentos o aproximadamente 10 millones de fragmentos.
* Extraer, normalizar, fragmentar y vectorizar contenido.
* Detectar documentos nuevos, modificados y eliminados.
* Reprocesar únicamente lo necesario.
* Crear índices independientes por colección.
* Consultar varias colecciones mediante una vista RAG unificada.
* Previsualizar texto extraído, metadatos y fragmentos.
* Probar recuperación y generación mediante chat.
* Mostrar citas y trazabilidad hasta el documento original.
* Exportar proyectos en un formato portable.
* Usarse mediante GUI y CLI.
* Funcionar con modelos locales o proveedores API.
* Descargar modelos locales bajo demanda.
* Pausar, reanudar, cancelar y recuperar trabajos interrumpidos.

El producto debe priorizar Windows 10 y Windows 11, pero el núcleo Python debe evitar dependencias innecesarias del sistema operativo.

**2. Principios obligatorios**

1. La GUI y la CLI deben utilizar exactamente los mismos casos de uso.
2. No debe existir lógica RAG dentro de widgets, ventanas o comandos CLI.
3. El núcleo no debe depender directamente de LangChain o LlamaIndex.
4. LangChain y LlamaIndex solo podrán añadirse posteriormente como adaptadores opcionales.
5. Los documentos originales nunca deben modificarse.
6. Las operaciones de indexación deben ser incrementales e idempotentes.
7. Una consulta nunca debe acceder a un índice parcialmente actualizado.
8. Las credenciales nunca deben almacenarse en texto plano.
9. Los modelos locales no deben incluirse en el instalador; deben descargarse bajo demanda.
10. Todo proveedor debe poder sustituirse mediante interfaces estables.
11. Los trabajos pesados nunca deben bloquear el hilo de la GUI.
12. Cada respuesta RAG debe poder explicar qué fragmentos, filtros y modelos utilizó.

**3. Arquitectura**

Implementa una arquitectura hexagonal o de puertos y adaptadores:

GUI PySide6 ─┐

├─> Application Services ─> Domain

CLI Typer ───┘ │

└─> Ports ─> Adapters

Capas:

src/embedcraft/

├── domain/

├── application/

├── ports/

├── adapters/

├── infrastructure/

├── gui/

├── cli/

└── bootstrap/

**domain**

Debe contener entidades y reglas independientes de frameworks:

* Project
* Source
* Document
* DocumentVersion
* Chunk
* Collection
* IndexRevision
* ProcessingProfile
* ProviderProfile
* Job
* JobStep
* RetrievalResult
* Citation
* ExportManifest

**application**

Casos de uso:

* Crear, abrir, editar y eliminar proyectos.
* Registrar fuentes.
* Analizar un lote antes de procesarlo.
* Iniciar, pausar, reanudar y cancelar trabajos.
* Crear previews.
* Procesar documentos.
* Publicar revisiones.
* Ejecutar búsquedas.
* Probar preguntas RAG.
* Exportar e importar paquetes.
* Descargar y administrar modelos.
* Validar conexiones con proveedores.
* Ejecutar evaluaciones.

**ports**

Define protocolos o clases abstractas pequeñas para:

* DocumentReader
* OCRProvider
* ChunkingStrategy
* EmbeddingProvider
* LLMProvider
* RerankerProvider
* VectorStore
* LexicalSearchStore
* SecretStore
* ModelRegistry
* ArtifactStore
* JobRepository
* ProjectRepository
* Exporter
* EventSink

Ningún contrato debe contener detalles de una marca concreta.

**adapters**

Implementaciones para:

* Formatos documentales.
* Modelos locales.
* Proveedores API.
* Bases vectoriales.
* almacenamiento de secretos.
* exportación e importación.
* persistencia local.

**4. Tecnologías**

Usa Python moderno con tipado estricto.

**Dependencias principales**

* PySide6: interfaz gráfica.
* Typer: CLI.
* Rich: salida estructurada en consola.
* Pydantic y pydantic-settings: configuración y contratos.
* SQLAlchemy y Alembic: persistencia y migraciones.
* SQLite: catálogo local, configuración, revisiones y trabajos.
* anyio: concurrencia estructurada.
* tenacity: reintentos controlados.
* orjson: serialización eficiente.
* blake3 y SHA-256: identificación, caché e integridad.
* PyArrow: archivos Parquet.
* keyring: Windows Credential Manager.
* structlog: registro estructurado.

**Lectores documentales**

Implementa inicialmente:

* TXT
* Markdown
* PDF mediante PyMuPDF
* DOCX mediante python-docx
* XLSX mediante openpyxl
* PPTX mediante python-pptx
* HTML mediante BeautifulSoup
* CSV
* JSON y JSONL

OCR debe ser opcional y ejecutarse como adaptador independiente.

**IA local**

* sentence-transformers para embeddings.
* Adaptador para Ollama.
* Preparar contrato para llama.cpp.
* Descargar modelos bajo demanda.
* Permitir seleccionar la carpeta de caché.
* Verificar integridad de las descargas.
* Permitir importar manualmente modelos para entornos sin Internet.

**Proveedores API**

Preparar adaptadores independientes para:

* OpenAI.
* Azure OpenAI.
* Cohere.
* API compatible con el protocolo de OpenAI.
* Endpoint HTTP personalizado.

Los paquetes específicos deben instalarse mediante extras opcionales cuando sea posible.

**Almacenamiento vectorial**

Implementar:

* LanceDB como backend local predeterminado.
* Qdrant para proyectos grandes.
* PostgreSQL/pgvector como integración profesional.
* FAISS como opción portable o especializada.
* Chroma como adaptador opcional.

SQLite no debe almacenar millones de vectores.

**Búsqueda**

Soportar:

* Búsqueda vectorial.
* Búsqueda léxica mediante SQLite FTS5.
* Búsqueda híbrida.
* Filtros por metadatos.
* Fusión de resultados de varias colecciones.
* Normalización de puntuaciones.
* Reranking opcional.

**5. Estructura recomendada del repositorio**

embedcraft-rag-studio/

├── pyproject.toml

├── README.md

├── LICENSE

├── CHANGELOG.md

├── alembic.ini

├── .gitignore

├── .pre-commit-config.yaml

├── src/

│ └── embedcraft/

│ ├── \_\_init\_\_.py

│ ├── domain/

│ │ ├── entities/

│ │ ├── value\_objects/

│ │ ├── services/

│ │ ├── events/

│ │ └── exceptions.py

│ ├── application/

│ │ ├── commands/

│ │ ├── queries/

│ │ ├── services/

│ │ └── dto/

│ ├── ports/

│ │ ├── documents.py

│ │ ├── embeddings.py

│ │ ├── llm.py

│ │ ├── reranking.py

│ │ ├── vector\_store.py

│ │ ├── secrets.py

│ │ └── jobs.py

│ ├── adapters/

│ │ ├── documents/

│ │ ├── embeddings/

│ │ ├── llm/

│ │ ├── rerankers/

│ │ ├── vector\_stores/

│ │ ├── secrets/

│ │ └── exports/

│ ├── infrastructure/

│ │ ├── database/

│ │ ├── jobs/

│ │ ├── models/

│ │ ├── artifacts/

│ │ ├── logging/

│ │ └── settings/

│ ├── gui/

│ │ ├── application.py

│ │ ├── main\_window.py

│ │ ├── views/

│ │ ├── viewmodels/

│ │ ├── widgets/

│ │ ├── workers/

│ │ ├── resources/

│ │ └── styles/

│ ├── cli/

│ │ ├── app.py

│ │ └── commands/

│ └── bootstrap/

│ ├── container.py

│ └── providers.py

├── tests/

│ ├── unit/

│ ├── integration/

│ ├── contract/

│ ├── gui/

│ ├── cli/

│ ├── fixtures/

│ └── acceptance/

├── docs/

│ ├── architecture/

│ ├── user-guide/

│ ├── cli/

│ └── export-format/

├── scripts/

├── packaging/

│ ├── pyinstaller/

│ ├── inno-setup/

│ └── windows/

└── samples/

Mantén los archivos pequeños, cohesivos y con una sola responsabilidad. Evita módulos centrales gigantes.

**6. Flujo de procesamiento**

Implementa este pipeline:

Descubrir

→ Extraer

→ Normalizar

→ Previsualizar

→ Fragmentar

→ Vectorizar

→ Escribir en staging

→ Validar

→ Activar revisión

**Descubrimiento**

Por cada documento, conserva:

* ID estable.
* Ruta relativa o URI.
* Tamaño.
* Fecha de modificación.
* MIME type.
* Hash del archivo.
* Hash del contenido normalizado.
* Estado.
* Fuente y colección.
* Metadatos del usuario.

Clasifica cada elemento como:

* Nuevo.
* Sin cambios.
* Modificado.
* Eliminado.
* No compatible.
* Fallido.

**Extracción**

Produce un documento canónico:

CanonicalDocument(

document\_id=...,

title=...,

text=...,

sections=...,

tables=...,

metadata=...,

source\_locator=...,

)

Un error en un archivo no debe cancelar todo el lote.

**Fragmentación**

Incluye estrategias:

* Tamaño fijo por tokens.
* Por encabezados o secciones.
* Recursiva.
* Semántica opcional.

Cada fragmento debe conservar:

* chunk\_id.
* document\_id.
* document\_version.
* Texto.
* Posición.
* Sección.
* Página, cuando exista.
* Hash.
* Metadatos heredados.
* Versión de la estrategia.
* Modelo de tokenización.

La GUI debe mostrar el resultado antes de publicar.

**Embeddings**

* Procesa en lotes configurables.
* Controla límites de memoria.
* Usa caché por hash del texto, modelo, dimensión y configuración.
* Registra nombre y versión del modelo.
* Valida dimensiones.
* Implementa reintentos con backoff para APIs.
* Permite CPU, GPU o endpoint remoto.
* No mezcles embeddings incompatibles dentro de una misma revisión.

**Publicación**

Usa revisiones:

draft → processing → staging → validating → active

└───────→ failed

La revisión activa anterior debe continuar disponible hasta que la nueva revisión haya sido validada.

Permite rollback.

**7. Índices separados y unificados**

**Índices separados**

Cada colección debe poder tener:

* Fuente propia.
* Perfil de procesamiento.
* Modelo de embeddings.
* Backend vectorial.
* Filtros.
* Política de actualización.

**Vista unificada**

No dupliques necesariamente los vectores.

Una vista unificada debe:

1. Consultar varias colecciones.
2. Aplicar filtros.
3. Normalizar puntuaciones.
4. Fusionar resultados.
5. Eliminar duplicados.
6. Ejecutar reranking opcional.
7. Conservar la colección de origen.
8. Generar citas trazables.

Impide unir colecciones incompatibles sin una estrategia explícita.

**8. GUI profesional**

Construye una interfaz PySide6 moderna y sobria.

Dirección visual:

* Barra lateral oscura.
* Área de trabajo clara.
* Tarjetas con bordes discretos.
* Color primario violeta/índigo.
* Verde para estados correctos.
* Naranja para advertencias.
* Rojo reservado para errores.
* Tipografía Segoe UI.
* Jerarquía visual empresarial.
* Sin apariencia de prototipo.
* Tema claro inicial y estructura preparada para tema oscuro.
* Escalado correcto para pantallas HiDPI.

Navegación:

Studio

├── Inicio

├── Proyectos RAG

├── Importaciones

├── Bibliotecas

└── Chat de prueba

Sistema

├── Proveedores

├── Modelos

├── Configuración

└── Registros

Pantallas mínimas:

* Inicio.
* Lista de proyectos.
* Creación y edición de proyecto.
* Importación por lotes.
* Monitor de procesamiento.
* Preview de documento.
* Preview de fragmentos.
* Explorador de colecciones.
* Chat de prueba.
* Inspector de recuperación.
* Proveedores.
* Administrador de modelos.
* Exportación e importación.
* Registros y errores.
* Configuración.

**Monitor de procesamiento**

Debe mostrar:

* Etapa actual.
* Progreso general.
* Progreso por documento.
* Documentos por minuto.
* Fragmentos generados.
* Tiempo estimado.
* Uso del perfil.
* Advertencias.
* Errores.
* Registro en vivo.
* Pausar.
* Reanudar.
* Cancelar.
* Reintentar fallidos.

Utiliza procesos trabajadores y señales seguras de Qt. No bloquees el event loop.

**9. Chat de prueba**

Debe existir en GUI y consola.

Funciones:

* Seleccionar proyecto, revisión o vista unificada.
* Seleccionar perfil LLM.
* Configurar top\_k.
* Activar búsqueda híbrida.
* Activar reranking.
* Aplicar filtros.
* Mostrar respuesta.
* Mostrar citas.
* Mostrar fragmentos recuperados.
* Mostrar puntuación original y rerankeada.
* Mostrar latencias por etapa.
* Mostrar tokens estimados.
* Permitir probar recuperación sin invocar un LLM.
* Exportar la sesión de diagnóstico.

Si no hay evidencia suficiente, el sistema debe indicarlo y evitar inventar información.

**10. CLI**

El ejecutable de consola será embedcraft.

Implementa:

embedcraft --help

embedcraft version

embedcraft project create NAME

embedcraft project list

embedcraft project show PROJECT

embedcraft project delete PROJECT

embedcraft project validate PROJECT

embedcraft source add PROJECT PATH

embedcraft source list PROJECT

embedcraft source remove PROJECT SOURCE

embedcraft ingest scan PROJECT

embedcraft ingest run PROJECT

embedcraft ingest status PROJECT

embedcraft ingest pause JOB\_ID

embedcraft ingest resume JOB\_ID

embedcraft ingest cancel JOB\_ID

embedcraft ingest retry JOB\_ID

embedcraft collection list PROJECT

embedcraft collection create PROJECT NAME

embedcraft collection inspect PROJECT COLLECTION

embedcraft search PROJECT QUERY

embedcraft chat PROJECT

embedcraft chat PROJECT --query "..."

embedcraft evaluate PROJECT DATASET

embedcraft provider list

embedcraft provider configure PROVIDER

embedcraft provider test PROVIDER

embedcraft model list

embedcraft model download MODEL

embedcraft model verify MODEL

embedcraft model remove MODEL

embedcraft export PROJECT OUTPUT

embedcraft import PACKAGE

embedcraft package verify PACKAGE

embedcraft doctor

embedcraft gui

Requisitos de CLI:

* Salida humana con Rich.
* --json para automatización.
* Códigos de salida documentados.
* Barras de progreso.
* Modo no interactivo.
* Mensajes de error accionables.
* Nunca imprimir secretos.
* Chat interactivo con comando para inspeccionar fuentes.

**11. Formato de exportación portable**

Usa extensión:

.ecraft

Debe ser un ZIP validable con esta estructura:

package/

├── manifest.json

├── project.yaml

├── profiles/

│ ├── processing.yaml

│ └── retrieval.yaml

├── data/

│ ├── documents.parquet

│ ├── document\_versions.parquet

│ ├── chunks.parquet

│ └── collections.parquet

├── vectors/

│ ├── embeddings.parquet

│ └── index/

├── reports/

│ ├── processing.json

│ └── quality.json

├── schemas/

└── checksums.sha256

manifest.json debe incluir:

* Versión del formato.
* Versión de EmbedCraft.
* ID del proyecto.
* Fecha de creación.
* Modelo de embeddings.
* Dimensión.
* Métrica.
* Estrategia de fragmentación.
* Revisión exportada.
* Conteos.
* Lista de archivos.
* Checksums.
* Requisitos de compatibilidad.

Reglas:

* Nunca exportar API keys.
* No exportar rutas absolutas privadas.
* Poder exportar con o sin vectores.
* Usar JSON, YAML y Parquet.
* Verificar checksums al importar.
* Rechazar paquetes corruptos.
* Ejecutar migraciones explícitas entre versiones.
* Permitir inspeccionar el paquete sin importarlo.

**12. Persistencia y trabajos**

Usa SQLite en modo WAL para:

* Proyectos.
* Fuentes.
* Documentos.
* Revisiones.
* Configuración.
* Trabajos.
* Pasos.
* Eventos.
* Referencias a artefactos.

Los trabajadores deben:

* Ejecutarse en procesos separados.
* Guardar checkpoints.
* Emitir eventos de progreso.
* Admitir cancelación cooperativa.
* Poder recuperarse tras cerrar la aplicación.
* Reintentar por documento.
* Aplicar límites de concurrencia.
* No duplicar resultados al reanudar.

No introduzcas Redis, Celery o servicios obligatorios en la edición local. Diseña los contratos para permitir un ejecutor remoto futuro.

**13. Seguridad**

* Almacena secretos con keyring.
* Nunca los incluyas en SQLite, logs o exportaciones.
* Redacta cabeceras sensibles.
* Valida rutas y evita path traversal.
* Valida ZIP antes de extraer.
* Limita tamaño y cantidad de archivos al importar paquetes.
* Deshabilita ejecución de macros.
* No ejecutes contenido incluido en documentos.
* Escapa HTML mostrado en previews.
* Confirma operaciones destructivas.
* Registra auditoría local de cambios importantes.
* Incluye modo offline.
* La telemetría debe estar desactivada por defecto.

**14. Evaluación RAG**

Incluye conjuntos de evaluación con:

* Pregunta.
* Documento esperado.
* Fragmentos relevantes opcionales.
* Respuesta de referencia opcional.

Calcula cuando corresponda:

* Recall@K.
* Precision@K.
* MRR.
* Hit rate.
* Cobertura de citas.
* Latencia.
* Tasa de errores.
* Comparación entre perfiles.

No uses evaluación generativa como único criterio.

**15. Errores y observabilidad**

Define errores por categoría:

* Configuración.
* Documento.
* Modelo.
* Red.
* Proveedor.
* Base vectorial.
* Compatibilidad.
* Integridad.
* Exportación.
* Error interno.

Cada error debe incluir:

* Código estable.
* Mensaje para el usuario.
* Detalle técnico.
* Acción recomendada.
* Identificador de correlación.
* Indicación de si puede reintentarse.

Los logs deben ser estructurados, rotativos y redactar secretos.

Incluye una pantalla y un comando doctor para comprobar:

* Base local.
* Permisos.
* Espacio disponible.
* Modelos.
* GPU.
* Proveedores.
* Bases vectoriales.
* Migraciones.
* Integridad de proyectos.

**16. Pruebas y calidad**

Usa:

* pytest.
* pytest-qt.
* pytest-asyncio.
* hypothesis.
* pytest-cov.
* Ruff.
* mypy.
* pre-commit.

Implementa:

* Pruebas unitarias del dominio.
* Pruebas contractuales para adaptadores.
* Pruebas de integración de SQLite.
* Pruebas de lectores.
* Pruebas del pipeline incremental.
* Pruebas de pausa y reanudación.
* Pruebas de publicación atómica.
* Pruebas de exportación e importación.
* Pruebas de CLI.
* Pruebas básicas de GUI.
* Pruebas con proveedores simulados.
* Pruebas de paquetes corruptos.
* Pruebas de redacción de secretos.

Criterios:

* Ninguna prueba debe necesitar una API pagada.
* Las pruebas deben ser deterministas.
* Usa archivos de muestra pequeños y legalmente redistribuibles.
* No marques una fase como terminada si sus pruebas fallan.

**17. Empaquetado para Windows**

Crea dos ejecutables:

EmbedCraft.exe

embedcraft.exe

Usa PyInstaller inicialmente en modo onedir, porque facilita:

* Plugins.
* Recursos Qt.
* Diagnóstico.
* Actualizaciones.
* Menor tiempo de inicio.

Crea un instalador con Inno Setup que:

* Instale para el usuario actual sin requerir administrador cuando sea posible.
* Cree accesos directos.
* Registre desinstalador.
* Ofrezca añadir la CLI al PATH.
* No incluya modelos.
* No elimine proyectos del usuario al desinstalar.
* Permita elegir la ubicación de caché posteriormente desde la aplicación.
* Muestre la versión.
* Incluya licencias de dependencias.
* Firme binarios cuando exista certificado.
* Genere checksums SHA-256.

Guarda datos en ubicaciones apropiadas:

%LOCALAPPDATA%/EmbedCraft/

%APPDATA%/EmbedCraft/

Separa:

* Configuración.
* Base de datos.
* Caché de modelos.
* Proyectos.
* Logs.
* Archivos temporales.

No escribas datos modificables dentro de Program Files.

**18. Implementación por fases**

Trabaja en este orden:

**Fase 1 — Fundación**

* Repositorio.
* Configuración.
* Entidades.
* Puertos.
* SQLite.
* Migraciones.
* Registro.
* Contenedor de dependencias.
* CLI básica.
* Pruebas.

**Fase 2 — Pipeline documental**

* Lectores.
* Documento canónico.
* Hashes.
* Fragmentación.
* Preview.
* Trabajos recuperables.
* Procesamiento incremental.

**Fase 3 — Embeddings e índices**

* Sentence Transformers.
* Caché.
* LanceDB.
* Qdrant.
* Revisiones.
* Publicación atómica.
* Búsqueda vectorial y léxica.

**Fase 4 — GUI**

* Sistema visual.
* Navegación.
* Proyectos.
* Importación.
* Monitor.
* Preview.
* Proveedores.
* Modelos.

**Fase 5 — Chat y diagnóstico**

* Retrieval.
* Reranking.
* LLM local/API.
* Chat GUI.
* Chat CLI.
* Citas.
* Inspector.

**Fase 6 — Portabilidad**

* Formato .ecraft.
* Exportación.
* Importación.
* Verificación.
* Migraciones de formato.

**Fase 7 — Evaluación y distribución**

* Métricas.
* Doctor.
* PyInstaller.
* Inno Setup.
* Pruebas en Windows limpio.
* Documentación.

Cada fase debe quedar ejecutable y verificada antes de comenzar la siguiente.

**19. Criterios de aceptación**

La primera versión se considerará válida cuando:

1. Pueda crearse un proyecto desde GUI y CLI.
2. Pueda importarse una carpeta con varios formatos.
3. Se puedan revisar el texto y los fragmentos.
4. Se genere un índice local con embeddings descargados bajo demanda.
5. Una segunda importación procese solo los cambios.
6. Un trabajo interrumpido pueda reanudarse.
7. El chat responda con citas verificables.
8. La recuperación pueda inspeccionarse sin usar un LLM.
9. Un proyecto pueda exportarse e importarse.
10. GUI y CLI produzcan resultados equivalentes.
11. Las credenciales estén protegidas.
12. El instalador funcione en una máquina Windows limpia.
13. La aplicación pueda funcionar completamente offline después de descargar los modelos.
14. Las pruebas automáticas pasen.
15. No existan errores estáticos críticos de Ruff o mypy.

**20. Método de trabajo obligatorio**

Antes de escribir código:

1. Inspecciona el repositorio.
2. Crea un plan de implementación por fases.
3. Identifica riesgos y dependencias.
4. Define las interfaces principales.
5. Presenta el árbol inicial de archivos.
6. Confirma que no existe código útil que vaya a sobrescribirse.

Durante la implementación:

* Realiza cambios pequeños y verificables.
* Escribe pruebas junto con cada capacidad.
* No inventes resultados de pruebas.
* No ocultes funcionalidades faltantes con mocks permanentes.
* No concentres todo en un único módulo.
* No acoples la GUI a proveedores concretos.
* Documenta decisiones importantes.
* Mantén compatibilidad entre Windows y el núcleo multiplataforma.
* Usa proveedores simulados en pruebas.
* Genera un lockfile reproducible.
* Mantén extras separados para proveedores y backends pesados.

Al finalizar cada fase, entrega:

* Funcionalidad implementada.
* Archivos creados o modificados.
* Pruebas ejecutadas.
* Resultado real de las pruebas.
* Decisiones tomadas.
* Limitaciones pendientes.
* Instrucciones para ejecutar GUI y CLI.

Comienza ahora por la **Fase 1 — Fundación**. Primero presenta el plan detallado, los contratos principales y el árbol del repositorio. Después implementa esa fase completamente y verifica sus pruebas antes de avanzar.