import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.identidad.entities.errors import TokenRecuperacionVencido, TokenRecuperacionYaUsado
from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword


class TestTokenRecuperacionPasswordCrear:
    def test_crea_con_token_unico_y_sin_usar(self):
        usuario_id = uuid.uuid4()

        token = TokenRecuperacionPassword.crear(usuario_id)

        assert token.usuario_id == usuario_id
        assert token.token
        assert token.usado_en is None

    def test_expira_en_1_hora_desde_generacion(self):
        token = TokenRecuperacionPassword.crear(uuid.uuid4())

        assert token.expira_en - token.generado_en == timedelta(hours=1)

    def test_tokens_de_usuarios_distintos_son_unicos(self):
        usuario_id = uuid.uuid4()

        primero = TokenRecuperacionPassword.crear(usuario_id)
        segundo = TokenRecuperacionPassword.crear(usuario_id)

        assert primero.token != segundo.token
        assert primero.id != segundo.id


class TestTokenRecuperacionPasswordInvalidar:
    def test_marca_usado_en_al_instante_dado(self):
        token = TokenRecuperacionPassword.crear(uuid.uuid4())
        ahora = datetime.now(UTC)

        token.invalidar(ahora)

        assert token.usado_en == ahora

    def test_invalidar_sobre_token_ya_usado_reemplaza_el_instante(self):
        token = TokenRecuperacionPassword.crear(uuid.uuid4())
        primer_instante = datetime.now(UTC)
        token.invalidar(primer_instante)

        segundo_instante = primer_instante + timedelta(minutes=1)
        token.invalidar(segundo_instante)

        assert token.usado_en == segundo_instante


class TestTokenRecuperacionPasswordVerificarVigente:
    def test_no_lanza_nada_si_el_token_es_vigente(self):
        token = TokenRecuperacionPassword.crear(uuid.uuid4())

        token.verificar_vigente(token.generado_en)

    def test_lanza_ya_usado_si_usado_en_no_es_null(self):
        token = TokenRecuperacionPassword.crear(uuid.uuid4())
        token.invalidar(datetime.now(UTC))

        with pytest.raises(TokenRecuperacionYaUsado):
            token.verificar_vigente(datetime.now(UTC))

    def test_lanza_vencido_si_ahora_es_posterior_a_expira_en(self):
        token = TokenRecuperacionPassword.crear(uuid.uuid4())

        with pytest.raises(TokenRecuperacionVencido):
            token.verificar_vigente(token.expira_en + timedelta(seconds=1))

    def test_lanza_vencido_si_ahora_es_exactamente_expira_en(self):
        token = TokenRecuperacionPassword.crear(uuid.uuid4())

        with pytest.raises(TokenRecuperacionVencido):
            token.verificar_vigente(token.expira_en)

    def test_ya_usado_tiene_prioridad_sobre_vencido(self):
        token = TokenRecuperacionPassword.crear(uuid.uuid4())
        token.invalidar(datetime.now(UTC))

        with pytest.raises(TokenRecuperacionYaUsado):
            token.verificar_vigente(token.expira_en + timedelta(seconds=1))
