"""Tests de integración de `listar_estudiantes_con_email` contra PostgreSQL (US-5.1.1).

Mismo patrón que `TestListarEstudiantes` de `tests/integration/inc4/test_comision_query_repository.py`
— el método nuevo coexiste con `listar_estudiantes`, agregando `email` al DTO.
"""

import uuid

from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.comision_query_repository import (
    SQLAlchemyComisionQueryRepository,
)
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil


class TestListarEstudiantesConEmail:
    async def test_comision_con_estudiantes_incluye_email(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        query_repo = SQLAlchemyComisionQueryRepository(session)
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        email_estudiante = f"ana.{uuid.uuid4()}@fiuner.edu.ar"
        estudiante = Usuario.crear_estudiante("Ana Pérez", email_estudiante, "hash", comision.id)
        await usuario_repo.guardar(estudiante)

        resultado = await query_repo.listar_estudiantes_con_email(comision.id)

        assert len(resultado) == 1
        assert resultado[0].id == estudiante.id
        assert resultado[0].nombre == "Ana Pérez"
        assert resultado[0].email == email_estudiante

    async def test_comision_sin_estudiantes_devuelve_lista_vacia(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        query_repo = SQLAlchemyComisionQueryRepository(session)
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        resultado = await query_repo.listar_estudiantes_con_email(comision.id)

        assert resultado == []

    async def test_no_afecta_a_listar_estudiantes_existente(self, session):
        """`listar_estudiantes` (sin email) sigue devolviendo solo id y nombre."""
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        query_repo = SQLAlchemyComisionQueryRepository(session)
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        estudiante = Usuario.crear_estudiante(
            "Bruno", f"bruno.{uuid.uuid4()}@fiuner.edu.ar", "hash", comision.id
        )
        await usuario_repo.guardar(estudiante)

        resultado = await query_repo.listar_estudiantes(comision.id)

        assert len(resultado) == 1
        assert resultado[0].id == estudiante.id
        assert resultado[0].nombre == "Bruno"
        assert not hasattr(resultado[0], "email")
