from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.identidad.entities.errors import JWTExpirado, JWTInvalido
from src.identidad.entities.jwt import JWTPayload
from src.identidad.entities.usuario import TipoPerfil
from src.identidad.interface_adapters.security.get_current_user import build_get_current_user
from tests.unit.inc1._fakes import FakeJWTIssuer


class TestGetCurrentUser:
    async def test_token_valido_resuelve_payload(self):
        payload = JWTPayload(usuario_id=uuid4(), rol=TipoPerfil.DOCENTE)
        fake_issuer = FakeJWTIssuer()
        fake_issuer.payload_a_devolver = payload
        get_current_user = build_get_current_user(fake_issuer)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-valido")

        resultado = await get_current_user(credentials)

        assert resultado == payload

    async def test_sin_header_authorization_responde_401(self):
        fake_issuer = FakeJWTIssuer()
        get_current_user = build_get_current_user(fake_issuer)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None)

        assert exc_info.value.status_code == 401

    async def test_token_invalido_responde_401(self):
        fake_issuer = FakeJWTIssuer()
        fake_issuer.excepcion_a_levantar = JWTInvalido()
        get_current_user = build_get_current_user(fake_issuer)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-malo")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401

    async def test_token_expirado_responde_401(self):
        fake_issuer = FakeJWTIssuer()
        fake_issuer.excepcion_a_levantar = JWTExpirado()
        get_current_user = build_get_current_user(fake_issuer)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-expirado")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
