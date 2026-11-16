"""`AutorizarAccesoSesionEnVivoUseCase` exige pertenecer a la comisión de la sesión (US-12.1.2)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import ComisionNoAutorizada, SesionNoExiste
from src.actividad_evaluativa.use_cases.autorizar_acceso_sesion_en_vivo import (
    AutorizarAccesoSesionEnVivoUseCase,
)
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc3._fakes import (
    FakeComisionConsultaPort,
    FakeEstudianteConsultaPort,
    FakeEventStore,
    FakePreguntaConsultaPort,
)


async def _escenario():
    """Una sesión de C1, docentes de C1 y C2, y estudiantes de C1 y C2."""
    c1, c2, materia_id = uuid4(), uuid4(), uuid4()
    comision_consulta = FakeComisionConsultaPort()
    comision_consulta.materias[c1] = materia_id
    pregunta_consulta = FakePreguntaConsultaPort()
    pregunta_consulta.ids_activas[materia_id] = [uuid4() for _ in range(10)]
    event_store = FakeEventStore()
    sesion = await CrearSesionEnVivoUseCase(
        comision_consulta, pregunta_consulta, event_store
    ).execute(c1, 5, 30)

    docente_c1, docente_c2 = uuid4(), uuid4()
    comision_consulta.asignaciones.update({(docente_c1, c1), (docente_c2, c2)})
    estudiantes = FakeEstudianteConsultaPort()
    estudiante_c1, estudiante_c2 = uuid4(), uuid4()
    estudiantes.comisiones_por_estudiante.update({estudiante_c1: c1, estudiante_c2: c2})

    use_case = AutorizarAccesoSesionEnVivoUseCase(event_store, comision_consulta, estudiantes)
    return use_case, sesion.id, docente_c1, docente_c2, estudiante_c1, estudiante_c2


class TestAutorizarAccesoSesionEnVivo:
    @pytest.mark.asyncio
    async def test_docente_asignado_pasa(self):
        use_case, sesion_id, docente_c1, *_ = await _escenario()
        await use_case.execute(sesion_id, docente_c1, TipoPerfil.DOCENTE)

    @pytest.mark.asyncio
    async def test_estudiante_de_la_comision_pasa(self):
        use_case, sesion_id, _, _, estudiante_c1, _ = await _escenario()
        await use_case.execute(sesion_id, estudiante_c1, TipoPerfil.ESTUDIANTE)

    @pytest.mark.asyncio
    async def test_administrador_pasa(self):
        use_case, sesion_id, *_ = await _escenario()
        await use_case.execute(sesion_id, uuid4(), TipoPerfil.ADMINISTRADOR)

    @pytest.mark.asyncio
    async def test_docente_de_otra_comision_levanta_comision_no_autorizada(self):
        use_case, sesion_id, _, docente_c2, *_ = await _escenario()
        with pytest.raises(ComisionNoAutorizada):
            await use_case.execute(sesion_id, docente_c2, TipoPerfil.DOCENTE)

    @pytest.mark.asyncio
    async def test_estudiante_de_otra_comision_levanta_comision_no_autorizada(self):
        use_case, sesion_id, _, _, _, estudiante_c2 = await _escenario()
        with pytest.raises(ComisionNoAutorizada):
            await use_case.execute(sesion_id, estudiante_c2, TipoPerfil.ESTUDIANTE)

    @pytest.mark.asyncio
    async def test_estudiante_sin_comision_levanta_comision_no_autorizada(self):
        use_case, sesion_id, *_ = await _escenario()
        with pytest.raises(ComisionNoAutorizada):
            await use_case.execute(sesion_id, uuid4(), TipoPerfil.ESTUDIANTE)

    @pytest.mark.asyncio
    async def test_sesion_inexistente_levanta_sesion_no_existe(self):
        use_case, _, docente_c1, *_ = await _escenario()
        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4(), docente_c1, TipoPerfil.DOCENTE)

    @pytest.mark.asyncio
    async def test_sesion_inexistente_con_administrador_tambien_levanta_sesion_no_existe(self):
        use_case, *_ = await _escenario()
        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4(), uuid4(), TipoPerfil.ADMINISTRADOR)
