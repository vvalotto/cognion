"""Tests unitarios de `ListarSesionesEnVivoUseCase` (US-6.3.2)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.entities.errors import ComisionNoAutorizada, ComisionRequerida
from src.actividad_evaluativa.entities.ports.materia_consulta_port import MateriaDTO
from src.actividad_evaluativa.entities.ports.sesiones_en_vivo_query_port import (
    SesionEnVivoResumen,
    SesionesEnVivoQueryPort,
)
from src.actividad_evaluativa.use_cases.listar_sesiones_en_vivo import ListarSesionesEnVivoUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc3._fakes import FakeEstudianteConsultaPort, FakeMateriaConsultaPort

DEFAULT_ESTADOS = [EstadoSesionEnVivo.EN_ESPERA, EstadoSesionEnVivo.EN_CURSO]


class _FakeSesionesEnVivoQueryPort(SesionesEnVivoQueryPort):
    """Fake simple, precargado a mano — sin pasar por el event store."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria."""
        self.sesiones: list[SesionEnVivoResumen] = []

    async def listar(
        self, comision_id, estados: list[EstadoSesionEnVivo]
    ) -> list[SesionEnVivoResumen]:
        """Filtra las sesiones precargadas por Comisión y estado, más recientes primero."""
        filtradas = [
            s for s in self.sesiones if s.comision_id == comision_id and s.estado in estados
        ]
        return sorted(filtradas, key=lambda s: s.creada_en, reverse=True)


def _sesion(comision_id, materia_id, estado=EstadoSesionEnVivo.EN_ESPERA, creada_en=None):
    return SesionEnVivoResumen(
        id=uuid4(),
        comision_id=comision_id,
        materia_id=materia_id,
        cantidad_preguntas=5,
        tiempo_limite_por_pregunta_segundos=30,
        estado=estado,
        creada_en=creada_en or datetime.now(UTC),
    )


def _armar():
    estudiantes = FakeEstudianteConsultaPort()
    sesiones_query = _FakeSesionesEnVivoQueryPort()
    materias = FakeMateriaConsultaPort()
    use_case = ListarSesionesEnVivoUseCase(estudiantes, sesiones_query, materias)
    return use_case, estudiantes, sesiones_query, materias


class TestEstudiante:
    async def test_ve_las_sesiones_de_su_comision(self):
        use_case, estudiantes, sesiones_query, materias = _armar()
        estudiante_id, comision_id, materia_id = uuid4(), uuid4(), uuid4()
        estudiantes.comisiones_por_estudiante[estudiante_id] = comision_id
        materias.materias[materia_id] = MateriaDTO(id=materia_id, nombre="Ingeniería de Software")
        sesiones_query.sesiones.append(_sesion(comision_id, materia_id))

        resultado = await use_case.execute(
            estudiante_id, TipoPerfil.ESTUDIANTE, None, DEFAULT_ESTADOS
        )

        assert len(resultado) == 1
        assert resultado[0].materia_nombre == "Ingeniería de Software"

    async def test_no_ve_sesiones_de_otra_comision(self):
        use_case, estudiantes, sesiones_query, _ = _armar()
        estudiante_id, comision_propia, otra_comision = uuid4(), uuid4(), uuid4()
        estudiantes.comisiones_por_estudiante[estudiante_id] = comision_propia
        sesiones_query.sesiones.append(_sesion(otra_comision, uuid4()))

        resultado = await use_case.execute(
            estudiante_id, TipoPerfil.ESTUDIANTE, None, DEFAULT_ESTADOS
        )

        assert resultado == []

    async def test_no_puede_pedir_la_comision_de_otro(self):
        use_case, estudiantes, _, _ = _armar()
        estudiante_id, comision_propia, otra_comision = uuid4(), uuid4(), uuid4()
        estudiantes.comisiones_por_estudiante[estudiante_id] = comision_propia

        with pytest.raises(ComisionNoAutorizada):
            await use_case.execute(
                estudiante_id, TipoPerfil.ESTUDIANTE, otra_comision, DEFAULT_ESTADOS
            )

    async def test_pedir_la_propia_comision_explicitamente_esta_permitido(self):
        use_case, estudiantes, sesiones_query, _ = _armar()
        estudiante_id, comision_id = uuid4(), uuid4()
        estudiantes.comisiones_por_estudiante[estudiante_id] = comision_id
        sesiones_query.sesiones.append(_sesion(comision_id, uuid4()))

        resultado = await use_case.execute(
            estudiante_id, TipoPerfil.ESTUDIANTE, comision_id, DEFAULT_ESTADOS
        )

        assert len(resultado) == 1

    async def test_sin_comision_propia_devuelve_lista_vacia(self):
        use_case, _, _, _ = _armar()

        resultado = await use_case.execute(uuid4(), TipoPerfil.ESTUDIANTE, None, DEFAULT_ESTADOS)

        assert resultado == []


