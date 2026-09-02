"""Fakes en memoria de los puertos del BC Actividad Evaluativa, para tests unitarios."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.actividad_evaluativa.entities.errors import ConcurrenciaOptimistaError
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoAlmacenado,
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.materia_consulta_port import (
    MateriaConsultaPort,
    MateriaDTO,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import (
    ContenidoPregunta,
    DetalleCorreccionPregunta,
    PreguntaConsultaPort,
)


class FakeEstudianteConsultaPort(EstudianteConsultaPort):
    """Consulta de estudiantes en memoria — devuelve lo que se le precarga en `estudiantes`."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria."""
        self.estudiantes: set[UUID] = set()

    async def existe(self, estudiante_id: UUID) -> bool:
        """Indica si el estudiante fue precargado como válido."""
        return estudiante_id in self.estudiantes


class FakeMateriaConsultaPort(MateriaConsultaPort):
    """Consulta de materias en memoria — devuelve lo que se le precarga en `materias`."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria."""
        self.materias: dict[UUID, MateriaDTO] = {}

    async def obtener(self, materia_id: UUID) -> MateriaDTO | None:
        """Busca una materia por id, o `None` si no existe."""
        return self.materias.get(materia_id)


class FakePreguntaConsultaPort(PreguntaConsultaPort):
    """Conteo de preguntas activas en memoria — devuelve lo que se le precarga en `conteos`."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria."""
        self.conteos: dict[UUID, int] = {}
        self.ids_activas: dict[UUID, list[UUID]] = {}
        self.correcciones: dict[UUID, bool] = {}
        self.detalles: dict[UUID, DetalleCorreccionPregunta] = {}
        self.contenidos: dict[UUID, ContenidoPregunta] = {}

    async def contar_activas_por_materia(self, materia_id: UUID) -> int:
        """Devuelve el conteo precargado para la materia, o 0 si no se precargó."""
        return self.conteos.get(materia_id, 0)

    async def listar_ids_activas_por_materia(self, materia_id: UUID) -> list[UUID]:
        """Devuelve los ids precargados para la materia, o lista vacía si no se precargó."""
        return list(self.ids_activas.get(materia_id, []))

    async def evaluar_correccion(self, pregunta_id: UUID, contenido: dict) -> bool:
        """Devuelve la corrección precargada para la pregunta, o `False` si no se precargó."""
        return self.correcciones.get(pregunta_id, False)

    async def obtener_detalle_correccion(self, pregunta_id: UUID) -> DetalleCorreccionPregunta:
        """Devuelve el detalle precargado para la pregunta, o uno vacío si no se precargó."""
        return self.detalles.get(
            pregunta_id,
            DetalleCorreccionPregunta(texto="", contenido_correcto={}, opciones=None),
        )

    async def obtener_contenido(self, pregunta_id: UUID) -> ContenidoPregunta:
        """Devuelve el contenido precargado para la pregunta, o uno vacío si no se precargó."""
        return self.contenidos.get(pregunta_id, ContenidoPregunta(texto="", opciones=None))


class FakeEventStore(EventStorePort):
    """Event store en memoria — mismo contrato de append-only que `SQLAlchemyEventStore`."""

    def __init__(self) -> None:
        """Inicializa los streams en memoria."""
        self._streams: dict[tuple[str, UUID], list[EventoAlmacenado]] = {}

    async def append(
        self,
        aggregate_type: str,
        aggregate_id: UUID,
        expected_sequence_number: int,
        events: list[EventoParaAlmacenar],
    ) -> None:
        """Agrega `events` al stream si `expected_sequence_number` coincide con lo persistido."""
        clave = (aggregate_type, aggregate_id)
        stream = self._streams.setdefault(clave, [])
        if len(stream) != expected_sequence_number:
            raise ConcurrenciaOptimistaError(
                aggregate_type, aggregate_id, expected_sequence_number, len(stream)
            )

        for evento in events:
            stream.append(
                EventoAlmacenado(
                    sequence_number=len(stream) + 1,
                    event_type=evento.event_type,
                    payload=evento.payload,
                    occurred_at=datetime.now(UTC),
                )
            )

    async def load(self, aggregate_type: str, aggregate_id: UUID) -> list[EventoAlmacenado]:
        """Devuelve el stream completo, o lista vacía si no tiene eventos todavía."""
        return list(self._streams.get((aggregate_type, aggregate_id), []))
