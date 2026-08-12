import uuid

import pytest

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import OpcionesInvalidas, PreguntaInactiva
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)


def _crear(opciones: list[Opcion]) -> PreguntaPlantillaOpcionMultiple:
    return PreguntaPlantillaOpcionMultiple.crear(
        banco_id=uuid.uuid4(),
        texto="¿Cuál es la capital de Entre Ríos?",
        opciones=opciones,
        unidad_tematica="Unidad 1",
        tema="Arquitectura",
        dificultad=Dificultad.MEDIO,
        importancia=Importancia.ALTO,
    )


class TestPreguntaPlantillaOpcionMultipleCrear:
    def test_crea_con_tres_opciones_y_una_correcta(self):
        opciones = [
            Opcion(texto="Paraná", es_correcta=True),
            Opcion(texto="Concordia", es_correcta=False),
            Opcion(texto="Gualeguaychú", es_correcta=False),
        ]

        pregunta = _crear(opciones)

        assert pregunta.id is not None
        assert pregunta.opciones == opciones
        assert pregunta.activa is True

    def test_rechaza_ninguna_opcion_correcta(self):
        opciones = [
            Opcion(texto="Paraná", es_correcta=False),
            Opcion(texto="Concordia", es_correcta=False),
            Opcion(texto="Gualeguaychú", es_correcta=False),
        ]

        with pytest.raises(OpcionesInvalidas):
            _crear(opciones)

    def test_rechaza_mas_de_una_opcion_correcta(self):
        opciones = [
            Opcion(texto="Paraná", es_correcta=True),
            Opcion(texto="Concordia", es_correcta=True),
        ]

        with pytest.raises(OpcionesInvalidas):
            _crear(opciones)

    def test_rechaza_menos_de_dos_opciones(self):
        opciones = [Opcion(texto="Paraná", es_correcta=True)]

        with pytest.raises(OpcionesInvalidas):
            _crear(opciones)


class TestPreguntaPlantillaOpcionMultipleEditar:
    def test_edita_texto_y_opciones(self):
        pregunta = _crear(
            [
                Opcion(texto="Paraná", es_correcta=True),
                Opcion(texto="Concordia", es_correcta=False),
                Opcion(texto="Gualeguaychú", es_correcta=False),
            ]
        )
        nuevas_opciones = [
            Opcion(texto="Paraná", es_correcta=False),
            Opcion(texto="Concordia", es_correcta=True),
        ]

        pregunta.editar(
            texto="¿Cuál es la capital de la provincia de Entre Ríos?",
            opciones=nuevas_opciones,
            unidad_tematica="Unidad 2",
            tema="Geografía",
            dificultad=Dificultad.BAJO,
            importancia=Importancia.MEDIO,
        )

        assert pregunta.texto == "¿Cuál es la capital de la provincia de Entre Ríos?"
        assert pregunta.opciones == nuevas_opciones
        assert pregunta.unidad_tematica == "Unidad 2"
        assert pregunta.tema == "Geografía"
        assert pregunta.dificultad == Dificultad.BAJO
        assert pregunta.importancia == Importancia.MEDIO

    def test_rechaza_edicion_que_deja_sin_opcion_correcta(self):
        pregunta = _crear(
            [
                Opcion(texto="Paraná", es_correcta=True),
                Opcion(texto="Concordia", es_correcta=False),
            ]
        )

        with pytest.raises(OpcionesInvalidas):
            pregunta.editar(
                texto=pregunta.texto,
                opciones=[
                    Opcion(texto="Paraná", es_correcta=False),
                    Opcion(texto="Concordia", es_correcta=False),
                ],
                unidad_tematica=pregunta.unidad_tematica,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad,
                importancia=pregunta.importancia,
            )

    def test_rechaza_edicion_de_pregunta_inactiva(self):
        pregunta = _crear(
            [
                Opcion(texto="Paraná", es_correcta=True),
                Opcion(texto="Concordia", es_correcta=False),
            ]
        )
        pregunta.activa = False

        with pytest.raises(PreguntaInactiva):
            pregunta.editar(
                texto=pregunta.texto,
                opciones=pregunta.opciones,
                unidad_tematica=pregunta.unidad_tematica,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad,
                importancia=pregunta.importancia,
            )


def _crear_vf(respuesta_correcta: bool) -> PreguntaPlantillaVerdaderoFalso:
    return PreguntaPlantillaVerdaderoFalso.crear(
        banco_id=uuid.uuid4(),
        texto="El sol es una estrella.",
        respuesta_correcta=respuesta_correcta,
        unidad_tematica="Unidad 1",
        tema="Astronomía",
        dificultad=Dificultad.MEDIO,
        importancia=Importancia.ALTO,
    )


class TestPreguntaPlantillaVerdaderoFalsoCrear:
    def test_crea_con_respuesta_verdadero(self):
        pregunta = _crear_vf(True)

        assert pregunta.id is not None
        assert pregunta.respuesta_correcta is True
        assert pregunta.activa is True

    def test_crea_con_respuesta_falso(self):
        pregunta = _crear_vf(False)

        assert pregunta.respuesta_correcta is False
        assert pregunta.activa is True


class TestPreguntaPlantillaVerdaderoFalsoEditar:
    def test_edita_texto_y_respuesta(self):
        pregunta = _crear_vf(True)

        pregunta.editar(
            texto="La luna es una estrella.",
            respuesta_correcta=False,
            unidad_tematica="Unidad 2",
            tema="Geografía",
            dificultad=Dificultad.BAJO,
            importancia=Importancia.MEDIO,
        )

        assert pregunta.texto == "La luna es una estrella."
        assert pregunta.respuesta_correcta is False
        assert pregunta.unidad_tematica == "Unidad 2"
        assert pregunta.tema == "Geografía"
        assert pregunta.dificultad == Dificultad.BAJO
        assert pregunta.importancia == Importancia.MEDIO

    def test_rechaza_edicion_de_pregunta_inactiva(self):
        pregunta = _crear_vf(True)
        pregunta.activa = False

        with pytest.raises(PreguntaInactiva):
            pregunta.editar(
                texto=pregunta.texto,
                respuesta_correcta=pregunta.respuesta_correcta,
                unidad_tematica=pregunta.unidad_tematica,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad,
                importancia=pregunta.importancia,
            )
