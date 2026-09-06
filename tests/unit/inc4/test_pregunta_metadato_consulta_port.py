"""Tests unitarios del puerto y DTO de `PreguntaMetadatoConsultaPort` (US-4.2.3)."""

import pytest

from src.analytics.entities.ports.pregunta_metadato_consulta_port import (
    MetadatoPreguntaResumen,
    PreguntaMetadatoConsultaPort,
)


class TestMetadatoPreguntaResumen:
    def test_es_inmutable(self):
        metadato = MetadatoPreguntaResumen(unidad_tematica="Unidad 1", tema="Herencia")

        with pytest.raises(AttributeError):
            metadato.tema = "Polimorfismo"  # type: ignore[misc]

    def test_conserva_los_valores_recibidos(self):
        metadato = MetadatoPreguntaResumen(unidad_tematica="Unidad 2", tema="Acoplamiento")

        assert metadato.unidad_tematica == "Unidad 2"
        assert metadato.tema == "Acoplamiento"


class TestPreguntaMetadatoConsultaPort:
    def test_es_abstracto_no_instanciable(self):
        with pytest.raises(TypeError):
            PreguntaMetadatoConsultaPort()  # type: ignore[abstract]
