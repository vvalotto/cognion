import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.materia import Materia
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


async def _pregunta_om_persistida(session, banco_id: uuid.UUID) -> PreguntaPlantillaOpcionMultiple:
    pregunta_repo = SQLAlchemyPreguntaRepository(session)
    pregunta = PreguntaPlantillaOpcionMultiple.crear(
        banco_id=banco_id,
        texto="¿Cuál es la capital de Entre Ríos?",
        opciones=[
            Opcion(texto="Paraná", es_correcta=True),
            Opcion(texto="Concordia", es_correcta=False),
        ],
        unidad_tematica="Unidad 1",
        tema="Arquitectura",
        dificultad=Dificultad.MEDIO,
        importancia=Importancia.ALTO,
    )
    await pregunta_repo.guardar(pregunta)
    return pregunta


async def _pregunta_vf_persistida(session, banco_id: uuid.UUID) -> PreguntaPlantillaVerdaderoFalso:
    pregunta_repo = SQLAlchemyPreguntaRepository(session)
    pregunta = PreguntaPlantillaVerdaderoFalso.crear(
        banco_id=banco_id,
        texto="El sol es una estrella.",
        respuesta_correcta=True,
        unidad_tematica="Unidad 1",
        tema="Astronomía",
        dificultad=Dificultad.MEDIO,
        importancia=Importancia.ALTO,
    )
    await pregunta_repo.guardar(pregunta)
    return pregunta


def _body_valido(banco_id: uuid.UUID) -> dict:
    return {
        "banco_id": str(banco_id),
        "texto": "¿Cuál es la capital de Entre Ríos?",
        "opciones": [
            {"texto": "Paraná", "es_correcta": True},
            {"texto": "Concordia", "es_correcta": False},
            {"texto": "Gualeguaychú", "es_correcta": False},
        ],
        "unidad_tematica": "Unidad 1",
        "tema": "Arquitectura",
        "dificultad": "medio",
        "importancia": "alto",
    }


class TestPreguntasAPIIntegration:
    """Escenarios de `tests/features/inc2/US-2.1.3-cargar-pregunta-opcion-multiple.feature`."""

    async def test_docente_carga_pregunta_exitosa(self, session, docente_headers):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple",
                json=_body_valido(banco.id),
                headers=docente_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["banco_id"] == str(banco.id)
        assert data["activa"] is True
        assert len(data["opciones"]) == 3

    async def test_rechazo_por_ninguna_opcion_correcta(self, session, docente_headers):
        banco = await _banco_persistido(session)
        body = _body_valido(banco.id)
        body["opciones"] = [
            {"texto": "Paraná", "es_correcta": False},
            {"texto": "Concordia", "es_correcta": False},
        ]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple", json=body, headers=docente_headers
            )

        assert response.status_code == 422

    async def test_rechazo_por_mas_de_una_opcion_correcta(self, session, docente_headers):
        banco = await _banco_persistido(session)
        body = _body_valido(banco.id)
        body["opciones"] = [
            {"texto": "Paraná", "es_correcta": True},
            {"texto": "Concordia", "es_correcta": True},
        ]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple", json=body, headers=docente_headers
            )

        assert response.status_code == 422

    async def test_rechazo_por_menos_de_dos_opciones(self, session, docente_headers):
        banco = await _banco_persistido(session)
        body = _body_valido(banco.id)
        body["opciones"] = [{"texto": "Paraná", "es_correcta": True}]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple", json=body, headers=docente_headers
            )

        assert response.status_code == 422

    async def test_rechazo_por_banco_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple",
                json=_body_valido(uuid.uuid4()),
                headers=docente_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self, session):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/preguntas/opcion-multiple", json=_body_valido(banco.id))

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, session, admin_headers):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/opcion-multiple",
                json=_body_valido(banco.id),
                headers=admin_headers,
            )

        assert response.status_code == 403


def _body_vf_valido(banco_id: uuid.UUID, respuesta_correcta: bool = True) -> dict:
    return {
        "banco_id": str(banco_id),
        "texto": "El sol es una estrella.",
        "respuesta_correcta": respuesta_correcta,
        "unidad_tematica": "Unidad 1",
        "tema": "Astronomía",
        "dificultad": "medio",
        "importancia": "alto",
    }


