from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt as pyjwt
import pytest

from src.identidad.entities.errors import JWTExpirado, JWTInvalido
from src.identidad.entities.usuario import TipoPerfil
from src.identidad.frameworks.security.jwt_pyjwt import PyJWTIssuer
from src.settings import settings


class TestPyJWTIssuer:
    def test_emite_token_con_claim_rol(self):
        issuer = PyJWTIssuer()
        usuario_id = uuid4()

        jwt_vo = issuer.emitir(usuario_id, TipoPerfil.DOCENTE)

        payload = pyjwt.decode(jwt_vo.token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["rol"] == "docente"
        assert payload["sub"] == str(usuario_id)
        assert jwt_vo.rol == TipoPerfil.DOCENTE

    def test_expira_60_minutos_despues_de_la_emision(self):
        issuer = PyJWTIssuer()
        antes = datetime.now(UTC)

        jwt_vo = issuer.emitir(uuid4(), TipoPerfil.ESTUDIANTE)

        delta_minutos = (jwt_vo.expira_en - antes).total_seconds() / 60
        assert 59.0 <= delta_minutos <= 61.0

    def test_emite_rol_distinto_por_cada_tipo_de_perfil(self):
        issuer = PyJWTIssuer()

        for tipo_perfil in TipoPerfil:
            jwt_vo = issuer.emitir(uuid4(), tipo_perfil)
            payload = pyjwt.decode(
                jwt_vo.token, settings.secret_key, algorithms=[settings.algorithm]
            )
            assert payload["rol"] == tipo_perfil.value


class TestPyJWTIssuerVerificar:
    def test_verifica_token_valido_y_resuelve_payload(self):
        issuer = PyJWTIssuer()
        usuario_id = uuid4()
        jwt_vo = issuer.emitir(usuario_id, TipoPerfil.ADMINISTRADOR)

        payload = issuer.verificar(jwt_vo.token)

        assert payload.usuario_id == usuario_id
        assert payload.rol == TipoPerfil.ADMINISTRADOR

    def test_token_expirado_levanta_jwtexpirado(self):
        issuer = PyJWTIssuer()
        payload = {
            "sub": str(uuid4()),
            "rol": TipoPerfil.DOCENTE.value,
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        }
        token = pyjwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

        with pytest.raises(JWTExpirado):
            issuer.verificar(token)

    def test_token_con_firma_invalida_levanta_jwtinvalido(self):
        issuer = PyJWTIssuer()
        payload = {
            "sub": str(uuid4()),
            "rol": TipoPerfil.DOCENTE.value,
            "exp": datetime.now(UTC) + timedelta(minutes=60),
        }
        token = pyjwt.encode(payload, "otra-clave-distinta", algorithm=settings.algorithm)

        with pytest.raises(JWTInvalido):
            issuer.verificar(token)

    def test_token_malformado_levanta_jwtinvalido(self):
        issuer = PyJWTIssuer()

        with pytest.raises(JWTInvalido):
            issuer.verificar("esto-no-es-un-jwt")

    def test_token_sin_claim_rol_levanta_jwtinvalido(self):
        issuer = PyJWTIssuer()
        payload = {
            "sub": str(uuid4()),
            "exp": datetime.now(UTC) + timedelta(minutes=60),
        }
        token = pyjwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

        with pytest.raises(JWTInvalido):
            issuer.verificar(token)
