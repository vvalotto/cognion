"""Presenters de Actividad Evaluativa (`US-12.2.4`, `ADR-031`): cada `presentar_*` arma su salida sin FastAPI."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
    EstadoSesionEnVivo,
)
from src.actividad_evaluativa.entities.evaluacion import PreguntaAsignada
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.entities.ports.actividad_query_port import ActividadResumen
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipanteResumen,
)
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    OpcionDistribuida,
    ParticipanteEnRanking,
)
from src.actividad_evaluativa.entities.ports.sesiones_en_vivo_query_port import SesionEnVivoResumen
from src.actividad_evaluativa.entities.revision_evaluacion import (
    DetallePreguntaRevision,
    RevisionEvaluacion,
)
from src.actividad_evaluativa.interface_adapters.presenters.actividad_presenter import (
    estado_de_actividad,
    presentar_actividad_resumen,
    presentar_actividades_resumen,
)
from src.actividad_evaluativa.interface_adapters.presenters.evaluacion_presenter import (
    presentar_revision,
)
from src.actividad_evaluativa.interface_adapters.presenters.sesion_en_vivo_presenter import (
    presentar_estado_sesion,
    presentar_participacion,
    presentar_participantes,
    presentar_ranking,
    presentar_sesion,
    presentar_sesiones_resumen,
)
from src.actividad_evaluativa.use_cases.obtener_estado_sesion import (
    EstadoSesion,
    PreguntaActualVista,
    ResultadoPregunta,
)

AHORA = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)


def _resumen(apertura: datetime, cierre: datetime, cerrada: bool = False) -> ActividadResumen:
    return ActividadResumen(
        id=uuid4(),
        materia_id=uuid4(),
        titulo="Parcial 1",
        fecha_apertura=apertura,
        fecha_cierre=cierre,
        cantidad_preguntas=10,
        cantidad_intentos_permitidos=1,
        cerrada_manualmente=cerrada,
        cantidad_evaluaciones_activas=2,
        cantidad_evaluaciones_finalizadas=5,
        comisiones_ids=frozenset({uuid4()}),
    )


def test_el_estado_de_una_actividad_se_deriva_de_las_fechas_y_del_cierre_manual() -> None:
    unas_horas = timedelta(hours=3)

    assert (
        estado_de_actividad(_resumen(AHORA - unas_horas, AHORA + unas_horas), AHORA) == "en_curso"
    )
    assert (
        estado_de_actividad(_resumen(AHORA + unas_horas, AHORA + 2 * unas_horas), AHORA)
        == "programada"
    )
    assert (
        estado_de_actividad(_resumen(AHORA - 2 * unas_horas, AHORA - unas_horas), AHORA)
        == "cerrada"
    )
    assert (
        estado_de_actividad(_resumen(AHORA - unas_horas, AHORA + unas_horas, cerrada=True), AHORA)
        == "cerrada"
    )


def test_presenta_el_resumen_con_estado_y_comisiones_como_lista() -> None:
    resumen = _resumen(AHORA - timedelta(hours=1), AHORA + timedelta(hours=1))

    salida = presentar_actividad_resumen(resumen, AHORA)

    assert salida.estado == "en_curso"
    assert salida.comisiones_ids == list(resumen.comisiones_ids)
    assert salida.cantidad_evaluaciones_finalizadas == 5
    assert [s.id for s in presentar_actividades_resumen([resumen], AHORA)] == [resumen.id]


def test_presenta_la_revision_con_su_detalle() -> None:
    pregunta_id, evaluacion_id = uuid4(), uuid4()
    revision = RevisionEvaluacion(
        evaluacion_id=evaluacion_id,
        cantidad_preguntas=1,
        cantidad_correctas=0,
        cantidad_incorrectas=1,
        detalle=[
            DetallePreguntaRevision(
                pregunta_id=pregunta_id,
                orden=0,
                texto="¿Qué es CBO?",
                respondida=True,
                contenido_propio={"opcion_indice": 1},
                es_correcta=False,
                contenido_correcto={"opcion_indice": 0},
                opciones=["Acoplamiento", "Cohesión"],
            )
        ],
    )

    salida = presentar_revision(revision)

    assert salida.cantidad_incorrectas == 1
    assert salida.detalle[0].contenido_correcto == {"opcion_indice": 0}
    assert salida.detalle[0].opciones == ["Acoplamiento", "Cohesión"]


def _sesion() -> ActividadEvaluativaEnVivo:
    preguntas = [PreguntaAsignada(pregunta_id=uuid4(), orden=i) for i in range(3)]
    return ActividadEvaluativaEnVivo.crear(uuid4(), uuid4(), preguntas, 30, "U1", "Capas")


def test_presenta_una_sesion_en_espera_sin_pregunta_actual() -> None:
    sesion = _sesion()

    salida = presentar_sesion(sesion)

    assert salida.estado == EstadoSesionEnVivo.EN_ESPERA.value
    assert salida.cantidad_preguntas == 3
    assert salida.pregunta_actual_indice is None
    assert (salida.unidad_tematica, salida.tema) == ("U1", "Capas")


def test_presenta_el_estado_con_pregunta_y_resultado() -> None:
    sesion = _sesion()
    estudiante_id = uuid4()
    pregunta = PreguntaActualVista(
        pregunta_id=uuid4(),
        enunciado="¿Qué es CBO?",
        tipo="opcion_multiple",
        opciones=["A", "B"],
        respuesta_correcta={
            "contenido": {"opcion_indice": 0},
            "texto": "A",
            "opciones": ["A", "B"],
        },
    )
    resultado = ResultadoPregunta(
        distribucion=[OpcionDistribuida("A", 4)],
        ranking=[ParticipanteEnRanking(1, estudiante_id, 3000, "Ana")],
    )
    estado = EstadoSesion(
        sesion=sesion,
        pregunta_actual=pregunta,
        ya_respondio=True,
        puntaje_acumulado=3000,
        total_participantes=8,
        cantidad_respuestas=4,
        resultado_pregunta=resultado,
    )

    salida = presentar_estado_sesion(estado)

    assert salida.pregunta_actual is not None
    assert salida.pregunta_actual.respuesta_correcta is not None
    assert salida.pregunta_actual.respuesta_correcta.texto == "A"
    assert salida.resultado_pregunta is not None
    assert salida.resultado_pregunta.distribucion[0].cantidad == 4
    assert salida.resultado_pregunta.ranking[0].nombre == "Ana"
    assert (salida.ya_respondio, salida.total_participantes) == (True, 8)


def test_el_estado_sin_pregunta_ni_resultado_los_deja_en_none() -> None:
    estado = EstadoSesion(
        sesion=_sesion(),
        pregunta_actual=None,
        ya_respondio=None,
        puntaje_acumulado=None,
        total_participantes=0,
        cantidad_respuestas=0,
        resultado_pregunta=None,
    )

    salida = presentar_estado_sesion(estado)

    assert salida.pregunta_actual is None
    assert salida.resultado_pregunta is None


def test_presenta_participacion_participantes_ranking_y_listado() -> None:
    sesion_id, estudiante_id = uuid4(), uuid4()
    participacion = ParticipacionEnVivo(
        id=uuid4(), sesion_id=sesion_id, estudiante_id=estudiante_id
    )
    resumen = SesionEnVivoResumen(
        id=sesion_id,
        comision_id=uuid4(),
        materia_id=uuid4(),
        cantidad_preguntas=5,
        tiempo_limite_por_pregunta_segundos=20,
        estado=EstadoSesionEnVivo.EN_CURSO,
        creada_en=AHORA,
        materia_nombre="ISW",
    )

    assert presentar_participacion(participacion).estudiante_id == estudiante_id
    assert (
        presentar_participantes([ParticipanteResumen(estudiante_id, AHORA, "Ana")])[0].nombre
        == "Ana"
    )
    assert (
        presentar_ranking([ParticipanteEnRanking(2, estudiante_id, 1500, "Ana")])[0].posicion == 2
    )
    listado = presentar_sesiones_resumen([resumen])
    assert (listado[0].estado, listado[0].materia_nombre) == (
        EstadoSesionEnVivo.EN_CURSO.value,
        "ISW",
    )
