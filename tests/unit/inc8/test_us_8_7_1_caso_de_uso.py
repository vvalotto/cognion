"""Caso de uso de la carga de datos iniciales (US-8.7.1), con repositorios en memoria."""

from __future__ import annotations

import pytest

from src.banco_preguntas.use_cases.cargar_datos_iniciales import ArchivoInvalido
from tests.unit.inc8._datos_iniciales import (
    Entorno,
    archivo,
    opcion_multiple,
    verdadero_falso,
)


async def test_crea_la_materia_su_banco_y_las_preguntas() -> None:
    """Escenario 1: base sin la materia."""
    entorno = Entorno()
    resultado = await entorno.caso_de_uso.execute(
        archivo(opcion_multiple("a"), verdadero_falso("b"))
    )
    assert (resultado.materia_creada, resultado.cargadas, resultado.omitidas) == (True, 2, 0)
    assert len(entorno.materias.materias) == 1 and len(entorno.bancos.bancos) == 1
    assert len(entorno.preguntas.preguntas) == 2


async def test_la_segunda_ejecucion_no_duplica() -> None:
    """Escenario 2: idempotencia."""
    entorno = Entorno()
    datos = archivo(opcion_multiple("a"), verdadero_falso("b"))
    await entorno.caso_de_uso.execute(datos)
    resultado = await entorno.caso_de_uso.execute(datos)
    assert (resultado.materia_creada, resultado.cargadas, resultado.omitidas) == (False, 0, 2)
    assert len(entorno.preguntas.preguntas) == 2


async def test_una_pregunta_invalida_no_carga_nada_del_archivo() -> None:
    """Escenario 3: sin opción correcta, el archivo entero se rechaza con la posición."""
    entorno = Entorno()
    datos = archivo(opcion_multiple("a"), opcion_multiple("b", correctas=0), opcion_multiple("c"))
    with pytest.raises(ArchivoInvalido, match="pregunta 2"):
        await entorno.caso_de_uso.execute(datos)
    assert not entorno.preguntas.preguntas and not entorno.materias.materias


async def test_simular_no_escribe_nada() -> None:
    """Escenario 5: informa lo que cargaría y la base queda igual."""
    entorno = Entorno()
    resultado = await entorno.caso_de_uso.execute(archivo(opcion_multiple("a")), simular=True)
    assert resultado.cargadas == 1 and resultado.materia_creada
    assert not entorno.preguntas.preguntas and not entorno.materias.materias


async def test_simular_valida_igual() -> None:
    """Simular también rechaza un archivo inválido."""
    with pytest.raises(ArchivoInvalido):
        await Entorno().caso_de_uso.execute(archivo(opcion_multiple("a", 0)), simular=True)


async def test_reutiliza_una_materia_existente() -> None:
    """Escenario 6: la materia creada antes se reutiliza y se le suman las preguntas nuevas."""
    entorno = Entorno()
    await entorno.caso_de_uso.execute(archivo(opcion_multiple("a")))
    resultado = await entorno.caso_de_uso.execute(
        archivo(opcion_multiple("a"), verdadero_falso("b"))
    )
    assert (resultado.materia_creada, resultado.cargadas, resultado.omitidas) == (False, 1, 1)
    assert len(entorno.materias.materias) == 1 and len(entorno.preguntas.preguntas) == 2


async def test_un_texto_repetido_dentro_del_archivo_se_omite() -> None:
    """Dos preguntas con el mismo texto en un archivo: se carga una."""
    entorno = Entorno()
    resultado = await entorno.caso_de_uso.execute(
        archivo(opcion_multiple("igual"), verdadero_falso("igual"))
    )
    assert (resultado.cargadas, resultado.omitidas) == (1, 1)


async def test_una_pregunta_eliminada_se_vuelve_a_cargar() -> None:
    """Solo cuentan las preguntas activas: una dada de baja no bloquea la recarga."""
    entorno = Entorno()
    await entorno.caso_de_uso.execute(archivo(verdadero_falso("a")))
    (existente,) = entorno.preguntas.preguntas.values()
    existente.eliminar()
    resultado = await entorno.caso_de_uso.execute(archivo(verdadero_falso("a")))
    assert resultado.cargadas == 1
