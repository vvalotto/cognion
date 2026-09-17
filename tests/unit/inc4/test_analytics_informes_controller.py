"""Tests unitarios de `AnalyticsInformesController` (US-4.2.4, US-ADJ-44/45/46)."""

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
from src.analytics.interface_adapters.controllers.analytics_informes_controller import (
    AnalyticsInformesController,
)
from src.analytics.use_cases.obtener_desempeno_por_comision import (
    ObtenerDesempenoPorComisionUseCase,
)
from src.analytics.use_cases.obtener_evolucion_temporal_comision import (
    ObtenerEvolucionTemporalComisionUseCase,
)
from src.analytics.use_cases.obtener_ranking_preguntas_falladas import (
    ObtenerRankingPreguntasFalladasUseCase,
)
from src.analytics.use_cases.obtener_tasa_error_por_tema import (
    ObtenerTasaErrorPorTemaUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(
        self,
        resumenes_por_estudiante: dict | None = None,
        respuestas: list[RespuestaVigente] | None = None,
        actividades_abiertas: list | None = None,
        titulos_actividades: dict | None = None,
    ) -> None:
        self._resumenes_por_estudiante = resumenes_por_estudiante or {}
        self._respuestas = respuestas or []
        self._actividades_abiertas = actividades_abiertas or []
        self._titulos_actividades = titulos_actividades or {}

    async def listar_evaluaciones_finalizadas(
        self, estudiante_id, materia_id
    ) -> list[EvaluacionDesempenoResumen]:
        return self._resumenes_por_estudiante.get(estudiante_id, [])

    async def listar_respuestas_vigentes_de_materia(
        self, materia_id, estudiante_ids
    ) -> list[RespuestaVigente]:
        return self._respuestas

    async def listar_actividades_abiertas(self, materia_id, comision_id):
        return self._actividades_abiertas

    async def obtener_titulos_actividades(self, actividad_ids):
        return self._titulos_actividades

    async def obtener_actividad_resumen(self, actividad_id):
        raise NotImplementedError

    async def listar_estados_de_actividad(self, actividad_id, estudiante_ids):
        raise NotImplementedError


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
) -> AnalyticsInformesController:
    evaluacion_desempeno_consulta = (
        evaluacion_desempeno_consulta or _EvaluacionDesempenoConsultaPortFake()
    )
    comision_consulta = comision_consulta or _ComisionConsultaPortFake()
    return AnalyticsInformesController(
        ObtenerTasaErrorPorTemaUseCase(
            evaluacion_desempeno_consulta,
            comision_consulta,
            pregunta_metadato_consulta or _PreguntaMetadatoConsultaPortFake(),
        ),
        ObtenerDesempenoPorComisionUseCase(comision_consulta, evaluacion_desempeno_consulta),
        ObtenerEvolucionTemporalComisionUseCase(comision_consulta, evaluacion_desempeno_consulta),
        ObtenerRankingPreguntasFalladasUseCase(
            evaluacion_desempeno_consulta,
            comision_consulta,
            pregunta_metadato_consulta or _PreguntaMetadatoConsultaPortFake(),
        ),
    )


class TestAnalyticsInformesController:
    @pytest.mark.asyncio
    async def test_obtener_tasa_error_por_tema_delega_en_el_use_case(self):
        pregunta_id = uuid4()
        respuestas = [
            RespuestaVigente(pregunta_id=pregunta_id, estudiante_id=uuid4(), es_correcta=False)
        ]
        metadatos = {
            pregunta_id: MetadatoPreguntaResumen(
                unidad_tematica="U1", tema="T1", enunciado="Enunciado de prueba"
            )
        }
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

    @pytest.mark.asyncio
    async def test_obtener_desempeno_por_comision_delega_en_el_use_case(self):
        materia_id, comision_id = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Ana Pérez")
        comision_consulta = _ComisionConsultaPortFake()
        comision_consulta.comisiones = [ComisionResumen(id=comision_id, horario="lu 10-12")]
        comision_consulta.estudiantes = [estudiante]
        controller = _controller(comision_consulta=comision_consulta)

        resultado = await controller.obtener_desempeno_por_comision(materia_id, comision_id)

        assert len(resultado) == 1
        assert resultado[0].estudiante_id == estudiante.id
        assert resultado[0].porcentaje_aciertos_acumulado is None

    @pytest.mark.asyncio
    async def test_obtener_evolucion_temporal_comision_delega_en_el_use_case(self):
        materia_id, comision_id = uuid4(), uuid4()
        comision_consulta = _ComisionConsultaPortFake()
        comision_consulta.comisiones = [ComisionResumen(id=comision_id, horario="lu 10-12")]
        controller = _controller(comision_consulta=comision_consulta)

        resultado = await controller.obtener_evolucion_temporal_comision(materia_id, comision_id)

        assert resultado == []

    @pytest.mark.asyncio
    async def test_obtener_ranking_preguntas_falladas_delega_en_el_use_case(self):
        pregunta_id = uuid4()
        respuestas = [
            RespuestaVigente(pregunta_id=pregunta_id, estudiante_id=uuid4(), es_correcta=True)
        ]
        metadatos = {
            pregunta_id: MetadatoPreguntaResumen(
                unidad_tematica="U1", tema="T1", enunciado="¿Cuánto es 2+2?"
            )
        }
        controller = _controller(
            evaluacion_desempeno_consulta=_EvaluacionDesempenoConsultaPortFake(
                respuestas=respuestas
            ),
            pregunta_metadato_consulta=_PreguntaMetadatoConsultaPortFake(metadatos),
        )

        resultado = await controller.obtener_ranking_preguntas_falladas(uuid4(), None)

        assert len(resultado) == 1
        assert resultado[0].enunciado == "¿Cuánto es 2+2?"
        assert resultado[0].tasa_error == 0.0

    @pytest.mark.asyncio
    async def test_obtener_ranking_preguntas_falladas_sin_respuestas_devuelve_lista_vacia(self):
        controller = _controller()

        resultado = await controller.obtener_ranking_preguntas_falladas(uuid4(), None)

        assert resultado == []
