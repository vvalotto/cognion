"""Test de integración del adapter in-process de Analytics hacia `ComisionQueryPort` (US-4.2.2).

Cubre el escenario "Analytics consume el adapter in-process" de
`tests/features/inc4/US-4.2.2-comision-query-port.feature`: el resultado debe coincidir con el
del endpoint HTTP equivalente, sin ida y vuelta por HTTP.
"""

import uuid

from src.analytics.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)
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


class TestComisionConsultaPortInProcess:
    async def test_listar_comisiones_por_materia_coincide_con_identidad(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear("Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)
        materia_id = uuid.uuid4()
        comision = Comision.crear(materia_id, "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        identidad_query = SQLAlchemyComisionQueryRepository(session)
        esperado = await identidad_query.listar_comisiones_por_materia(materia_id)

        analytics_port = ComisionConsultaPortInProcess(session)
        resultado = await analytics_port.listar_comisiones_por_materia(materia_id)

        assert [(c.id, c.horario) for c in resultado] == [
            (c.id, c.horario) for c in esperado
        ]

    async def test_listar_estudiantes_coincide_con_identidad(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear("Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        estudiante = Usuario.crear_estudiante(
            "Ana Pérez", f"ana.{uuid.uuid4()}@fiuner.edu.ar", "hash", comision.id
        )
        await usuario_repo.guardar(estudiante)

        identidad_query = SQLAlchemyComisionQueryRepository(session)
        esperado = await identidad_query.listar_estudiantes(comision.id)

        analytics_port = ComisionConsultaPortInProcess(session)
        resultado = await analytics_port.listar_estudiantes(comision.id)

        assert [(e.id, e.nombre) for e in resultado] == [(e.id, e.nombre) for e in esperado]
