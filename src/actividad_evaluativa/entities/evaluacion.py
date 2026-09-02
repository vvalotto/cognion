"""Aggregate `Evaluacion` (`BC-actividad-evaluativa-modelo.md` §3, §5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid5

from src.actividad_evaluativa.entities.errors import (
    EvaluacionNoSuspendida,
    EvaluacionSuspendida,
    EvaluacionYaFinalizada,
    EvaluacionYaSuspendida,
    IntentosAgotados,
    PreguntaNoAsignada,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado

_NAMESPACE_EVALUACION = UUID("a3f1c2d4-6b8e-4a1f-9c3d-2e5f7a8b9c0d")


class EstadoEvaluacion(StrEnum):
    """Estados del ciclo de vida de una `Evaluacion` (`BC-actividad-evaluativa-modelo.md` §5).

    `US-3.1.3` produce `EN_CURSO`, `SUSPENDIDA` llega con `US-3.2.2`, `FINALIZADA` (terminal)
    con `US-3.2.3`.
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

        El primer evento es siempre `EvaluacionIniciada` (arma los campos base). Los eventos
        siguientes se aplican según su `event_type` — `RespuestaRegistrada` (`US-3.2.1`) se
        acumula en `respuestas`, `EvaluacionSuspendida`/`EvaluacionReanudada` (`US-3.2.2`)
        mutan `estado` — el stream nunca reordena ni reemplaza eventos existentes.
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
            _aplicar_evento(evaluacion, evento)
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

    def validar_para_suspender(self) -> None:
        """Valida INV-AE-12 para `SuspenderEvaluacion` — no muta `self.estado`.

        No valida período vigente: pausar debe poder hacerse incluso si la actividad ya
        venció (la revalidación de vigencia ocurre recién al reanudar o registrar respuesta).
        """
        _validar_para_suspender(self)

    def validar_para_reanudar(self) -> None:
        """Valida INV-AE-11 para `ReanudarEvaluacion` — no muta `self.estado`."""
        _validar_para_reanudar(self)

    def validar_para_finalizar(self) -> None:
        """Valida que la `Evaluacion` no esté ya `Finalizada` — no muta `self.estado`."""
        _validar_para_finalizar(self)

    def respuesta_vigente_de(self, pregunta_id: UUID) -> Respuesta | None:
        """Devuelve la `Respuesta` vigente de `pregunta_id` (INV-AE-09), o `None` si no respondió.

        La vigente es la de `confirmada_en` más reciente entre los reintentos de esa pregunta —
        usada por `ObtenerRevisionEvaluacion` (RF-13) para no exponer respuestas superadas.
        """
        respuestas_de_la_pregunta = [
            respuesta for respuesta in self.respuestas if respuesta.pregunta_id == pregunta_id
        ]
        if not respuestas_de_la_pregunta:
            return None
        return max(respuestas_de_la_pregunta, key=lambda respuesta: respuesta.confirmada_en)


def _validar_para_suspender(evaluacion: Evaluacion) -> None:
    """Implementa INV-AE-12 para `validar_para_suspender` (misma extracción que INV-AE-07/08/12)."""
    if evaluacion.estado is EstadoEvaluacion.SUSPENDIDA:
        raise EvaluacionYaSuspendida(evaluacion.id)
    if evaluacion.estado is EstadoEvaluacion.FINALIZADA:
        raise EvaluacionYaFinalizada(evaluacion.id)


def _validar_para_reanudar(evaluacion: Evaluacion) -> None:
    """Implementa INV-AE-11 para `validar_para_reanudar` (misma extracción que INV-AE-07/08/12)."""
    if evaluacion.estado is EstadoEvaluacion.EN_CURSO:
        raise EvaluacionNoSuspendida(evaluacion.id)
    if evaluacion.estado is EstadoEvaluacion.FINALIZADA:
        raise EvaluacionYaFinalizada(evaluacion.id)


def _validar_para_finalizar(evaluacion: Evaluacion) -> None:
    """Implementa el único rechazo de `validar_para_finalizar` — ya `Finalizada`.

    `FinalizarEvaluacion` es válido desde `EnCurso` o `Suspendida` — no hay más restricciones
    (a diferencia de `SuspenderEvaluacion`/`ReanudarEvaluacion`, no valida período vigente).
    """
    if evaluacion.estado is EstadoEvaluacion.FINALIZADA:
        raise EvaluacionYaFinalizada(evaluacion.id)


def _aplicar_evento(evaluacion: Evaluacion, evento: EventoAlmacenado) -> None:
    """Aplica un evento del stream posterior a `EvaluacionIniciada`, según su `event_type`.

    Extraído a función de módulo para que `reconstruir` no acumule un `if/elif` por tipo de
    evento dentro del propio método (mismo criterio de bajar CBO/CC ya aplicado en el BC).
    """
    if evento.event_type == "RespuestaRegistrada":
        payload = evento.payload
        evaluacion.respuestas.append(
            Respuesta(
                id=UUID(payload["respuesta_id"]),
                pregunta_id=UUID(payload["pregunta_id"]),
                numero_intento=payload["numero_intento"],
                contenido=payload["contenido"],
                es_correcta=payload["es_correcta"],
                confirmada_en=datetime.fromisoformat(payload["ocurrido_en"]),
            )
        )
    elif evento.event_type == "EvaluacionSuspendida":
        evaluacion.estado = EstadoEvaluacion.SUSPENDIDA
    elif evento.event_type == "EvaluacionReanudada":
        evaluacion.estado = EstadoEvaluacion.EN_CURSO
    elif evento.event_type == "EvaluacionFinalizada":
        evaluacion.estado = EstadoEvaluacion.FINALIZADA


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
