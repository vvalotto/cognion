import uuid

import pytest

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import OpcionesInvalidas
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple


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
