"""Aggregate `ActividadEvaluativaEnVivo` (`BC-actividad-evaluativa-modelo.md` §14)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.errors import (
    NoQuedanPreguntas,
    OpcionesNoMostradasTodavia,
    OpcionesYaMostradas,
    PreguntaActualNoCerrada,
    PreguntaNoActual,
    PreguntaYaCerrada,
    SesionNoEnCurso,
    SesionYaCancelada,
    SesionYaFinalizada,
    SesionYaIniciada,
    TiempoAgotado,
    TiempoLimiteInvalido,
)
from src.actividad_evaluativa.entities.evaluacion import PreguntaAsignada
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado


class EstadoSesionEnVivo(StrEnum):
    """Estados posibles de una sesión en vivo."""

    EN_ESPERA = "EnEspera"
    EN_CURSO = "EnCurso"
    FINALIZADA = "Finalizada"
    CANCELADA = "Cancelada"
    """Terminal: el Docente la descartó sin iniciarla (`US-ADJ-58`, INV-AEV-10)."""


@dataclass
class ActividadEvaluativaEnVivo:
    """Sesión sincrónica dirigida por el Docente para una Comisión puntual (`ADR-015`).

    Igual que `ActividadEvaluativaPeriodoAbierto`, no crece con la cantidad de estudiantes ni de
    respuestas — esas viven en `ParticipacionEnVivo`. `US-6.1.2` solo ejercita la construcción
    inicial (`EnEspera`, sin pregunta actual); las transiciones posteriores las agregan
    `US-6.1.4` y la Iteración 2.
    """

    id: UUID
    comision_id: UUID
    materia_id: UUID
    preguntas: list[PreguntaAsignada]
    tiempo_limite_por_pregunta_segundos: int
    unidad_tematica: str | None = field(default=None)
    """`None` (default) significa "cualquier unidad", combinable con `tema` (AND)."""
    tema: str | None = field(default=None)
    """`None` (default) significa "cualquier tema" del banco de la Materia."""
    estado: EstadoSesionEnVivo = field(default=EstadoSesionEnVivo.EN_ESPERA)
    pregunta_actual_indice: int | None = field(default=None)
    opciones_mostradas: bool = field(default=False)
    opciones_mostradas_en: datetime | None = field(default=None)
    """Instante de `OpcionesEnVivoMostradas`: referencia de `tiempo_respuesta` (INV-AEV-08)."""
    pregunta_actual_cerrada: bool = field(default=False)

    @staticmethod
    def crear(
        comision_id: UUID,
        materia_id: UUID,
        preguntas: list[PreguntaAsignada],
        tiempo_limite_por_pregunta_segundos: int,
        unidad_tematica: str | None = None,
        tema: str | None = None,
    ) -> ActividadEvaluativaEnVivo:
        """Crea la sesión en `EnEspera` con el set de preguntas ya fijado, validando INV-AEV-02.

        INV-AEV-01 (preguntas suficientes en el banco) no se valida acá — requiere consultar a
        BC Banco de Preguntas vía puerto, responsabilidad del Use Case
        (`CrearSesionEnVivoUseCase`).
        """
        if tiempo_limite_por_pregunta_segundos <= 0:
            raise TiempoLimiteInvalido(tiempo_limite_por_pregunta_segundos)

        return ActividadEvaluativaEnVivo(
            id=uuid4(),
            comision_id=comision_id,
            materia_id=materia_id,
            preguntas=preguntas,
            tiempo_limite_por_pregunta_segundos=tiempo_limite_por_pregunta_segundos,
            unidad_tematica=unidad_tematica or None,
            tema=tema or None,
        )

    @staticmethod
    def reconstruir(eventos: list[EventoAlmacenado]) -> ActividadEvaluativaEnVivo:
        """Reconstruye la sesión reproduciendo su stream completo (replay, `ADR-002`).

        El primer evento es siempre `SesionEnVivoCreada` (arma los campos base). Los siguientes
        se aplican según su `event_type`; modifican `estado` y, con `SesionEnVivoIniciada`, la
        pregunta actual. Los demás campos de cada transición los define la US que emite el
        evento (Iteración 2).
        """
        payload = eventos[0].payload
        sesion = ActividadEvaluativaEnVivo(
            id=UUID(payload["sesion_id"]),
            comision_id=UUID(payload["comision_id"]),
            materia_id=UUID(payload["materia_id"]),
            preguntas=[
                PreguntaAsignada(pregunta_id=UUID(p["pregunta_id"]), orden=p["orden"])
                for p in payload["preguntas"]
            ],
            tiempo_limite_por_pregunta_segundos=int(payload["tiempo_limite_por_pregunta_segundos"]),
            unidad_tematica=payload.get("unidad_tematica") or None,
            tema=payload.get("tema") or None,
        )
        for evento in eventos[1:]:
            _aplicar_evento(sesion, evento)
        return sesion

    def validar_para_unirse(self) -> None:
        """Valida que la sesión admita nuevas uniones — rechaza si está `Finalizada` o `Cancelada`.

        Una sesión `EnEspera` o ya `EnCurso` admite la unión (unión tardía, `US-6.1.3`). No muta
        `self` (mismo criterio que `Evaluacion.validar_para_suspender`).
        """
        _rechazar_si_cancelada(self)
        if self.estado == EstadoSesionEnVivo.FINALIZADA:
            raise SesionYaFinalizada(self.id)

    def iniciar(self) -> None:
        """Pasa la sesión de `EnEspera` a `EnCurso` con la primera pregunta como actual.

        Levanta `SesionYaCancelada` si fue cancelada y `SesionYaIniciada` si ya no está `EnEspera`
        (`EnCurso` o `Finalizada`) — no hay caso de uso de "reiniciar" una sesión ya arrancada.
        INV-AEV-11 (al menos un participante, `US-ADJ-58`) no se valida acá: las participaciones
        viven en `ParticipacionEnVivo`, las consulta `IniciarSesionEnVivoUseCase` por puerto.
        """
        _rechazar_si_cancelada(self)
        if self.estado != EstadoSesionEnVivo.EN_ESPERA:
            raise SesionYaIniciada(self.id)
        self.estado = EstadoSesionEnVivo.EN_CURSO
        self.pregunta_actual_indice = 0
        self.opciones_mostradas = False
        self.pregunta_actual_cerrada = False

    def mostrar_opciones(self, ahora: datetime) -> None:
        """Revela las opciones de la pregunta actual y arranca el temporizador (`US-6.2.2`).

        Levanta `SesionNoEnCurso` si la sesión no está `EnCurso` y `OpcionesYaMostradas`
        (INV-AEV-09) si ya se mostraron — sin mutar en ninguno de los dos casos.
        """
        _validar_para_mostrar_opciones(self)
        self.opciones_mostradas = True
        self.opciones_mostradas_en = ahora

    def cerrar_pregunta(self) -> None:
        """Cierra la pregunta actual: deja de aceptar respuestas (`US-6.2.5`).

        Levanta `SesionNoEnCurso`, `OpcionesNoMostradasTodavia` (INV-AEV-09) o `PreguntaYaCerrada`
        sin mutar. El cierre es manual: es independiente del corte por `TiempoAgotado`.
        """
        _validar_para_cerrar(self)
        self.pregunta_actual_cerrada = True

    def avanzar(self) -> None:
        """Pasa a la siguiente pregunta, con las opciones ocultas y sin cerrar (`US-6.2.6`).

        Levanta `SesionNoEnCurso`, `PreguntaActualNoCerrada` (INV-AEV-03) o `NoQuedanPreguntas`
        sin mutar.
        """
        _validar_para_avanzar(self)
        _pasar_a_pregunta(self, (self.pregunta_actual_indice or 0) + 1)

    def cancelar(self) -> None:
        """Descarta una sesión que nunca se inició: pasa a `Cancelada` (`US-ADJ-58`, INV-AEV-10).

        Levanta `SesionYaCancelada` o `SesionYaIniciada` (ya `EnCurso` o `Finalizada`) sin mutar.
        Una sesión iniciada se termina con `finalizar()`.
        """
        _validar_para_cancelar(self)
        self.estado = EstadoSesionEnVivo.CANCELADA

    def finalizar(self) -> None:
        """Da por terminada la sesión: pasa a `Finalizada` (`US-6.2.7`).

        Levanta `SesionYaFinalizada` o `SesionNoEnCurso` sin mutar. Se puede finalizar antes de
        agotar el set de preguntas y en cualquier etapa de la pregunta actual (INV-AEV-03
        modificado por `US-ADJ-58`): una pregunta abierta queda sin cerrar, sin histograma, y las
        respuestas que ya recibió cuentan para el ranking.
        """
        _validar_para_finalizar(self)
        self.estado = EstadoSesionEnVivo.FINALIZADA

    def validar_para_responder(self, pregunta_id: UUID, ahora: datetime) -> float:
        """Valida que `pregunta_id` admita una respuesta y devuelve el tiempo de respuesta (s).

        No muta `self`. El tiempo se mide en el servidor desde `opciones_mostradas_en`
        (`US-6.2.4`); el rechazo por `TiempoAgotado` (INV-AEV-08) no depende de que el Docente
        haya cerrado la pregunta.
        """
        return _validar_para_responder(self, pregunta_id, ahora)

    def pregunta_actual(self) -> PreguntaAsignada:
        """Devuelve la pregunta actual — solo válido con la sesión ya iniciada."""
        if self.pregunta_actual_indice is None:
            raise ValueError("La sesión todavía no tiene una pregunta actual.")
        return self.preguntas[self.pregunta_actual_indice]


def _validar_para_mostrar_opciones(sesion: ActividadEvaluativaEnVivo) -> None:
    """Rechaza si la sesión no está `EnCurso` o si las opciones ya se mostraron (INV-AEV-09).

    Vive fuera de la clase para no sumar `SesionNoEnCurso`/`OpcionesYaMostradas` a su acoplamiento
    (CBO, `feedback_cbo_pre_push_no_fase7`).
    """
    if sesion.estado != EstadoSesionEnVivo.EN_CURSO:
        raise SesionNoEnCurso(sesion.id)
    if sesion.opciones_mostradas:
        raise OpcionesYaMostradas(sesion.id)


def _validar_para_cerrar(sesion: ActividadEvaluativaEnVivo) -> None:
    """Rechaza el cierre si la sesión no está `EnCurso`, sin opciones mostradas o ya cerrada."""
    if sesion.estado != EstadoSesionEnVivo.EN_CURSO:
        raise SesionNoEnCurso(sesion.id)
    if not sesion.opciones_mostradas:
        raise OpcionesNoMostradasTodavia(sesion.id)
    if sesion.pregunta_actual_cerrada:
        raise PreguntaYaCerrada(sesion.id)


def _validar_para_avanzar(sesion: ActividadEvaluativaEnVivo) -> None:
    """Rechaza avanzar si no está `EnCurso`, la pregunta no se cerró o era la última."""
    if sesion.estado != EstadoSesionEnVivo.EN_CURSO:
        raise SesionNoEnCurso(sesion.id)
    if not sesion.pregunta_actual_cerrada:
        raise PreguntaActualNoCerrada(sesion.id)
    if (sesion.pregunta_actual_indice or 0) + 1 >= len(sesion.preguntas):
        raise NoQuedanPreguntas(sesion.id)


def _validar_para_finalizar(sesion: ActividadEvaluativaEnVivo) -> None:
    """Rechaza finalizar si ya estaba `Finalizada` o si no está `EnCurso` (EnEspera, Cancelada)."""
    if sesion.estado == EstadoSesionEnVivo.FINALIZADA:
        raise SesionYaFinalizada(sesion.id)
    if sesion.estado != EstadoSesionEnVivo.EN_CURSO:
        raise SesionNoEnCurso(sesion.id)


def _rechazar_si_cancelada(sesion: ActividadEvaluativaEnVivo) -> None:
    """Levanta `SesionYaCancelada` si la sesión fue cancelada (`US-ADJ-58`)."""
    if sesion.estado == EstadoSesionEnVivo.CANCELADA:
        raise SesionYaCancelada(sesion.id)


def _validar_para_cancelar(sesion: ActividadEvaluativaEnVivo) -> None:
    """Rechaza cancelar si ya estaba `Cancelada` o si ya no está `EnEspera` (INV-AEV-10)."""
    _rechazar_si_cancelada(sesion)
    if sesion.estado != EstadoSesionEnVivo.EN_ESPERA:
        raise SesionYaIniciada(sesion.id)


def _pasar_a_pregunta(sesion: ActividadEvaluativaEnVivo, indice: int) -> None:
    """Deja la sesión en el estado inicial de la pregunta `indice`: solo el enunciado."""
    sesion.pregunta_actual_indice = indice
    sesion.opciones_mostradas = False
    sesion.opciones_mostradas_en = None
    sesion.pregunta_actual_cerrada = False


def _validar_para_responder(
    sesion: ActividadEvaluativaEnVivo, pregunta_id: UUID, ahora: datetime
) -> float:
    """Aplica las reglas de `validar_para_responder` — fuera de la clase por CBO."""
    if sesion.estado != EstadoSesionEnVivo.EN_CURSO:
        raise SesionNoEnCurso(sesion.id)
    if sesion.pregunta_actual().pregunta_id != pregunta_id:
        raise PreguntaNoActual(sesion.id, pregunta_id)
    if sesion.pregunta_actual_cerrada:
        raise PreguntaYaCerrada(sesion.id)
    if not sesion.opciones_mostradas or sesion.opciones_mostradas_en is None:
        raise OpcionesNoMostradasTodavia(sesion.id)
    tiempo = (ahora - sesion.opciones_mostradas_en).total_seconds()
    if tiempo > sesion.tiempo_limite_por_pregunta_segundos:
        raise TiempoAgotado(sesion.id, tiempo)
    return tiempo


_ESTADO_POR_EVENTO = {
    "SesionEnVivoIniciada": EstadoSesionEnVivo.EN_CURSO,
    "SesionEnVivoFinalizada": EstadoSesionEnVivo.FINALIZADA,
    "SesionEnVivoCancelada": EstadoSesionEnVivo.CANCELADA,
}


def _aplicar_evento(sesion: ActividadEvaluativaEnVivo, evento: EventoAlmacenado) -> None:
    """Aplica un evento posterior a `SesionEnVivoCreada`; los `event_type` sin efecto se ignoran."""
    nuevo_estado = _ESTADO_POR_EVENTO.get(evento.event_type)
    if nuevo_estado is not None:
        sesion.estado = nuevo_estado
    if evento.event_type == "SesionEnVivoIniciada":
        # Default 0: la primera pregunta — mantiene compatibles los streams sembrados con
        # payload mínimo en los tests de `US-6.1.3`.
        sesion.pregunta_actual_indice = evento.payload.get("pregunta_actual_indice", 0)
    if evento.event_type == "OpcionesEnVivoMostradas":
        sesion.opciones_mostradas = True
        sesion.opciones_mostradas_en = datetime.fromisoformat(evento.payload["ocurrido_en"])
    if evento.event_type == "PreguntaEnVivoCerrada":
        sesion.pregunta_actual_cerrada = True
    if evento.event_type == "SiguientePreguntaPresentada":
        _pasar_a_pregunta(sesion, evento.payload["pregunta_actual_indice"])
