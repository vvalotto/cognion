"""Puerto de consulta (CQRS, solo lectura) de la participación del Estudiante en el modo en vivo.

Segundo puerto de Analytics hacia Actividad Evaluativa (junto a
`EvaluacionDesempenoConsultaPort`, `US-4.1.1`) — mismo criterio de DTO propio, sin exponer los
aggregates ajenos (`ActividadEvaluativaEnVivo`, `ParticipacionEnVivo`). Consumido por
`ObtenerDesempenoEstudianteUseCase` (`US-4.1.2`, ampliado en `US-ADJ-56`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SesionEnVivoDesempenoResumen:
    """Resumen de una sesión en vivo `Finalizada` en la que participó un Estudiante.

    `posicion`/`total_participantes` reflejan el ranking final de la sesión completa, no solo
    del Estudiante consultado — mismo criterio de "posición del ranking final" del wireframe
    (`wireframes-analytics.md` §6.1).
    """

    sesion_id: UUID
    comision_id: UUID
    materia_id: UUID
    finalizada_en: datetime
    cantidad_preguntas: int
    cantidad_correctas: int
    cantidad_incorrectas: int
    puntaje_final: int
    posicion: int
    total_participantes: int


class SesionEnVivoDesempenoConsultaPort(ABC):
    """Consulta de solo lectura: sesiones en vivo finalizadas en las que participó un Estudiante."""

    @abstractmethod
    async def listar_sesiones_finalizadas(
        self, estudiante_id: UUID, materia_id: UUID | None
    ) -> list[SesionEnVivoDesempenoResumen]:
        """Devuelve las sesiones en vivo `Finalizada` en las que participó el estudiante.

        Sin `materia_id`, devuelve las de todas las materias. Una sesión que el estudiante nunca
        se unió, o que todavía no está `Finalizada` (`EnEspera`, `EnCurso`) o fue `Cancelada`,
        nunca aparece en el resultado.
        """
