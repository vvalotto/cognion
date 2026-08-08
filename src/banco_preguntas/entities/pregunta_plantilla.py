"""Plantillas de pregunta del banco — un aggregate distinto por tipo concreto."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import OpcionesInvalidas
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion


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
        """Crea la pregunta validando INV-BP-02 e INV-BP-03; levanta `OpcionesInvalidas` si no se cumplen."""
        if len(opciones) < 2:
            raise OpcionesInvalidas("Se requieren al menos 2 opciones.")

        correctas = [opcion for opcion in opciones if opcion.es_correcta]
        if len(correctas) != 1:
            raise OpcionesInvalidas("Debe haber exactamente una opción marcada como correcta.")

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
