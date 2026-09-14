"""Router base del BC Analytics — endpoints de consulta de desempeño (`US-4.1.2`, `US-4.2.1`, `US-4.2.4`)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.analytics.entities.errors import ActividadNoExiste, ComisionNoPerteneceAMateria
from src.analytics.entities.ports.estudiante_consulta_port import EstudianteConsultaPort
from src.analytics.frameworks.api.schemas import (
    CompletitudFilaResponse,
    CompletitudPorActividadResponse,
    CompletitudResumenResponse,
    DesempenoComisionFilaResponse,
    DesempenoEstudianteResponse,
    EvaluacionDetalleResponse,
    EvolucionTemporalComisionPuntoResponse,
    EvolucionTemporalPuntoResponse,
    RankingPreguntaFalladaResponse,
    ResumenDesempenoResponse,
    TasaErrorTemaResponse,
)
from src.analytics.frameworks.dependencies import (
    get_analytics_completitud_controller,
    get_analytics_controller,
    get_analytics_informes_controller,
    get_current_user,
    get_estudiante_consulta_port,
    require_docente,
    require_estudiante,
)
from src.analytics.interface_adapters.controllers.analytics_completitud_controller import (
    AnalyticsCompletitudController,
)
from src.analytics.interface_adapters.controllers.analytics_controller import (
    AnalyticsController,
)
from src.analytics.interface_adapters.controllers.analytics_informes_controller import (
    AnalyticsInformesController,
)
from src.analytics.use_cases.obtener_desempeno_estudiante import DesempenoEstudiante
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _a_response(desempeno: DesempenoEstudiante) -> DesempenoEstudianteResponse:
    """Arma el `DesempenoEstudianteResponse` a partir del resultado del Use Case."""
    return DesempenoEstudianteResponse(
        evaluaciones=[
            EvaluacionDetalleResponse(
                evaluacion_id=e.evaluacion_id,
                actividad_id=e.actividad_id,
                finalizada_en=e.finalizada_en,
                cantidad_correctas=e.cantidad_correctas,
                cantidad_incorrectas=e.cantidad_incorrectas,
            )
            for e in desempeno.evaluaciones
        ],
        resumen=ResumenDesempenoResponse(
            total_correctas=desempeno.resumen.total_correctas,
            total_incorrectas=desempeno.resumen.total_incorrectas,
            porcentaje_acierto=desempeno.resumen.porcentaje_acierto,
            cantidad_evaluaciones=desempeno.resumen.cantidad_evaluaciones,
        ),
    )


@router.get(
    "/materias/{materia_id}/mi-desempeno",
    response_model=DesempenoEstudianteResponse,
    dependencies=[Depends(require_estudiante)],
)
async def obtener_mi_desempeno(
    materia_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: AnalyticsController = Depends(get_analytics_controller),
) -> DesempenoEstudianteResponse:
    """Desempeño del Estudiante autenticado en `materia_id`: detalle y resumen (RF-15).

    `estudiante_id` sale siempre del token — nunca de un parámetro de la request, evita que
    un estudiante consulte el desempeño de otro (esa consulta es exclusiva del Docente,
    `US-4.2.1`, con su propio endpoint y su propia verificación de rol).
    """
    desempeno = await controller.obtener_mi_desempeno(usuario.usuario_id, materia_id)
    return _a_response(desempeno)


@router.get(
    "/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno",
    response_model=DesempenoEstudianteResponse,
    dependencies=[Depends(require_docente)],
)
async def obtener_desempeno_de_estudiante(
    materia_id: UUID,
    estudiante_id: UUID,
    estudiante_consulta: EstudianteConsultaPort = Depends(get_estudiante_consulta_port),
    controller: AnalyticsController = Depends(get_analytics_controller),
) -> DesempenoEstudianteResponse:
    """Desempeño de un Estudiante elegido por el Docente en `materia_id`: detalle y resumen (RF-16).

    Sin restricción de pertenencia a una comisión que el Docente dicte — RBAC estándar de rol
    `docente`, hot spot de autorización resuelto con Víctor
    (`docs/design/domain/BC-analytics-modelo.md` §4). A diferencia de `obtener_mi_desempeno`,
    acá `estudiante_id` sí puede ser inválido (viene del path, no del token) — se valida su
    existencia antes de invocar el Use Case.
    """
    if not await estudiante_consulta.existe(estudiante_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un Estudiante con id {estudiante_id}.",
        )
    desempeno = await controller.obtener_desempeno_de_estudiante(estudiante_id, materia_id)
    return _a_response(desempeno)


@router.get(
    "/materias/{materia_id}/tasa-error-por-tema",
    response_model=list[TasaErrorTemaResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_tasa_error_por_tema(
    materia_id: UUID,
    comision_id: UUID | None = None,
    controller: AnalyticsInformesController = Depends(get_analytics_informes_controller),
) -> list[TasaErrorTemaResponse]:
    """Tasa de error por unidad/tema de una materia, agregada o acotada a una comisión (RF-17).

    Sin `comision_id`, agrega toda la materia. `comision_id` que no pertenece a `materia_id`
    → 422 (`ComisionNoPerteneceAMateria`).
    """
    try:
        tasas = await controller.obtener_tasa_error_por_tema(materia_id, comision_id)
    except ComisionNoPerteneceAMateria as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return [
        TasaErrorTemaResponse(
            unidad_tematica=tasa.unidad_tematica,
            tema=tasa.tema,
            cantidad_respuestas=tasa.cantidad_respuestas,
            cantidad_incorrectas=tasa.cantidad_incorrectas,
            tasa_error=tasa.tasa_error,
        )
        for tasa in tasas
    ]


@router.get(
    "/materias/{materia_id}/comisiones/{comision_id}/desempeno",
    response_model=list[DesempenoComisionFilaResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_desempeno_por_comision(
    materia_id: UUID,
    comision_id: UUID,
    controller: AnalyticsInformesController = Depends(get_analytics_informes_controller),
) -> list[DesempenoComisionFilaResponse]:
    """Desempeño de todos los estudiantes de una comisión (`US-ADJ-44`, RF-20).

    `comision_id` que no pertenece a `materia_id` → 422 (`ComisionNoPerteneceAMateria`, mismo
    criterio que `obtener_tasa_error_por_tema`).
    """
    try:
        filas = await controller.obtener_desempeno_por_comision(materia_id, comision_id)
    except ComisionNoPerteneceAMateria as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return [
        DesempenoComisionFilaResponse(
            estudiante_id=fila.estudiante_id,
            nombre=fila.nombre,
            porcentaje_aciertos_acumulado=fila.porcentaje_aciertos_acumulado,
            actividades_pendientes=fila.actividades_pendientes,
        )
        for fila in filas
    ]


@router.get(
    "/materias/{materia_id}/estudiantes/{estudiante_id}/evolucion-temporal",
    response_model=list[EvolucionTemporalPuntoResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_evolucion_temporal_estudiante(
    materia_id: UUID,
    estudiante_id: UUID,
    estudiante_consulta: EstudianteConsultaPort = Depends(get_estudiante_consulta_port),
    controller: AnalyticsController = Depends(get_analytics_controller),
) -> list[EvolucionTemporalPuntoResponse]:
    """Evolución temporal individual de un estudiante (`US-ADJ-45`, RF-21).

    `estudiante_id` inexistente → 404, mismo criterio que `obtener_desempeno_de_estudiante`.
    """
    if not await estudiante_consulta.existe(estudiante_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un Estudiante con id {estudiante_id}.",
        )
    puntos = await controller.obtener_evolucion_temporal_estudiante(estudiante_id, materia_id)
    return [
        EvolucionTemporalPuntoResponse(
            actividad_id=punto.actividad_id,
            titulo_actividad=punto.titulo_actividad,
            finalizada_en=punto.finalizada_en,
            porcentaje_acierto=punto.porcentaje_acierto,
        )
        for punto in puntos
    ]


@router.get(
    "/materias/{materia_id}/comisiones/{comision_id}/evolucion-temporal",
    response_model=list[EvolucionTemporalComisionPuntoResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_evolucion_temporal_comision(
    materia_id: UUID,
    comision_id: UUID,
    controller: AnalyticsInformesController = Depends(get_analytics_informes_controller),
) -> list[EvolucionTemporalComisionPuntoResponse]:
    """Evolución temporal promedio de una comisión (`US-ADJ-45`, RF-21).

    `comision_id` que no pertenece a `materia_id` → 422 (`ComisionNoPerteneceAMateria`).
    """
    try:
        puntos = await controller.obtener_evolucion_temporal_comision(materia_id, comision_id)
    except ComisionNoPerteneceAMateria as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return [
        EvolucionTemporalComisionPuntoResponse(
            actividad_id=punto.actividad_id,
            titulo_actividad=punto.titulo_actividad,
            porcentaje_aciertos_promedio=punto.porcentaje_aciertos_promedio,
        )
        for punto in puntos
    ]


@router.get(
    "/materias/{materia_id}/ranking-preguntas-falladas",
    response_model=list[RankingPreguntaFalladaResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_ranking_preguntas_falladas(
    materia_id: UUID,
    comision_id: UUID | None = None,
    controller: AnalyticsInformesController = Depends(get_analytics_informes_controller),
) -> list[RankingPreguntaFalladaResponse]:
    """Ranking de preguntas más falladas de una materia, agregado o acotado a comisión (RF-22).

    Sin `comision_id`, agrega toda la materia. `comision_id` que no pertenece a `materia_id`
    → 422 (`ComisionNoPerteneceAMateria`).
    """
    try:
        ranking = await controller.obtener_ranking_preguntas_falladas(materia_id, comision_id)
    except ComisionNoPerteneceAMateria as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return [
        RankingPreguntaFalladaResponse(
            pregunta_id=fila.pregunta_id,
            enunciado=fila.enunciado,
            unidad_tematica=fila.unidad_tematica,
            tema=fila.tema,
            cantidad_presentaciones=fila.cantidad_presentaciones,
            cantidad_fallos=fila.cantidad_fallos,
            tasa_error=fila.tasa_error,
        )
        for fila in ranking
    ]


@router.get(
    "/actividades/{actividad_id}/completitud",
    response_model=CompletitudPorActividadResponse,
    dependencies=[Depends(require_docente)],
)
async def obtener_completitud_por_actividad(
    actividad_id: UUID,
    controller: AnalyticsCompletitudController = Depends(get_analytics_completitud_controller),
) -> CompletitudPorActividadResponse:
    """Completitud del roster aplicable de una actividad puntual (`US-ADJ-47`, RF-23).

    `actividad_id` inexistente → 404 (`ActividadNoExiste`).
    """
    try:
        completitud = await controller.obtener_completitud_por_actividad(actividad_id)
    except ActividadNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CompletitudPorActividadResponse(
        detalle=[
            CompletitudFilaResponse(
                estudiante_id=fila.estudiante_id, nombre=fila.nombre, estado=fila.estado
            )
            for fila in completitud.detalle
        ],
        resumen=CompletitudResumenResponse(
            finalizadas=completitud.resumen.finalizadas,
            en_curso=completitud.resumen.en_curso,
            suspendidas=completitud.resumen.suspendidas,
            sin_iniciar=completitud.resumen.sin_iniciar,
        ),
    )
