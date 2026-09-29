"""Projects view for creating and managing RAG projects and data sources."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from embedcraft.bootstrap.container import container
from embedcraft.domain.entities import Project, Source
from embedcraft.gui.components.card import Card


class CreateProjectDialog(QDialog):
    """Modal dialog to register a new RAG project."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nuevo Proyecto RAG")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("ej. base-conocimiento-legal")
        form.addRow("Nombre:*", self.name_edit)

        self.desc_edit = QLineEdit(self)
        self.desc_edit.setPlaceholderText("Descripción opcional del corpus")
        form.addRow("Descripción:", self.desc_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validación", "El nombre del proyecto es obligatorio.")
            return
        self.accept()

    def get_data(self) -> tuple[str, str]:
        return self.name_edit.text().strip(), self.desc_edit.text().strip()


class ProjectsView(QWidget):
    """View to administer projects and configure their sources."""

    project_created = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("workspace")
        self._selected_project_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header action bar
        action_bar = QHBoxLayout()
        title = QLabel("Proyectos y Fuentes", self)
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        action_bar.addWidget(title)
        action_bar.addStretch()

        btn_import = QPushButton("📥 Importar .ecraft", self)
        btn_import.clicked.connect(self._import_ecraft_package)
        action_bar.addWidget(btn_import)

        btn_export = QPushButton("📤 Exportar .ecraft", self)
        btn_export.clicked.connect(self._export_ecraft_package)
        action_bar.addWidget(btn_export)

        btn_create = QPushButton("+ Nuevo Proyecto", self)
        btn_create.setProperty("class", "primaryBtn")
        btn_create.clicked.connect(self._open_create_dialog)
        action_bar.addWidget(btn_create)

        layout.addLayout(action_bar)

        # Splitter: Projects on left, Sources on right
        splitter = QSplitter(self)

        # 1. Projects Table Card
        proj_card = Card("Proyectos Registrados", "Seleccione un proyecto para ver sus fuentes", self)
        self.proj_table = QTableWidget(self)
        self.proj_table.setColumnCount(3)
        self.proj_table.setHorizontalHeaderLabels(["Nombre", "Descripción", "Revisión"])
        self.proj_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.proj_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.proj_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.proj_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.proj_table.setSelectionMode(QTableWidget.SingleSelection)
        self.proj_table.itemSelectionChanged.connect(self._on_project_selected)
        proj_card.add_widget(self.proj_table)
        splitter.addWidget(proj_card)

        # 2. Sources Management Card
        src_card = Card("Fuentes de Datos", "Carpetas o archivos agregados al proyecto", self)
        src_actions = QHBoxLayout()
        btn_add_folder = QPushButton("📁 Añadir Carpeta", self)
        btn_add_folder.clicked.connect(self._add_folder_source)
        src_actions.addWidget(btn_add_folder)

        btn_add_file = QPushButton("📄 Añadir Archivo", self)
        btn_add_file.clicked.connect(self._add_file_source)
        src_actions.addWidget(btn_add_file)

        src_actions.addStretch()
        src_card.add_layout(src_actions)

        self.src_table = QTableWidget(self)
        self.src_table.setColumnCount(3)
        self.src_table.setHorizontalHeaderLabels(["Nombre", "Ruta / URI", "Tipo"])
        self.src_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.src_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.src_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        src_card.add_widget(self.src_table)

        splitter.addWidget(src_card)
        splitter.setSizes([450, 450])
        layout.addWidget(splitter)

        self.reload_projects()

    def reload_projects(self):
        try:
            with container.get_session() as session:
                repo = container.get_project_repository(session)
                projects = repo.list_all()

                self.proj_table.setRowCount(len(projects))
                for idx, p in enumerate(projects):
                    item_name = QTableWidgetItem(p.name)
                    item_name.setData(32, p.id)  # Qt.UserRole = 32
                    self.proj_table.setItem(idx, 0, item_name)
                    self.proj_table.setItem(idx, 1, QTableWidgetItem(p.description or "—"))
                    rev = p.active_revision_id[:8] if p.active_revision_id else "Sin revisión"
                    self.proj_table.setItem(idx, 2, QTableWidgetItem(rev))

                if projects and not self._selected_project_id:
                    self.proj_table.selectRow(0)

        except Exception:
            pass

    def _on_project_selected(self):
        rows = self.proj_table.selectedItems()
        if not rows:
            return
        proj_id = rows[0].data(32)
        self._selected_project_id = proj_id
        self._reload_sources(proj_id)

    def _reload_sources(self, project_id: str):
        try:
            with container.get_session() as session:
                src_repo = container.get_source_repository(session)
                sources = src_repo.list_by_project(project_id)

                self.src_table.setRowCount(len(sources))
                for idx, s in enumerate(sources):
                    self.src_table.setItem(idx, 0, QTableWidgetItem(s.name))
                    self.src_table.setItem(idx, 1, QTableWidgetItem(s.uri_or_path))
                    self.src_table.setItem(idx, 2, QTableWidgetItem(s.source_type.value))
        except Exception:
            pass

    def _open_create_dialog(self):
        dialog = CreateProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, desc = dialog.get_data()
            try:
                with container.get_session() as session:
                    repo = container.get_project_repository(session)
                    p = repo.create(Project(name=name, description=desc))
                    session.commit()
                    self._selected_project_id = p.id
                    self.reload_projects()
                    self.project_created.emit(p.id)
                    QMessageBox.information(self, "Éxito", f"Proyecto '{name}' creado exitosamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo al crear proyecto: {e!s}")

    def _add_folder_source(self):
        if not self._selected_project_id:
            QMessageBox.warning(self, "Atención", "Seleccione un proyecto primero.")
            return

        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta Documental")
        if folder:
            path_obj = Path(folder)
            try:
                with container.get_session() as session:
                    src_repo = container.get_source_repository(session)
                    src_repo.add(
                        Source(
                            project_id=self._selected_project_id,
                            name=path_obj.name,
                            uri_or_path=str(path_obj),
                        )
                    )
                    session.commit()
                    self._reload_sources(self._selected_project_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo agregar la fuente: {e!s}")

    def _add_file_source(self):
        if not self._selected_project_id:
            QMessageBox.warning(self, "Atención", "Seleccione un proyecto primero.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo Documental",
            "",
            "Documentos (*.txt *.md *.pdf *.docx *.xlsx *.pptx *.csv *.json *.jsonl *.html);;Todos los archivos (*.*)",
        )
        if file_path:
            path_obj = Path(file_path)
            try:
                with container.get_session() as session:
                    src_repo = container.get_source_repository(session)
                    src_repo.add(
                        Source(
                            project_id=self._selected_project_id,
                            name=path_obj.name,
                            uri_or_path=str(path_obj),
                        )
                    )
                    session.commit()
                    self._reload_sources(self._selected_project_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo agregar el archivo: {e!s}")

    def _export_ecraft_package(self):
        if not self._selected_project_id:
            QMessageBox.warning(self, "Atención", "Seleccione un proyecto para exportar.")
            return

        with container.get_session() as session:
            proj = container.get_project_repository(session).get_by_id(self._selected_project_id)
            if not proj:
                return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Paquete .ecraft",
            f"{proj.name}.ecraft",
            "EmbedCraft Package (*.ecraft)",
        )
        if file_path:
            try:
                with container.get_session() as session:
                    export_svc = container.get_export_service(session)
                    manifest = export_svc.export_project(proj.name, Path(file_path))
                    QMessageBox.information(
                        self,
                        "Exportación Completada",
                        f"Proyecto '{manifest.project_name}' exportado con éxito a:\n{file_path}\n\n"
                        f"Documentos: {manifest.document_count} | Chunks: {manifest.chunk_count}",
                    )
            except Exception as e:
                QMessageBox.critical(self, "Error de Exportación", f"No se pudo exportar: {e!s}")

    def _import_ecraft_package(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Paquete .ecraft",
            "",
            "EmbedCraft Package (*.ecraft)",
        )
        if file_path:
            try:
                with container.get_session() as session:
                    import_svc = container.get_import_service(session)
                    imported = import_svc.import_project(Path(file_path))
                    session.commit()
                    self._selected_project_id = imported.id
                    self.reload_projects()
                    self.project_created.emit(imported.id)
                    QMessageBox.information(
                        self,
                        "Importación Completada",
                        f"Proyecto '{imported.name}' importado exitosamente desde:\n{file_path}",
                    )
            except Exception as e:
                QMessageBox.critical(self, "Error de Importación", f"Fallo al importar paquete: {e!s}")
