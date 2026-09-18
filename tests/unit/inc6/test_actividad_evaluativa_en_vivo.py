"""Tests unitarios del aggregate `ActividadEvaluativaEnVivo` y su evento (US-6.1.2)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
    EstadoSesionEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ComisionNoExiste,
    TiempoLimiteInvalido,
)
from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.eventos_en_vivo import SesionEnVivoCreada


def _preguntas(cantidad: int = 3):
    return Evaluacion.armar_preguntas_asignadas([uuid4() for _ in range(cantidad)])


class TestCrear:
    def test_crea_en_espera_sin_pregunta_actual(self):
        comision_id, materia_id = uuid4(), uuid4()
        preguntas = _preguntas()

        sesion = ActividadEvaluativaEnVivo.crear(comision_id, materia_id, preguntas, 30)

        assert sesion.comision_id == comision_id
        assert sesion.materia_id == materia_id
        assert sesion.preguntas == preguntas
        assert sesion.tiempo_limite_por_pregunta_segundos == 30
        assert sesion.estado == EstadoSesionEnVivo.EN_ESPERA
        assert sesion.pregunta_actual_indice is None
        assert sesion.opciones_mostradas is False
        assert sesion.pregunta_actual_cerrada is False

    def test_unidad_y_tema_vacios_se_normalizan_a_none(self):
        sesion = ActividadEvaluativaEnVivo.crear(
            uuid4(), uuid4(), _preguntas(), 30, unidad_tematica="", tema=""
        )

        assert sesion.unidad_tematica is None
        assert sesion.tema is None

    def test_conserva_unidad_y_tema(self):
        sesion = ActividadEvaluativaEnVivo.crear(
            uuid4(), uuid4(), _preguntas(), 30, unidad_tematica="U1", tema="T1"
        )

        assert sesion.unidad_tematica == "U1"
        assert sesion.tema == "T1"

    @pytest.mark.parametrize("tiempo", [0, -5])
    def test_rechaza_tiempo_limite_no_positivo(self, tiempo):
        with pytest.raises(TiempoLimiteInvalido):
            ActividadEvaluativaEnVivo.crear(uuid4(), uuid4(), _preguntas(), tiempo)

    def test_cada_sesion_tiene_id_propio(self):
        a = ActividadEvaluativaEnVivo.crear(uuid4(), uuid4(), _preguntas(), 30)
        b = ActividadEvaluativaEnVivo.crear(uuid4(), uuid4(), _preguntas(), 30)

        assert a.id != b.id


class TestSesionEnVivoCreada:
    def test_desde_sesion_copia_los_campos(self):
        sesion = ActividadEvaluativaEnVivo.crear(
            uuid4(), uuid4(), _preguntas(), 45, unidad_tematica="U1", tema="T1"
        )

        evento = SesionEnVivoCreada.desde_sesion(sesion)

        assert evento.sesion_id == sesion.id
        assert evento.comision_id == sesion.comision_id
        assert evento.materia_id == sesion.materia_id
        assert evento.preguntas == sesion.preguntas
        assert evento.tiempo_limite_por_pregunta_segundos == 45
        assert evento.unidad_tematica == "U1"
        assert evento.tema == "T1"


class TestErrores:
    def test_tiempo_limite_invalido_guarda_el_valor_y_arma_mensaje(self):
        error = TiempoLimiteInvalido(0)

        assert error.tiempo_limite_segundos == 0
        assert "0" in str(error)

    def test_comision_no_existe_guarda_el_id_y_arma_mensaje(self):
        comision_id = uuid4()

        error = ComisionNoExiste(comision_id)

        assert error.comision_id == comision_id
        assert str(comision_id) in str(error)
