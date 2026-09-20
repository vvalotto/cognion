"""Tests unitarios de `calcular_puntaje` y `NivelesDePregunta` (US-6.2.1, RF-10)."""

import pytest

from src.actividad_evaluativa.entities.puntaje_en_vivo import (
    NivelesDePregunta,
    NivelPregunta,
    calcular_puntaje,
)

BAJO, MEDIO, ALTO = NivelPregunta.BAJO, NivelPregunta.MEDIO, NivelPregunta.ALTO


class TestCalcularPuntajeCorrecta:
    @pytest.mark.parametrize(
        ("tiempo", "dificultad", "importancia", "esperado"),
        [
            (0, ALTO, ALTO, 4000),
            (30, BAJO, BAJO, 500),
            (15, MEDIO, BAJO, 1125),
            (0, BAJO, BAJO, 1000),
            (0, MEDIO, MEDIO, 2250),
            (15, ALTO, MEDIO, 2250),
        ],
    )
    def test_aplica_la_formula_del_spike(self, tiempo, dificultad, importancia, esperado):
        assert calcular_puntaje(True, tiempo, 30, dificultad, importancia) == esperado

    def test_devuelve_un_entero(self):
        assert isinstance(calcular_puntaje(True, 7, 30, MEDIO, ALTO), int)

    def test_redondea_una_sola_vez_al_final(self):
        # 1000 × (0.5 + 0.5 × (1 − 1/3)) = 833.33… → 833
        assert calcular_puntaje(True, 1, 3, BAJO, BAJO) == 833

    def test_mas_rapido_nunca_puntua_menos(self):
        puntajes = [calcular_puntaje(True, t, 30, MEDIO, MEDIO) for t in range(31)]

        assert puntajes == sorted(puntajes, reverse=True)


class TestCalcularPuntajeBordes:
    def test_incorrecta_vale_cero_sin_importar_tiempo_ni_niveles(self):
        assert calcular_puntaje(False, 0, 30, ALTO, ALTO) == 0
        assert calcular_puntaje(False, 15, 30, BAJO, BAJO) == 0

    def test_tiempo_mayor_al_limite_se_acota_al_limite(self):
        assert calcular_puntaje(True, 99, 30, MEDIO, MEDIO) == calcular_puntaje(
            True, 30, 30, MEDIO, MEDIO
        )
        assert calcular_puntaje(True, 99, 30, BAJO, BAJO) == 500

    def test_tiempo_negativo_se_toma_como_cero(self):
        assert calcular_puntaje(True, -5, 30, ALTO, ALTO) == 4000

    @pytest.mark.parametrize("limite", [0, -1, -30.5])
    def test_limite_no_positivo_lanza_value_error(self, limite):
        with pytest.raises(ValueError):
            calcular_puntaje(True, 0, limite, BAJO, BAJO)

    def test_limite_no_positivo_lanza_aun_si_es_incorrecta(self):
        with pytest.raises(ValueError):
            calcular_puntaje(False, 0, 0, BAJO, BAJO)


class TestNivelesDePregunta:
    def test_es_inmutable_y_comparable_por_valor(self):
        niveles = NivelesDePregunta(ALTO, MEDIO)

        assert niveles == NivelesDePregunta(ALTO, MEDIO)
        with pytest.raises(AttributeError):
            niveles.dificultad = BAJO  # type: ignore[misc]
