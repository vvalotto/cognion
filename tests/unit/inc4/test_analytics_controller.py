"""Tests unitarios de `AnalyticsController` — desempeño individual (US-4.1.2, US-4.2.1, US-ADJ-45)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
    RespuestaVigente,
)
from src.analytics.interface_adapters.controllers.analytics_controller import (
    AnalyticsController,
)
from src.analytics.use_cases.obtener_desempeno_estudiante import (
    ObtenerDesempenoEstudianteUseCase,
)
from src.analytics.use_cases.obtener_evolucion_temporal_estudiante import (
    ObtenerEvolucionTemporalEstudianteUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(
        self,
        resumenes: list[EvaluacionDesempenoResumen] | None = None,
        titulos_actividades: dict | None = None,
    ) -> None:
        self._resumenes = resumenes or []
        self._titulos_actividades = titulos_actividades or {}

    async def listar_evaluaciones_finalizadas(
        self, estudiante_id, materia_id
    ) -> list[EvaluacionDesempenoResumen]:
        return self._resumenes

    async def listar_respuestas_vigentes_de_materia(
        self, materia_id, estudiante_ids
    ) -> list[RespuestaVigente]:
        raise NotImplementedError

    async def listar_actividades_abiertas(self, materia_id, comision_id):
        raise NotImplementedError

    async def obtener_titulos_actividades(self, actividad_ids):
        return self._titulos_actividades

    async def obtener_actividad_resumen(self, actividad_id):
        raise NotImplementedError

    async def listar_estados_de_actividad(self, actividad_id, estudiante_ids):
        raise NotImplementedError


def _controller(
    evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort | None = None,
) -> AnalyticsController:
    evaluacion_desempeno_consulta = (
        evaluacion_desempeno_consulta or _EvaluacionDesempenoConsultaPortFake()
    )
    return AnalyticsController(
        ObtenerDesempenoEstudianteUseCase(evaluacion_desempeno_consulta),
        ObtenerEvolucionTemporalEstudianteUseCase(evaluacion_desempeno_consulta),
    )


class TestAnalyticsController:
    @pytest.mark.asyncio
    async def test_delega_en_el_use_case_y_devuelve_su_resultado(self):
        resumen = EvaluacionDesempenoResumen(
            evaluacion_id=uuid4(),
            actividad_id=uuid4(),
            materia_id=uuid4(),
            finalizada_en=datetime(2026, 1, 1, tzinfo=UTC),
            cantidad_correctas=8,
            cantidad_incorrectas=2,
        )
        controller = _controller(_EvaluacionDesempenoConsultaPortFake(resumenes=[resumen]))

        resultado = await controller.obtener_mi_desempeno(uuid4(), uuid4())

        assert len(resultado.evaluaciones) == 1
        assert resultado.resumen.total_correctas == 8
        assert resultado.resumen.total_incorrectas == 2

    @pytest.mark.asyncio
    async def test_obtener_desempeno_de_estudiante_delega_en_el_mismo_use_case(self):
        """`obtener_desempeno_de_estudiante` (US-4.2.1) hace exactamente el mismo cálculo."""
        resumen = EvaluacionDesempenoResumen(
            evaluacion_id=uuid4(),
            actividad_id=uuid4(),
            materia_id=uuid4(),
            finalizada_en=datetime(2026, 1, 1, tzinfo=UTC),
            cantidad_correctas=8,
            cantidad_incorrectas=2,
        )
        controller = _controller(_EvaluacionDesempenoConsultaPortFake(resumenes=[resumen]))

        resultado = await controller.obtener_desempeno_de_estudiante(uuid4(), uuid4())

        assert len(resultado.evaluaciones) == 1
        assert resultado.resumen.total_correctas == 8
        assert resultado.resumen.total_incorrectas == 2

    @pytest.mark.asyncio
    async def test_obtener_desempeno_de_estudiante_sin_evaluaciones_devuelve_resumen_en_cero(
        self,
    ):
        controller = _controller()

        resultado = await controller.obtener_desempeno_de_estudiante(uuid4(), uuid4())

        assert resultado.evaluaciones == []
        assert resultado.resumen.total_correctas == 0
        assert resultado.resumen.total_incorrectas == 0
        assert resultado.resumen.porcentaje_acierto == 0

    @pytest.mark.asyncio
    async def test_obtener_evolucion_temporal_estudiante_delega_en_el_use_case(self):
        resumen = EvaluacionDesempenoResumen(
            evaluacion_id=uuid4(),
            actividad_id=uuid4(),
            materia_id=uuid4(),
            finalizada_en=datetime(2026, 1, 1, tzinfo=UTC),
            cantidad_correctas=1,
            cantidad_incorrectas=0,
        )
        controller = _controller(_EvaluacionDesempenoConsultaPortFake(resumenes=[resumen]))

        resultado = await controller.obtener_evolucion_temporal_estudiante(uuid4(), uuid4())

        assert len(resultado) == 1
        assert resultado[0].porcentaje_acierto == 100
