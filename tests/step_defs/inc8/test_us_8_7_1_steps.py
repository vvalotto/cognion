"""Steps BDD de US-8.7.1 — Carga de datos iniciales desde archivos JSON o Markdown.

Ejecutan el comando real (`_main`) contra PostgreSQL: requieren una base descartable inline.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.banco_preguntas.frameworks.cli.cargar_datos_iniciales import _main
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc8/US-8.7.1-carga-datos-iniciales.feature")

MATERIA_MD = "Gestión de Proyectos"


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    """Deja vacías las tablas del Banco antes y después de cada escenario."""
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def ctx(tmp_path: Path) -> dict[str, Any]:
    """Estado compartido entre los steps de un escenario."""
    return {"dir": tmp_path}


# ---------------------------------------------------------------- ayudas


def _contar(tabla: str) -> int:
    async def consulta() -> int:
        async with SessionLocal() as session:
            return int((await session.execute(text(f"SELECT count(*) FROM {tabla}"))).scalar_one())

    return run_async(consulta())


def _preguntas(cantidad: int, prefijo: str = "p") -> list[dict[str, Any]]:
    return [
        {
            "tipo": "opcion_multiple",
            "texto": f"{prefijo} {i}",
            "unidad_tematica": "U",
            "tema": "T",
            "dificultad": "medio",
            "importancia": "medio",
            "opciones": [{"texto": "a", "es_correcta": True}, {"texto": "b", "es_correcta": False}],
        }
        for i in range(1, cantidad + 1)
    ]


def _json(
    ctx: dict[str, Any], materia: str, preguntas: list[dict[str, Any]], nombre: str = "a.json"
) -> Path:
    ruta = ctx["dir"] / nombre
    ruta.write_text(json.dumps({"materia": materia, "preguntas": preguntas}), encoding="utf-8")
    return ruta


def _cuestionario(unidad: str = "09 – Incertidumbre", defecto: str | None = None) -> str:
    niveles = ["Fácil"] * 6 + ["Medio"] * 10 + ["Difícil"] * 4
    bloques = [f"# Cuestionario\n\n**Unidad temática:** {unidad}\n**Preguntas:** 20\n"]
    for i, nivel in enumerate(niveles, start=1):
        if defecto == "un Nivel desconocido" and i == 3:
            nivel = "Imposible"
        letra = (
            "z" if defecto == "una respuesta correcta que no está en opciones" and i == 3 else "b"
        )
        marca = "" if defecto == "una pregunta sin Nivel" and i == 3 else f" *(Nivel: {nivel})*"
        bloques.append(
            f"---\n\n**Pregunta {i}.** Enunciado {i} de {unidad}\n\na) Opción A\nb) Opción B\nc) Opción C\n\n"
            f"✅ **Respuesta correcta: {letra})** — Justificación.{marca}\n"
        )
    return "\n".join(bloques)


def _ejecutar(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str], *argumentos: str) -> None:
    ctx["codigo"] = run_async(_main(list(argumentos)))
    ctx["texto"] = capsys.readouterr().out


# ---------------------------------------------------------------- Given


@given(parsers.parse('una base sin la materia "{materia}"'))
def base_sin_materia(ctx: dict[str, Any], materia: str) -> None:
    ctx["materia"] = materia
    assert _contar("materia") == 0


@given("un archivo JSON con esa materia y 2 preguntas válidas")
def archivo_dos_preguntas(ctx: dict[str, Any]) -> None:
    ctx["ruta"] = _json(ctx, ctx["materia"], _preguntas(2))


@given("el archivo ya fue cargado una vez")
def archivo_ya_cargado(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    ctx["ruta"] = _json(ctx, "Ingeniería de Software", _preguntas(2))
    _ejecutar(ctx, capsys, str(ctx["ruta"]))
    assert ctx["codigo"] == 0 and _contar("pregunta_plantilla") == 2


@given("un archivo JSON con 3 preguntas y la segunda no tiene ninguna opción correcta")
def archivo_segunda_invalida(ctx: dict[str, Any]) -> None:
    preguntas = _preguntas(3)
    preguntas[1]["opciones"] = [
        {"texto": "a", "es_correcta": False},
        {"texto": "b", "es_correcta": False},
    ]
    ctx["ruta"] = _json(ctx, "Materia", preguntas)


@given("una carpeta con un archivo válido y un archivo con una pregunta inválida")
def carpeta_con_invalido(ctx: dict[str, Any]) -> None:
    _json(ctx, "Valida", _preguntas(2), "a_valida.json")
    invalida = _preguntas(2, "q")
    invalida[1]["dificultad"] = "inexistente"
    _json(ctx, "Invalida", invalida, "b_invalida.json")
    ctx["ruta"] = ctx["dir"]


@given("un archivo JSON válido")
def archivo_valido(ctx: dict[str, Any]) -> None:
    ctx["ruta"] = _json(ctx, "Materia", _preguntas(2))


@given(parsers.parse('una materia "{materia}" creada previamente con una pregunta'))
def materia_previa(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str], materia: str) -> None:
    ctx["materia"] = materia
    previa = _json(ctx, materia, _preguntas(1), "previa.json")
    _ejecutar(ctx, capsys, str(previa))
    assert (_contar("materia"), _contar("pregunta_plantilla")) == (1, 1)


@given("un archivo con JSON malformado")
def archivo_malformado(ctx: dict[str, Any]) -> None:
    ruta = ctx["dir"] / "roto.json"
    ruta.write_text("{", encoding="utf-8")
    ctx["ruta"] = ruta


@given("una ruta que no existe")
def ruta_inexistente(ctx: dict[str, Any]) -> None:
    ctx["ruta"] = ctx["dir"] / "no_existe.json"


@given(parsers.parse('un cuestionario Markdown "{nombre}" de 20 preguntas con unidad "{unidad}"'))
def cuestionario_de_20(ctx: dict[str, Any], nombre: str, unidad: str) -> None:
    ruta = ctx["dir"] / nombre
    ruta.write_text(_cuestionario(unidad), encoding="utf-8")
    ctx["ruta"] = ruta


@given("una carpeta con los 17 cuestionarios y otros archivos Markdown que no son cuestionarios")
def carpeta_con_17(ctx: dict[str, Any]) -> None:
    for i in range(1, 18):
        (ctx["dir"] / f"Tema {i:02d} - Cuestionario.md").write_text(
            _cuestionario(f"{i:02d} – Unidad"), encoding="utf-8"
        )
    (ctx["dir"] / "bitacora-docente.md").write_text("# bitácora", encoding="utf-8")
    (ctx["dir"] / "usuarios.md").write_text("# usuarios", encoding="utf-8")
    ctx["ruta"] = ctx["dir"]


@given("un cuestionario Markdown válido")
def cuestionario_valido(ctx: dict[str, Any]) -> None:
    ruta = ctx["dir"] / "Riesgos - Cuestionario.md"
    ruta.write_text(_cuestionario(), encoding="utf-8")
    ctx["ruta"] = ruta


@given(parsers.parse("un cuestionario Markdown con {defecto}"))
def cuestionario_con_defecto(ctx: dict[str, Any], defecto: str) -> None:
    ruta = ctx["dir"] / "Riesgos - Cuestionario.md"
    ruta.write_text(_cuestionario(defecto=defecto), encoding="utf-8")
    ctx["ruta"] = ruta


# ---------------------------------------------------------------- When


@when("se ejecuta el comando de carga sobre el archivo")
@when("se ejecuta el comando de carga sobre la carpeta")
def ejecutar_sobre_ruta(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    ctx["antes"] = (_contar("materia"), _contar("pregunta_plantilla"))
    _ejecutar(ctx, capsys, str(ctx["ruta"]))


@when("se ejecuta de nuevo el comando de carga sobre el mismo archivo")
def ejecutar_de_nuevo(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    ctx["antes"] = (_contar("materia"), _contar("pregunta_plantilla"))
    _ejecutar(ctx, capsys, str(ctx["ruta"]))


@when("se ejecuta el comando de carga con --simular")
def ejecutar_simulando(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    ctx["antes"] = (_contar("materia"), _contar("pregunta_plantilla"))
    _ejecutar(ctx, capsys, str(ctx["ruta"]), "--simular")


@when("se carga un archivo con esa materia y una pregunta nueva")
def cargar_con_pregunta_nueva(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    ruta = _json(ctx, ctx["materia"], _preguntas(2), "nueva.json")
    _ejecutar(ctx, capsys, str(ruta))


@when("se ejecuta el comando de carga")
def ejecutar_sin_mas(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    _ejecutar(ctx, capsys, str(ctx["ruta"]))


@when(parsers.parse('se ejecuta el comando de carga con --materia "{materia}"'))
def ejecutar_con_materia(
    ctx: dict[str, Any], capsys: pytest.CaptureFixture[str], materia: str
) -> None:
    ctx["materia"] = materia
    _ejecutar(ctx, capsys, str(ctx["ruta"]), "--materia", materia)


@when("se ejecuta el comando de carga sin --materia")
def ejecutar_sin_materia(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    _ejecutar(ctx, capsys, str(ctx["ruta"]))


# ---------------------------------------------------------------- Then


@then("existen la materia, su banco y las 2 preguntas")
def existen_materia_banco_preguntas() -> None:
    assert (_contar("materia"), _contar("banco"), _contar("pregunta_plantilla")) == (1, 1, 2)


@then("el resumen informa 2 cargadas, 0 omitidas y 0 con error")
def resumen_dos_cargadas(ctx: dict[str, Any]) -> None:
    assert "2 cargadas, 0 omitidas por repetidas, 0 con error" in ctx["texto"]


@then("la salida es 0")
def salida_cero(ctx: dict[str, Any]) -> None:
    assert ctx["codigo"] == 0


@then("la salida es distinta de cero")
def salida_distinta_de_cero(ctx: dict[str, Any]) -> None:
    assert ctx["codigo"] != 0


@then("no se agrega ninguna pregunta")
def no_se_agrega_nada(ctx: dict[str, Any]) -> None:
    assert (_contar("materia"), _contar("pregunta_plantilla")) == ctx["antes"]


@then("el resumen informa 0 cargadas y 2 omitidas por duplicadas")
def resumen_dos_omitidas(ctx: dict[str, Any]) -> None:
    assert "0 cargadas, 2 omitidas por repetidas" in ctx["texto"]


@then("no se carga ninguna pregunta de ese archivo")
def nada_cargado() -> None:
    assert (_contar("materia"), _contar("pregunta_plantilla")) == (0, 0)


@then("el mensaje indica la posición 2 y el motivo")
def mensaje_con_posicion(ctx: dict[str, Any]) -> None:
    assert "pregunta 2" in ctx["texto"] and "exactamente una opción" in ctx["texto"]


@then("el archivo válido se carga completo")
def valido_cargado() -> None:
    assert _contar("pregunta_plantilla") == 2


@then("el archivo inválido no carga nada")
def invalido_no_carga(ctx: dict[str, Any]) -> None:
    assert _contar("materia") == 1 and "b_invalida.json: ERROR" in ctx["texto"]


@then("se informa lo que se cargaría")
def se_informa_lo_que_cargaria(ctx: dict[str, Any]) -> None:
    assert "[simulación]" in ctx["texto"] and "2 cargadas" in ctx["texto"]


@then("la base queda idéntica")
def base_identica(ctx: dict[str, Any]) -> None:
    assert (_contar("materia"), _contar("pregunta_plantilla")) == ctx["antes"]


@then("se reutiliza la materia y su banco")
def materia_reutilizada() -> None:
    assert (_contar("materia"), _contar("banco")) == (1, 1)


@then("el banco queda con 2 preguntas")
def banco_con_dos() -> None:
    assert _contar("pregunta_plantilla") == 2


@then("se muestra un mensaje claro sin traza")
def mensaje_sin_traza(ctx: dict[str, Any]) -> None:
    assert ctx["texto"].strip() and "Traceback" not in ctx["texto"]


@then(parsers.parse('se cargan 20 preguntas en la materia "{materia}"'))
def veinte_en_la_materia(materia: str) -> None:
    async def consulta() -> tuple[int, str]:
        async with SessionLocal() as session:
            fila = (
                await session.execute(
                    text(
                        "SELECT count(p.id), m.nombre FROM pregunta_plantilla p "
                        "JOIN banco b ON b.id = p.banco_id JOIN materia m ON m.id = b.materia_id GROUP BY m.nombre"
                    )
                )
            ).one()
            return int(fila[0]), fila[1]

    assert run_async(consulta()) == (20, materia)


@then(parsers.parse('la unidad temática es "{unidad}" y el tema es "{tema}"'))
def unidad_y_tema(unidad: str, tema: str) -> None:
    async def consulta() -> set[tuple[str, str]]:
        async with SessionLocal() as session:
            filas = await session.execute(
                text("SELECT DISTINCT unidad_tematica, tema FROM pregunta_plantilla")
            )
            return {(f[0], f[1]) for f in filas}

    assert run_async(consulta()) == {(unidad, tema)}


@then('la dificultad "Fácil", "Medio" y "Difícil" queda como bajo, medio y alto')
def dificultades_mapeadas() -> None:
    async def consulta() -> dict[str, int]:
        async with SessionLocal() as session:
            filas = await session.execute(
                text("SELECT dificultad, count(*) FROM pregunta_plantilla GROUP BY dificultad")
            )
            return {f[0]: int(f[1]) for f in filas}

    assert run_async(consulta()) == {"bajo": 6, "medio": 10, "alto": 4}


@then("la importancia es la misma que la dificultad")
def importancia_igual() -> None:
    async def consulta() -> int:
        async with SessionLocal() as session:
            return int(
                (
                    await session.execute(
                        text(
                            "SELECT count(*) FROM pregunta_plantilla WHERE dificultad <> importancia"
                        )
                    )
                ).scalar_one()
            )

    assert run_async(consulta()) == 0


@then("se cargan 340 preguntas en una única materia")
def trescientas_cuarenta() -> None:
    assert (_contar("materia"), _contar("pregunta_plantilla")) == (1, 340)


@then('los archivos que no terminan en " - Cuestionario.md" se ignoran')
def se_ignoran_otros(ctx: dict[str, Any]) -> None:
    assert "bitacora-docente.md" not in ctx["texto"] and "usuarios.md" not in ctx["texto"]


@then("una segunda ejecución omite las 340")
def segunda_omite_340(ctx: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    _ejecutar(ctx, capsys, str(ctx["ruta"]), "--materia", ctx["materia"])
    assert ctx["codigo"] == 0 and _contar("pregunta_plantilla") == 340
    assert ctx["texto"].count("0 cargadas, 20 omitidas por repetidas") == 17


@then("se muestra un error claro antes de leer el archivo")
def error_antes_de_leer(ctx: dict[str, Any]) -> None:
    assert "--materia" in ctx["texto"] and _contar("materia") == 0


@then("ese archivo no carga nada y el mensaje indica la pregunta")
def archivo_no_carga_y_indica_pregunta(ctx: dict[str, Any]) -> None:
    assert _contar("pregunta_plantilla") == 0 and "pregunta 3" in ctx["texto"]
