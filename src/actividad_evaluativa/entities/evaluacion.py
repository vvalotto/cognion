"""Aggregate `Evaluacion` (`BC-actividad-evaluativa-modelo.md` §3, §5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid5

from src.actividad_evaluativa.entities.errors import (
    EvaluacionSuspendida,
    EvaluacionYaFinalizada,
    IntentosAgotados,
    PreguntaNoAsignada,
)
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


@dataclass(frozen=True)
class Respuesta:
    """Una confirmación del estudiante para una pregunta — Entity, `id` propio (INV-AE-09).

    Inmutable una vez creada: `RegistrarRespuesta` nunca modifica ni borra una `Respuesta`
    existente, solo agrega una nueva (`BC-actividad-evaluativa-modelo.md` §5).
    """

    id: UUID
    pregunta_id: UUID
    numero_intento: int
    contenido: dict[str, Any]
    es_correcta: bool
    confirmada_en: datetime = field(default_factory=lambda: datetime.now(UTC))


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
    respuestas: list[Respuesta] = field(default_factory=list)

    @staticmethod
    def id_para(actividad_id: UUID, estudiante_id: UUID) -> UUID:
        """Deriva el id determinístico del par `(actividad_id, estudiante_id)`.

        No es un `uuid4` aleatorio: es la clave natural del aggregate, codificada como UUID
        para poder usarla como `aggregate_id` del event store sin ensanchar ningún puerto con
        una búsqueda por par (mismo criterio de `US-3.1.2`/`US-2.1.9`).
        """
        return uuid5(_NAMESPACE_EVALUACION, f"{actividad_id}:{estudiante_id}")

    @staticmethod
    def armar_preguntas_asignadas(ids_muestreados: list[UUID]) -> list[PreguntaAsignada]:
        """Arma la lista de `PreguntaAsignada` a partir de una muestra ya sampleada.

        `orden` es la posición dentro de la muestra — el sampleo aleatorio en sí (RF-12) es
        responsabilidad del Use Case, que no conoce la construcción del Value Object.
        """
        return [
            PreguntaAsignada(pregunta_id=pregunta_id, orden=orden)
            for orden, pregunta_id in enumerate(ids_muestreados)
        ]

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
        """Reconstruye la `Evaluacion` reproduciendo su stream completo (replay, `ADR-002`).

        El primer evento es siempre `EvaluacionIniciada` (arma los campos base). Cada evento
        siguiente es una `RespuestaRegistrada` (`US-3.2.1`) que se acumula en `respuestas` —
        el stream nunca reordena ni reemplaza eventos existentes.
        """
        primero = eventos[0]
        payload = primero.payload
        preguntas_asignadas = [
            PreguntaAsignada(pregunta_id=UUID(p["pregunta_id"]), orden=p["orden"])
            for p in payload["preguntas_asignadas"]
        ]
        evaluacion = Evaluacion(
            id=UUID(payload["evaluacion_id"]),
            actividad_id=UUID(payload["actividad_id"]),
            estudiante_id=UUID(payload["estudiante_id"]),
            preguntas_asignadas=preguntas_asignadas,
            estado=EstadoEvaluacion.EN_CURSO,
            iniciada_en=datetime.fromisoformat(payload["ocurrido_en"]),
        )
        for evento in eventos[1:]:
            payload_respuesta = evento.payload
            evaluacion.respuestas.append(
                Respuesta(
                    id=UUID(payload_respuesta["respuesta_id"]),
                    pregunta_id=UUID(payload_respuesta["pregunta_id"]),
                    numero_intento=payload_respuesta["numero_intento"],
                    contenido=payload_respuesta["contenido"],
                    es_correcta=payload_respuesta["es_correcta"],
                    confirmada_en=datetime.fromisoformat(payload_respuesta["ocurrido_en"]),
                )
            )
        return evaluacion

    def contar_respuestas_de(self, pregunta_id: UUID) -> int:
        """Cuenta las `Respuesta` ya registradas para `pregunta_id` — sostiene INV-AE-08."""
        return sum(1 for respuesta in self.respuestas if respuesta.pregunta_id == pregunta_id)

    def validar_para_registrar_respuesta(
        self, pregunta_id: UUID, cantidad_intentos_permitidos: int
    ) -> int:
        """Valida INV-AE-07/08/12 y devuelve el `numero_intento` de la nueva `Respuesta`.

        El llamador (Use Case) es quien conoce `es_correcta` (consulta a Banco de Preguntas) y
        arma la `Respuesta` en sí, recién después de persistir `RespuestaRegistrada` en el
        event store (INV-AE-09); este método no muta `self.respuestas`.
        """
        return _validar_para_registrar_respuesta(self, pregunta_id, cantidad_intentos_permitidos)


def _validar_para_registrar_respuesta(
    evaluacion: Evaluacion, pregunta_id: UUID, cantidad_intentos_permitidos: int
) -> int:
    """Implementa INV-AE-07/08/12 para `validar_para_registrar_respuesta`.

    Función de módulo, no método, para no acoplar `Evaluacion` a los 4 errores de dominio que
    puede levantar (mismo criterio de extracción de responsabilidad ya aplicado en `US-3.1.3`
    para bajar CBO sin cambiar comportamiento).
    """
    if evaluacion.estado is EstadoEvaluacion.SUSPENDIDA:
        raise EvaluacionSuspendida(evaluacion.id)
    if evaluacion.estado is EstadoEvaluacion.FINALIZADA:
        raise EvaluacionYaFinalizada(evaluacion.id)
    if not any(p.pregunta_id == pregunta_id for p in evaluacion.preguntas_asignadas):
        raise PreguntaNoAsignada(evaluacion.id, pregunta_id)

    numero_intento = evaluacion.contar_respuestas_de(pregunta_id) + 1
    if numero_intento > cantidad_intentos_permitidos:
        raise IntentosAgotados(pregunta_id, cantidad_intentos_permitidos)

    return numero_intento
