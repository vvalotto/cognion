"""Tests unitarios de las funciones puras del adapter in-process (US-ADJ-56).

Sin sesión de BD — mismo criterio que
`tests/unit/inc4/test_evaluacion_desempeno_consulta_port_in_process.py`: `EventoModel` y
`RankingPorSesionModel` se instancian directamente en memoria, sin persistir.
"""

from datetime import UTC, datetime
from uuid import uuid4

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado
from src.actividad_evaluativa.frameworks.db.models import EventoModel, RankingPorSesionModel
from src.analytics.frameworks.adapters.sesion_en_vivo_desempeno_consulta_port_in_process import (
    _resumen_de_participacion,
    _resumenes,
    _SesionFinalizada,
    _streams_de_estudiante,
)


def _evento(
    aggregate_id, event_type: str, payload: dict, sequence_number: int, occurred_at=None
) -> EventoModel:
    return EventoModel(
        aggregate_type="ParticipacionEnVivo",
        aggregate_id=aggregate_id,
        sequence_number=sequence_number,
        event_type=event_type,
        payload=payload,
        occurred_at=occurred_at or datetime(2026, 1, 1, tzinfo=UTC),
    )


def _estudiante_unido(sesion_id, estudiante_id, sequence_number: int = 1) -> EventoModel:
    return _evento(
        uuid4(),
        "EstudianteUnido",
        {
            "sesion_id": str(sesion_id),
            "estudiante_id": str(estudiante_id),
            "unido_en": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
        },
        sequence_number,
    )


def _respuesta_en_vivo(
    pregunta_id, es_correcta: bool, puntaje: int, sequence_number: int
) -> EventoModel:
    return _evento(
        uuid4(),
        "RespuestaEnVivoRegistrada",
        {
            "pregunta_id": str(pregunta_id),
            "contenido": {"opcion_indice": 0},
            "es_correcta": es_correcta,
            "tiempo_respuesta_segundos": 4.2,
            "puntaje": puntaje,
        },
        sequence_number,
    )


