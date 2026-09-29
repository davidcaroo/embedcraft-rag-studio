# Guía de Inicio Rápido de EmbedCraft RAG Studio

Bienvenido a **EmbedCraft RAG Studio**, la plataforma para construir y evaluar pipelines RAG profesionales de forma local, privada y determinista.

## 1. Inicio con la Interfaz Gráfica

Para abrir la consola gráfica de escritorio en Windows:
```powershell
embedcraft gui
```
O ejecute directamente `EmbedCraft.exe` si instaló la aplicación mediante el instalador de Windows.

### Flujo en GUI:
1. **Crear Proyecto**: Vaya a **Proyectos RAG** y pulse `+ Nuevo Proyecto`.
2. **Añadir Fuentes**: Pulse `📁 Añadir Carpeta` o `📄 Añadir Archivo` para asociar documentos PDF, DOCX, TXT, MD, XLSX, PPTX, CSV, JSON o HTML.
3. **Monitorizar Ingestión**: Observe en **Monitor** el escaneo incremental y la fragmentación en vivo.
4. **Inspeccionar Fragmentos**: Abra **Previsualización** para revisar el contenido normalizado y tokens de cada chunk.
5. **Generar Índice**: En **Colecciones**, publique una nueva revisión atómica de embeddings.
6. **Chat y Diagnóstico**: En **Chat RAG**, configure Top-K, active búsqueda híbrida y formule preguntas con citas y desglose de latencia.

## 2. Flujo Completo desde la Consola CLI

```powershell
# 1. Crear proyecto
embedcraft project create demo-legal --description "Documentos normativos"

# 2. Agregar fuentes de documentos
embedcraft source add demo-legal ./documentos

# 3. Procesar e ingerir archivos incrementalmente
embedcraft ingest run demo-legal

# 4. Publicar revisión del índice vectorial y léxico
embedcraft index publish demo-legal

# 5. Probar búsqueda híbrida con citas
embedcraft search demo-legal "responsabilidad contractual" --mode hybrid

# 6. Ejecutar chat RAG con diagnóstico
embedcraft chat demo-legal --query "¿Cuál es el plazo de garantía legal?"

# 7. Evaluar métricas de recuperación (Recall@K, Hit Rate, MRR)
embedcraft evaluate demo-legal ./dataset_eval.json --k 5

# 8. Exportar proyecto a formato portable .ecraft
embedcraft export demo-legal ./demo-legal.ecraft
```
