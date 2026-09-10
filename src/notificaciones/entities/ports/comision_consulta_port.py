"""Puerto de consulta de comisiones y destinatarios con email, dueño de BC Identidad.

Copia propia de Notificaciones — no reutiliza el `ComisionConsultaPort` ya existente en
Analytics/Banco de Preguntas porque ninguna de esas copias expone `email` (pensadas para
selectores de UI, solo `id`/`nombre`). Comunicación entre BCs solo por puertos definidos en
`entities/ports/` (`CLAUDE.md`) — este puerto evita que Notificaciones importe directamente
ningún módulo de `src/identidad/` (`BC-notificaciones-modelo.md` §5).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DestinatarioNotificacion:
    """Estudiante destinatario de una notificación, con el email necesario para enviarla."""

    estudiante_id: UUID
    nombre: str
    email: str


class ComisionConsultaPort(ABC):
    """Resuelve comisiones y su roster de estudiantes con email, de BC Identidad."""

    @abstractmethod
    async def listar_comisiones_por_materia(self, materia_id: UUID) -> list[UUID]:
        """Lista los ids de las comisiones activas de una materia.

        Usado solo cuando el disparo de notificación llega con `comisiones_ids` vacío
        (la actividad no está restringida a ninguna comisión en particular). Materia sin
        comisiones → lista vacía.
        """
        ...

    @abstractmethod
    async def listar_destinatarios(
        self, comision_ids: list[UUID]
    ) -> list[DestinatarioNotificacion]:
        """Lista el roster combinado de estudiantes de las comisiones indicadas.

        Si un estudiante está inscripto en más de una de las comisiones dadas, aparece una
        sola vez en el resultado. Comisión(es) sin inscriptos → lista vacía.
        """
        ...
