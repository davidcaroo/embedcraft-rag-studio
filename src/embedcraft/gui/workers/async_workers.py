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
                doc_repo = container.get_document_repository(session)

                # Scan sources
                scan_diff = ingest_svc.scan_sources(self.project_id)
                total = scan_diff.new_count + scan_diff.modified_count + scan_diff.deleted_count
                self.log_emitted.emit(
                    f"Escaneo finalizado: {scan_diff.new_count} nuevos, {scan_diff.modified_count} modificados, {scan_diff.deleted_count} eliminados.",
                    "INFO",
                )

                if total == 0:
                    self.progress_updated.emit(100, 100, "Completado")
                    total_chunks = len(doc_repo.list_chunks_by_project(self.project_id))
                    total_docs = doc_repo.count_by_project(self.project_id)
                    self.log_emitted.emit("Las fuentes ya están actualizadas. No hay documentos pendientes por procesar.", "INFO")
                    self.job_finished.emit({
                        "status": "up_to_date",
                        "processed_documents": total_docs,
                        "generated_chunks": total_chunks,
                    })
                    return

                # Progress callback
                def on_progress(done: int, tot: int, path: str):
                    if self._is_cancelled:
                        raise InterruptedError("Operación cancelada por el usuario.")
                    self.progress_updated.emit(done, tot, path)
                    self.log_emitted.emit(f"Procesando [{done}/{tot}]: {path}", "DEBUG")

                job = ingest_svc.run_ingestion(self.project_id, progress_callback=on_progress)
                session.commit()

                step = job.steps[0] if job.steps else None
                processed_docs = step.items_processed if step else 0
                failed_docs = step.items_failed if step else 0
                total_chunks = len(doc_repo.list_chunks_by_project(self.project_id))

                self.progress_updated.emit(100, 100, "Finalizado")
                msg = f"Ingestión completada con éxito. Documentos procesados: {processed_docs}, Fragmentos: {total_chunks}"
                if failed_docs:
                    msg += f" (Fallidos: {failed_docs})"
                self.log_emitted.emit(msg, "SUCCESS")
                self.job_finished.emit({
                    "status": "completed",
                    "processed_documents": processed_docs,
                    "generated_chunks": total_chunks,
                    "failed_documents": failed_docs,
                })

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
