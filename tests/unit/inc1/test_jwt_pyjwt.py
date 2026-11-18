from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt as pyjwt
import pytest

from src.settings import Settings, settings
from src.shared.entities.errors import JWTExpirado, JWTInvalido
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


class TestPyJWTIssuer:
    def test_emite_token_con_claim_rol(self):
        issuer = PyJWTIssuer()
        usuario_id = uuid4()

        jwt_vo = issuer.emitir(usuario_id, TipoPerfil.DOCENTE)

        payload = pyjwt.decode(jwt_vo.token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["rol"] == "docente"
        assert payload["sub"] == str(usuario_id)
        assert jwt_vo.rol == TipoPerfil.DOCENTE

    def test_el_vencimiento_por_defecto_es_una_jornada(self, monkeypatch):
        """8 horas (US-12.1.3, AQ-04): con 60 minutos la sesión se cerraba en mitad de la clase.

        Se ignoran el `.env` y la variable de entorno: lo que se fija es el valor por defecto del código.
        """
        monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)

        sin_entorno = Settings(_env_file=None, database_url="x", secret_key="x")

        assert sin_entorno.access_token_expire_minutes == 480

    def test_respeta_el_vencimiento_configurado(self, monkeypatch):
        monkeypatch.setattr(settings, "access_token_expire_minutes", 5)
        antes = datetime.now(UTC)

        jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.ESTUDIANTE)

        delta_minutos = (jwt_vo.expira_en - antes).total_seconds() / 60
        assert 4.0 <= delta_minutos <= 6.0

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