def _sesion(comision_id, materia_id, cantidad_preguntas: int = 5) -> ActividadEvaluativaEnVivo:
    preguntas = [{"pregunta_id": str(uuid4()), "orden": i} for i in range(cantidad_preguntas)]
    payload = {
        "sesion_id": str(uuid4()),
        "comision_id": str(comision_id),
        "materia_id": str(materia_id),
        "preguntas": preguntas,
        "tiempo_limite_por_pregunta_segundos": 20,
    }
    return ActividadEvaluativaEnVivo.reconstruir(
        [
            EventoAlmacenado(
                sequence_number=1,
                event_type="SesionEnVivoCreada",
                payload=payload,
                occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        ]
    )


def _fila_ranking(sesion_id, estudiante_id, puntaje: int) -> RankingPorSesionModel:
    return RankingPorSesionModel(
        sesion_id=sesion_id,
        estudiante_id=estudiante_id,
        puntaje_acumulado=puntaje,
        ultima_actualizacion=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestStreamsDeEstudiante:
    def test_filtra_solo_los_streams_del_estudiante_indicado(self):
        estudiante_buscado, otro_estudiante = uuid4(), uuid4()
        sesion_id = uuid4()
        streams = [
            [_estudiante_unido(sesion_id, estudiante_buscado)],
            [_estudiante_unido(sesion_id, otro_estudiante)],
        ]

        resultado = _streams_de_estudiante(streams, estudiante_buscado)

        assert len(resultado) == 1
        assert resultado[0][0].payload["estudiante_id"] == str(estudiante_buscado)

    def test_sin_streams_del_estudiante_devuelve_lista_vacia(self):
        streams = [[_estudiante_unido(uuid4(), uuid4())]]

        resultado = _streams_de_estudiante(streams, uuid4())

        assert resultado == []


class TestResumenDeParticipacion:
    def test_se_unio_pero_no_respondio(self):
        sesion = _sesion(uuid4(), uuid4())
        estudiante_id = uuid4()
        eventos = [_estudiante_unido(sesion.id, estudiante_id)]
        sesion_finalizada = _SesionFinalizada(
            sesion=sesion, finalizada_en=datetime(2026, 1, 2, tzinfo=UTC)
        )
        ranking = [_fila_ranking(sesion.id, estudiante_id, 0)]

        resumen = _resumen_de_participacion(eventos, sesion_finalizada, ranking)

        assert resumen is not None
        assert resumen.cantidad_correctas == 0
        assert resumen.cantidad_incorrectas == 0
        assert resumen.puntaje_final == 0
        assert resumen.posicion == 1
        assert resumen.total_participantes == 1

    def test_cuenta_correctas_e_incorrectas_y_suma_el_puntaje(self):
        sesion = _sesion(uuid4(), uuid4())
        estudiante_id = uuid4()
        eventos = [
            _estudiante_unido(sesion.id, estudiante_id),
            _respuesta_en_vivo(uuid4(), True, 500, 2),
            _respuesta_en_vivo(uuid4(), False, 0, 3),
            _respuesta_en_vivo(uuid4(), True, 300, 4),
        ]
        sesion_finalizada = _SesionFinalizada(
            sesion=sesion, finalizada_en=datetime(2026, 1, 2, tzinfo=UTC)
        )
        ranking = [_fila_ranking(sesion.id, estudiante_id, 800)]

        resumen = _resumen_de_participacion(eventos, sesion_finalizada, ranking)

        assert resumen is not None
        assert resumen.cantidad_correctas == 2
        assert resumen.cantidad_incorrectas == 1
        assert resumen.puntaje_final == 800
        assert resumen.cantidad_preguntas == 5

    def test_sin_fila_de_ranking_devuelve_none(self):
        sesion = _sesion(uuid4(), uuid4())
        estudiante_id = uuid4()
        eventos = [_estudiante_unido(sesion.id, estudiante_id)]
        sesion_finalizada = _SesionFinalizada(
            sesion=sesion, finalizada_en=datetime(2026, 1, 2, tzinfo=UTC)
        )

        resumen = _resumen_de_participacion(eventos, sesion_finalizada, [])

        assert resumen is None

    def test_posicion_refleja_el_orden_ya_resuelto_del_ranking(self):
        sesion = _sesion(uuid4(), uuid4())
        estudiante_id, otro_estudiante = uuid4(), uuid4()
        eventos = [_estudiante_unido(sesion.id, estudiante_id)]
        sesion_finalizada = _SesionFinalizada(
            sesion=sesion, finalizada_en=datetime(2026, 1, 2, tzinfo=UTC)
        )
        # El ranking ya viene ordenado (responsabilidad de la query) — acá solo el 2° puesto.
        ranking = [
            _fila_ranking(sesion.id, otro_estudiante, 900),
            _fila_ranking(sesion.id, estudiante_id, 500),
        ]

        resumen = _resumen_de_participacion(eventos, sesion_finalizada, ranking)

        assert resumen is not None
        assert resumen.posicion == 2
        assert resumen.total_participantes == 2


class TestResumenes:
    def test_descarta_participaciones_de_sesiones_no_finalizadas(self):
        sesion_id_finalizada = uuid4()
        sesion_id_sin_finalizar = uuid4()
        estudiante_id = uuid4()
        sesion = _sesion(uuid4(), uuid4())
        participaciones = [
            [_estudiante_unido(sesion_id_finalizada, estudiante_id)],
            [_estudiante_unido(sesion_id_sin_finalizar, estudiante_id)],
        ]
        sesiones_finalizadas = {
            sesion_id_finalizada: _SesionFinalizada(
                sesion=sesion, finalizada_en=datetime(2026, 1, 2, tzinfo=UTC)
            )
        }
        ranking_por_sesion = {
            sesion_id_finalizada: [_fila_ranking(sesion_id_finalizada, estudiante_id, 100)]
        }

        resultado = _resumenes(participaciones, sesiones_finalizadas, ranking_por_sesion)

        assert len(resultado) == 1
        assert resultado[0].sesion_id == sesion.id

    def test_sin_participaciones_devuelve_lista_vacia(self):
        resultado = _resumenes([], {}, {})

        assert resultado == []
