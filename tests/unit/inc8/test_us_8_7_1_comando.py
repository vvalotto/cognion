"""Comando `cargar_datos_iniciales` (US-8.7.1), con el caso de uso sobre repositorios en memoria."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.exc import OperationalError

from src.banco_preguntas.frameworks.cli.cargar_datos_iniciales import ejecutar
from tests.unit.inc8._datos_iniciales import CUESTIONARIO, Entorno, escribir

PREGUNTA = {
    "tipo": "verdadero_falso",
    "texto": "¿Sí?",
    "unidad_tematica": "U",
    "tema": "T",
    "dificultad": "medio",
    "importancia": "medio",
    "respuesta_correcta": True,
}


def _json(carpeta: Path, nombre: str, materia: str, preguntas: list[dict[str, object]]) -> Path:
    return escribir(carpeta, nombre, json.dumps({"materia": materia, "preguntas": preguntas}))


async def _correr(entorno: Entorno, *argumentos: object) -> tuple[int, list[str]]:
    salida: list[str] = []
    codigo = await ejecutar([str(a) for a in argumentos], entorno.caso_de_uso, salida.append)
    return codigo, salida


async def test_archivo_json_valido(tmp_path: Path) -> None:
    """Escenario 1: carga y resumen."""
    entorno = Entorno()
    ruta = _json(tmp_path, "a.json", "Mat", [PREGUNTA])
    codigo, salida = await _correr(entorno, ruta)
    assert codigo == 0 and "1 cargadas, 0 omitidas" in salida[0] and "(nueva)" in salida[0]
    assert len(entorno.preguntas.preguntas) == 1


async def test_segunda_ejecucion_sale_en_cero_y_omite(tmp_path: Path) -> None:
    """Escenario 2."""
    entorno = Entorno()
    ruta = _json(tmp_path, "a.json", "Mat", [PREGUNTA])
    await _correr(entorno, ruta)
    codigo, salida = await _correr(entorno, ruta)
    assert codigo == 0 and "0 cargadas, 1 omitidas" in salida[0]


async def test_carpeta_con_un_archivo_invalido(tmp_path: Path) -> None:
    """Escenario 4: el válido se carga, el inválido no, y la salida es distinta de cero."""
    entorno = Entorno()
    _json(tmp_path, "a.json", "Buena", [PREGUNTA])
    _json(tmp_path, "b.json", "Mala", [{**PREGUNTA, "dificultad": "x"}])
    codigo, salida = await _correr(entorno, tmp_path)
    assert codigo == 1
    assert any("a.json" in linea and "1 cargadas" in linea for linea in salida)
    assert any("b.json: ERROR" in linea and "No se cargó nada" in linea for linea in salida)
    assert {m.nombre for m in entorno.materias.materias.values()} == {"Buena"}


async def test_simular_no_escribe(tmp_path: Path) -> None:
    """Escenario 5."""
    entorno = Entorno()
    codigo, salida = await _correr(entorno, _json(tmp_path, "a.json", "M", [PREGUNTA]), "--simular")
    assert codigo == 0 and salida[0].startswith("[simulación] ")
    assert not entorno.materias.materias


async def test_ruta_inexistente_y_carpeta_vacia(tmp_path: Path) -> None:
    """Escenario 7: mensajes claros, salida distinta de cero."""
    codigo, salida = await _correr(Entorno(), tmp_path / "nada")
    assert codigo == 1 and "No existe la ruta" in salida[0]
    codigo, salida = await _correr(Entorno(), tmp_path)
    assert codigo == 1 and "No hay archivos" in salida[0]


async def test_json_malformado(tmp_path: Path) -> None:
    """Escenario 7: JSON roto."""
    codigo, salida = await _correr(Entorno(), escribir(tmp_path, "a.json", "{"))
    assert codigo == 1 and "JSON inválido" in salida[0]


async def test_cuestionario_markdown_con_materia(tmp_path: Path) -> None:
    """Escenario 8."""
    entorno = Entorno()
    ruta = escribir(tmp_path, "Riesgos - Cuestionario.md", CUESTIONARIO)
    codigo, salida = await _correr(entorno, ruta, "--materia", "Gestión de Proyectos")
    assert codigo == 0 and "2 cargadas" in salida[0]


async def test_carpeta_ignora_los_markdown_que_no_son_cuestionarios(tmp_path: Path) -> None:
    """Escenario 9: solo se procesan `* - Cuestionario.md`."""
    entorno = Entorno()
    escribir(tmp_path, "A - Cuestionario.md", CUESTIONARIO)
    escribir(tmp_path, "bitacora.md", "# nada")
    escribir(tmp_path, "usuarios.md", "# nada")
    codigo, salida = await _correr(entorno, tmp_path, "--materia", "Mat")
    assert codigo == 0 and len(salida) == 2 and "A - Cuestionario.md" in salida[0]


async def test_markdown_sin_materia_falla_antes_de_leer(tmp_path: Path) -> None:
    """Escenario 10."""
    entorno = Entorno()
    ruta = escribir(tmp_path, "Riesgos - Cuestionario.md", CUESTIONARIO)
    codigo, salida = await _correr(entorno, ruta)
    assert codigo == 1 and "--materia" in salida[0] and not entorno.materias.materias


async def test_markdown_invalido(tmp_path: Path) -> None:
    """Escenario 11."""
    ruta = escribir(tmp_path, "Riesgos - Cuestionario.md", CUESTIONARIO.replace("Fácil", "Raro"))
    codigo, salida = await _correr(Entorno(), ruta, "--materia", "M")
    assert codigo == 1 and "pregunta 1" in salida[0]


async def test_archivo_con_extension_no_soportada(tmp_path: Path) -> None:
    """Un archivo que no es .json ni .md se rechaza con un mensaje."""
    codigo, salida = await _correr(Entorno(), escribir(tmp_path, "a.txt", "x"))
    assert codigo == 1 and "formato no soportado" in salida[0]


async def test_base_inaccesible_sin_traza(tmp_path: Path) -> None:
    """Escenario 7: si la base falla, mensaje claro y salida distinta de cero."""
    entorno = Entorno()

    async def fallar(*_: object, **__: object) -> None:
        raise OperationalError("select", {}, Exception("sin conexión"))

    entorno.materias.obtener_por_nombre = fallar  # type: ignore[method-assign]
    codigo, salida = await _correr(entorno, _json(tmp_path, "a.json", "M", [PREGUNTA]))
    assert codigo == 1 and "No se pudo acceder a la base" in salida[0]


def test_argumentos_invalidos_terminan_con_el_uso() -> None:
    """Sin ruta, argparse informa el uso y sale con 2."""
    import asyncio

    with pytest.raises(SystemExit) as salida:
        asyncio.run(ejecutar([], Entorno().caso_de_uso))
    assert salida.value.code == 2
