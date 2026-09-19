"""Tests unitarios de `ParticipacionEnVivo`, `EstudianteUnido` y los errores de US-6.1.3."""

from datetime import UTC, datetime
from uuid import uuid4

from src.actividad_evaluativa.entities.errors import SesionNoExiste, SesionYaFinalizada
from src.actividad_evaluativa.entities.eventos_en_vivo import EstudianteUnido
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado


class TestIdPara:
    def test_es_determinístico_para_el_mismo_par(self):
        sesion_id, estudiante_id = uuid4(), uuid4()

        assert ParticipacionEnVivo.id_para(sesion_id, estudiante_id) == ParticipacionEnVivo.id_para(
            sesion_id, estudiante_id
        )

    def test_difiere_si_cambia_el_estudiante_o_la_sesion(self):
        sesion_id, estudiante_id = uuid4(), uuid4()
        base = ParticipacionEnVivo.id_para(sesion_id, estudiante_id)

        assert ParticipacionEnVivo.id_para(sesion_id, uuid4()) != base
        assert ParticipacionEnVivo.id_para(uuid4(), estudiante_id) != base

    def test_no_colisiona_con_el_par_invertido(self):
        a, b = uuid4(), uuid4()

        assert ParticipacionEnVivo.id_para(a, b) != ParticipacionEnVivo.id_para(b, a)


class TestUnirse:
    def test_crea_participacion_sin_respuestas(self):
        sesion_id, estudiante_id = uuid4(), uuid4()

        participacion = ParticipacionEnVivo.unirse(sesion_id, estudiante_id)

        assert participacion.id == ParticipacionEnVivo.id_para(sesion_id, estudiante_id)
        assert participacion.sesion_id == sesion_id
        assert participacion.estudiante_id == estudiante_id
        assert participacion.respuestas == []
        assert participacion.unido_en.tzinfo is not None


class TestReconstruir:
    def test_reconstruye_desde_el_evento_estudiante_unido(self):
        sesion_id, estudiante_id = uuid4(), uuid4()
        unido_en = datetime(2026, 9, 19, 10, 30, tzinfo=UTC)
        evento = EventoAlmacenado(
            sequence_number=1,
            event_type="EstudianteUnido",
            payload={
                "sesion_id": str(sesion_id),
                "estudiante_id": str(estudiante_id),
                "unido_en": unido_en.isoformat(),
            },
            occurred_at=unido_en,
        )

        participacion = ParticipacionEnVivo.reconstruir([evento])

        assert participacion.id == ParticipacionEnVivo.id_para(sesion_id, estudiante_id)
        assert participacion.sesion_id == sesion_id
        assert participacion.estudiante_id == estudiante_id
        assert participacion.unido_en == unido_en


class TestEstudianteUnido:
    def test_desde_participacion_copia_los_campos(self):
        participacion = ParticipacionEnVivo.unirse(uuid4(), uuid4())

        evento = EstudianteUnido.desde_participacion(participacion)

        assert evento.sesion_id == participacion.sesion_id
        assert evento.estudiante_id == participacion.estudiante_id
        assert evento.unido_en == participacion.unido_en


class TestErrores:
    def test_sesion_no_existe_guarda_el_id_y_arma_mensaje(self):
        sesion_id = uuid4()

        error = SesionNoExiste(sesion_id)

        assert error.sesion_id == sesion_id
        assert str(sesion_id) in str(error)

    def test_sesion_ya_finalizada_guarda_el_id_y_arma_mensaje(self):
        sesion_id = uuid4()

        error = SesionYaFinalizada(sesion_id)

        assert error.sesion_id == sesion_id
        assert "finalizada" in str(error)
