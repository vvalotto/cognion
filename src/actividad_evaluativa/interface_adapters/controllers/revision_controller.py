"""Controller de la API para la revisión de una evaluación finalizada.

US-3.2.3, RF-13, US-ADJ-44.
"""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.revision_evaluacion import RevisionEvaluacion
from src.actividad_evaluativa.use_cases.obtener_revision_evaluacion import (
    ObtenerRevisionEvaluacionUseCase,
)


class RevisionController:
    """Adapta requests HTTP a la query de revisión — separado de `EvaluacionesController`.

    Command/query aparte, mismo criterio ya aplicado en Incremento 2
    (`BancosController`/`PreguntasController`, `CuentasController`/`UsuariosController`) para
    no repetir el CRITICAL de CBO que salió tres veces al mezclar ambos en un solo controller.
    """

    def __init__(self, obtener_revision_evaluacion: ObtenerRevisionEvaluacionUseCase) -> None:
        """Recibe el caso de uso de la query de revisión."""
        self._obtener_revision_evaluacion = obtener_revision_evaluacion

    async def obtener_revision(
        self, evaluacion_id: UUID, usuario_id: UUID, verificar_propietario: bool = True
    ) -> RevisionEvaluacion:
        """Delega la composición de la revisión en el caso de uso correspondiente.

        `verificar_propietario=False` habilita el drill-down del Docente (`US-ADJ-44`) sobre la
        evaluación de un Estudiante que no es quien hace la request.
        """
        return await self._obtener_revision_evaluacion.execute(
            evaluacion_id, usuario_id, verificar_propietario
        )
