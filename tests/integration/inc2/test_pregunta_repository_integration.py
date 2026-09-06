import uuid

from sqlalchemy import select

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
from src.banco_preguntas.frameworks.db.models import PreguntaPlantillaModel
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


class TestSQLAlchemyBancoRepositoryObtenerPorId:
    async def test_obtener_por_id_existente(self, session):
        banco_repo = SQLAlchemyBancoRepository(session)
        banco = await _banco_persistido(session)

        recuperado = await banco_repo.obtener_por_id(banco.id)

        assert recuperado is not None
        assert recuperado.id == banco.id
        assert recuperado.materia_id == banco.materia_id

    async def test_obtener_por_id_inexistente_retorna_none(self, session):
        banco_repo = SQLAlchemyBancoRepository(session)

        assert await banco_repo.obtener_por_id(uuid.uuid4()) is None


class TestSQLAlchemyPreguntaRepositoryIntegration:
    async def test_guardar_pregunta_opcion_multiple(self, session):
        banco = await _banco_persistido(session)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta = PreguntaPlantillaOpcionMultiple.crear(
            banco_id=banco.id,
            metadatos=MetadatosPregunta(
                texto="¿Cuál es la capital de Entre Ríos?",
                unidad_tematica="Unidad 1",
                tema="Arquitectura",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
            ),
            opciones=[
                Opcion(texto="Paraná", es_correcta=True),
                Opcion(texto="Concordia", es_correcta=False),
            ],
        )

        await pregunta_repo.guardar(pregunta)

        resultado = await session.execute(
            select(PreguntaPlantillaModel).where(PreguntaPlantillaModel.id == pregunta.id)
        )
        fila = resultado.scalar_one()
        assert fila.banco_id == banco.id
        assert fila.tipo == "opcion_multiple"
        assert fila.opciones == [
            {"texto": "Paraná", "es_correcta": True},
            {"texto": "Concordia", "es_correcta": False},
        ]
        assert fila.respuesta_correcta is None
        assert fila.dificultad == "medio"
        assert fila.importancia == "alto"
        assert fila.activa is True

    async def test_guardar_pregunta_verdadero_falso(self, session):
        banco = await _banco_persistido(session)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta = PreguntaPlantillaVerdaderoFalso.crear(
            banco_id=banco.id,
            metadatos=MetadatosPregunta(
                texto="El sol es una estrella.",
                unidad_tematica="Unidad 1",
                tema="Astronomía",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
            ),
            respuesta_correcta=True,
        )

        await pregunta_repo.guardar(pregunta)

        resultado = await session.execute(
            select(PreguntaPlantillaModel).where(PreguntaPlantillaModel.id == pregunta.id)
        )
        fila = resultado.scalar_one()
        assert fila.banco_id == banco.id
        assert fila.tipo == "verdadero_falso"
        assert fila.opciones is None
        assert fila.respuesta_correcta is True
        assert fila.dificultad == "medio"
        assert fila.importancia == "alto"
        assert fila.activa is True

    async def test_obtener_por_id_pregunta_opcion_multiple(self, session):
        banco = await _banco_persistido(session)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta = PreguntaPlantillaOpcionMultiple.crear(
            banco_id=banco.id,
            metadatos=MetadatosPregunta(
                texto="¿Cuál es la capital de Entre Ríos?",
                unidad_tematica="Unidad 1",
                tema="Arquitectura",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
            ),
            opciones=[
                Opcion(texto="Paraná", es_correcta=True),
                Opcion(texto="Concordia", es_correcta=False),
            ],
        )
        await pregunta_repo.guardar(pregunta)

        recuperada = await pregunta_repo.obtener_por_id(pregunta.id)

        assert isinstance(recuperada, PreguntaPlantillaOpcionMultiple)
        assert recuperada.id == pregunta.id
        assert recuperada.opciones == pregunta.opciones

    async def test_obtener_por_id_pregunta_verdadero_falso(self, session):
        banco = await _banco_persistido(session)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta = PreguntaPlantillaVerdaderoFalso.crear(
            banco_id=banco.id,
            metadatos=MetadatosPregunta(
                texto="El sol es una estrella.",
                unidad_tematica="Unidad 1",
                tema="Astronomía",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
            ),
            respuesta_correcta=True,
        )
        await pregunta_repo.guardar(pregunta)

        recuperada = await pregunta_repo.obtener_por_id(pregunta.id)

        assert isinstance(recuperada, PreguntaPlantillaVerdaderoFalso)
        assert recuperada.respuesta_correcta is True

    async def test_obtener_por_id_inexistente_retorna_none(self, session):
        pregunta_repo = SQLAlchemyPreguntaRepository(session)

        assert await pregunta_repo.obtener_por_id(uuid.uuid4()) is None

    async def test_actualizar_pregunta_opcion_multiple(self, session):
        banco = await _banco_persistido(session)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta = PreguntaPlantillaOpcionMultiple.crear(
            banco_id=banco.id,
            metadatos=MetadatosPregunta(
                texto="¿Cuál es la capital de Entre Ríos?",
                unidad_tematica="Unidad 1",
                tema="Arquitectura",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
            ),
            opciones=[
                Opcion(texto="Paraná", es_correcta=True),
                Opcion(texto="Concordia", es_correcta=False),
            ],
        )
        await pregunta_repo.guardar(pregunta)

        pregunta.editar(
            metadatos=MetadatosPregunta(
                texto="¿Cuál es la capital de la provincia de Entre Ríos?",
                unidad_tematica="Unidad 2",
                tema="Geografía",
                dificultad=Dificultad.BAJO,
                importancia=Importancia.MEDIO,
            ),
            opciones=[
                Opcion(texto="Paraná", es_correcta=False),
                Opcion(texto="Concordia", es_correcta=True),
            ],
        )
        await pregunta_repo.actualizar(pregunta)

        resultado = await session.execute(
            select(PreguntaPlantillaModel).where(PreguntaPlantillaModel.id == pregunta.id)
        )
        fila = resultado.scalar_one()
        assert fila.texto == "¿Cuál es la capital de la provincia de Entre Ríos?"
        assert fila.opciones == [
            {"texto": "Paraná", "es_correcta": False},
            {"texto": "Concordia", "es_correcta": True},
        ]
        assert fila.dificultad == "bajo"
        assert fila.importancia == "medio"

    async def test_actualizar_pregunta_verdadero_falso(self, session):
        banco = await _banco_persistido(session)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta = PreguntaPlantillaVerdaderoFalso.crear(
            banco_id=banco.id,
            metadatos=MetadatosPregunta(
                texto="El sol es una estrella.",
                unidad_tematica="Unidad 1",
                tema="Astronomía",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
            ),
            respuesta_correcta=True,
        )
        await pregunta_repo.guardar(pregunta)

        pregunta.editar(
            metadatos=MetadatosPregunta(
                texto="La luna es una estrella.",
                unidad_tematica="Unidad 2",
                tema="Geografía",
                dificultad=Dificultad.BAJO,
                importancia=Importancia.MEDIO,
            ),
            respuesta_correcta=False,
        )
        await pregunta_repo.actualizar(pregunta)

        resultado = await session.execute(
            select(PreguntaPlantillaModel).where(PreguntaPlantillaModel.id == pregunta.id)
        )
        fila = resultado.scalar_one()
        assert fila.texto == "La luna es una estrella."
        assert fila.respuesta_correcta is False

    async def test_actualizar_pregunta_eliminada_persiste_activa_false(self, session):
        banco = await _banco_persistido(session)
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta = PreguntaPlantillaVerdaderoFalso.crear(
            banco_id=banco.id,
            metadatos=MetadatosPregunta(
                texto="El sol es una estrella.",
                unidad_tematica="Unidad 1",
                tema="Astronomía",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
            ),
            respuesta_correcta=True,
        )
        await pregunta_repo.guardar(pregunta)

        pregunta.eliminar()
        await pregunta_repo.actualizar(pregunta)

        resultado = await session.execute(
            select(PreguntaPlantillaModel).where(PreguntaPlantillaModel.id == pregunta.id)
        )
        fila = resultado.scalar_one()
        assert fila.activa is False
