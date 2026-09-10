"""Test de integración del adapter in-process de Notificaciones hacia `ComisionQueryPort`
(US-5.1.1).

Cubre los escenarios "Roster combinado de varias comisiones sin duplicados", "Resolver todas
las comisiones de una materia" y "Comisión sin estudiantes" de
`tests/features/inc5/US-5.1.1-infraestructura-notificaciones.feature` contra PostgreSQL real
— la lógica de dedupe ya se verificó con dobles en `tests/unit/inc5/`, este test confirma el
cableado real contra Identidad.
"""

import uuid

from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.notificaciones.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)
from src.shared.entities.tipo_perfil import TipoPerfil


class TestComisionConsultaPortInProcess:
    async def test_roster_combinado_de_varias_comisiones_sin_duplicados(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        materia_id = uuid.uuid4()
        comision_a = Comision.crear(materia_id, "lu 10-12", admin.id)
        comision_b = Comision.crear(materia_id, "ma 14-16", admin.id)
        await comision_repo.guardar(comision_a)
        await comision_repo.guardar(comision_b)

        estudiante_en_ambas = Usuario.crear_estudiante(
            "Ana Pérez", f"ana.{uuid.uuid4()}@fiuner.edu.ar", "hash", comision_a.id
        )
        estudiante_solo_a = Usuario.crear_estudiante(
            "Bruno Díaz", f"bruno.{uuid.uuid4()}@fiuner.edu.ar", "hash", comision_a.id
        )
        await usuario_repo.guardar(estudiante_en_ambas)
        await usuario_repo.guardar(estudiante_solo_a)

        notificaciones_port = ComisionConsultaPortInProcess(session)
        resultado = await notificaciones_port.listar_destinatarios([comision_a.id, comision_b.id])

        assert len(resultado) == 2
        assert {d.estudiante_id for d in resultado} == {
            estudiante_en_ambas.id,
            estudiante_solo_a.id,
        }

    async def test_resolver_todas_las_comisiones_de_una_materia(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        materia_id = uuid.uuid4()
        comisiones = [
            Comision.crear(materia_id, f"horario-{i}", admin.id) for i in range(3)
        ]
        for comision in comisiones:
            await comision_repo.guardar(comision)
        comision_inactiva = Comision.crear(materia_id, "horario-inactiva", admin.id)
        await comision_repo.guardar(comision_inactiva)
        comision_inactiva.deshabilitar()
        await comision_repo.actualizar(comision_inactiva)

        notificaciones_port = ComisionConsultaPortInProcess(session)
        resultado = await notificaciones_port.listar_comisiones_por_materia(materia_id)

        assert set(resultado) == {c.id for c in comisiones}

    async def test_comision_sin_estudiantes_devuelve_lista_vacia(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        notificaciones_port = ComisionConsultaPortInProcess(session)
        resultado = await notificaciones_port.listar_destinatarios([comision.id])

        assert resultado == []
