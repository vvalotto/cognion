"""Aggregate `ActividadEvaluativaPeriodoAbierto` (`BC-actividad-evaluativa-modelo.md` §5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.errors import (
    ActividadYaCerrada,
    CantidadIntentosInvalida,
    NoSePuedeAcortarConEvaluacionesActivas,
    PeriodoInvalido,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado


@dataclass
class ActividadEvaluativaPeriodoAbierto:
    """Ventana de disponibilidad administrada por el Docente (`ADR-015`).

    Primer evento de su propio stream en el event store (`US-3.1.1`) — no crece con la
    cantidad de estudiantes ni de respuestas (esas viven en `Evaluacion`, `US-3.1.3`).
    """

    id: UUID
    materia_id: UUID
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int
    cantidad_intentos_permitidos: int
    cerrada_manualmente: bool = field(default=False)

    @staticmethod
    def crear(
        materia_id: UUID,
        fecha_apertura: datetime,
        fecha_cierre: datetime,
        cantidad_preguntas: int,
        cantidad_intentos_permitidos: int,
    ) -> ActividadEvaluativaPeriodoAbierto:
        """Crea la actividad validando INV-AE-02/03.

        INV-AE-01 (preguntas suficientes en el banco de la materia) no se valida acá — requiere
        consultar a BC Banco de Preguntas vía puerto, responsabilidad del Use Case
        (`CrearActividadPeriodoAbiertoUseCase`).
        """
        if fecha_apertura >= fecha_cierre:
            raise PeriodoInvalido(fecha_apertura, fecha_cierre)
        if cantidad_intentos_permitidos < 1:
            raise CantidadIntentosInvalida(cantidad_intentos_permitidos)

        return ActividadEvaluativaPeriodoAbierto(
            id=uuid4(),
            materia_id=materia_id,
            fecha_apertura=fecha_apertura,
            fecha_cierre=fecha_cierre,
            cantidad_preguntas=cantidad_preguntas,
            cantidad_intentos_permitidos=cantidad_intentos_permitidos,
        )

    @staticmethod
    def reconstruir(eventos: list[EventoAlmacenado]) -> ActividadEvaluativaPeriodoAbierto:
        """Reconstruye la actividad reproduciendo su stream completo (replay, `ADR-002`).

        El primer evento es siempre `ActividadEvaluativaCreada` (arma los campos base). Los
        eventos siguientes se aplican según su `event_type` — `PeriodoDisponibilidadModificado`
        (`US-3.3.1`) es el primero que agrega un segundo evento posible a este stream, que hasta
        acá siempre tenía un único evento.
        """
        primero = eventos[0]
        payload = primero.payload
        actividad = ActividadEvaluativaPeriodoAbierto(
            id=UUID(payload["actividad_id"]),
            materia_id=UUID(payload["materia_id"]),
            fecha_apertura=datetime.fromisoformat(payload["fecha_apertura"]),
            fecha_cierre=datetime.fromisoformat(payload["fecha_cierre"]),
            cantidad_preguntas=int(payload["cantidad_preguntas"]),
            cantidad_intentos_permitidos=int(payload["cantidad_intentos_permitidos"]),
        )
        for evento in eventos[1:]:
            _aplicar_evento(actividad, evento)
        return actividad

    def validar_para_modificar_periodo(
        self, nueva_fecha_cierre: datetime, hay_evaluaciones_activas: bool
    ) -> None:
        """Valida INV-AE-02/04/04b antes de emitir `PeriodoDisponibilidadModificado`.

        No muta `self` — la mutación ocurre en el Use Case, después de persistir el evento
        (mismo criterio que `Evaluacion.validar_para_suspender()`, `US-3.2.2`).
        """
        if self.cerrada_manualmente:
            raise ActividadYaCerrada(self.id)
        if nueva_fecha_cierre <= self.fecha_apertura:
            raise PeriodoInvalido(self.fecha_apertura, nueva_fecha_cierre)
        acorta = nueva_fecha_cierre < self.fecha_cierre
        if acorta and hay_evaluaciones_activas:
            raise NoSePuedeAcortarConEvaluacionesActivas(self.id)


def _aplicar_evento(actividad: ActividadEvaluativaPeriodoAbierto, evento: EventoAlmacenado) -> None:
    """Aplica un evento del stream posterior a `ActividadEvaluativaCreada`, según su `event_type`.

    Extraído a función de módulo por el mismo criterio ya aplicado en
    `Evaluacion.reconstruir()`/`_aplicar_evento` (`US-3.2.2`).
    """
    if evento.event_type == "PeriodoDisponibilidadModificado":
        actividad.fecha_cierre = datetime.fromisoformat(evento.payload["nueva_fecha_cierre"])
