"""Comando operativo: carga materias y preguntas desde archivos JSON o Markdown (`US-8.7.1`).

Uso:

    python -m src.banco_preguntas.frameworks.cli.cargar_datos_iniciales <ruta> [opciones]

Opciones: `--materia NOMBRE` y `--simular` (valida sin escribir).

`<ruta>` es un archivo `.json` o `.md`, o una carpeta con `*.json` y `* - Cuestionario.md`.
`--materia` es obligatorio para los `.md`, que no traen la materia. Es idempotente: omite las
preguntas cuyo texto ya está activo en el banco. Códigos de salida: 0 todo bien, 1 algún archivo
falló o la entrada es inválida.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from src.banco_preguntas.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)
from src.banco_preguntas.interface_adapters.gateways.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.banco_preguntas.interface_adapters.gateways.pregunta_repository import (
    SQLAlchemyPreguntaRepository,
)
from src.banco_preguntas.interface_adapters.importadores.json_importador import leer_json
from src.banco_preguntas.interface_adapters.importadores.markdown_importador import (
    SUFIJO_CUESTIONARIO,
    leer_cuestionario,
)
from src.banco_preguntas.use_cases.cargar_datos_iniciales import (
    ArchivoDeDatos,
    ArchivoInvalido,
    CargarDatosInicialesUseCase,
)
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)
from src.banco_preguntas.use_cases.cargar_pregunta_verdadero_falso import (
    CargarPreguntaVerdaderoFalsoUseCase,
)
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase
from src.shared.frameworks.db import SessionLocal

SALIDA_OK = 0
SALIDA_ERROR = 1


def _parsear(argumentos: Sequence[str]) -> argparse.Namespace:
    """Interpreta los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="cargar_datos_iniciales", description=__doc__.split("\n")[0]
    )
    parser.add_argument("ruta", type=Path, help="archivo .json/.md o carpeta")
    parser.add_argument("--materia", help="materia destino (obligatoria para archivos .md)")
    parser.add_argument("--simular", action="store_true", help="validar sin escribir en la base")
    return parser.parse_args(argumentos)


def _descubrir(ruta: Path) -> list[Path]:
    """Lista los archivos a procesar: el archivo dado o los de la carpeta, en orden alfabético."""
    if ruta.is_file():
        return [ruta]
    candidatos = [
        archivo
        for archivo in ruta.iterdir()
        if archivo.suffix == ".json" or archivo.name.endswith(SUFIJO_CUESTIONARIO)
    ]
    return sorted(candidatos, key=lambda archivo: archivo.name)


def _leer(archivo: Path, materia: str | None) -> ArchivoDeDatos:
    """Lee el archivo con el importador de su formato."""
    if archivo.suffix == ".json":
        return leer_json(archivo)
    if archivo.suffix == ".md" and materia:
        return leer_cuestionario(archivo, materia)
    raise ArchivoInvalido("formato no soportado (usá .json, o .md con --materia)")


def _archivos_a_procesar(
    opciones: argparse.Namespace, imprimir: Callable[[str], None]
) -> list[Path]:
    """Valida la entrada y devuelve los archivos a procesar; lista vacía si hay que abortar."""
    if not opciones.ruta.exists():
        imprimir(f"No existe la ruta: {opciones.ruta}")
        return []
    archivos = _descubrir(opciones.ruta)
    if not archivos:
        imprimir(f"No hay archivos .json ni '{SUFIJO_CUESTIONARIO}' en {opciones.ruta}")
    elif any(a.suffix == ".md" for a in archivos) and not opciones.materia:
        imprimir("Los cuestionarios .md no traen la materia: indicala con --materia.")
        return []
    return archivos


async def _procesar(
    archivo: Path,
    opciones: argparse.Namespace,
    caso_de_uso: CargarDatosInicialesUseCase,
    imprimir: Callable[[str], None],
) -> bool:
    """Carga un archivo e imprime su resumen; devuelve `False` si el archivo era inválido."""
    prefijo = "[simulación] " if opciones.simular else ""
    try:
        datos = _leer(archivo, opciones.materia)
        resultado = await caso_de_uso.execute(datos, simular=opciones.simular)
    except ArchivoInvalido as error:
        imprimir(f"{prefijo}{archivo.name}: ERROR — {error}. No se cargó nada de este archivo.")
        return False
    nueva = " (nueva)" if resultado.materia_creada else ""
    imprimir(
        f"{prefijo}{archivo.name}: materia '{resultado.materia}'{nueva} — "
        f"{resultado.cargadas} cargadas, {resultado.omitidas} omitidas por repetidas, "
        "0 con error."
    )
    return True


async def ejecutar(
    argumentos: Sequence[str],
    caso_de_uso: CargarDatosInicialesUseCase,
    imprimir: Callable[[str], None] = print,
) -> int:
    """Procesa los archivos indicados y devuelve el código de salida del proceso."""
    opciones = _parsear(argumentos)
    archivos = _archivos_a_procesar(opciones, imprimir)
    if not archivos:
        return SALIDA_ERROR

    fallidos = 0
    for archivo in archivos:
        try:
            if not await _procesar(archivo, opciones, caso_de_uso, imprimir):
                fallidos += 1
        except (SQLAlchemyError, OSError) as error:
            imprimir(f"No se pudo acceder a la base de datos: {type(error).__name__}.")
            return SALIDA_ERROR
    imprimir(f"Archivos: {len(archivos) - fallidos} bien, {fallidos} con error.")
    return SALIDA_ERROR if fallidos else SALIDA_OK


async def _main(argumentos: Sequence[str]) -> int:  # pragma: no cover - cableado real
    """Arma las dependencias reales y ejecuta el comando."""
    async with SessionLocal() as session:
        materias = SQLAlchemyMateriaRepository(session)
        bancos = SQLAlchemyBancoRepository(session)
        preguntas = SQLAlchemyPreguntaRepository(session)
        comisiones = ComisionConsultaPortInProcess(session)
        caso_de_uso = CargarDatosInicialesUseCase(
            materias,
            bancos,
            preguntas,
            CrearMateriaUseCase(materias, bancos),
            CargarPreguntaOpcionMultipleUseCase(bancos, preguntas, comisiones),
            CargarPreguntaVerdaderoFalsoUseCase(bancos, preguntas, comisiones),
        )
        return await ejecutar(argumentos, caso_de_uso)


def main() -> None:  # pragma: no cover - punto de entrada
    """Punto de entrada del comando."""
    raise SystemExit(asyncio.run(_main(sys.argv[1:])))


if __name__ == "__main__":  # pragma: no cover
    main()
