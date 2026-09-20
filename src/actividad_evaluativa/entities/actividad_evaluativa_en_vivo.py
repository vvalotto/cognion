"""Aggregate `ActividadEvaluativaEnVivo` (`BC-actividad-evaluativa-modelo.md` §14)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.errors import (
    OpcionesYaMostradas,
    SesionNoEnCurso,
    SesionYaFinalizada,
    SesionYaIniciada,
    TiempoLimiteInvalido,
)
from src.actividad_evaluativa.entities.evaluacion import PreguntaAsignada
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado


class EstadoSesionEnVivo(StrEnum):
    """Estados posibles de una sesión en vivo."""

    EN_ESPERA = "EnEspera"
    EN_CURSO = "EnCurso"
    FINALIZADA = "Finalizada"


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
        """Valida que la sesión admita nuevas uniones — solo se rechaza si está `Finalizada`.

        Una sesión `EnEspera` o ya `EnCurso` admite la unión (unión tardía, `US-6.1.3`). No muta
        `self` (mismo criterio que `Evaluacion.validar_para_suspender`).
        """
        if self.estado == EstadoSesionEnVivo.FINALIZADA:
            raise SesionYaFinalizada(self.id)

    def iniciar(self) -> None:
        """Pasa la sesión de `EnEspera` a `EnCurso` con la primera pregunta como actual.

        Levanta `SesionYaIniciada` si ya no está `EnEspera` (`EnCurso` o `Finalizada`) — no hay
        caso de uso de "reiniciar" una sesión ya arrancada. No exige participantes: el dominio no
        impone un mínimo (`US-6.1.4`).
        """
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


_ESTADO_POR_EVENTO = {
    "SesionEnVivoIniciada": EstadoSesionEnVivo.EN_CURSO,
    "SesionEnVivoFinalizada": EstadoSesionEnVivo.FINALIZADA,
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
