import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.identidad.entities.errors import InvitacionVencida, InvitacionYaUsada
from src.identidad.entities.invitacion import Invitacion


class TestInvitacionCrear:
    def test_crea_con_token_unico_y_sin_usar(self):
        comision_id = uuid.uuid4()
        docente_id = uuid.uuid4()

        invitacion = Invitacion.crear(comision_id, docente_id)

        assert invitacion.comision_id == comision_id
        assert invitacion.docente_id == docente_id
        assert invitacion.token
        assert invitacion.usada_en is None

    def test_expira_en_7_dias_desde_generacion(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())

        assert invitacion.expira_en - invitacion.generada_en == timedelta(days=7)

    def test_tokens_de_invitaciones_distintas_son_unicos(self):
        comision_id = uuid.uuid4()
        docente_id = uuid.uuid4()

        primera = Invitacion.crear(comision_id, docente_id)
        segunda = Invitacion.crear(comision_id, docente_id)

        assert primera.token != segunda.token
        assert primera.id != segunda.id


class TestInvitacionEsVigente:
    def test_vigente_si_no_vencida_y_no_usada(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())

        assert invitacion.es_vigente(datetime.now(UTC)) is True

    def test_no_vigente_si_vencida(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())

        assert invitacion.es_vigente(invitacion.expira_en + timedelta(seconds=1)) is False

    def test_no_vigente_si_ya_usada(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        invitacion.aceptar(datetime.now(UTC))

        assert invitacion.es_vigente(datetime.now(UTC)) is False


class TestInvitacionAceptar:
    def test_marca_usada_en_al_instante_dado(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        ahora = datetime.now(UTC)

        invitacion.aceptar(ahora)

        assert invitacion.usada_en == ahora

    def test_rechaza_aceptar_invitacion_vencida(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())

        with pytest.raises(InvitacionVencida):
            invitacion.aceptar(invitacion.expira_en + timedelta(seconds=1))

    def test_rechaza_aceptar_invitacion_ya_usada(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        invitacion.aceptar(datetime.now(UTC))

        with pytest.raises(InvitacionYaUsada):
            invitacion.aceptar(datetime.now(UTC))


class TestInvitacionVerificarVigente:
    def test_no_lanza_si_es_vigente(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())

        invitacion.verificar_vigente(datetime.now(UTC))

    def test_lanza_invitacion_vencida_si_expiro(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())

        with pytest.raises(InvitacionVencida):
            invitacion.verificar_vigente(invitacion.expira_en + timedelta(seconds=1))

    def test_lanza_invitacion_ya_usada_si_usada_en_no_es_null(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        invitacion.aceptar(datetime.now(UTC))

        with pytest.raises(InvitacionYaUsada):
            invitacion.verificar_vigente(datetime.now(UTC))

    def test_prioriza_ya_usada_sobre_vencida(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        invitacion.aceptar(datetime.now(UTC))
        invitacion.expira_en = datetime.now(UTC) - timedelta(days=1)

        with pytest.raises(InvitacionYaUsada):
            invitacion.verificar_vigente(datetime.now(UTC))
