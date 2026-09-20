"""Integración de los read models de la sesión en vivo contra la DB real (US-6.2.3)."""

import asyncio
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import text

from src.actividad_evaluativa.entities.errors import ConcurrenciaOptimistaError
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.adapters.proyecciones_en_vivo_repository import (
    SQLAlchemyProyeccionesEnVivo,
    SQLAlchemyProyeccionesEnVivoQuery,
)
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.shared.frameworks.db import SessionLocal


async def _confirmar(operacion) -> None:
    """Ejecuta `operacion(proyecciones)` en una sesión propia y confirma."""
    async with SessionLocal() as session:
        await operacion(SQLAlchemyProyeccionesEnVivo(session))
        await session.commit()


async def _ranking(sesion_id):
    async with SessionLocal() as session:
        return await SQLAlchemyProyeccionesEnVivoQuery(session).ranking(sesion_id)


class TestRanking:
    async def test_participante_inicializado_aparece_con_cero_puntos(self):
        sesion_id, estudiante_id = uuid4(), uuid4()

        await _confirmar(lambda p: p.inicializar_participante(sesion_id, estudiante_id))

        ranking = await _ranking(sesion_id)
        assert [(r.posicion, r.estudiante_id, r.puntaje_acumulado) for r in ranking] == [
            (1, estudiante_id, 0)
        ]

    async def test_inicializar_dos_veces_no_reinicia_ni_duplica(self):
        sesion_id, estudiante_id = uuid4(), uuid4()
        await _confirmar(lambda p: p.inicializar_participante(sesion_id, estudiante_id))
        await _confirmar(
            lambda p: p.registrar_respuesta(sesion_id, estudiante_id, uuid4(), "0", 1500)
        )

        await _confirmar(lambda p: p.inicializar_participante(sesion_id, estudiante_id))

        ranking = await _ranking(sesion_id)
        assert [(r.estudiante_id, r.puntaje_acumulado) for r in ranking] == [(estudiante_id, 1500)]

    async def test_registrar_respuesta_suma_puntaje_e_incrementa_la_opcion(self):
        sesion_id, estudiante_id, pregunta_id = uuid4(), uuid4(), uuid4()
        await _confirmar(
            lambda p: p.registrar_respuesta(sesion_id, estudiante_id, uuid4(), "0", 1000)
        )

        await _confirmar(
            lambda p: p.registrar_respuesta(sesion_id, estudiante_id, pregunta_id, "2", 500)
        )

        ranking = await _ranking(sesion_id)
        assert ranking[0].puntaje_acumulado == 1500
        async with SessionLocal() as session:
            consulta = SQLAlchemyProyeccionesEnVivoQuery(session)
            assert [
                (o.opcion, o.cantidad) for o in await consulta.distribucion(sesion_id, pregunta_id)
            ] == [("2", 1)]

    async def test_orden_por_puntaje_y_desempate_por_quien_llego_antes(self):
        sesion_id = uuid4()
        primero, segundo, lider = uuid4(), uuid4(), uuid4()
        await _confirmar(lambda p: p.registrar_respuesta(sesion_id, primero, uuid4(), "0", 800))
        await _confirmar(lambda p: p.registrar_respuesta(sesion_id, segundo, uuid4(), "0", 800))
        await _confirmar(lambda p: p.registrar_respuesta(sesion_id, lider, uuid4(), "0", 2000))

        ranking = await _ranking(sesion_id)

        assert [r.estudiante_id for r in ranking] == [lider, primero, segundo]
        assert [r.posicion for r in ranking] == [1, 2, 3]

    async def test_ranking_de_otra_sesion_no_se_mezcla(self):
        sesion_a, sesion_b = uuid4(), uuid4()
        await _confirmar(lambda p: p.inicializar_participante(sesion_a, uuid4()))

        assert await _ranking(sesion_b) == []


