import uuid

import pytest

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import PreguntaNoExiste, PreguntaYaEliminada
from src.banco_preguntas.entities.eventos import PreguntaEliminada
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.use_cases.eliminar_pregunta import EliminarPreguntaUseCase
from tests.unit.inc2._fakes import FakePreguntaRepository


def _pregunta_om() -> PreguntaPlantillaOpcionMultiple:
    return PreguntaPlantillaOpcionMultiple.crear(
        banco_id=uuid.uuid4(),
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


def _pregunta_vf() -> PreguntaPlantillaVerdaderoFalso:
    return PreguntaPlantillaVerdaderoFalso.crear(
        banco_id=uuid.uuid4(),
        texto="El sol es una estrella.",
        respuesta_correcta=True,
        unidad_tematica="Unidad 1",
        tema="Astronomía",
        dificultad=Dificultad.MEDIO,
        importancia=Importancia.ALTO,
    )


class TestEliminarPreguntaUseCase:
    async def test_elimina_pregunta_opcion_multiple(self):
        pregunta_repo = FakePreguntaRepository()
        pregunta = _pregunta_om()
        await pregunta_repo.guardar(pregunta)
        use_case = EliminarPreguntaUseCase(pregunta_repo)

        eliminada, evento = await use_case.execute(pregunta_id=pregunta.id)

        assert eliminada.activa is False
        assert pregunta_repo.preguntas[pregunta.id].activa is False
        assert isinstance(evento, PreguntaEliminada)
        assert evento.pregunta_id == pregunta.id
        assert evento.banco_id == pregunta.banco_id

    async def test_elimina_pregunta_verdadero_falso(self):
        pregunta_repo = FakePreguntaRepository()
        pregunta = _pregunta_vf()
        await pregunta_repo.guardar(pregunta)
        use_case = EliminarPreguntaUseCase(pregunta_repo)

        eliminada, evento = await use_case.execute(pregunta_id=pregunta.id)

        assert eliminada.activa is False
        assert isinstance(evento, PreguntaEliminada)

    async def test_rechaza_pregunta_inexistente(self):
        pregunta_repo = FakePreguntaRepository()
        use_case = EliminarPreguntaUseCase(pregunta_repo)

        with pytest.raises(PreguntaNoExiste):
            await use_case.execute(pregunta_id=uuid.uuid4())

    async def test_rechaza_pregunta_ya_eliminada(self):
        pregunta_repo = FakePreguntaRepository()
        pregunta = _pregunta_vf()
        pregunta.activa = False
        await pregunta_repo.guardar(pregunta)
        use_case = EliminarPreguntaUseCase(pregunta_repo)

        with pytest.raises(PreguntaYaEliminada):
            await use_case.execute(pregunta_id=pregunta.id)
