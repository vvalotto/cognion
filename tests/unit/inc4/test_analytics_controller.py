"""Tests unitarios de `AnalyticsController` (US-4.1.2, US-4.2.1, US-4.2.4)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.analytics.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    ComisionResumen,
    EstudianteResumen,
)
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
    RespuestaVigente,
)
from src.analytics.entities.ports.pregunta_metadato_consulta_port import (
    MetadatoPreguntaResumen,
    PreguntaMetadatoConsultaPort,
)
from src.analytics.interface_adapters.controllers.analytics_controller import (
    AnalyticsController,
)
from src.analytics.use_cases.obtener_desempeno_estudiante import (
    ObtenerDesempenoEstudianteUseCase,
)
from src.analytics.use_cases.obtener_tasa_error_por_tema import (
    ObtenerTasaErrorPorTemaUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(
        self,
        resumenes: list[EvaluacionDesempenoResumen] | None = None,
        respuestas: list[RespuestaVigente] | None = None,
    ) -> None:
        self._resumenes = resumenes or []
        self._respuestas = respuestas or []

    async def listar_evaluaciones_finalizadas(
        self, estudiante_id, materia_id
    ) -> list[EvaluacionDesempenoResumen]:
        return self._resumenes

    async def listar_respuestas_vigentes_de_materia(
        self, materia_id, estudiante_ids
    ) -> list[RespuestaVigente]:
        return self._respuestas


class _ComisionConsultaPortFake(ComisionConsultaPort):
    def __init__(self) -> None:
        self.comisiones: list[ComisionResumen] = []
        self.estudiantes: list[EstudianteResumen] = []

    async def listar_comisiones_por_materia(self, materia_id) -> list[ComisionResumen]:
        return self.comisiones

    async def listar_estudiantes(self, comision_id) -> list[EstudianteResumen]:
        return self.estudiantes


class _PreguntaMetadatoConsultaPortFake(PreguntaMetadatoConsultaPort):
    def __init__(self, metadatos: dict | None = None) -> None:
        self._metadatos = metadatos or {}

    async def obtener_metadatos(self, pregunta_ids) -> dict:
        return {pid: self._metadatos[pid] for pid in pregunta_ids if pid in self._metadatos}


def _controller(
    evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort | None = None,
    comision_consulta: ComisionConsultaPort | None = None,
    pregunta_metadato_consulta: PreguntaMetadatoConsultaPort | None = None,
) -> AnalyticsController:
    evaluacion_desempeno_consulta = (
        evaluacion_desempeno_consulta or _EvaluacionDesempenoConsultaPortFake()
    )
    return AnalyticsController(
        ObtenerDesempenoEstudianteUseCase(evaluacion_desempeno_consulta),
        ObtenerTasaErrorPorTemaUseCase(
            evaluacion_desempeno_consulta,
            comision_consulta or _ComisionConsultaPortFake(),
            pregunta_metadato_consulta or _PreguntaMetadatoConsultaPortFake(),
        ),
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
    async def test_obtener_tasa_error_por_tema_delega_en_el_use_case(self):
        pregunta_id = uuid4()
        respuestas = [
            RespuestaVigente(pregunta_id=pregunta_id, estudiante_id=uuid4(), es_correcta=False)
        ]
        metadatos = {pregunta_id: MetadatoPreguntaResumen(unidad_tematica="U1", tema="T1")}
        controller = _controller(
            evaluacion_desempeno_consulta=_EvaluacionDesempenoConsultaPortFake(
                respuestas=respuestas
            ),
            pregunta_metadato_consulta=_PreguntaMetadatoConsultaPortFake(metadatos),
        )

        resultado = await controller.obtener_tasa_error_por_tema(uuid4(), None)

        assert len(resultado) == 1
        assert resultado[0].unidad_tematica == "U1"
        assert resultado[0].tema == "T1"
        assert resultado[0].tasa_error == 1.0

    @pytest.mark.asyncio
    async def test_obtener_tasa_error_por_tema_sin_respuestas_devuelve_lista_vacia(self):
        controller = _controller()

        resultado = await controller.obtener_tasa_error_por_tema(uuid4(), None)

        assert resultado == []