class TestDistribucion:
    async def test_solo_devuelve_opciones_con_respuestas_y_el_total(self):
        sesion_id, pregunta_id = uuid4(), uuid4()
        for opcion in ("0", "0", "3"):
            await _confirmar(
                lambda p, o=opcion: p.registrar_respuesta(sesion_id, uuid4(), pregunta_id, o, 0)
            )

        async with SessionLocal() as session:
            consulta = SQLAlchemyProyeccionesEnVivoQuery(session)
            assert [
                (o.opcion, o.cantidad) for o in await consulta.distribucion(sesion_id, pregunta_id)
            ] == [
                ("0", 2),
                ("3", 1),
            ]
            assert await consulta.cantidad_respuestas(sesion_id, pregunta_id) == 3
            assert await consulta.cantidad_respuestas(sesion_id, uuid4()) == 0

    async def test_60_respuestas_simultaneas_a_la_misma_opcion_no_pierden_ninguna(self):
        sesion_id, pregunta_id = uuid4(), uuid4()

        await asyncio.gather(
            *[
                _confirmar(
                    lambda p: p.registrar_respuesta(sesion_id, uuid4(), pregunta_id, "1", 100)
                )
                for _ in range(60)
            ]
        )

        async with SessionLocal() as session:
            consulta = SQLAlchemyProyeccionesEnVivoQuery(session)
            assert [
                (o.opcion, o.cantidad) for o in await consulta.distribucion(sesion_id, pregunta_id)
            ] == [("1", 60)]
        assert len(await _ranking(sesion_id)) == 60


class TestAtomicidadConElEventStore:
    async def test_evento_y_proyeccion_se_confirman_juntos(self):
        sesion_id, estudiante_id, agregado_id = uuid4(), uuid4(), uuid4()
        async with SessionLocal() as session:
            await SQLAlchemyProyeccionesEnVivo(session).inicializar_participante(
                sesion_id, estudiante_id
            )
            await SQLAlchemyEventStore(session).append(
                "ParticipacionEnVivo", agregado_id, 0, [EventoParaAlmacenar("EstudianteUnido", {})]
            )

        assert len(await _ranking(sesion_id)) == 1
        async with SessionLocal() as session:
            assert (
                len(await SQLAlchemyEventStore(session).load("ParticipacionEnVivo", agregado_id))
                == 1
            )

    async def test_si_el_append_falla_por_concurrencia_ni_evento_ni_proyeccion_quedan(self):
        sesion_id, estudiante_id, agregado_id = uuid4(), uuid4(), uuid4()
        async with SessionLocal() as session:
            proyecciones = SQLAlchemyProyeccionesEnVivo(session)
            await proyecciones.inicializar_participante(sesion_id, estudiante_id)
            with pytest.raises(ConcurrenciaOptimistaError):
                await SQLAlchemyEventStore(session).append(
                    "ParticipacionEnVivo",
                    agregado_id,
                    5,
                    [EventoParaAlmacenar("EstudianteUnido", {})],
                )
            await proyecciones.descartar_pendientes()
            # un commit posterior no debe resucitar la proyección descartada
            await session.commit()

        assert await _ranking(sesion_id) == []
        async with SessionLocal() as session:
            assert (
                await SQLAlchemyEventStore(session).load("ParticipacionEnVivo", agregado_id) == []
            )


class TestMigracion:
    async def test_es_reversible_por_round_trip(self):
        def _alembic(*args: str) -> None:
            subprocess.run(
                [sys.executable, "-m", "alembic", *args], check=True, capture_output=True
            )

        async def _tablas() -> set[str]:
            async with SessionLocal() as session:
                filas = await session.execute(
                    text(
                        "SELECT tablename FROM pg_tables WHERE tablename IN "
                        "('ranking_por_sesion', 'distribucion_por_pregunta')"
                    )
                )
                return {f[0] for f in filas}

        assert await _tablas() == {"ranking_por_sesion", "distribucion_por_pregunta"}
        try:
            await asyncio.to_thread(_alembic, "downgrade", "e31e7dfcab3a")
            assert await _tablas() == set()
        finally:
            await asyncio.to_thread(_alembic, "upgrade", "head")
        assert await _tablas() == {"ranking_por_sesion", "distribucion_por_pregunta"}