class TestDocente:
    async def test_debe_indicar_la_comision(self):
        use_case, _, _, _ = _armar()

        with pytest.raises(ComisionRequerida):
            await use_case.execute(uuid4(), TipoPerfil.DOCENTE, None, DEFAULT_ESTADOS)

    async def test_recupera_la_sesion_activa_de_la_comision(self):
        use_case, _, sesiones_query, materias = _armar()
        comision_id, materia_id = uuid4(), uuid4()
        materias.materias[materia_id] = MateriaDTO(id=materia_id, nombre="Gestión de Proyectos")
        sesiones_query.sesiones.append(
            _sesion(comision_id, materia_id, estado=EstadoSesionEnVivo.EN_CURSO)
        )

        resultado = await use_case.execute(
            uuid4(), TipoPerfil.DOCENTE, comision_id, DEFAULT_ESTADOS
        )

        assert len(resultado) == 1
        assert resultado[0].estado == EstadoSesionEnVivo.EN_CURSO

    async def test_puede_pedir_tambien_las_finalizadas(self):
        use_case, _, sesiones_query, _ = _armar()
        comision_id, materia_id = uuid4(), uuid4()
        sesiones_query.sesiones.append(
            _sesion(comision_id, materia_id, estado=EstadoSesionEnVivo.FINALIZADA)
        )

        sin_finalizadas = await use_case.execute(
            uuid4(), TipoPerfil.DOCENTE, comision_id, DEFAULT_ESTADOS
        )
        con_finalizadas = await use_case.execute(
            uuid4(), TipoPerfil.DOCENTE, comision_id, [EstadoSesionEnVivo.FINALIZADA]
        )

        assert sin_finalizadas == []
        assert len(con_finalizadas) == 1


class TestGenerales:
    async def test_sin_sesiones_devuelve_lista_vacia(self):
        use_case, _, _, _ = _armar()

        resultado = await use_case.execute(uuid4(), TipoPerfil.DOCENTE, uuid4(), DEFAULT_ESTADOS)

        assert resultado == []

    async def test_orden_por_recientes(self):
        use_case, _, sesiones_query, _ = _armar()
        comision_id, materia_id = uuid4(), uuid4()
        vieja = _sesion(comision_id, materia_id, creada_en=datetime(2026, 1, 1, tzinfo=UTC))
        nueva = _sesion(comision_id, materia_id, creada_en=datetime(2026, 1, 2, tzinfo=UTC))
        sesiones_query.sesiones.extend([vieja, nueva])

        resultado = await use_case.execute(
            uuid4(), TipoPerfil.DOCENTE, comision_id, DEFAULT_ESTADOS
        )

        assert [s.id for s in resultado] == [nueva.id, vieja.id]

    async def test_materia_no_resoluble_deja_nombre_vacio(self):
        use_case, _, sesiones_query, _ = _armar()
        comision_id, materia_id = uuid4(), uuid4()
        sesiones_query.sesiones.append(_sesion(comision_id, materia_id))

        resultado = await use_case.execute(
            uuid4(), TipoPerfil.DOCENTE, comision_id, DEFAULT_ESTADOS
        )

        assert resultado[0].materia_nombre == ""
