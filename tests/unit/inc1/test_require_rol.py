from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.identidad.entities.jwt import JWTPayload
from src.identidad.entities.usuario import TipoPerfil
from src.identidad.interface_adapters.security.require_rol import require_rol


async def _dummy_get_current_user() -> JWTPayload:
    raise AssertionError("no debería invocarse — el test pasa el usuario explícitamente")


class TestRequireRol:
    async def test_rol_permitido_devuelve_el_usuario(self):
        payload = JWTPayload(usuario_id=uuid4(), rol=TipoPerfil.ADMINISTRADOR)
        dependency = require_rol([TipoPerfil.ADMINISTRADOR], _dummy_get_current_user)

        resultado = await dependency(payload)

        assert resultado == payload

    async def test_rol_entre_varios_permitidos_devuelve_el_usuario(self):
        payload = JWTPayload(usuario_id=uuid4(), rol=TipoPerfil.DOCENTE)
        dependency = require_rol(
            [TipoPerfil.ADMINISTRADOR, TipoPerfil.DOCENTE], _dummy_get_current_user
        )

        resultado = await dependency(payload)

        assert resultado == payload

    async def test_rol_no_permitido_responde_403(self):
        payload = JWTPayload(usuario_id=uuid4(), rol=TipoPerfil.ESTUDIANTE)
        dependency = require_rol([TipoPerfil.ADMINISTRADOR], _dummy_get_current_user)

        with pytest.raises(HTTPException) as exc_info:
            await dependency(payload)

        assert exc_info.value.status_code == 403

    async def test_docente_rechazado_en_administracion_de_cuentas(self):
        payload = JWTPayload(usuario_id=uuid4(), rol=TipoPerfil.DOCENTE)
        dependency = require_rol([TipoPerfil.ADMINISTRADOR], _dummy_get_current_user)

        with pytest.raises(HTTPException) as exc_info:
            await dependency(payload)

        assert exc_info.value.status_code == 403
