"""Aggregate `Evaluacion` (`BC-actividad-evaluativa-modelo.md` §3, §5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid5

from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado

_NAMESPACE_EVALUACION = UUID("a3f1c2d4-6b8e-4a1f-9c3d-2e5f7a8b9c0d")


class EstadoEvaluacion(StrEnum):
    """Estados del ciclo de vida de una `Evaluacion` (`BC-actividad-evaluativa-modelo.md` §5).

    `US-3.1.3` solo produce `EN_CURSO` — `SUSPENDIDA`/`FINALIZADA` llegan con `US-3.2.2`/`US-3.2.3`.
    """

    EN_CURSO = "EnCurso"
    SUSPENDIDA = "Suspendida"
    FINALIZADA = "Finalizada"


@dataclass(frozen=True)
class PreguntaAsignada:
    """Una pregunta fijada al set de un estudiante — sin identidad propia (Value Object)."""

    pregunta_id: UUID
    orden: int


@dataclass
class Evaluacion:
    """Recorrido de un Estudiante particular dentro de una `ActividadEvaluativaPeriodoAbierto`.

    Un aggregate por `(actividad_id, estudiante_id)`, con `id` propio pero determinístico
    (`id_para`) — el stream del event store se indexa por ese id, que sirve a la vez de
    mecanismo de idempotencia (INV-AE-06): dos `IniciarEvaluacion` del mismo par resuelven al
    mismo stream.
    """

    id: UUID
    actividad_id: UUID
    estudiante_id: UUID
    preguntas_asignadas: list[PreguntaAsignada]
    estado: EstadoEvaluacion = field(default=EstadoEvaluacion.EN_CURSO)
    iniciada_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def id_para(actividad_id: UUID, estudiante_id: UUID) -> UUID:
        """Deriva el id determinístico del par `(actividad_id, estudiante_id)`.

        No es un `uuid4` aleatorio: es la clave natural del aggregate, codificada como UUID
        para poder usarla como `aggregate_id` del event store sin ensanchar ningún puerto con
        una búsqueda por par (mismo criterio de `US-3.1.2`/`US-2.1.9`).
        """
        return uuid5(_NAMESPACE_EVALUACION, f"{actividad_id}:{estudiante_id}")

    @staticmethod
    def crear(
        actividad_id: UUID,
        estudiante_id: UUID,
        preguntas_asignadas: list[PreguntaAsignada],
    ) -> Evaluacion:
        """Crea la `Evaluacion` con el set de preguntas ya fijado (INV-AE-05).

        Sin validación propia — INV-AE-05/06 y `FueraDePeriodo` son responsabilidad del Use
        Case, que necesita el event store y la `ActividadEvaluativaPeriodoAbierto` cargada.
        """
        return Evaluacion(
            id=Evaluacion.id_para(actividad_id, estudiante_id),
            actividad_id=actividad_id,
            estudiante_id=estudiante_id,
            preguntas_asignadas=preguntas_asignadas,
            estado=EstadoEvaluacion.EN_CURSO,
        )

    @staticmethod
    def reconstruir(eventos: list[EventoAlmacenado]) -> Evaluacion:
        """Reconstruye la `Evaluacion` reproduciendo su stream (replay, `ADR-002`).

        Por ahora el stream solo tiene `EvaluacionIniciada` — el único evento de `US-3.1.3`.
        """
        primero = eventos[0]
        payload = primero.payload
        preguntas_asignadas = [
            PreguntaAsignada(pregunta_id=UUID(p["pregunta_id"]), orden=p["orden"])
            for p in payload["preguntas_asignadas"]
        ]
        return Evaluacion(
            id=UUID(payload["evaluacion_id"]),
            actividad_id=UUID(payload["actividad_id"]),
            estudiante_id=UUID(payload["estudiante_id"]),
            preguntas_asignadas=preguntas_asignadas,
            estado=EstadoEvaluacion.EN_CURSO,
            iniciada_en=datetime.fromisoformat(payload["ocurrido_en"]),
        )