class TestPreguntasVerdaderoFalsoAPIIntegration:
    """Escenarios de `tests/features/inc2/US-2.1.4-cargar-pregunta-verdadero-falso.feature`."""

    async def test_docente_carga_pregunta_exitosa_respuesta_verdadero(
        self, session, docente_headers
    ):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/verdadero-falso",
                json=_body_vf_valido(banco.id, respuesta_correcta=True),
                headers=docente_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["banco_id"] == str(banco.id)
        assert data["respuesta_correcta"] is True
        assert data["activa"] is True

    async def test_docente_carga_pregunta_exitosa_respuesta_falso(self, session, docente_headers):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/verdadero-falso",
                json=_body_vf_valido(banco.id, respuesta_correcta=False),
                headers=docente_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["respuesta_correcta"] is False

    async def test_rechazo_por_banco_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/verdadero-falso",
                json=_body_vf_valido(uuid.uuid4()),
                headers=docente_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self, session):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/verdadero-falso", json=_body_vf_valido(banco.id)
            )

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, session, admin_headers):
        banco = await _banco_persistido(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/preguntas/verdadero-falso",
                json=_body_vf_valido(banco.id),
                headers=admin_headers,
            )

        assert response.status_code == 403


def _body_editar_om(pregunta: PreguntaPlantillaOpcionMultiple) -> dict:
    return {
        "texto": "¿Cuál es la capital de la provincia de Entre Ríos?",
        "unidad_tematica": "Unidad 2",
        "tema": "Geografía",
        "dificultad": "bajo",
        "importancia": "medio",
        "opciones": [
            {"texto": "Paraná", "es_correcta": False},
            {"texto": "Concordia", "es_correcta": True},
        ],
    }


def _body_editar_vf() -> dict:
    return {
        "texto": "La luna es una estrella.",
        "unidad_tematica": "Unidad 2",
        "tema": "Geografía",
        "dificultad": "bajo",
        "importancia": "medio",
        "respuesta_correcta": False,
    }


class TestEditarPreguntaAPIIntegration:
    """Escenarios de `tests/features/inc2/US-2.1.5-editar-pregunta.feature`."""

    async def test_edicion_exitosa_opcion_multiple(self, session, docente_headers):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_om_persistida(session, banco.id)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/preguntas/{pregunta.id}",
                json=_body_editar_om(pregunta),
                headers=docente_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["texto"] == "¿Cuál es la capital de la provincia de Entre Ríos?"
        assert data["opciones"] == [
            {"texto": "Paraná", "es_correcta": False},
            {"texto": "Concordia", "es_correcta": True},
        ]

    async def test_edicion_exitosa_verdadero_falso(self, session, docente_headers):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_vf_persistida(session, banco.id)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/preguntas/{pregunta.id}",
                json=_body_editar_vf(),
                headers=docente_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["texto"] == "La luna es una estrella."
        assert data["respuesta_correcta"] is False

    async def test_rechazo_por_dejar_sin_opcion_correcta(self, session, docente_headers):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_om_persistida(session, banco.id)
        body = _body_editar_om(pregunta)
        body["opciones"] = [
            {"texto": "Paraná", "es_correcta": False},
            {"texto": "Concordia", "es_correcta": False},
        ]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/preguntas/{pregunta.id}", json=body, headers=docente_headers
            )

        assert response.status_code == 422

    async def test_rechazo_por_pregunta_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/preguntas/{uuid.uuid4()}",
                json=_body_editar_vf(),
                headers=docente_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_por_pregunta_inactiva(self, session, docente_headers):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_vf_persistida(session, banco.id)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta.activa = False
        await pregunta_repo.actualizar(pregunta)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/preguntas/{pregunta.id}",
                json=_body_editar_vf(),
                headers=docente_headers,
            )

        assert response.status_code == 409

    async def test_rechazo_sin_autenticacion(self, session):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_vf_persistida(session, banco.id)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(f"/preguntas/{pregunta.id}", json=_body_editar_vf())

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, session, admin_headers):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_vf_persistida(session, banco.id)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/preguntas/{pregunta.id}",
                json=_body_editar_vf(),
                headers=admin_headers,
            )

        assert response.status_code == 403


class TestEliminarPreguntaAPIIntegration:
    """Escenarios de `tests/features/inc2/US-2.1.6-eliminar-pregunta.feature`."""

    async def test_eliminacion_exitosa(self, session, docente_headers):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_vf_persistida(session, banco.id)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/preguntas/{pregunta.id}", headers=docente_headers)

        assert response.status_code == 204

        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        recuperada = await pregunta_repo.obtener_por_id(pregunta.id)
        assert recuperada is not None
        assert recuperada.activa is False

    async def test_rechazo_por_pregunta_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/preguntas/{uuid.uuid4()}", headers=docente_headers)

        assert response.status_code == 404

    async def test_rechazo_por_pregunta_ya_eliminada(self, session, docente_headers):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_vf_persistida(session, banco.id)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta.activa = False
        await pregunta_repo.actualizar(pregunta)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/preguntas/{pregunta.id}", headers=docente_headers)

        assert response.status_code == 409

    async def test_rechazo_sin_autenticacion(self, session):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_vf_persistida(session, banco.id)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/preguntas/{pregunta.id}")

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, session, admin_headers):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_vf_persistida(session, banco.id)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/preguntas/{pregunta.id}", headers=admin_headers)

        assert response.status_code == 403
