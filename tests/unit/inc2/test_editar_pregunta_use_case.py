import uuid

import pytest

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import (
    OpcionesInvalidas,
    PreguntaInactiva,
    PreguntaNoExiste,
)
from src.banco_preguntas.entities.eventos import PreguntaEditada
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.use_cases.editar_pregunta import EditarPreguntaUseCase
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


class TestEditarPreguntaUseCase:
    async def test_edita_pregunta_opcion_multiple(self):
        pregunta_repo = FakePreguntaRepository()
        pregunta = _pregunta_om()
        await pregunta_repo.guardar(pregunta)
        use_case = EditarPreguntaUseCase(pregunta_repo)
        nuevas_opciones = [
            Opcion(texto="Paraná", es_correcta=False),
            Opcion(texto="Concordia", es_correcta=True),
        ]

        editada, evento = await use_case.execute(
            pregunta_id=pregunta.id,
            texto="¿Cuál es la capital de la provincia de Entre Ríos?",
            unidad_tematica="Unidad 2",
            tema="Geografía",
            dificultad=Dificultad.BAJO,
            importancia=Importancia.MEDIO,
            opciones=nuevas_opciones,
        )

        assert editada.texto == "¿Cuál es la capital de la provincia de Entre Ríos?"
        assert editada.opciones == nuevas_opciones
        assert pregunta_repo.preguntas[pregunta.id].opciones == nuevas_opciones
        assert isinstance(evento, PreguntaEditada)
        assert evento.pregunta_id == pregunta.id
        assert evento.banco_id == pregunta.banco_id

    async def test_edita_pregunta_verdadero_falso(self):
        pregunta_repo = FakePreguntaRepository()
        pregunta = _pregunta_vf()
        await pregunta_repo.guardar(pregunta)
        use_case = EditarPreguntaUseCase(pregunta_repo)

        editada, evento = await use_case.execute(
            pregunta_id=pregunta.id,
            texto="La luna es una estrella.",
            unidad_tematica="Unidad 2",
            tema="Geografía",
            dificultad=Dificultad.BAJO,
            importancia=Importancia.MEDIO,
            respuesta_correcta=False,
        )

        assert editada.texto == "La luna es una estrella."
        assert editada.respuesta_correcta is False
        assert isinstance(evento, PreguntaEditada)

    async def test_rechaza_pregunta_inexistente(self):
        pregunta_repo = FakePreguntaRepository()
        use_case = EditarPreguntaUseCase(pregunta_repo)

        with pytest.raises(PreguntaNoExiste):
            await use_case.execute(
                pregunta_id=uuid.uuid4(),
                texto="texto",
                unidad_tematica="Unidad 1",
                tema="Tema",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
                respuesta_correcta=True,
            )

    async def test_rechaza_edicion_sin_opcion_correcta(self):
        pregunta_repo = FakePreguntaRepository()
        pregunta = _pregunta_om()
        await pregunta_repo.guardar(pregunta)
        use_case = EditarPreguntaUseCase(pregunta_repo)

        with pytest.raises(OpcionesInvalidas):
            await use_case.execute(
                pregunta_id=pregunta.id,
                texto=pregunta.texto,
                unidad_tematica=pregunta.unidad_tematica,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad,
                importancia=pregunta.importancia,
                opciones=[
                    Opcion(texto="Paraná", es_correcta=False),
                    Opcion(texto="Concordia", es_correcta=False),
                ],
            )

    async def test_rechaza_edicion_de_pregunta_inactiva(self):
        pregunta_repo = FakePreguntaRepository()
        pregunta = _pregunta_vf()
        pregunta.activa = False
        await pregunta_repo.guardar(pregunta)
        use_case = EditarPreguntaUseCase(pregunta_repo)

        with pytest.raises(PreguntaInactiva):
            await use_case.execute(
                pregunta_id=pregunta.id,
                texto=pregunta.texto,
                unidad_tematica=pregunta.unidad_tematica,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad,
                importancia=pregunta.importancia,
                respuesta_correcta=pregunta.respuesta_correcta,
            )
