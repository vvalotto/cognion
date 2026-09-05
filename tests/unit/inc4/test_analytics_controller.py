"""Tests unitarios de `AnalyticsController` (US-4.1.2, US-4.2.1)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
)
from src.analytics.interface_adapters.controllers.analytics_controller import (
    AnalyticsController,
)
from src.analytics.use_cases.obtener_desempeno_estudiante import (
    ObtenerDesempenoEstudianteUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(self, resumenes: list[EvaluacionDesempenoResumen]) -> None:
        self._resumenes = resumenes

    async def listar_evaluaciones_finalizadas(
        self, estudiante_id, materia_id
    ) -> list[EvaluacionDesempenoResumen]:
        return self._resumenes


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
        use_case = ObtenerDesempenoEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake([resumen])
        )
        controller = AnalyticsController(use_case)

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
        use_case = ObtenerDesempenoEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake([resumen])
        )
        controller = AnalyticsController(use_case)

        resultado = await controller.obtener_desempeno_de_estudiante(uuid4(), uuid4())

        assert len(resultado.evaluaciones) == 1
        assert resultado.resumen.total_correctas == 8
        assert resultado.resumen.total_incorrectas == 2

    @pytest.mark.asyncio
    async def test_obtener_desempeno_de_estudiante_sin_evaluaciones_devuelve_resumen_en_cero(
        self,
    ):
        use_case = ObtenerDesempenoEstudianteUseCase(_EvaluacionDesempenoConsultaPortFake([]))
        controller = AnalyticsController(use_case)

        resultado = await controller.obtener_desempeno_de_estudiante(uuid4(), uuid4())

        assert resultado.evaluaciones == []
        assert resultado.resumen.total_correctas == 0
        assert resultado.resumen.total_incorrectas == 0
        assert resultado.resumen.porcentaje_acierto == 0
