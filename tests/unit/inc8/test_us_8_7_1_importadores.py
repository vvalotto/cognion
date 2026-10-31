"""Importadores JSON y Markdown de la carga de datos iniciales (US-8.7.1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.interface_adapters.importadores.json_importador import leer_json
from src.banco_preguntas.interface_adapters.importadores.markdown_importador import (
    leer_cuestionario,
)
from src.banco_preguntas.use_cases.cargar_datos_iniciales import ArchivoInvalido
from tests.unit.inc8._datos_iniciales import CUESTIONARIO, escribir

OM = {
    "tipo": "opcion_multiple",
    "texto": "¿Cuál?",
    "unidad_tematica": "U",
    "tema": "T",
    "dificultad": "bajo",
    "importancia": "alto",
    "opciones": [{"texto": "x", "es_correcta": True}, {"texto": "y", "es_correcta": False}],
}
VF = {**{k: v for k, v in OM.items() if k != "opciones"}, "tipo": "verdadero_falso"}


def _json(carpeta: Path, contenido: object) -> Path:
    return escribir(carpeta, "a.json", json.dumps(contenido))


# ---------------------------------------------------------------- JSON


def test_json_valido_con_los_dos_tipos(tmp_path: Path) -> None:
    """Se leen opción múltiple y verdadero/falso con sus metadatos."""
    datos = leer_json(
        _json(
            tmp_path, {"materia": " Mat ", "preguntas": [OM, {**VF, "respuesta_correcta": False}]}
        )
    )
    assert datos.materia == "Mat" and len(datos.preguntas) == 2
    om, vf = datos.preguntas
    assert om.opciones is not None and om.metadatos.dificultad is Dificultad.BAJO
    assert om.metadatos.importancia is Importancia.ALTO
    assert vf.opciones is None and vf.respuesta_correcta is False


@pytest.mark.parametrize(
    ("contenido", "mensaje"),
    [
        ([], "objeto"),
        ({"preguntas": []}, "materia"),
        ({"materia": "M"}, "preguntas"),
        ({"materia": "M", "preguntas": [5]}, "pregunta 1: no es un objeto"),
        ({"materia": "M", "preguntas": [{**OM, "tipo": "otro"}]}, "tipo"),
        ({"materia": "M", "preguntas": [{**OM, "dificultad": "facil"}]}, "dificultad"),
        ({"materia": "M", "preguntas": [{**OM, "texto": ""}]}, "texto"),
        ({"materia": "M", "preguntas": [{**OM, "tema": "x" * 201}]}, "200"),
        ({"materia": "M", "preguntas": [{**OM, "opciones": "no"}]}, "opciones"),
        ({"materia": "M", "preguntas": [{**OM, "opciones": [{"texto": "a"}]}]}, "es_correcta"),
        ({"materia": "M", "preguntas": [VF]}, "respuesta_correcta"),
    ],
)
def test_json_invalido_indica_la_pregunta_y_el_motivo(
    tmp_path: Path, contenido: object, mensaje: str
) -> None:
    """Escenario 7: formato incorrecto, con mensaje claro."""
    with pytest.raises(ArchivoInvalido, match=mensaje):
        leer_json(_json(tmp_path, contenido))


def test_json_malformado_y_archivo_ausente(tmp_path: Path) -> None:
    """Escenario 7: JSON roto o ruta inexistente no producen trazas."""
    with pytest.raises(ArchivoInvalido, match="JSON inválido"):
        leer_json(escribir(tmp_path, "roto.json", "{"))
    with pytest.raises(ArchivoInvalido, match="no se pudo leer"):
        leer_json(tmp_path / "no_existe.json")


# ---------------------------------------------------------------- Markdown


def test_markdown_valido_deriva_unidad_tema_dificultad_e_importancia(tmp_path: Path) -> None:
    """Escenario 8: unidad de la cabecera, tema del nombre, importancia igual a la dificultad."""
    ruta = escribir(tmp_path, "Riesgos - Cuestionario.md", CUESTIONARIO)
    datos = leer_cuestionario(ruta, "Gestión de Proyectos")
    assert datos.materia == "Gestión de Proyectos" and len(datos.preguntas) == 2
    primera, segunda = datos.preguntas
    assert primera.metadatos.texto == "¿Qué es un riesgo?"
    assert primera.metadatos.unidad_tematica == "09 – Incertidumbre"
    assert primera.metadatos.tema == "Riesgos"
    assert (primera.metadatos.dificultad, primera.metadatos.importancia) == (
        Dificultad.BAJO,
        Importancia.BAJO,
    )
    assert (segunda.metadatos.dificultad, segunda.metadatos.importancia) == (
        Dificultad.ALTO,
        Importancia.ALTO,
    )
    assert primera.opciones is not None
    assert [o.es_correcta for o in primera.opciones] == [False, True, False, False]
    assert len(segunda.opciones or ()) == 3


@pytest.mark.parametrize(
    ("viejo", "nuevo", "mensaje"),
    [
        ("Nivel: Fácil", "Nivel: Imposible", "Nivel desconocido"),
        (" *(Nivel: Fácil)*", "", "falta el Nivel"),
        ("Respuesta correcta: b)", "Respuesta correcta: z)", "respuesta correcta"),
        ("**Unidad temática:** 09 – Incertidumbre", "", "Unidad temática"),
    ],
)
def test_markdown_invalido(tmp_path: Path, viejo: str, nuevo: str, mensaje: str) -> None:
    """Escenario 11: Nivel desconocido o ausente, respuesta inexistente, sin unidad."""
    ruta = escribir(tmp_path, "Riesgos - Cuestionario.md", CUESTIONARIO.replace(viejo, nuevo, 1))
    with pytest.raises(ArchivoInvalido, match=mensaje):
        leer_cuestionario(ruta, "M")


def test_markdown_sin_preguntas_y_archivo_ausente(tmp_path: Path) -> None:
    """Un archivo sin preguntas o inexistente se rechaza con un mensaje."""
    vacio = escribir(tmp_path, "X - Cuestionario.md", "**Unidad temática:** U\n")
    with pytest.raises(ArchivoInvalido, match="ninguna pregunta"):
        leer_cuestionario(vacio, "M")
    with pytest.raises(ArchivoInvalido, match="no se pudo leer"):
        leer_cuestionario(tmp_path / "no.md", "M")


def test_markdown_el_encabezado_con_preguntas_no_cuenta_como_pregunta(tmp_path: Path) -> None:
    """`**Preguntas:** 2` de la cabecera no es una pregunta."""
    ruta = escribir(tmp_path, "Riesgos - Cuestionario.md", CUESTIONARIO)
    assert len(leer_cuestionario(ruta, "M").preguntas) == 2
