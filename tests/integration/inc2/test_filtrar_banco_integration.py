import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
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


async def _banco_persistido(session) -> Banco:
    materia_repo = SQLAlchemyMateriaRepository(session)
    banco_repo = SQLAlchemyBancoRepository(session)
    materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
    await materia_repo.guardar(materia)
    banco = Banco.crear(materia.id)
    await banco_repo.guardar(banco)
    return banco


async def _pregunta_om_persistida(
    session,
    banco_id: uuid.UUID,
    unidad: str = "Unidad 1",
    tema: str = "Arquitectura",
    dificultad: Dificultad = Dificultad.MEDIO,
    importancia: Importancia = Importancia.ALTO,
) -> PreguntaPlantillaOpcionMultiple:
    pregunta_repo = SQLAlchemyPreguntaRepository(session)
    pregunta = PreguntaPlantillaOpcionMultiple.crear(
        banco_id=banco_id,
        metadatos=MetadatosPregunta(
            texto="¿Cuál es la capital de Entre Ríos?",
            unidad_tematica=unidad,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
        ),
        opciones=[
            Opcion(texto="Paraná", es_correcta=True),
            Opcion(texto="Concordia", es_correcta=False),
        ],
    )
    await pregunta_repo.guardar(pregunta)
    return pregunta


async def _pregunta_vf_persistida(
    session,
    banco_id: uuid.UUID,
    unidad: str = "Unidad 1",
    tema: str = "Astronomía",
    dificultad: Dificultad = Dificultad.MEDIO,
    importancia: Importancia = Importancia.ALTO,
) -> PreguntaPlantillaVerdaderoFalso:
    pregunta_repo = SQLAlchemyPreguntaRepository(session)
    pregunta = PreguntaPlantillaVerdaderoFalso.crear(
        banco_id=banco_id,
        metadatos=MetadatosPregunta(
            texto="El sol es una estrella.",
            unidad_tematica=unidad,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
        ),
        respuesta_correcta=True,
    )
    await pregunta_repo.guardar(pregunta)
    return pregunta


class TestSQLAlchemyPreguntaRepositoryFiltrar:
    """`SQLAlchemyPreguntaRepository.filtrar` contra PostgreSQL real."""

    async def test_filtra_por_dificultad_e_importancia(self, session):
        banco = await _banco_persistido(session)
        match = await _pregunta_om_persistida(
            session, banco.id, dificultad=Dificultad.ALTO, importancia=Importancia.ALTO
        )
        await _pregunta_vf_persistida(
            session, banco.id, dificultad=Dificultad.BAJO, importancia=Importancia.ALTO
        )

        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        resultado = await pregunta_repo.filtrar(
            banco_id=banco.id, dificultad="alto", importancia="alto"
        )

        assert [p.id for p in resultado.preguntas] == [match.id]
        assert resultado.total == 1

    async def test_sin_filtros_devuelve_solo_activas(self, session):
        banco = await _banco_persistido(session)
        activas = [await _pregunta_om_persistida(session, banco.id) for _ in range(3)]
        inactiva = await _pregunta_vf_persistida(session, banco.id)
        inactiva.eliminar()
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        await pregunta_repo.actualizar(inactiva)

        resultado = await pregunta_repo.filtrar(banco_id=banco.id)

        ids_resultado = {p.id for p in resultado.preguntas}
        assert ids_resultado == {p.id for p in activas}
        assert inactiva.id not in ids_resultado
        assert resultado.total == 3

    async def test_ningun_resultado(self, session):
        banco = await _banco_persistido(session)
        await _pregunta_om_persistida(session, banco.id, dificultad=Dificultad.ALTO)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)

        resultado = await pregunta_repo.filtrar(banco_id=banco.id, dificultad="bajo")

        assert resultado.preguntas == []
        assert resultado.total == 0

    async def test_filtra_por_unidad_y_tema(self, session):
        banco = await _banco_persistido(session)
        match = await _pregunta_om_persistida(session, banco.id, unidad="Unidad 2", tema="Testing")
        await _pregunta_om_persistida(session, banco.id, unidad="Unidad 1", tema="Testing")
        pregunta_repo = SQLAlchemyPreguntaRepository(session)

        resultado = await pregunta_repo.filtrar(
            banco_id=banco.id, unidad="Unidad 2", tema="Testing"
        )

        assert [p.id for p in resultado.preguntas] == [match.id]

    async def test_orden_estable_por_fecha_creacion_con_desempate_por_id(self, session):
        banco = await _banco_persistido(session)
        primera = await _pregunta_om_persistida(session, banco.id)
        segunda = await _pregunta_vf_persistida(session, banco.id)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)

        resultado = await pregunta_repo.filtrar(banco_id=banco.id)

        assert [p.id for p in resultado.preguntas] == [primera.id, segunda.id]

    async def test_pagina_y_tamanio_pagina_aplican_limit_y_offset(self, session):
        banco = await _banco_persistido(session)
        preguntas = [await _pregunta_om_persistida(session, banco.id) for _ in range(5)]
        pregunta_repo = SQLAlchemyPreguntaRepository(session)

        pagina_1 = await pregunta_repo.filtrar(banco_id=banco.id, pagina=1, tamanio_pagina=2)
        pagina_2 = await pregunta_repo.filtrar(banco_id=banco.id, pagina=2, tamanio_pagina=2)

        assert [p.id for p in pagina_1.preguntas] == [p.id for p in preguntas[0:2]]
        assert [p.id for p in pagina_2.preguntas] == [p.id for p in preguntas[2:4]]
        assert pagina_1.total == 5
        assert pagina_2.total == 5

    async def test_pagina_fuera_de_rango_devuelve_vacio_sin_error(self, session):
        banco = await _banco_persistido(session)
        await _pregunta_om_persistida(session, banco.id)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)

        resultado = await pregunta_repo.filtrar(banco_id=banco.id, pagina=99, tamanio_pagina=20)

        assert resultado.preguntas == []
        assert resultado.total == 1


