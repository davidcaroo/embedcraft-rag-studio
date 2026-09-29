"""Application service for system diagnostics and health checks (embedcraft doctor)."""

from __future__ import annotations

import shutil
import sys

from pydantic import BaseModel
from sqlalchemy import text

from embedcraft.infrastructure.database.connection import db_manager
from embedcraft.infrastructure.settings import settings


class DiagnosticCheck(BaseModel):
    category: str
    name: str
    status: str  # ok, warning, error
    message: str
    detail: str = ""


class SystemService:
    def run_doctor(self) -> list[DiagnosticCheck]:
        results: list[DiagnosticCheck] = []

        # 1. Python environment
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 11):  # noqa: UP036
            results.append(
                DiagnosticCheck(
                    category="Entorno",
                    name="Versión de Python",
                    status="ok",
                    message=f"Python {py_ver} compatible.",
                )
            )
        else:
            results.append(
                DiagnosticCheck(
                    category="Entorno",
                    name="Versión de Python",
                    status="error",
                    message=f"Python {py_ver} no compatible (se requiere >= 3.11).",
                )
            )

        # 2. Base directory and permissions
        base_dir = settings.base_dir
        try:
            test_file = base_dir / ".write_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
            results.append(
                DiagnosticCheck(
                    category="Almacenamiento",
                    name="Permisos de escritura en directorio base",
                    status="ok",
                    message=f"Directorio accesible: {base_dir}",
                )
            )
        except Exception as e:  # noqa: BLE001
            results.append(
                DiagnosticCheck(
                    category="Almacenamiento",
                    name="Permisos de escritura en directorio base",
                    status="error",
                    message="Sin permisos de escritura en directorio base.",
                    detail=str(e),
                )
            )

        # 3. Available disk space
        try:
            _, _, free = shutil.disk_usage(base_dir)
            free_gb = free / (1024**3)
            if free_gb < 2.0:
                status = "warning"
                msg = f"Espacio en disco bajo: {free_gb:.2f} GB disponibles."
            else:
                status = "ok"
                msg = f"Espacio en disco suficiente: {free_gb:.2f} GB disponibles."
            results.append(
                DiagnosticCheck(
                    category="Almacenamiento",
                    name="Espacio libre en disco",
                    status=status,
                    message=msg,
                )
            )
        except Exception as e:  # noqa: BLE001
            results.append(
                DiagnosticCheck(
                    category="Almacenamiento",
                    name="Espacio libre en disco",
                    status="warning",
                    message="No se pudo comprobar el espacio en disco.",
                    detail=str(e),
                )
            )

        # 4. SQLite database connection and WAL mode
        try:
            with db_manager.get_session() as session:
                journal_mode = session.execute(text("PRAGMA journal_mode;")).scalar()
                busy_timeout = session.execute(text("PRAGMA busy_timeout;")).scalar()
                results.append(
                    DiagnosticCheck(
                        category="Base de datos",
                        name="Conectividad SQLite",
                        status="ok",
                        message=f"Conectado a {settings.database_path.name} (journal_mode={journal_mode}, busy_timeout={busy_timeout}ms).",
                    )
                )
        except Exception as e:  # noqa: BLE001
            results.append(
                DiagnosticCheck(
                    category="Base de datos",
                    name="Conectividad SQLite",
                    status="error",
                    message="Error de conexión a la base de datos.",
                    detail=str(e),
                )
            )

        # 5. Security - Keyring availability
        try:
            import keyring
            backend = keyring.get_keyring()
            results.append(
                DiagnosticCheck(
                    category="Seguridad",
                    name="Almacén de credenciales (Keyring)",
                    status="ok",
                    message=f"Backend activo: {backend.__class__.__name__}",
                )
            )
        except Exception as e:  # noqa: BLE001
            results.append(
                DiagnosticCheck(
                    category="Seguridad",
                    name="Almacén de credenciales (Keyring)",
                    status="warning",
                    message="Keyring no disponible directamente. Se usará fallback seguro.",
                    detail=str(e),
                )
            )

        return results
