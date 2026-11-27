"""`US-12.2.5` (`IM-05`): la restricción de un solo proceso está escrita y se hace cumplir.

El canal de la sesión en vivo guarda las conexiones en la memoria del proceso: con dos procesos, parte de los
alumnos no recibe los mensajes y no hay ningún error que lo avise. Agregar `--workers` «para que ande más rápido»
lo rompería en silencio; esta guarda lo detecta antes.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
ARCHIVOS_DE_DESPLIEGUE = [
    RAIZ / "Dockerfile",
    *sorted((RAIZ / "deploy").rglob("docker-compose*.y*ml")),
]
PATRON_WORKERS = re.compile(r"--workers[ =]+(\d+)")
PATRON_CONCURRENCIA = re.compile(r"WEB_CONCURRENCY\D{0,5}(\d+)")


def _procesos_declarados(texto: str) -> list[int]:
    return [int(n) for n in PATRON_WORKERS.findall(texto) + PATRON_CONCURRENCIA.findall(texto)]


@pytest.mark.parametrize("archivo", ARCHIVOS_DE_DESPLIEGUE, ids=lambda a: str(a.relative_to(RAIZ)))
def test_ningun_archivo_de_despliegue_pide_mas_de_un_proceso(archivo: Path) -> None:
    codigo = "\n".join(
        linea
        for linea in archivo.read_text(encoding="utf-8").splitlines()
        if not linea.lstrip().startswith("#")
    )

    assert all(n <= 1 for n in _procesos_declarados(codigo)), (
        f"{archivo.relative_to(RAIZ)} pide más de un proceso: la sesión en vivo solo funciona con uno "
        "(US-12.2.5, IM-05)"
    )


def test_hay_archivos_de_despliegue_que_revisar() -> None:
    assert len(ARCHIVOS_DE_DESPLIEGUE) >= 3


def test_detecta_workers_y_concurrencia_mayores_que_uno() -> None:
    assert _procesos_declarados(
        'CMD ["uvicorn", "x:y", "--workers", "2"]'.replace('", "', " ")
    ) == [2]
    assert _procesos_declarados("uvicorn x:y --workers=4") == [4]
    assert _procesos_declarados("WEB_CONCURRENCY=3") == [3]
    assert _procesos_declarados("environment:\n  WEB_CONCURRENCY: 2") == [2]
    assert _procesos_declarados("uvicorn x:y --workers 1") == [1]
    assert _procesos_declarados("uvicorn x:y") == []


def test_el_dockerfile_y_la_guia_advierten_de_la_restriccion() -> None:
    assert "UN SOLO PROCESO" in (RAIZ / "Dockerfile").read_text(encoding="utf-8")
    guia = (RAIZ / "docs" / "INSTALACION.md").read_text(encoding="utf-8")
    assert "un solo proceso" in guia.lower()