class TestFiltrarPreguntasAPIIntegration:
    """Escenarios de `tests/features/inc2/US-2.1.7-filtrar-banco.feature`."""

    async def test_filtro_combinado_por_dificultad_e_importancia(self, session, docente_headers):
        banco = await _banco_persistido(session)
        match = await _pregunta_om_persistida(
            session, banco.id, dificultad=Dificultad.ALTO, importancia=Importancia.ALTO
        )
        await _pregunta_vf_persistida(
            session, banco.id, dificultad=Dificultad.BAJO, importancia=Importancia.ALTO
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/bancos/{banco.id}/preguntas",
                params={"dificultad": "alto", "importancia": "alto"},
                headers=docente_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert [p["id"] for p in data["preguntas"]] == [str(match.id)]
        assert data["total"] == 1

    async def test_sin_filtros_adicionales(self, session, docente_headers):
        banco = await _banco_persistido(session)
        for _ in range(5):
            await _pregunta_om_persistida(session, banco.id)
        inactiva = await _pregunta_vf_persistida(session, banco.id)
        inactiva.eliminar()
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        await pregunta_repo.actualizar(inactiva)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/bancos/{banco.id}/preguntas", headers=docente_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["preguntas"]) == 5
        assert data["total"] == 5
        assert str(inactiva.id) not in [p["id"] for p in data["preguntas"]]

    async def test_ningun_resultado(self, session, docente_headers):
        banco = await _banco_persistido(session)
        await _pregunta_om_persistida(session, banco.id, dificultad=Dificultad.ALTO)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/bancos/{banco.id}/preguntas",
                params={"dificultad": "bajo"},
                headers=docente_headers,
            )

        assert response.status_code == 200
        assert response.json() == {"preguntas": [], "total": 0}

    async def test_pagina_y_tamanio_pagina_via_api(self, session, docente_headers):
        banco = await _banco_persistido(session)
        for _ in range(5):
            await _pregunta_om_persistida(session, banco.id)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/bancos/{banco.id}/preguntas",
                params={"pagina": 2, "tamanio_pagina": 2},
                headers=docente_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["preguntas"]) == 2
        assert data["total"] == 5

    async def test_rechazo_por_banco_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/bancos/{uuid.uuid4()}/preguntas", headers=docente_headers
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self, session):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/bancos/{banco.id}/preguntas")

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, session, admin_headers):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/bancos/{banco.id}/preguntas", headers=admin_headers)

        assert response.status_code == 403
