"""Utilidades compartidas por los ejecutables simulados (`gcloud` y `docker`) de US-8.6.4.

Se copia junto a ellos al PATH aislado del test; leen y escriben el estado y el registro de
llamadas en las rutas que indican las variables `FAKE_ESTADO` y `FAKE_LOG`.
"""

import json
import os


def cargar() -> dict:
    """Estado actual de la nube o del host simulado."""
    with open(os.environ["FAKE_ESTADO"], encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar(estado: dict) -> None:
    """Guarda el estado tras una creación o un borrado simulados."""
    with open(os.environ["FAKE_ESTADO"], "w", encoding="utf-8") as archivo:
        json.dump(estado, archivo)


def registrar(texto: str) -> None:
    """Agrega una línea al registro de llamadas que revisa el test."""
    with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as archivo:
        archivo.write(texto + "\n")
