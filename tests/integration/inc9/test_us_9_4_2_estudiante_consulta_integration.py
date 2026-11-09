"""Caracterización de `EstudianteConsultaPortInProcess` de Actividad Evaluativa (US-9.4.2, ADR-026).

Fija el comportamiento del adaptador contra PostgreSQL real; debe dar lo mismo antes y después de que
deje de leer `UsuarioModel` de Identidad. Requiere base descartable (`DATABASE_URL` inline).
"""

from __future__ import annotations

import uuid

from sqlalchemy import event

from src.actividad_evaluativa.frameworks.adapters.estudiante_consulta_port_in_process import (
    EstudianteConsultaPortInProcess,
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


async def _estudiante(session, nombre: str, email: str) -> tuple[Usuario, Comision]:
    usuarios = SQLAlchemyUsuarioRepository(session)
    admin = Usuario.crear("Vic", f"adm.{email}", "hash", TipoPerfil.ADMINISTRADOR)
    await usuarios.guardar(admin)
    comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
    await SQLAlchemyComisionRepository(session).guardar(comision)
    estudiante = Usuario.crear_estudiante(nombre, email, "hash", comision.id)
    await usuarios.guardar(estudiante)
    return estudiante, comision


class TestObtenerNombres:
    async def test_lista_vacia(self, session):
        assert await EstudianteConsultaPortInProcess(session).obtener_nombres([]) == {}

    async def test_ids_existentes(self, session):
        ana, _ = await _estudiante(session, "Ana", "ana.942a@fiuner.edu.ar")
        beto, _ = await _estudiante(session, "Beto", "beto.942a@fiuner.edu.ar")

        resultado = await EstudianteConsultaPortInProcess(session).obtener_nombres(
            [ana.id, beto.id]
        )

        assert resultado == {ana.id: "Ana", beto.id: "Beto"}

    async def test_id_inexistente_no_aparece(self, session):
        ana, _ = await _estudiante(session, "Ana", "ana.942b@fiuner.edu.ar")
        fantasma = uuid.uuid4()

        resultado = await EstudianteConsultaPortInProcess(session).obtener_nombres(
            [ana.id, fantasma]
        )

        assert resultado == {ana.id: "Ana"}

    async def test_una_sola_sentencia_por_lote(self, session):
        ana, _ = await _estudiante(session, "Ana", "ana.942c@fiuner.edu.ar")
        beto, _ = await _estudiante(session, "Beto", "beto.942c@fiuner.edu.ar")
        adaptador = EstudianteConsultaPortInProcess(session)
        sentencias: list[str] = []

        def contar(conn, cursor, statement, parameters, context, executemany):
            sentencias.append(statement)

        motor = session.bind.sync_engine
        event.listen(motor, "before_cursor_execute", contar)
        try:
            await adaptador.obtener_nombres([ana.id, beto.id, uuid.uuid4()])
        finally:
            event.remove(motor, "before_cursor_execute", contar)

        assert len(sentencias) == 1


class TestExisteYComision:
    async def test_existe_y_comision_id(self, session):
        ana, comision = await _estudiante(session, "Ana", "ana.942d@fiuner.edu.ar")
        adaptador = EstudianteConsultaPortInProcess(session)

        assert await adaptador.existe(ana.id) is True
        assert await adaptador.existe(uuid.uuid4()) is False
        assert await adaptador.obtener_comision_id(ana.id) == comision.id
        assert await adaptador.obtener_comision_id(uuid.uuid4()) is None
