"""Lee un cuestionario Markdown de opción múltiple (`US-8.7.1`).

Cada archivo es un tema: la unidad temática sale de su cabecera y el tema, del nombre del archivo.
La dificultad sale del `Nivel` de cada pregunta y la importancia se deriva de ella.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.use_cases.cargar_datos_iniciales import (
    ArchivoDeDatos,
    ArchivoInvalido,
    PreguntaACargar,
)

SUFIJO_CUESTIONARIO = " - Cuestionario.md"
_NIVELES = {
    "fácil": (Dificultad.BAJO, Importancia.BAJO),
    "medio": (Dificultad.MEDIO, Importancia.MEDIO),
    "difícil": (Dificultad.ALTO, Importancia.ALTO),
}
_UNIDAD = re.compile(r"\*\*Unidad temática:\*\*\s*(.+)")
_ROTULO = r"\*\*Pregunta\s+\d+\.\*\*"
_ENUNCIADO = re.compile(_ROTULO + r"\s*(.*?)(?=^\s*[a-f]\)\s)", re.S | re.M)
_OPCION = re.compile(r"^\s*([a-f])\)\s*(.+?)\s*$", re.M)
_CORRECTA = re.compile(r"Respuesta correcta:\s*([a-f])\)")
_NIVEL = re.compile(r"\(Nivel:\s*([^)]+)\)")


def _pregunta(bloque: str, unidad: str, tema: str) -> PreguntaACargar:
    """Convierte un bloque `**Pregunta N.** ...` en una pregunta de opción múltiple."""
    enunciado = _ENUNCIADO.search(bloque)
    correcta = _CORRECTA.search(bloque)
    nivel = _NIVEL.search(bloque)
    if enunciado is None or not enunciado.group(1).strip():
        raise ArchivoInvalido("no se encontró el enunciado o las opciones")
    if nivel is None:
        raise ArchivoInvalido("falta el Nivel")
    niveles = _NIVELES.get(nivel.group(1).strip().lower())
    if niveles is None:
        raise ArchivoInvalido(f"Nivel desconocido: {nivel.group(1).strip()}")
    opciones = _OPCION.findall(bloque.split("Respuesta correcta:")[0])
    letras = [letra for letra, _ in opciones]
    if correcta is None or correcta.group(1) not in letras:
        raise ArchivoInvalido("la respuesta correcta no está entre las opciones")

    dificultad, importancia = niveles
    metadatos = MetadatosPregunta(
        texto=" ".join(enunciado.group(1).split()),
        unidad_tematica=unidad,
        tema=tema,
        dificultad=dificultad,
        importancia=importancia,
    )
    return PreguntaACargar(
        metadatos=metadatos,
        opciones=tuple(Opcion(texto, letra == correcta.group(1)) for letra, texto in opciones),
    )


def leer_cuestionario(ruta: Path, materia: str) -> ArchivoDeDatos:
    """Lee un cuestionario Markdown; levanta `ArchivoInvalido` si el formato no sirve."""
    try:
        contenido = ruta.read_text(encoding="utf-8")
    except OSError as error:
        raise ArchivoInvalido(f"no se pudo leer el archivo: {error.strerror}") from error

    cabecera = _UNIDAD.search(contenido)
    if cabecera is None:
        raise ArchivoInvalido("falta la línea '**Unidad temática:**'")
    tema = ruta.name.removesuffix(SUFIJO_CUESTIONARIO).removesuffix(".md")
    bloques = [b for b in re.split(r"^\s*---\s*$", contenido, flags=re.M) if re.search(_ROTULO, b)]
    if not bloques:
        raise ArchivoInvalido("no se encontró ninguna pregunta")

    preguntas = []
    for posicion, bloque in enumerate(bloques, start=1):
        try:
            preguntas.append(_pregunta(bloque, cabecera.group(1).strip(), tema))
        except ArchivoInvalido as error:
            raise ArchivoInvalido(f"pregunta {posicion}: {error}") from error
    return ArchivoDeDatos(origen=ruta.name, materia=materia, preguntas=tuple(preguntas))
