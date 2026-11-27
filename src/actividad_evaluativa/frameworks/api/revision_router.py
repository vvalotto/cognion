"""Router FastAPI de la revisión completa de una evaluación finalizada.

US-3.2.3, RF-13, US-ADJ-44.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.actividad_evaluativa.frameworks.api.schemas import (
    RevisionEvaluacionResponse,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    get_current_user,
    get_revision_controller,
    require_estudiante_o_docente,
)
from src.actividad_evaluativa.interface_adapters.controllers.revision_controller import (
    RevisionController,
)
from src.actividad_evaluativa.interface_adapters.presenters.evaluacion_presenter import (
    RevisionEvaluacionSalida,
)
from src.shared.entities.jwt import JWTPayload
from src.shared.entities.tipo_perfil import TipoPerfil

router = APIRouter(prefix="/evaluaciones", tags=["actividad_evaluativa"])


@router.get(
    "/{evaluacion_id}/revision",
    response_model=RevisionEvaluacionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_estudiante_o_docente)],
)
async def obtener_revision(
    evaluacion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: RevisionController = Depends(get_revision_controller),
) -> RevisionEvaluacionSalida:
    """Devuelve la revisión completa de una evaluación (RF-13).

    El propio Estudiante dueño siempre puede pedir la suya. Un Docente puede pedir la de
    cualquier Estudiante — drill-down de "Desempeño por comisión" (`US-ADJ-44`, RF-20), sin
    verificación de pertenencia Docente↔Materia (RBAC por rol, mismo precedente que `US-4.2.1`).
    Responde 404/422 ante los rechazos de dominio — 422 si todavía no fue finalizada.
    """
    verificar_propietario = usuario.rol is TipoPerfil.ESTUDIANTE
    return await controller.obtener_revision(
        evaluacion_id, usuario.usuario_id, verificar_propietario
    )
