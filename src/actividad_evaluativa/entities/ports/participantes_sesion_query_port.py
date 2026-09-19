"""Puerto de consulta (CQRS) del read model `participantes_por_sesion` (`US-6.1.3`).

Sostiene la sala de espera del Docente (`BC-actividad-evaluativa-modelo.md` §15). Separado de
`EventStorePort` por el mismo criterio de command/query que `EvaluacionActivaQueryPort`: acá la
operación es una consulta transversal a los streams de `ParticipacionEnVivo` de una sesión, no
la reconstrucción de uno solo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ParticipanteResumen:
    """Un Estudiante unido a una sesión en vivo."""

    estudiante_id: UUID
    unido_en: datetime


class ParticipantesSesionQueryPort(ABC):
    """Consulta de solo lectura de los participantes de una sesión en vivo."""

    @abstractmethod
    async def listar(self, sesion_id: UUID) -> list[ParticipanteResumen]:
        """Devuelve los Estudiantes unidos a `sesion_id`, en orden de unión (más antiguo primero).

        Lista vacía si nadie se unió todavía.
        """
