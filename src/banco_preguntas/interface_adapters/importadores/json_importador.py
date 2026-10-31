"""Lee un archivo JSON de materia y preguntas (`US-8.7.1`)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.use_cases.cargar_datos_iniciales import (
    ArchivoDeDatos,
    ArchivoInvalido,
    PreguntaACargar,
)

_LIMITES = {"texto": 2000, "unidad_tematica": 200, "tema": 200}


def _texto(dato: dict[str, Any], campo: str) -> str:
    """Devuelve un campo de texto obligatorio, respetando el largo máximo de la API."""
    valor = dato.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise ArchivoInvalido(f"falta '{campo}' o no es un texto")
    if len(valor) > _LIMITES.get(campo, 2000):
        raise ArchivoInvalido(f"'{campo}' supera los {_LIMITES[campo]} caracteres")
    return valor


def _nivel(dato: dict[str, Any], campo: str, tipo: type[Dificultad] | type[Importancia]) -> Any:
    """Convierte `dificultad` o `importancia` a su enum, aceptando `bajo`, `medio` o `alto`."""
    try:
        return tipo(str(dato.get(campo)))
    except ValueError as error:
        raise ArchivoInvalido(f"'{campo}' debe ser bajo, medio o alto") from error


def _opciones(dato: dict[str, Any]) -> tuple[Opcion, ...]:
    """Convierte la lista de opciones; la regla de una sola correcta la valida el dominio."""
    crudas = dato.get("opciones")
    if not isinstance(crudas, list):
        raise ArchivoInvalido("falta 'opciones' o no es una lista")
    opciones = []
    for cruda in crudas:
        if not isinstance(cruda, dict) or not isinstance(cruda.get("es_correcta"), bool):
            raise ArchivoInvalido(
                "cada opción necesita 'texto' y 'es_correcta' (verdadero o falso)"
            )
        opciones.append(Opcion(texto=_texto(cruda, "texto"), es_correcta=cruda["es_correcta"]))
    return tuple(opciones)


def _pregunta(dato: Any) -> PreguntaACargar:
    """Convierte una pregunta del JSON según su tipo."""
    if not isinstance(dato, dict):
        raise ArchivoInvalido("no es un objeto")
    metadatos = MetadatosPregunta(
        texto=_texto(dato, "texto"),
        unidad_tematica=_texto(dato, "unidad_tematica"),
        tema=_texto(dato, "tema"),
        dificultad=_nivel(dato, "dificultad", Dificultad),
        importancia=_nivel(dato, "importancia", Importancia),
    )
    tipo = dato.get("tipo")
    if tipo == "opcion_multiple":
        return PreguntaACargar(metadatos=metadatos, opciones=_opciones(dato))
    if tipo == "verdadero_falso":
        if not isinstance(dato.get("respuesta_correcta"), bool):
            raise ArchivoInvalido("'respuesta_correcta' debe ser verdadero o falso")
        return PreguntaACargar(metadatos=metadatos, respuesta_correcta=dato["respuesta_correcta"])
    raise ArchivoInvalido("'tipo' debe ser opcion_multiple o verdadero_falso")


def leer_json(ruta: Path) -> ArchivoDeDatos:
    """Lee y valida el formato de un archivo JSON; levanta `ArchivoInvalido` si no sirve."""
    try:
        contenido = json.loads(ruta.read_text(encoding="utf-8"))
    except OSError as error:
        raise ArchivoInvalido(f"no se pudo leer el archivo: {error.strerror}") from error
    except json.JSONDecodeError as error:
        raise ArchivoInvalido(f"JSON inválido en la línea {error.lineno}: {error.msg}") from error

    if not isinstance(contenido, dict):
        raise ArchivoInvalido("el archivo debe ser un objeto con 'materia' y 'preguntas'")
    materia = contenido.get("materia")
    crudas = contenido.get("preguntas")
    if not isinstance(materia, str) or not materia.strip() or not isinstance(crudas, list):
        raise ArchivoInvalido("el archivo debe tener 'materia' y una lista 'preguntas'")

    preguntas = []
    for posicion, cruda in enumerate(crudas, start=1):
        try:
            preguntas.append(_pregunta(cruda))
        except ArchivoInvalido as error:
            raise ArchivoInvalido(f"pregunta {posicion}: {error}") from error
    return ArchivoDeDatos(origen=ruta.name, materia=materia.strip(), preguntas=tuple(preguntas))
