"""Presenters de Analytics (`US-12.2.4`, `ADR-031`): cada `presentar_*` arma su salida sin FastAPI."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.analytics.interface_adapters.presenters.analytics_presenter import (
    CompletitudFilaSalida,
    DesempenoComisionFilaSalida,
    EvolucionTemporalComisionPuntoSalida,
    EvolucionTemporalPuntoSalida,
    RankingPreguntaFalladaSalida,
    TasaErrorTemaSalida,
    presentar_completitud,
    presentar_desempeno_comision,
    presentar_desempeno_estudiante,
    presentar_evolucion_comision,
    presentar_evolucion_estudiante,
    presentar_ranking_preguntas,
    presentar_tasas_error,
)
from src.analytics.use_cases.obtener_completitud_por_actividad import (
    CompletitudFila,
    CompletitudPorActividad,
    CompletitudResumen,
)
from src.analytics.use_cases.obtener_desempeno_estudiante import (
    DesempenoEstudiante,
    EvaluacionDetalle,
    ResumenDesempeno,
    SesionEnVivoDetalle,
)
from src.analytics.use_cases.obtener_desempeno_por_comision import DesempenoComisionFila
from src.analytics.use_cases.obtener_evolucion_temporal_comision import (
    EvolucionTemporalComisionPunto,
)
from src.analytics.use_cases.obtener_evolucion_temporal_estudiante import EvolucionTemporalPunto
from src.analytics.use_cases.obtener_ranking_preguntas_falladas import RankingPreguntaFallada
from src.analytics.use_cases.obtener_tasa_error_por_tema import TasaErrorTema

AHORA = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)


def test_presenta_el_desempeno_de_un_estudiante_con_detalle_resumen_y_sesiones() -> None:
    evaluacion_id, actividad_id, sesion_id = uuid4(), uuid4(), uuid4()
    desempeno = DesempenoEstudiante(
        evaluaciones=[EvaluacionDetalle(evaluacion_id, actividad_id, AHORA, 8, 2)],
        resumen=ResumenDesempeno(8, 2, 80, 1),
        sesiones_en_vivo=[SesionEnVivoDetalle(sesion_id, "Lu 10-12", AHORA, 5, 3, 2, 4200, 2, 30)],
    )

    salida = presentar_desempeno_estudiante(desempeno)

    assert salida.evaluaciones[0].evaluacion_id == evaluacion_id
    assert salida.evaluaciones[0].cantidad_correctas == 8
    assert salida.resumen.porcentaje_acierto == 80
    assert salida.sesiones_en_vivo[0].posicion == 2
    assert salida.sesiones_en_vivo[0].comision_horario == "Lu 10-12"


def test_presenta_las_filas_de_tasa_de_error_ranking_y_desempeno_por_comision() -> None:
    pregunta_id, estudiante_id = uuid4(), uuid4()

    tasas = presentar_tasas_error([TasaErrorTema("U1", "Capas", 10, 4, 0.4)])
    ranking = presentar_ranking_preguntas(
        [RankingPreguntaFallada(pregunta_id, "¿Qué es CBO?", "U1", "Capas", 10, 6, 0.6)]
    )
    filas = presentar_desempeno_comision([DesempenoComisionFila(estudiante_id, "Ana", None, 2)])

    assert tasas == [TasaErrorTemaSalida("U1", "Capas", 10, 4, 0.4)]
    assert ranking == [
        RankingPreguntaFalladaSalida(pregunta_id, "¿Qué es CBO?", "U1", "Capas", 10, 6, 0.6)
    ]
    assert filas == [DesempenoComisionFilaSalida(estudiante_id, "Ana", None, 2)]


def test_presenta_las_series_de_evolucion_temporal() -> None:
    actividad_id = uuid4()

    individual = presentar_evolucion_estudiante(
        [EvolucionTemporalPunto(actividad_id, "Parcial 1", AHORA, 75)]
    )
    comision = presentar_evolucion_comision(
        [EvolucionTemporalComisionPunto(actividad_id, "Parcial 1", 66.5)]
    )

    assert individual == [EvolucionTemporalPuntoSalida(actividad_id, "Parcial 1", AHORA, 75)]
    assert comision == [EvolucionTemporalComisionPuntoSalida(actividad_id, "Parcial 1", 66.5)]


def test_presenta_la_completitud_de_una_actividad() -> None:
    estudiante_id = uuid4()
    completitud = CompletitudPorActividad(
        detalle=[CompletitudFila(estudiante_id, "Ana", "finalizada")],
        resumen=CompletitudResumen(finalizadas=1, en_curso=0, suspendidas=0, sin_iniciar=2),
    )

    salida = presentar_completitud(completitud)

    assert salida.detalle == [CompletitudFilaSalida(estudiante_id, "Ana", "finalizada")]
    assert salida.resumen.sin_iniciar == 2
