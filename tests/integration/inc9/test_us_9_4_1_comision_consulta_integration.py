"""Caracterización de `ComisionConsultaPortInProcess` de Banco de Preguntas (US-9.4.1, ADR-026).

Fija el comportamiento del adaptador contra PostgreSQL real; debe dar lo mismo antes y después de que
deje de leer `ComisionModel` de Identidad. Requiere base descartable (`DATABASE_URL` inline).
"""

from __future__ import annotations

import uuid

from src.banco_preguntas.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil


async def _admin(session, email: str) -> Usuario:
    admin = Usuario.crear("Vic", email, "hash", TipoPerfil.ADMINISTRADOR)
    await SQLAlchemyUsuarioRepository(session).guardar(admin)
    return admin


class TestTieneComisiones:
    async def test_materia_sin_comisiones(self, session):
        adaptador = ComisionConsultaPortInProcess(session)

        assert await adaptador.tiene_comisiones(uuid.uuid4()) is False

    async def test_materia_con_comision_activa(self, session):
        admin = await _admin(session, "adm.941a@fiuner.edu.ar")
        materia_id = uuid.uuid4()
        await SQLAlchemyComisionRepository(session).guardar(
            Comision.crear(materia_id, "lu 10-12", admin.id)
        )

        assert await ComisionConsultaPortInProcess(session).tiene_comisiones(materia_id) is True

    async def test_materia_solo_con_comisiones_deshabilitadas(self, session):
        admin = await _admin(session, "adm.941b@fiuner.edu.ar")
        materia_id = uuid.uuid4()
        comision = Comision.crear(materia_id, "lu 10-12", admin.id)
        repo = SQLAlchemyComisionRepository(session)
        await repo.guardar(comision)
        comision.deshabilitar()
        await repo.actualizar(comision)

        assert await ComisionConsultaPortInProcess(session).tiene_comisiones(materia_id) is True

    async def test_las_comisiones_de_otra_materia_no_cuentan(self, session):
        admin = await _admin(session, "adm.941c@fiuner.edu.ar")
        await SQLAlchemyComisionRepository(session).guardar(
            Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        )

        assert await ComisionConsultaPortInProcess(session).tiene_comisiones(uuid.uuid4()) is False


class TestEstaAsignadoAMateria:
    async def test_docente_asignado_a_una_comision_de_la_materia(self, session):
        admin = await _admin(session, "adm.941d@fiuner.edu.ar")
        docente = Usuario.crear("Doc", "doc.941d@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        await SQLAlchemyUsuarioRepository(session).guardar(docente)
        materia_id = uuid.uuid4()
        comision = Comision.crear(materia_id, "lu 10-12", admin.id)
        repo = SQLAlchemyComisionRepository(session)
        await repo.guardar(comision)
        comision.asignar_docente(docente.id)
        await repo.actualizar(comision)
        adaptador = ComisionConsultaPortInProcess(session)

        assert await adaptador.esta_asignado_a_materia(docente.id, materia_id) is True
        assert await adaptador.esta_asignado_a_materia(docente.id, uuid.uuid4()) is False
        assert await adaptador.esta_asignado_a_materia(uuid.uuid4(), materia_id) is False
