"""Tests unitarios del helper `resolver_nombres` (US-6.3.1)."""

from uuid import uuid4

from src.actividad_evaluativa.use_cases._resolucion_nombres import (
    NOMBRE_SIN_RESOLVER,
    resolver_nombres,
)
from tests.unit.inc3._fakes import FakeEstudianteConsultaPort


class TestResolverNombres:
    async def test_resuelve_los_nombres_precargados(self):
        consulta = FakeEstudianteConsultaPort()
        a, b = uuid4(), uuid4()
        consulta.nombres_por_estudiante[a] = "Ana Torres"
        consulta.nombres_por_estudiante[b] = "Beto Gómez"

        resultado = await resolver_nombres(consulta, [a, b])

        assert resultado == {a: "Ana Torres", b: "Beto Gómez"}

    async def test_id_sin_nombre_resoluble_usa_el_texto_de_reemplazo(self):
        consulta = FakeEstudianteConsultaPort()
        sin_cuenta = uuid4()

        resultado = await resolver_nombres(consulta, [sin_cuenta])

        assert resultado == {sin_cuenta: NOMBRE_SIN_RESOLVER}

    async def test_ids_repetidos_se_resuelven_una_sola_vez(self):
        consulta = FakeEstudianteConsultaPort()
        a = uuid4()
        consulta.nombres_por_estudiante[a] = "Ana Torres"
        llamados: list[list] = []
        original = consulta.obtener_nombres

        async def contar_llamada(ids):
            llamados.append(list(ids))
            return await original(ids)

        consulta.obtener_nombres = contar_llamada  # type: ignore[method-assign]

        resultado = await resolver_nombres(consulta, [a, a, a])

        assert resultado == {a: "Ana Torres"}
        assert len(llamados) == 1
        assert llamados[0] == [a]

    async def test_lista_vacia_no_llama_al_puerto(self):
        consulta = FakeEstudianteConsultaPort()
        llamado = False
        original = consulta.obtener_nombres

        async def marcar_llamada(ids):
            nonlocal llamado
            llamado = True
            return await original(ids)

        consulta.obtener_nombres = marcar_llamada  # type: ignore[method-assign]

        resultado = await resolver_nombres(consulta, [])

        assert resultado == {}
        assert llamado is False
