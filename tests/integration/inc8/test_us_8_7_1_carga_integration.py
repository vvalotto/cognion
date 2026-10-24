"""Carga de datos iniciales contra PostgreSQL real, con el cableado verdadero del comando (US-8.7.1).

Requiere una base descartable (`DATABASE_URL` inline): estos tests vacían las tablas del Banco.
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import text

from src.banco_preguntas.frameworks.cli.cargar_datos_iniciales import _main
from src.shared.frameworks.db import SessionLocal
from tests.unit.inc8._datos_iniciales import CUESTIONARIO, escribir

PREGUNTAS = [
    {
        "tipo": "opcion_multiple",
        "texto": "¿Cuál es un control de versiones?",
        "unidad_tematica": "Configuración",
        "tema": "Herramientas",
        "dificultad": "bajo",
        "importancia": "medio",
        "opciones": [
            {"texto": "Git", "es_correcta": True},
            {"texto": "Docker", "es_correcta": False},
        ],
    },
    {
        "tipo": "verdadero_falso",
        "texto": "Un commit atómico agrupa cambios no relacionados.",
        "unidad_tematica": "Configuración",
        "tema": "Buenas prácticas",
        "dificultad": "bajo",
        "importancia": "medio",
        "respuesta_correcta": False,
    },
]


async def _contar(tabla: str) -> int:
    async with SessionLocal() as session:
        return int((await session.execute(text(f"SELECT count(*) FROM {tabla}"))).scalar_one())


def _archivo(carpeta: Path, materia: str = "Materia de prueba") -> Path:
    return escribir(carpeta, "a.json", json.dumps({"materia": materia, "preguntas": PREGUNTAS}))


async def test_carga_json_y_segunda_ejecucion_idempotente(tmp_path: Path) -> None:
    """Escenarios 1 y 2: crea materia, banco y preguntas; repetir no duplica."""
    ruta = _archivo(tmp_path)
    assert await _main([str(ruta)]) == 0
    assert (
        await _contar("materia"),
        await _contar("banco"),
        await _contar("pregunta_plantilla"),
    ) == (1, 1, 2)
    assert await _main([str(ruta)]) == 0
    assert await _contar("pregunta_plantilla") == 2


async def test_simular_no_modifica_la_base(tmp_path: Path) -> None:
    """Escenario 5."""
    assert await _main([str(_archivo(tmp_path)), "--simular"]) == 0
    assert (await _contar("materia"), await _contar("pregunta_plantilla")) == (0, 0)


async def test_cuestionarios_markdown_con_metadatos_derivados(tmp_path: Path) -> None:
    """Escenarios 8 y 9: carpeta de cuestionarios, ignorando lo que no lo es."""
    escribir(tmp_path, "Riesgos - Cuestionario.md", CUESTIONARIO)
    escribir(tmp_path, "bitacora.md", "# nada")
    assert await _main([str(tmp_path), "--materia", "Gestión de Proyectos"]) == 0
    async with SessionLocal() as session:
        filas = (
            await session.execute(
                text(
                    "SELECT unidad_tematica, tema, dificultad, importancia "
                    "FROM pregunta_plantilla ORDER BY dificultad"
                )
            )
        ).all()
    assert [tuple(f) for f in filas] == [
        ("09 – Incertidumbre", "Riesgos", "alto", "alto"),
        ("09 – Incertidumbre", "Riesgos", "bajo", "bajo"),
    ]
    assert await _main([str(tmp_path), "--materia", "Gestión de Proyectos"]) == 0
    assert await _contar("pregunta_plantilla") == 2


async def test_un_archivo_invalido_no_deja_nada_cargado(tmp_path: Path) -> None:
    """Escenario 3: una pregunta sin opción correcta anula el archivo completo."""
    invalida = {**PREGUNTAS[0], "opciones": [{"texto": "a", "es_correcta": False}] * 2}
    ruta = escribir(
        tmp_path, "a.json", json.dumps({"materia": "M", "preguntas": [PREGUNTAS[1], invalida]})
    )
    assert await _main([str(ruta)]) == 1
    assert (await _contar("materia"), await _contar("pregunta_plantilla")) == (0, 0)


async def test_reutiliza_una_materia_creada_antes(tmp_path: Path) -> None:
    """Escenario 6: la materia ya existente se reutiliza y se agregan las preguntas nuevas."""
    primera = escribir(tmp_path, "a.json", json.dumps({"materia": "M", "preguntas": PREGUNTAS[:1]}))
    segunda = escribir(tmp_path, "b.json", json.dumps({"materia": "M", "preguntas": PREGUNTAS}))
    assert await _main([str(primera)]) == 0 and await _main([str(segunda)]) == 0
    assert (
        await _contar("materia"),
        await _contar("banco"),
        await _contar("pregunta_plantilla"),
    ) == (1, 1, 2)
