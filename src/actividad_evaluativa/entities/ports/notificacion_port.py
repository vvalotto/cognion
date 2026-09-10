"""Puerto de disparo de notificaciones, dueño de BC Actividad Evaluativa (`US-5.1.1`).

Puerto de **disparo** (no de consulta) — a diferencia de los demás puertos cruzados de este
BC, Actividad Evaluativa es quien lo posee e invoca, no quien lo consulta. Comunicación entre
BCs solo por puertos definidos en `entities/ports/` (`CLAUDE.md`) — evita que Actividad
Evaluativa importe directamente `src/notificaciones/`.

Contrato declarado en esta US, sin implementación cableada todavía: ningún adapter lo
implementa y ningún Use Case lo invoca hasta `US-5.1.2` (`NotificacionPortInProcess`, único
punto de Actividad Evaluativa que importará `src.notificaciones`,
`BC-notificaciones-modelo.md` §5).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class NotificacionPort(ABC):
    """Dispara las notificaciones de apertura y cierre de una Actividad Evaluativa (RF-14)."""

    @abstractmethod
    async def notificar_apertura(
        self,
        actividad_id: UUID,
        materia_id: UUID,
        materia_nombre: str,
        titulo: str,
        fecha_apertura: datetime,
        fecha_cierre: datetime,
        comisiones_ids: list[UUID],
    ) -> None:
        """Notifica la apertura de una actividad a sus destinatarios.

        `materia_nombre` viaja aparte de `materia_id` porque el email debe mostrar el nombre
        de la materia y ni el evento `ActividadEvaluativaCreada` ni este puerto lo llevaban
        hasta `US-5.1.2` — quien invoca ya lo tiene en memoria (`MateriaConsultaPort.obtener`)
        y lo pasa directo, sin que Notificaciones necesite su propio `MateriaConsultaPort`.

        Se invoca al final de `CrearActividadPeriodoAbiertoUseCase.execute()`, después de
        persistir `ActividadEvaluativaCreada`. Nunca propaga una excepción hacia quien la
        invoca — el manejo de fallos de envío es responsabilidad exclusiva de Notificaciones.
        """
        ...

    @abstractmethod
    async def notificar_cierre(
        self,
        actividad_id: UUID,
        materia_id: UUID,
        titulo: str,
        comisiones_ids: list[UUID],
    ) -> None:
        """Notifica el cierre manual de una actividad a sus destinatarios.

        Se invoca al final de `CerrarActividadUseCase.execute()`, después de persistir
        `ActividadEvaluativaCerrada` — solo ante cierre manual, nunca ante el vencimiento
        natural del período. Nunca propaga una excepción hacia quien la invoca.
        """
        ...
