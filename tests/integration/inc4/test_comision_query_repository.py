"""Tests de integración de `SQLAlchemyComisionQueryRepository` contra PostgreSQL (US-4.2.2)."""

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


class TestListarComisionesPorMateria:
    async def test_materia_con_comisiones(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        query_repo = SQLAlchemyComisionQueryRepository(session)
        admin = Usuario.crear("Vic", "vic.query1@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)
        materia_id = uuid.uuid4()
        comision_1 = Comision.crear(materia_id, "lu 10-12", admin.id)
        comision_2 = Comision.crear(materia_id, "ma 14-16", admin.id)
        await comision_repo.guardar(comision_1)
        await comision_repo.guardar(comision_2)

        resultado = await query_repo.listar_comisiones_por_materia(materia_id)

        assert {c.id for c in resultado} == {comision_1.id, comision_2.id}

    async def test_materia_sin_comisiones_devuelve_lista_vacia(self, session):
        query_repo = SQLAlchemyComisionQueryRepository(session)

        resultado = await query_repo.listar_comisiones_por_materia(uuid.uuid4())

        assert resultado == []


class TestListarEstudiantes:
    async def test_comision_con_estudiantes(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        query_repo = SQLAlchemyComisionQueryRepository(session)
        admin = Usuario.crear("Vic", "vic.query2@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        estudiante = Usuario.crear_estudiante(
            "Ana Pérez", "ana.query@fiuner.edu.ar", "hash", comision.id
        )
        await usuario_repo.guardar(estudiante)

        resultado = await query_repo.listar_estudiantes(comision.id)

        assert len(resultado) == 1
        assert resultado[0].id == estudiante.id
        assert resultado[0].nombre == "Ana Pérez"

    async def test_comision_sin_estudiantes_devuelve_lista_vacia(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        query_repo = SQLAlchemyComisionQueryRepository(session)
        admin = Usuario.crear("Vic", "vic.query3@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        resultado = await query_repo.listar_estudiantes(comision.id)

        assert resultado == []
