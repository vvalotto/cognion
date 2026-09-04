"""Router base del BC Analytics — endpoints de consulta de desempeño (`US-4.1.2`)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from src.analytics.frameworks.api.schemas import (
    DesempenoEstudianteResponse,
    EvaluacionDetalleResponse,
    ResumenDesempenoResponse,
)
from src.analytics.frameworks.dependencies import (
    get_analytics_controller,
    get_current_user,
    require_estudiante,
)
from src.analytics.interface_adapters.controllers.analytics_controller import (
    AnalyticsController,
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
