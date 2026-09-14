"""Tests unitarios de `AnalyticsCompletitudController` (US-ADJ-47)."""

from uuid import uuid4

import pytest

from src.analytics.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    ComisionResumen,
    EstudianteResumen,
)
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    ActividadResumen,
    EvaluacionDesempenoConsultaPort,
)
from src.analytics.interface_adapters.controllers.analytics_completitud_controller import (
    AnalyticsCompletitudController,
)
from src.analytics.use_cases.obtener_completitud_por_actividad import (
    ObtenerCompletitudPorActividadUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(
        self, actividad_resumen: ActividadResumen | None = None, estados: dict | None = None
    ) -> None:
        self._actividad_resumen = actividad_resumen
        self._estados = estados or {}

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
        return self._estados


class _ComisionConsultaPortFake(ComisionConsultaPort):
    def __init__(self) -> None:
        self.comisiones: list[ComisionResumen] = []
        self.estudiantes: list[EstudianteResumen] = []

    async def listar_comisiones_por_materia(self, materia_id) -> list[ComisionResumen]:
        return self.comisiones

    async def listar_estudiantes(self, comision_id) -> list[EstudianteResumen]:
        return self.estudiantes


class TestAnalyticsCompletitudController:
    @pytest.mark.asyncio
    async def test_obtener_completitud_por_actividad_delega_en_el_use_case(self):
        materia_id, comision_id = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Ana Pérez")
        comision_consulta = _ComisionConsultaPortFake()
        comision_consulta.comisiones = [ComisionResumen(id=comision_id, horario="lu 10-12")]
        comision_consulta.estudiantes = [estudiante]
        evaluacion_desempeno_consulta = _EvaluacionDesempenoConsultaPortFake(
            actividad_resumen=ActividadResumen(
                materia_id=materia_id, comisiones_ids=frozenset({comision_id})
            ),
            estados={estudiante.id: "finalizada"},
        )
        controller = AnalyticsCompletitudController(
            ObtenerCompletitudPorActividadUseCase(evaluacion_desempeno_consulta, comision_consulta)
        )

        resultado = await controller.obtener_completitud_por_actividad(uuid4())

        assert resultado.resumen.finalizadas == 1
        assert resultado.detalle[0].estudiante_id == estudiante.id
