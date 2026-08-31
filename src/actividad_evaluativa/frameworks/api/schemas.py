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


class EvaluacionResponse(BaseModel):
    """Representación de una `Evaluacion` devuelta por la API.

    `preguntas_respondidas` (`US-3.4.6`) trae los ids de `PreguntaAsignada` con al menos una
    `Respuesta` confirmada — insumo de los puntos de navegación (verde/azul/gris) de
    `#est-rendir`.
    """

    id: UUID
    actividad_id: UUID
    estudiante_id: UUID
    preguntas_asignadas: list[PreguntaAsignadaResponse]
    preguntas_respondidas: list[UUID]
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
