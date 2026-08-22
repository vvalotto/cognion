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
    texto: str
    respuesta_correcta: bool
    unidad_tematica: str
    tema: str
    dificultad: Dificultad
    importancia: Importancia
    activa: bool = field(default=True)
    fecha_creacion: datetime = field(default_factory=_ahora)

    @staticmethod
    def crear(
        banco_id: UUID,
        texto: str,
        respuesta_correcta: bool,
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
    ) -> PreguntaPlantillaVerdaderoFalso:
        """Crea la pregunta — sin invariantes de negocio adicionales sobre `respuesta_correcta`."""
        return PreguntaPlantillaVerdaderoFalso(
            id=uuid4(),
            banco_id=banco_id,
            texto=texto,
            respuesta_correcta=respuesta_correcta,
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
        )

    def editar(
        self,
        texto: str,
        respuesta_correcta: bool,
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
    ) -> None:
        """Edita la pregunta in-place — sin invariantes adicionales sobre `respuesta_correcta`.

        Levanta `PreguntaInactiva` si `activa = false`.
        """
        if not self.activa:
            raise PreguntaInactiva(self.id)

        self.texto = texto
        self.respuesta_correcta = respuesta_correcta
        self.unidad_tematica = unidad_tematica
        self.tema = tema
        self.dificultad = dificultad
        self.importancia = importancia

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
    texto: str
    opciones: list[Opcion]
    unidad_tematica: str
    tema: str
    dificultad: Dificultad
    importancia: Importancia
    activa: bool = field(default=True)
    fecha_creacion: datetime = field(default_factory=_ahora)

    @staticmethod
    def crear(
        banco_id: UUID,
        texto: str,
        opciones: list[Opcion],
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
    ) -> PreguntaPlantillaOpcionMultiple:
        """Crea la pregunta validando INV-BP-02/03; levanta `OpcionesInvalidas` si no se cumplen."""
        _validar_opciones(opciones)

        return PreguntaPlantillaOpcionMultiple(
            id=uuid4(),
            banco_id=banco_id,
            texto=texto,
            opciones=opciones,
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
        )

    def editar(
        self,
        texto: str,
        opciones: list[Opcion],
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
    ) -> None:
        """Edita la pregunta in-place, reaplicando INV-BP-02/03.

        Levanta `PreguntaInactiva` si `activa = false`, `OpcionesInvalidas` si las opciones
        editadas violan INV-BP-02/03.
        """
        if not self.activa:
            raise PreguntaInactiva(self.id)

        _validar_opciones(opciones)

        self.texto = texto
        self.opciones = opciones
        self.unidad_tematica = unidad_tematica
        self.tema = tema
        self.dificultad = dificultad
        self.importancia = importancia

    def eliminar(self) -> None:
        """Da de baja lógica la pregunta (INV-BP-04) — `activa` pasa a `False`.

        Levanta `PreguntaYaEliminada` si `activa` ya era `False`.
        """
        if not self.activa:
            raise PreguntaYaEliminada(self.id)

        self.activa = False
