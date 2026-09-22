"""Schemas Pydantic de request/response de la API del BC Actividad Evaluativa."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _a_utc_si_naive(dt: datetime) -> datetime:
    """Asigna UTC a un datetime sin tzinfo (`<input type="datetime-local">` no manda offset).

    Simplificación conocida (`US-ADJ-09`): el navegador no manda el timezone real del
    usuario, así que la hora local ingresada se trata como si fuera UTC — evita el
    `TypeError` de comparar datetimes naive/aware sin rediseñar el manejo de timezone de
    punta a punta.
    """
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


class CrearActividadRequest(BaseModel):
    """Body de la request de alta de actividad de período abierto."""

    materia_id: UUID
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int = Field(..., ge=1)
    cantidad_intentos_permitidos: int = Field(..., ge=1)
    titulo: str = ""
    comisiones_ids: list[UUID] = []
    """Vacío (default) = visible para todas las Comisiones de la Materia."""
    unidad_tematica: str | None = None
    """`None`/omitido (default) = las preguntas salen de cualquier unidad temática del banco,
    combinable con `tema` (AND)."""
    tema: str | None = None
    """`None`/omitido (default) = las preguntas salen de cualquier tema del banco."""

    _normalizar_fechas = field_validator("fecha_apertura", "fecha_cierre")(_a_utc_si_naive)


class ActividadResponse(BaseModel):
    """Representación de una `ActividadEvaluativaPeriodoAbierto` devuelta por la API."""

    id: UUID
    materia_id: UUID
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int
    cantidad_intentos_permitidos: int
    cerrada_manualmente: bool
    titulo: str
    comisiones_ids: list[UUID]
    unidad_tematica: str | None
    tema: str | None


class ActividadResumenResponse(BaseModel):
    """Resumen de una actividad para el listado por materia (`US-3.4.2`, RF-11).

    `estado` es puramente derivado (fecha actual + `cerrada_manualmente`) — no persiste un
    campo propio en el dominio.
    """

    id: UUID
    materia_id: UUID
    titulo: str
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int
    cantidad_intentos_permitidos: int
    estado: str
    cerrada_manualmente: bool
    cantidad_evaluaciones_activas: int
    cantidad_evaluaciones_finalizadas: int
    comisiones_ids: list[UUID]
    unidad_tematica: str | None
    tema: str | None


class ActividadVisibleResponse(BaseModel):
    """Actividad con el `Badge` de estado desde la perspectiva del Estudiante (`US-3.4.5`)."""

    id: UUID
    materia_id: UUID
    titulo: str
    fecha_apertura: datetime
    fecha_cierre: datetime
    estado: str
    evaluacion_id: UUID | None


class ModificarPeriodoDisponibilidadRequest(BaseModel):
    """Body de la request de modificación del período de disponibilidad (US-3.3.1, RF-11b)."""

    nueva_fecha_cierre: datetime

    _normalizar_fecha = field_validator("nueva_fecha_cierre")(_a_utc_si_naive)


class ModificarTituloRequest(BaseModel):
    """Body de la request de edición de título de una actividad (`US-ADJ-10`)."""

    nuevo_titulo: str


class IniciarEvaluacionRequest(BaseModel):
    """Body de la request de inicio de evaluación — `estudiante_id` sale del JWT, no del body."""

    actividad_id: UUID


class PreguntaAsignadaResponse(BaseModel):
    """Representación de una `PreguntaAsignada` devuelta por la API.

    `enunciado`/`opciones` (`US-3.4.6`) traen el contenido para renderizar la Card de
    `#est-rendir` sin exponer la respuesta correcta — `opciones` es `None` para preguntas de
    Verdadero/Falso.
    """

    pregunta_id: UUID
    orden: int
    enunciado: str
    opciones: list[str] | None


class RespuestaConfirmadaResponse(BaseModel):
    """Contenido de la `Respuesta` vigente de una pregunta ya respondida (`US-ADJ-12`).

    Expone la propia elección del Estudiante (para prellenar `#est-rendir` al revisitar una
    pregunta ya respondida) — nunca `es_correcta`, mismo criterio de "sin feedback inmediato"
    que `RespuestaResponse`.
    """

    pregunta_id: UUID
    contenido: dict[str, Any]


class EvaluacionResponse(BaseModel):
    """Representación de una `Evaluacion` devuelta por la API.

    `preguntas_respondidas` (`US-3.4.6`) trae los ids de `PreguntaAsignada` con al menos una
    `Respuesta` confirmada — insumo de los puntos de navegación (verde/azul/gris) de
    `#est-rendir`. `respuestas_confirmadas` (`US-ADJ-12`) trae el contenido de la respuesta
    vigente de cada una — insumo para prellenar la pantalla al revisitarla.
    """

    id: UUID
    actividad_id: UUID
    estudiante_id: UUID
    preguntas_asignadas: list[PreguntaAsignadaResponse]
    preguntas_respondidas: list[UUID]
    respuestas_confirmadas: list[RespuestaConfirmadaResponse]
    estado: str
    iniciada_en: datetime


class RegistrarRespuestaRequest(BaseModel):
    """Body de la request de confirmación de una respuesta."""

    pregunta_id: UUID
    contenido: dict[str, Any]


class RespuestaResponse(BaseModel):
    """Representación de una `Respuesta` devuelta por la API.

    Sin `es_correcta` ni `contenido` — el estudiante no debe poder inferir si acertó desde la
    respuesta HTTP (hot spot "sin feedback inmediato", `BC-actividad-evaluativa-modelo.md` §5).
    """

    id: UUID
    pregunta_id: UUID
    numero_intento: int
    confirmada_en: datetime


class DetallePreguntaRevisionResponse(BaseModel):
    """Representación de un `DetallePreguntaRevision` devuelto por la API (RF-13).

    `contenido_correcto` es `None` cuando el estudiante acertó — la API no expone la respuesta
    correcta salvo que haya fallado o no respondido.
    """

    pregunta_id: UUID
    orden: int
    texto: str
    respondida: bool
    contenido_propio: dict[str, Any] | None
    es_correcta: bool
    contenido_correcto: dict[str, Any] | None
    opciones: list[str] | None


class RevisionEvaluacionResponse(BaseModel):
    """Representación de una `RevisionEvaluacion` devuelta por la API (RF-13)."""

    evaluacion_id: UUID
    cantidad_preguntas: int
    cantidad_correctas: int
    cantidad_incorrectas: int
    detalle: list[DetallePreguntaRevisionResponse]


class CrearSesionEnVivoRequest(BaseModel):
    """Body de la request de alta de una sesión en vivo (`US-6.1.2`, RF-08).

    `tiempo_limite_por_pregunta_segundos` no lleva `gt=0` a propósito: INV-AEV-02 se valida en
    el aggregate (`TiempoLimiteInvalido`, 422), no con el 422 genérico de Pydantic.
    """

    comision_id: UUID
    cantidad_preguntas: int = Field(..., ge=1)
    tiempo_limite_por_pregunta_segundos: int
    unidad_tematica: str | None = None
    """`None`/omitido (default) = las preguntas salen de cualquier unidad temática del banco."""
    tema: str | None = None
    """`None`/omitido (default) = las preguntas salen de cualquier tema del banco."""


class SesionEnVivoResponse(BaseModel):
    """Resumen de una `ActividadEvaluativaEnVivo`, sin las preguntas (`US-6.1.2`/`US-6.1.4`)."""

    id: UUID
    comision_id: UUID
    materia_id: UUID
    unidad_tematica: str | None
    tema: str | None
    cantidad_preguntas: int
    tiempo_limite_por_pregunta_segundos: int
    estado: str
    pregunta_actual_indice: int | None = None
    """`None` con la sesión `EnEspera`; posición de la pregunta actual una vez iniciada."""


class ParticipacionEnVivoResponse(BaseModel):
    """Confirmación de unión de un Estudiante a una sesión en vivo (`US-6.1.3`)."""

    sesion_id: UUID
    estudiante_id: UUID
    unido_en: datetime


class ResponderEnVivoRequest(BaseModel):
    """Body de la respuesta a una pregunta en vivo — `estudiante_id` sale del JWT (`US-6.2.4`).

    `contenido` debe ser exactamente `{"opcion_indice": int}` (opción múltiple) o
    `{"valor": bool}` (Verdadero/Falso), el mismo shape que `Respuesta.contenido`.
    """

    pregunta_id: UUID
    contenido: dict[str, Any]

    @field_validator("contenido")
    @classmethod
    def _validar_contenido(cls, contenido: dict[str, Any]) -> dict[str, Any]:
        """Rechaza (422) cualquier `contenido` que no tenga uno de los dos shapes válidos."""
        es_opcion = contenido.keys() == {"opcion_indice"} and (
            isinstance(contenido["opcion_indice"], int)
            and not isinstance(contenido["opcion_indice"], bool)
        )
        es_valor = contenido.keys() == {"valor"} and isinstance(contenido["valor"], bool)
        if not (es_opcion or es_valor):
            raise ValueError('contenido debe ser {"opcion_indice": int} o {"valor": bool}')
        return contenido


class RespuestaEnVivoResponse(BaseModel):
    """Feedback personal de una respuesta en vivo — sin ranking (`US-6.2.4`)."""

    es_correcta: bool
    puntaje: int
    puntaje_acumulado: int


class RespuestaCorrectaResponse(BaseModel):
    """Respuesta correcta de la pregunta actual — solo con la pregunta cerrada (`US-6.2.8`)."""

    contenido: dict[str, Any]
    texto: str
    opciones: list[str] | None


class PreguntaActualResponse(BaseModel):
    """Pregunta actual de la sesión en vivo según lo que ya se reveló (`US-6.2.8`)."""

    pregunta_id: UUID
    enunciado: str
    tipo: str
    opciones: list[str] | None = None
    respuesta_correcta: RespuestaCorrectaResponse | None = None


class EstadoSesionEnVivoResponse(BaseModel):
    """Estado consultable de una sesión en vivo, para reconexión y sala de espera (`US-6.2.8`)."""

    estado: str
    comision_id: UUID
    cantidad_preguntas: int
    tiempo_limite_por_pregunta_segundos: int
    pregunta_actual_indice: int | None
    opciones_mostradas: bool
    opciones_mostradas_en: datetime | None
    pregunta_actual_cerrada: bool
    pregunta_actual: PreguntaActualResponse | None
    ya_respondio: bool | None = None
    """Solo para el Estudiante: si ya respondió la pregunta actual."""
    puntaje_acumulado: int | None = None
    """Solo para el Estudiante: su puntaje acumulado."""


class ParticipanteResponse(BaseModel):
    """Un Estudiante unido a la sesión, para la sala de espera del Docente (`US-6.2.8`)."""

    estudiante_id: UUID
    unido_en: datetime
    nombre: str
    """Resuelto contra Identidad — `"Estudiante sin nombre"` si la cuenta ya no existe
    (`US-6.3.1`)."""


class RankingItemResponse(BaseModel):
    """Una fila del ranking de la sesión en vivo (`US-6.2.8`)."""

    posicion: int
    estudiante_id: UUID
    puntaje_acumulado: int
    nombre: str
    """Resuelto contra Identidad — `"Estudiante sin nombre"` si la cuenta ya no existe
    (`US-6.3.1`)."""
