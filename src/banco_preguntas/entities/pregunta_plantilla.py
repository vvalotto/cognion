"""Plantillas de pregunta del banco — un aggregate distinto por tipo concreto."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import (
    OpcionesInvalidas,
    PreguntaInactiva,
    PreguntaYaEliminada,
)
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion


def _validar_opciones(opciones: list[Opcion]) -> None:
    """Valida INV-BP-02 e INV-BP-03; levanta `OpcionesInvalidas` si no se cumplen."""
    if len(opciones) < 2:
        raise OpcionesInvalidas("Se requieren al menos 2 opciones.")

    correctas = [opcion for opcion in opciones if opcion.es_correcta]
    if len(correctas) != 1:
        raise OpcionesInvalidas("Debe haber exactamente una opción marcada como correcta.")


def _ahora() -> datetime:
    """Timestamp actual en UTC — usado como `fecha_creacion` por defecto."""
    return datetime.now(UTC)


@dataclass
class PreguntaPlantillaVerdaderoFalso:
    """Pregunta de Verdadero/Falso — respuesta correcta fija, sin lista de opciones."""

    id: UUID
    banco_id: UUID
    metadatos: MetadatosPregunta
    respuesta_correcta: bool
    activa: bool = field(default=True)
    fecha_creacion: datetime = field(default_factory=_ahora)

    @property
    def texto(self) -> str:
        """Delegado a `metadatos.texto` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.texto

    @property
    def unidad_tematica(self) -> str:
        """Delegado a `metadatos.unidad_tematica` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.unidad_tematica

    @property
    def tema(self) -> str:
        """Delegado a `metadatos.tema` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.tema

    @property
    def dificultad(self) -> Dificultad:
        """Delegado a `metadatos.dificultad` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.dificultad

    @property
    def importancia(self) -> Importancia:
        """Delegado a `metadatos.importancia` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.importancia

    @staticmethod
    def crear(
        banco_id: UUID,
        metadatos: MetadatosPregunta,
        respuesta_correcta: bool,
    ) -> PreguntaPlantillaVerdaderoFalso:
        """Crea la pregunta — sin invariantes de negocio adicionales sobre `respuesta_correcta`."""
        return PreguntaPlantillaVerdaderoFalso(
            id=uuid4(),
            banco_id=banco_id,
            metadatos=metadatos,
            respuesta_correcta=respuesta_correcta,
        )

    def editar(self, metadatos: MetadatosPregunta, respuesta_correcta: bool) -> None:
        """Edita la pregunta in-place — sin invariantes adicionales sobre `respuesta_correcta`.

        Levanta `PreguntaInactiva` si `activa = false`.
        """
        if not self.activa:
            raise PreguntaInactiva(self.id)

        self.metadatos = metadatos
        self.respuesta_correcta = respuesta_correcta

    def eliminar(self) -> None:
        """Da de baja lógica la pregunta (INV-BP-04) — `activa` pasa a `False`.

        Levanta `PreguntaYaEliminada` si `activa` ya era `False`.
        """
        if not self.activa:
            raise PreguntaYaEliminada(self.id)

        self.activa = False


@dataclass
class PreguntaPlantillaOpcionMultiple:
    """Pregunta de opción múltiple — mínimo 2 opciones, exactamente una correcta."""

    id: UUID
    banco_id: UUID
    metadatos: MetadatosPregunta
    opciones: list[Opcion]
    activa: bool = field(default=True)
    fecha_creacion: datetime = field(default_factory=_ahora)

    @property
    def texto(self) -> str:
        """Delegado a `metadatos.texto` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.texto

    @property
    def unidad_tematica(self) -> str:
        """Delegado a `metadatos.unidad_tematica` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.unidad_tematica

    @property
    def tema(self) -> str:
        """Delegado a `metadatos.tema` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.tema

    @property
    def dificultad(self) -> Dificultad:
        """Delegado a `metadatos.dificultad` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.dificultad

    @property
    def importancia(self) -> Importancia:
        """Delegado a `metadatos.importancia` — compatibilidad de lectura (`US-ADJ-17`)."""
        return self.metadatos.importancia

    @staticmethod
    def crear(
        banco_id: UUID,
        metadatos: MetadatosPregunta,
        opciones: list[Opcion],
    ) -> PreguntaPlantillaOpcionMultiple:
        """Crea la pregunta validando INV-BP-02/03; levanta `OpcionesInvalidas` si no se cumplen."""
        _validar_opciones(opciones)

        return PreguntaPlantillaOpcionMultiple(
            id=uuid4(),
            banco_id=banco_id,
            metadatos=metadatos,
            opciones=opciones,
        )

    def editar(self, metadatos: MetadatosPregunta, opciones: list[Opcion]) -> None:
        """Edita la pregunta in-place, reaplicando INV-BP-02/03.

        Levanta `PreguntaInactiva` si `activa = false`, `OpcionesInvalidas` si las opciones
        editadas violan INV-BP-02/03.
        """
        if not self.activa:
            raise PreguntaInactiva(self.id)

        _validar_opciones(opciones)

        self.metadatos = metadatos
        self.opciones = opciones

    def eliminar(self) -> None:
        """Da de baja lógica la pregunta (INV-BP-04) — `activa` pasa a `False`.

        Levanta `PreguntaYaEliminada` si `activa` ya era `False`.
        """
        if not self.activa:
            raise PreguntaYaEliminada(self.id)

        self.activa = False
