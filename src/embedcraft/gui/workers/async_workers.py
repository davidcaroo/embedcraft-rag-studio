"""Asynchronous Qt background workers for ingestion and indexing."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from embedcraft.bootstrap.container import container


class IngestionWorker(QObject):
    """Worker running document discovery, extraction, and chunking in background thread."""

    progress_updated = Signal(int, int, str)  # current, total, filename
    log_emitted = Signal(str, str)  # message, level
    job_finished = Signal(dict)  # summary dictionary
    job_failed = Signal(str)  # error message

    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self._is_cancelled = False

    def run(self):
        try:
            self.log_emitted.emit(f"Iniciando escaneo e ingestión para proyecto {self.project_id}...", "INFO")
            with container.get_session() as session:
                ingest_svc = container.get_ingestion_service(session)

                # Scan sources
                scan_diff = ingest_svc.scan_sources(self.project_id)
                total = len(scan_diff.new_paths) + len(scan_diff.modified_paths) + len(scan_diff.deleted_paths)
                self.log_emitted.emit(
                    f"Escaneo finalizado: {len(scan_diff.new_paths)} nuevos, {len(scan_diff.modified_paths)} modificados, {len(scan_diff.deleted_paths)} eliminados.",
                    "INFO",
                )

                if total == 0:
                    self.progress_updated.emit(100, 100, "Completado")
                    self.job_finished.emit({
                        "status": "up_to_date",
                        "processed": 0,
                        "chunks": 0,
                    })
                    return

                # Progress callback
                def on_progress(done: int, tot: int, path: str):
                    if self._is_cancelled:
                        raise InterruptedError("Operación cancelada por el usuario.")
                    self.progress_updated.emit(done, tot, path)
                    self.log_emitted.emit(f"Procesando [{done}/{tot}]: {path}", "DEBUG")

                summary = ingest_svc.run_ingestion(self.project_id, progress_callback=on_progress)
                session.commit()

                self.progress_updated.emit(100, 100, "Finalizado")
                self.log_emitted.emit(
                    f"Ingestión completada con éxito. Documentos: {summary.processed_documents}, Fragmentos: {summary.generated_chunks}",
                    "SUCCESS",
                )
                self.job_finished.emit(summary.model_dump())

        except Exception as e:
            err = f"Error durante la ingestión: {e!s}"
            self.log_emitted.emit(err, "ERROR")
            self.job_failed.emit(err)

    def cancel(self):
        self._is_cancelled = True


class IndexingWorker(QObject):
    """Worker running vectorization, staging, and atomic index publication."""

    status_changed = Signal(str)  # Revision status
    log_emitted = Signal(str, str)  # message, level
    job_finished = Signal(dict)  # revision details
    job_failed = Signal(str)  # error message

    def __init__(self, project_id: str, collection_name: str = "default"):
        super().__init__()
        self.project_id = project_id
        self.collection_name = collection_name

    def run(self):
        try:
            self.status_changed.emit("Iniciando indexación...")
            self.log_emitted.emit(f"Indexando colección '{self.collection_name}' en proyecto {self.project_id}...", "INFO")

            with container.get_session() as session:
                indexing_svc = container.get_indexing_service(session)
                revision = indexing_svc.create_and_publish_revision(
                    project_identifier=self.project_id,
                    collection_name=self.collection_name,
                )
                session.commit()

                self.status_changed.emit("ACTIVE")
                self.log_emitted.emit(
                    f"Revisión #{revision.revision_number} publicada y activa con éxito (Total fragmentos: {revision.total_chunks}).",
                    "SUCCESS",
                )
                self.job_finished.emit(revision.model_dump(mode="json"))

        except Exception as e:
            err = f"Fallo al publicar índice: {e!s}"
            self.status_changed.emit("FAILED")
            self.log_emitted.emit(err, "ERROR")
            self.job_failed.emit(err)
