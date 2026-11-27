"""Presenters de Banco de Preguntas (`US-12.2.4`, `ADR-031`): cada `presentar_*` arma su salida sin FastAPI."""

from __future__ import annotations

from uuid import uuid4

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
from src.banco_preguntas.entities.resultado_paginado_preguntas import ResultadoPaginadoPreguntas
from src.banco_preguntas.interface_adapters.presenters.banco_presenter import (
    MateriaBasicaSalida,
    MateriaListItemSalida,
    MateriaSalida,
    OpcionSalida,
    PreguntaOpcionMultipleSalida,
    PreguntaVerdaderoFalsoSalida,
    presentar_materia_basica,
    presentar_materia_creada,
    presentar_materias,
    presentar_pregunta,
    presentar_preguntas_paginadas,
)

METADATOS = MetadatosPregunta(
    "¿Qué es CBO?", "U1", "Acoplamiento", Dificultad.MEDIO, Importancia.ALTO
)


def _opcion_multiple(banco_id):
    return PreguntaPlantillaOpcionMultiple.crear(
        banco_id=banco_id,
        metadatos=METADATOS,
        opciones=[Opcion("Acoplamiento entre clases", True), Opcion("Una clase base", False)],
    )


def test_presenta_una_materia_creada_una_basica_y_el_listado() -> None:
    materia = Materia.crear("Ingeniería de Software")
    banco = Banco.crear(materia.id)

    assert presentar_materia_creada(materia, banco) == MateriaSalida(
        materia.id, "Ingeniería de Software", banco.id
    )
    assert presentar_materia_basica(materia) == MateriaBasicaSalida(
        materia.id, "Ingeniería de Software", True
    )
    assert presentar_materias([(materia, banco, 7)]) == [
        MateriaListItemSalida(materia.id, "Ingeniería de Software", banco.id, 7, True)
    ]


def test_presenta_una_pregunta_de_opcion_multiple_con_sus_opciones() -> None:
    pregunta = _opcion_multiple(uuid4())

    salida = presentar_pregunta(pregunta)

    assert isinstance(salida, PreguntaOpcionMultipleSalida)
    assert salida.opciones == [
        OpcionSalida("Acoplamiento entre clases", True),
        OpcionSalida("Una clase base", False),
    ]
    assert salida.dificultad is Dificultad.MEDIO
    assert salida.activa is True


def test_presenta_una_pregunta_verdadero_falso() -> None:
    pregunta = PreguntaPlantillaVerdaderoFalso.crear(
        banco_id=uuid4(), metadatos=METADATOS, respuesta_correcta=True
    )

    salida = presentar_pregunta(pregunta)

    assert isinstance(salida, PreguntaVerdaderoFalsoSalida)
    assert salida.respuesta_correcta is True
    assert salida.id == pregunta.id


def test_presenta_una_pagina_con_los_dos_tipos_y_el_total() -> None:
    banco_id = uuid4()
    om = _opcion_multiple(banco_id)
    vf = PreguntaPlantillaVerdaderoFalso.crear(
        banco_id=banco_id, metadatos=METADATOS, respuesta_correcta=False
    )

    salida = presentar_preguntas_paginadas(ResultadoPaginadoPreguntas(preguntas=[om, vf], total=9))

    assert [type(p) for p in salida.preguntas] == [
        PreguntaOpcionMultipleSalida,
        PreguntaVerdaderoFalsoSalida,
    ]
    assert salida.total == 9
