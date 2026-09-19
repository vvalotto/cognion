"""Aggregate `ActividadEvaluativaEnVivo` (`BC-actividad-evaluativa-modelo.md` §14)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.errors import SesionYaFinalizada, TiempoLimiteInvalido
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
        se aplican según su `event_type`; por ahora solo modifican `estado` — los demás campos
        de cada transición los define la US que emite el evento (`US-6.1.4` y la Iteración 2).
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


_ESTADO_POR_EVENTO = {
    "SesionEnVivoIniciada": EstadoSesionEnVivo.EN_CURSO,
    "SesionEnVivoFinalizada": EstadoSesionEnVivo.FINALIZADA,
}


def _aplicar_evento(sesion: ActividadEvaluativaEnVivo, evento: EventoAlmacenado) -> None:
    """Aplica un evento posterior a `SesionEnVivoCreada`; los `event_type` sin efecto se ignoran."""
    nuevo_estado = _ESTADO_POR_EVENTO.get(evento.event_type)
    if nuevo_estado is not None:
        sesion.estado = nuevo_estado
