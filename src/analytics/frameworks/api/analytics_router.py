"""Router base del BC Analytics — endpoints de consulta de desempeño (`US-4.1.2`, `US-4.2.1`, `US-4.2.4`)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from src.analytics.frameworks.api.schemas import (
    CompletitudPorActividadResponse,
    DesempenoComisionFilaResponse,
    DesempenoEstudianteResponse,
    EvolucionTemporalComisionPuntoResponse,
    EvolucionTemporalPuntoResponse,
    RankingPreguntaFalladaResponse,
    TasaErrorTemaResponse,
)
from src.analytics.frameworks.dependencies import (
    get_analytics_completitud_controller,
    get_analytics_controller,
    get_analytics_informes_controller,
    get_current_user,
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
from src.analytics.interface_adapters.presenters.analytics_presenter import (
    CompletitudPorActividadSalida,
    DesempenoComisionFilaSalida,
    DesempenoEstudianteSalida,
    EvolucionTemporalComisionPuntoSalida,
    EvolucionTemporalPuntoSalida,
    RankingPreguntaFalladaSalida,
    TasaErrorTemaSalida,
)
from src.shared.entities.jwt import JWTPayload

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/materias/{materia_id}/mi-desempeno",
    response_model=DesempenoEstudianteResponse,
    dependencies=[Depends(require_estudiante)],
)
async def obtener_mi_desempeno(
    materia_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: AnalyticsController = Depends(get_analytics_controller),
) -> DesempenoEstudianteSalida:
    """Desempeño del Estudiante autenticado en `materia_id`: detalle y resumen (RF-15).

    `estudiante_id` sale siempre del token — nunca de un parámetro de la request, evita que
    un estudiante consulte el desempeño de otro (esa consulta es exclusiva del Docente,
    `US-4.2.1`, con su propio endpoint y su propia verificación de rol).
    """
    return await controller.obtener_mi_desempeno(usuario.usuario_id, materia_id)


@router.get(
    "/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno",
    response_model=DesempenoEstudianteResponse,
    dependencies=[Depends(require_docente)],
)
async def obtener_desempeno_de_estudiante(
    materia_id: UUID,
    estudiante_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: AnalyticsController = Depends(get_analytics_controller),
) -> DesempenoEstudianteSalida:
    """Desempeño de un Estudiante elegido por el Docente en `materia_id`: detalle y resumen (RF-16).

    El Docente debe tener al menos una Comisión asignada en `materia_id` (`US-ADJ-57`) —
    reemplaza el hot spot de autorización documentado en
    `docs/design/domain/BC-analytics-modelo.md` §4. A diferencia de `obtener_mi_desempeno`,
    acá `estudiante_id` sí puede ser inválido (viene del path, no del token) — se valida su
    existencia antes de invocar el Use Case.
    """
    return await controller.obtener_desempeno_de_estudiante(
        estudiante_id, materia_id, usuario.usuario_id
    )


@router.get(
    "/materias/{materia_id}/tasa-error-por-tema",
    response_model=list[TasaErrorTemaResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_tasa_error_por_tema(
    materia_id: UUID,
    comision_id: UUID | None = None,
    usuario: JWTPayload = Depends(get_current_user),
    controller: AnalyticsInformesController = Depends(get_analytics_informes_controller),
) -> list[TasaErrorTemaSalida]:
    """Tasa de error por unidad/tema de una materia, agregada o acotada a una comisión (RF-17).

    Sin `comision_id`, agrega toda la materia. `comision_id` que no pertenece a `materia_id`
    → 422 (`ComisionNoPerteneceAMateria`). Docente sin autorización sobre la materia, o sobre
    la comisión puntual → 403 (`US-ADJ-57`).
    """
    return await controller.obtener_tasa_error_por_tema(materia_id, comision_id, usuario.usuario_id)


@router.get(
    "/materias/{materia_id}/comisiones/{comision_id}/desempeno",
    response_model=list[DesempenoComisionFilaResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_desempeno_por_comision(
    materia_id: UUID,
    comision_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: AnalyticsInformesController = Depends(get_analytics_informes_controller),
) -> list[DesempenoComisionFilaSalida]:
    """Desempeño de todos los estudiantes de una comisión (`US-ADJ-44`, RF-20).

    `comision_id` que no pertenece a `materia_id` → 422 (`ComisionNoPerteneceAMateria`, mismo
    criterio que `obtener_tasa_error_por_tema`). Docente sin autorización → 403 (`US-ADJ-57`).
    """
    return await controller.obtener_desempeno_por_comision(
        materia_id, comision_id, usuario.usuario_id
    )


@router.get(
    "/materias/{materia_id}/estudiantes/{estudiante_id}/evolucion-temporal",
    response_model=list[EvolucionTemporalPuntoResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_evolucion_temporal_estudiante(
    materia_id: UUID,
    estudiante_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: AnalyticsController = Depends(get_analytics_controller),
) -> list[EvolucionTemporalPuntoSalida]:
    """Evolución temporal individual de un estudiante (`US-ADJ-45`, RF-21).

    `estudiante_id` inexistente → 404, mismo criterio que `obtener_desempeno_de_estudiante`.
    Docente sin Comisión asignada en `materia_id` → 403 (`US-ADJ-57`).
    """
    return await controller.obtener_evolucion_temporal_estudiante(
        estudiante_id, materia_id, usuario.usuario_id
    )


@router.get(
    "/materias/{materia_id}/comisiones/{comision_id}/evolucion-temporal",
    response_model=list[EvolucionTemporalComisionPuntoResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_evolucion_temporal_comision(
    materia_id: UUID,
    comision_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: AnalyticsInformesController = Depends(get_analytics_informes_controller),
) -> list[EvolucionTemporalComisionPuntoSalida]:
    """Evolución temporal promedio de una comisión (`US-ADJ-45`, RF-21).

    `comision_id` que no pertenece a `materia_id` → 422 (`ComisionNoPerteneceAMateria`).
    Docente sin autorización → 403 (`US-ADJ-57`).
    """
    return await controller.obtener_evolucion_temporal_comision(
        materia_id, comision_id, usuario.usuario_id
    )


@router.get(
    "/materias/{materia_id}/ranking-preguntas-falladas",
    response_model=list[RankingPreguntaFalladaResponse],
    dependencies=[Depends(require_docente)],
)
async def obtener_ranking_preguntas_falladas(
    materia_id: UUID,
    comision_id: UUID | None = None,
    usuario: JWTPayload = Depends(get_current_user),
    controller: AnalyticsInformesController = Depends(get_analytics_informes_controller),
) -> list[RankingPreguntaFalladaSalida]:
    """Ranking de preguntas más falladas de una materia, agregado o acotado a comisión (RF-22).

    Sin `comision_id`, agrega toda la materia. `comision_id` que no pertenece a `materia_id`
    → 422 (`ComisionNoPerteneceAMateria`). Docente sin autorización → 403 (`US-ADJ-57`).
    """
    return await controller.obtener_ranking_preguntas_falladas(
        materia_id, comision_id, usuario.usuario_id
    )


@router.get(
    "/actividades/{actividad_id}/completitud",
    response_model=CompletitudPorActividadResponse,
    dependencies=[Depends(require_docente)],
)
async def obtener_completitud_por_actividad(
    actividad_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: AnalyticsCompletitudController = Depends(get_analytics_completitud_controller),
) -> CompletitudPorActividadSalida:
    """Completitud del roster aplicable de una actividad puntual (`US-ADJ-47`, RF-23).

    `actividad_id` inexistente → 404 (`ActividadNoExiste`). Docente sin Comisión asignada en
    la materia de la actividad → 403 (`US-ADJ-57`).
    """
    return await controller.obtener_completitud_por_actividad(actividad_id, usuario.usuario_id)
