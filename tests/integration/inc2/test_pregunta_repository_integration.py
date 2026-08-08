import uuid

from sqlalchemy import select

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.materia import Materia
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
            texto="El sol es una estrella.",
            respuesta_correcta=True,
            unidad_tematica="Unidad 1",
            tema="Astronomía",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
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
