"""Value Object que agrupa los metadatos de clasificación de una pregunta (RF-06)."""

from __future__ import annotations

from dataclasses import dataclass

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia


@dataclass(frozen=True)
class MetadatosPregunta:
    """Agrupa `texto`, `unidad_tematica`, `tema`, `dificultad` e `importancia`.

    Reemplaza el Data Clump que antes se repetía como 5 parámetros sueltos en `crear`/`editar`
    de ambos tipos de `PreguntaPlantilla` y en `PreguntasController` (`US-ADJ-17`). Sin
    validación propia — agrupador estructural, no invariante de dominio nueva.
    """

    texto: str
    unidad_tematica: str
    tema: str
    dificultad: Dificultad
    importancia: Importancia

    @classmethod
    def desde_valores_persistidos(
        cls,
        *,
        texto: str,
        unidad_tematica: str,
        tema: str,
        dificultad: str,
        importancia: str,
    ) -> MetadatosPregunta:
        """Construye desde los valores `str` crudos de la fila de BD.

        Centraliza la conversión a `Dificultad`/`Importancia` acá para que la gateway
        (`SQLAlchemyPreguntaRepository`) no necesite importar esos dos tipos directamente —
        evita sumarlos a su CBO (`US-ADJ-17`, ya en el umbral por la propia introducción de
        este Value Object).
        """
        return cls(
            texto=texto,
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=Dificultad(dificultad),
            importancia=Importancia(importancia),
        )
