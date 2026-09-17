"""Tests unitarios de `ObtenerCompletitudPorActividadUseCase` (US-ADJ-47)."""

from uuid import uuid4

import pytest

from src.analytics.entities.errors import ActividadNoExiste
from src.analytics.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    ComisionResumen,
    EstudianteResumen,
)
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    ActividadResumen,
    EvaluacionDesempenoConsultaPort,
)
from src.analytics.use_cases.obtener_completitud_por_actividad import (
    ObtenerCompletitudPorActividadUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(
        self,
        actividad_resumen: ActividadResumen | None = None,
        estados: dict | None = None,
    ) -> None:
        self._actividad_resumen = actividad_resumen
        self._estados = estados or {}
        self.ultimo_estudiante_ids: list | None = None

    async def listar_evaluaciones_finalizadas(self, estudiante_id, materia_id):
        raise NotImplementedError

    async def listar_respuestas_vigentes_de_materia(self, materia_id, estudiante_ids):
        raise NotImplementedError

    async def listar_actividades_abiertas(self, materia_id, comision_id):
        raise NotImplementedError

    async def obtener_titulos_actividades(self, actividad_ids):
        raise NotImplementedError

    async def obtener_actividad_resumen(self, actividad_id):
        return self._actividad_resumen

    async def listar_estados_de_actividad(self, actividad_id, estudiante_ids):
        self.ultimo_estudiante_ids = estudiante_ids
        return self._estados


class _ComisionConsultaPortFake(ComisionConsultaPort):
    def __init__(
        self,
        comisiones: list[ComisionResumen] | None = None,
        estudiantes_por_comision: dict | None = None,
    ) -> None:
        self._comisiones = comisiones or []
        self._estudiantes_por_comision = estudiantes_por_comision or {}

    async def listar_comisiones_por_materia(self, materia_id) -> list[ComisionResumen]:
        return self._comisiones

    async def listar_estudiantes(self, comision_id) -> list[EstudianteResumen]:
        return self._estudiantes_por_comision.get(comision_id, [])


class TestObtenerCompletitudPorActividadUseCase:
    @pytest.mark.asyncio
    async def test_actividad_inexistente_levanta_error(self):
        use_case = ObtenerCompletitudPorActividadUseCase(
            _EvaluacionDesempenoConsultaPortFake(actividad_resumen=None),
            _ComisionConsultaPortFake(),
        )

        with pytest.raises(ActividadNoExiste):
            await use_case.execute(uuid4())

    @pytest.mark.asyncio
    async def test_estados_mixtos_arman_detalle_y_resumen(self):
        materia_id, comision_id = uuid4(), uuid4()
        finalizado = EstudianteResumen(id=uuid4(), nombre="Finalizó")
        en_curso = EstudianteResumen(id=uuid4(), nombre="En curso")
        suspendido = EstudianteResumen(id=uuid4(), nombre="Suspendió")
        nunca_inicio = EstudianteResumen(id=uuid4(), nombre="Nunca inició")
        use_case = ObtenerCompletitudPorActividadUseCase(
            _EvaluacionDesempenoConsultaPortFake(
                actividad_resumen=ActividadResumen(
                    materia_id=materia_id, comisiones_ids=frozenset({comision_id})
                ),
                estados={
                    finalizado.id: "finalizada",
                    en_curso.id: "en_curso",
                    suspendido.id: "suspendida",
                },
            ),
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes_por_comision={
                    comision_id: [finalizado, en_curso, suspendido, nunca_inicio]
                },
            ),
        )

        resultado = await use_case.execute(uuid4())

        assert resultado.resumen.finalizadas == 1
        assert resultado.resumen.en_curso == 1
        assert resultado.resumen.suspendidas == 1
        assert resultado.resumen.sin_iniciar == 1
        estados_por_id = {fila.estudiante_id: fila.estado for fila in resultado.detalle}
        assert estados_por_id[nunca_inicio.id] == "sin_iniciar"
        assert len(resultado.detalle) == 4

    @pytest.mark.asyncio
    async def test_sin_restriccion_de_comision_agrega_todas_las_de_la_materia(self):
        materia_id = uuid4()
        comision_1, comision_2 = uuid4(), uuid4()
        estudiante_1 = EstudianteResumen(id=uuid4(), nombre="A")
        estudiante_2 = EstudianteResumen(id=uuid4(), nombre="B")
        use_case = ObtenerCompletitudPorActividadUseCase(
            _EvaluacionDesempenoConsultaPortFake(
                actividad_resumen=ActividadResumen(
                    materia_id=materia_id, comisiones_ids=frozenset()
                ),
            ),
            _ComisionConsultaPortFake(
                comisiones=[
                    ComisionResumen(id=comision_1, horario="lu 10-12"),
                    ComisionResumen(id=comision_2, horario="ma 10-12"),
                ],
                estudiantes_por_comision={
                    comision_1: [estudiante_1],
                    comision_2: [estudiante_2],
                },
            ),
        )

        resultado = await use_case.execute(uuid4())

        assert {fila.estudiante_id for fila in resultado.detalle} == {
            estudiante_1.id,
            estudiante_2.id,
        }

    @pytest.mark.asyncio
    async def test_roster_vacio_devuelve_resumen_en_cero(self):
        materia_id, comision_id = uuid4(), uuid4()
        use_case = ObtenerCompletitudPorActividadUseCase(
            _EvaluacionDesempenoConsultaPortFake(
                actividad_resumen=ActividadResumen(
                    materia_id=materia_id, comisiones_ids=frozenset({comision_id})
                ),
            ),
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")]
            ),
        )

        resultado = await use_case.execute(uuid4())

        assert resultado.detalle == []
        assert resultado.resumen.finalizadas == 0
        assert resultado.resumen.en_curso == 0
        assert resultado.resumen.suspendidas == 0
        assert resultado.resumen.sin_iniciar == 0

    @pytest.mark.asyncio
    async def test_delega_actividad_id_y_estudiante_ids_al_puerto(self):
        materia_id, comision_id = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="A")
        actividad_id = uuid4()
        puerto_evaluacion = _EvaluacionDesempenoConsultaPortFake(
            actividad_resumen=ActividadResumen(
                materia_id=materia_id, comisiones_ids=frozenset({comision_id})
            ),
        )
        use_case = ObtenerCompletitudPorActividadUseCase(
            puerto_evaluacion,
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes_por_comision={comision_id: [estudiante]},
            ),
        )

        await use_case.execute(actividad_id)

        assert puerto_evaluacion.ultimo_estudiante_ids == [estudiante.id]
