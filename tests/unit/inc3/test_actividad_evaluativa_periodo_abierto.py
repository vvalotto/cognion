from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.errors import (
    ActividadYaCerrada,
    CantidadIntentosInvalida,
    NoSePuedeAcortarConEvaluacionesActivas,
    PeriodoInvalido,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado


def _fechas() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura, cierre


class TestActividadEvaluativaPeriodoAbiertoCrear:
    def test_crea_actividad_valida(self):
        materia_id = uuid4()
        apertura, cierre = _fechas()

        actividad = ActividadEvaluativaPeriodoAbierto.crear(
            materia_id=materia_id,
            fecha_apertura=apertura,
            fecha_cierre=cierre,
            cantidad_preguntas=10,
            cantidad_intentos_permitidos=1,
        )

        assert actividad.materia_id == materia_id
        assert actividad.fecha_apertura == apertura
        assert actividad.fecha_cierre == cierre
        assert actividad.cantidad_preguntas == 10
        assert actividad.cantidad_intentos_permitidos == 1
        assert actividad.cerrada_manualmente is False
        assert actividad.id is not None

    def test_genera_id_distinto_por_actividad(self):
        apertura, cierre = _fechas()

        actividad_1 = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)
        actividad_2 = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)

        assert actividad_1.id != actividad_2.id

    def test_rechaza_apertura_igual_a_cierre(self):
        apertura, _ = _fechas()

        with pytest.raises(PeriodoInvalido):
            ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, apertura, 10, 1)

    def test_rechaza_apertura_posterior_a_cierre(self):
        apertura, cierre = _fechas()

        with pytest.raises(PeriodoInvalido):
            ActividadEvaluativaPeriodoAbierto.crear(uuid4(), cierre, apertura, 10, 1)

    def test_rechaza_cantidad_intentos_cero(self):
        apertura, cierre = _fechas()

        with pytest.raises(CantidadIntentosInvalida):
            ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 0)

    def test_rechaza_cantidad_intentos_negativa(self):
        apertura, cierre = _fechas()

        with pytest.raises(CantidadIntentosInvalida):
            ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, -1)

    def test_acepta_cantidad_intentos_mayor_a_uno(self):
        apertura, cierre = _fechas()

        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 3)

        assert actividad.cantidad_intentos_permitidos == 3


def _evento_creada(actividad: ActividadEvaluativaPeriodoAbierto) -> EventoAlmacenado:
    return EventoAlmacenado(
        sequence_number=1,
        event_type="ActividadEvaluativaCreada",
        payload={
            "actividad_id": str(actividad.id),
            "materia_id": str(actividad.materia_id),
            "fecha_apertura": actividad.fecha_apertura.isoformat(),
            "fecha_cierre": actividad.fecha_cierre.isoformat(),
            "cantidad_preguntas": actividad.cantidad_preguntas,
            "cantidad_intentos_permitidos": actividad.cantidad_intentos_permitidos,
            "ocurrido_en": "2026-01-01T00:00:00+00:00",
        },
        occurred_at=datetime.now(UTC),
    )


def _evento_modificado(actividad_id, nueva_fecha_cierre: datetime) -> EventoAlmacenado:
    return EventoAlmacenado(
        sequence_number=2,
        event_type="PeriodoDisponibilidadModificado",
        payload={
            "actividad_id": str(actividad_id),
            "nueva_fecha_cierre": nueva_fecha_cierre.isoformat(),
            "ocurrido_en": "2026-01-02T00:00:00+00:00",
        },
        occurred_at=datetime.now(UTC),
    )


def _evento_cerrada(actividad_id, sequence_number: int = 2) -> EventoAlmacenado:
    return EventoAlmacenado(
        sequence_number=sequence_number,
        event_type="ActividadEvaluativaCerrada",
        payload={
            "actividad_id": str(actividad_id),
            "ocurrido_en": "2026-01-02T00:00:00+00:00",
        },
        occurred_at=datetime.now(UTC),
    )


class TestActividadEvaluativaPeriodoAbiertoReconstruir:
    def test_reconstruye_desde_un_unico_evento(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)

        reconstruida = ActividadEvaluativaPeriodoAbierto.reconstruir([_evento_creada(actividad)])

        assert reconstruida.id == actividad.id
        assert reconstruida.fecha_cierre == cierre
        assert reconstruida.cerrada_manualmente is False

    def test_reconstruye_aplicando_periodo_disponibilidad_modificado(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)
        nueva_fecha_cierre = cierre + timedelta(days=3)

        reconstruida = ActividadEvaluativaPeriodoAbierto.reconstruir(
            [_evento_creada(actividad), _evento_modificado(actividad.id, nueva_fecha_cierre)]
        )

        assert reconstruida.fecha_cierre == nueva_fecha_cierre
        assert reconstruida.fecha_apertura == apertura

    def test_reconstruye_aplicando_actividad_evaluativa_cerrada(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)

        reconstruida = ActividadEvaluativaPeriodoAbierto.reconstruir(
            [_evento_creada(actividad), _evento_cerrada(actividad.id)]
        )

        assert reconstruida.cerrada_manualmente is True
        assert reconstruida.fecha_cierre == cierre


class TestActividadEvaluativaPeriodoAbiertoValidarParaModificarPeriodo:
    def test_extender_siempre_se_permite_con_evaluaciones_activas(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)

        actividad.validar_para_modificar_periodo(
            cierre + timedelta(days=1), hay_evaluaciones_activas=True
        )

    def test_acortar_sin_evaluaciones_activas_se_permite(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)

        actividad.validar_para_modificar_periodo(
            cierre - timedelta(hours=1), hay_evaluaciones_activas=False
        )

    def test_acortar_con_evaluaciones_activas_se_rechaza(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)

        with pytest.raises(NoSePuedeAcortarConEvaluacionesActivas):
            actividad.validar_para_modificar_periodo(
                cierre - timedelta(hours=1), hay_evaluaciones_activas=True
            )

    def test_nueva_fecha_anterior_a_apertura_se_rechaza(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)

        with pytest.raises(PeriodoInvalido):
            actividad.validar_para_modificar_periodo(
                apertura - timedelta(hours=1), hay_evaluaciones_activas=False
            )

    def test_actividad_cerrada_manualmente_se_rechaza(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)
        actividad.cerrada_manualmente = True

        with pytest.raises(ActividadYaCerrada):
            actividad.validar_para_modificar_periodo(
                cierre + timedelta(days=1), hay_evaluaciones_activas=False
            )


class TestActividadEvaluativaPeriodoAbiertoValidarParaCerrar:
    def test_actividad_vigente_se_permite_cerrar(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)

        actividad.validar_para_cerrar()

    def test_actividad_ya_cerrada_se_rechaza(self):
        apertura, cierre = _fechas()
        actividad = ActividadEvaluativaPeriodoAbierto.crear(uuid4(), apertura, cierre, 10, 1)
        actividad.cerrada_manualmente = True

        with pytest.raises(ActividadYaCerrada):
            actividad.validar_para_cerrar()
