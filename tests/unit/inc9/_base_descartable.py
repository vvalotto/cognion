"""Base de datos descartable propia para probar migraciones con `alembic` real (US-8.3.4).

Nunca toca la base de `DATABASE_URL`: solo toma sus credenciales y crea otra con un nombre único,
que borra al terminar. Para crearla intenta primero con el rol de `DATABASE_URL` (superusuario en
el CI) y después con el usuario del sistema (o `PGADMIN_USER`), como
`tests/uat/inc8/verificar_migraciones.sh`. Si ninguno puede, el test se saltea con aviso.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url

from src.settings import settings

RAIZ = Path(__file__).resolve().parents[3]


class BaseDescartable:
    """Una base PostgreSQL temporal sobre la que se corre `alembic` como subproceso."""

    def __init__(self) -> None:
        """Toma las credenciales de `DATABASE_URL` y elige un nombre único."""
        origen = make_url(settings.database_url)
        self.rol = origen.username or ""
        self.clave = origen.password or ""
        self.host = origen.host or "localhost"
        self.puerto = str(origen.port or 5432)
        self.nombre = f"cognion_mig_{uuid.uuid4().hex[:10]}"
        self.url = origen.set(database=self.nombre).render_as_string(hide_password=False)
        self._creada = False
        self._admin: tuple[str | None, str | None] = (None, None)

    def _psql(
        self, base: str, sql: str, *, usuario: str | None, clave: str | None
    ) -> subprocess.CompletedProcess[str]:
        comando = ["psql", "-h", self.host, "-p", self.puerto, "-d", base, "-At", "-c", sql]
        if usuario:
            comando += ["-U", usuario]
        entorno = {**os.environ, **({"PGPASSWORD": clave} if clave else {})}
        return subprocess.run(comando, capture_output=True, text=True, env=entorno, check=False)

    def crear(self) -> None:
        """Crea la base; si ningún rol puede, saltea el test."""
        if shutil.which("psql") is None:
            pytest.skip("psql no está instalado: no se puede crear la base descartable")
        candidatos = [(self.rol, self.clave), (os.environ.get("PGADMIN_USER"), None)]
        for usuario, clave in candidatos:
            sql = f'CREATE DATABASE "{self.nombre}" OWNER "{self.rol}"'
            if self._psql("postgres", sql, usuario=usuario, clave=clave).returncode == 0:
                self._creada = True
                self._admin = (usuario, clave)
                return
        pytest.skip("ningún rol puede crear bases de datos (hace falta CREATEDB o PGADMIN_USER)")

    def borrar(self) -> None:
        """Borra la base si se creó."""
        if self._creada:
            usuario, clave = self._admin
            self._psql(
                "postgres", f'DROP DATABASE IF EXISTS "{self.nombre}"', usuario=usuario, clave=clave
            )
            self._creada = False

    def alembic(self, *argumentos: str) -> subprocess.CompletedProcess[str]:
        """Corre `alembic <argumentos>` contra esta base, desde la raíz del proyecto."""
        entorno = {
            **os.environ,
            "DATABASE_URL": self.url,
            "SECRET_KEY": "verificacion-de-migraciones",
            "ENTORNO": "desarrollo",
        }
        return subprocess.run(
            [sys.executable, "-m", "alembic", *argumentos],
            capture_output=True,
            text=True,
            cwd=RAIZ,
            env=entorno,
            check=False,
        )

    def consulta(self, sql: str) -> str:
        """Resultado de una consulta SQL sobre esta base, sin formato."""
        usuario, clave = self._admin
        return self._psql(self.nombre, sql, usuario=usuario, clave=clave).stdout.strip()

    def revision_actual(self) -> str:
        """Identificador de la revisión actual de `alembic` (primera palabra de `alembic current`)."""
        salida = self.alembic("current").stdout.strip().splitlines()
        return salida[-1].split()[0] if salida else ""
