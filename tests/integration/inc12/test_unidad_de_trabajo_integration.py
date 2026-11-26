"""Unidad de trabajo contra PostgreSQL real (`US-12.2.1`, `ADR-028`).

Requiere una base descartable (`DATABASE_URL` inline): estos tests vacían las tablas de Identidad.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from src.identidad.entities.errors import CredencialesInvalidas, EmailYaRegistrado
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.repositories.usuario_repository import SQLAlchemyUsuarioRepository
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal, unidad_de_trabajo


def _administrador(email: str) -> Usuario:
    return Usuario.crear("Admin", email, BcryptPasswordHasher().hash("x"), TipoPerfil.ADMINISTRADOR)


def _email() -> str:
    return f"uow.{uuid.uuid4()}@fiuner.edu.ar"


async def _existe(email: str) -> bool:
    async with SessionLocal() as session:
        resultado = await session.execute(
            text("SELECT count(*) FROM usuario WHERE email = :e"), {"e": email}
        )
        return int(resultado.scalar_one()) == 1


class TestEmailUnicoConPuntoDeGuardado:
    async def test_la_escritura_previa_sobrevive_al_email_duplicado(self) -> None:
        """Con `session.rollback()` se perdía todo lo pendiente del request; con `begin_nested()` no."""
        previo, repetido = _email(), _email()

        with pytest.raises(EmailYaRegistrado):
            async with unidad_de_trabajo() as session:
                repositorio = SQLAlchemyUsuarioRepository(session)
                await repositorio.guardar(_administrador(previo))
                await repositorio.guardar(_administrador(repetido))
                await repositorio.guardar(_administrador(repetido))

        assert await _existe(previo)
        assert await _existe(repetido)

    async def test_un_email_ya_guardado_se_rechaza_sin_tocar_lo_anterior(self) -> None:
        existente, nuevo = _email(), _email()
        async with unidad_de_trabajo() as session:
            await SQLAlchemyUsuarioRepository(session).guardar(_administrador(existente))

        with pytest.raises(EmailYaRegistrado):
            async with unidad_de_trabajo() as session:
                repositorio = SQLAlchemyUsuarioRepository(session)
                await repositorio.guardar(_administrador(nuevo))
                await repositorio.guardar(_administrador(existente))

        assert await _existe(nuevo)
        assert await _existe(existente)


class TestConfirmarORevertir:
    async def test_confirma_al_salir_bien(self) -> None:
        email = _email()
        async with unidad_de_trabajo() as session:
            await SQLAlchemyUsuarioRepository(session).guardar(_administrador(email))

        assert await _existe(email)

    async def test_un_error_controlado_confirma_lo_escrito(self) -> None:
        """El intento fallido de login que cuenta para el bloqueo no puede perderse (`INV-ID-21`)."""
        email = _email()
        with pytest.raises(CredencialesInvalidas):
            async with unidad_de_trabajo() as session:
                await SQLAlchemyUsuarioRepository(session).guardar(_administrador(email))
                raise CredencialesInvalidas()

        assert await _existe(email)

    async def test_una_falla_tecnica_revierte_todo(self) -> None:
        email = _email()
        with pytest.raises(RuntimeError):
            async with unidad_de_trabajo() as session:
                await SQLAlchemyUsuarioRepository(session).guardar(_administrador(email))
                raise RuntimeError("se cayó la base")

        assert not await _existe(email)

    async def test_el_repositorio_solo_hace_flush_y_no_confirma(self) -> None:
        """Sin la unidad de trabajo, lo guardado por un repositorio no queda en la base."""
        email = _email()
        async with SessionLocal() as session:
            await SQLAlchemyUsuarioRepository(session).guardar(_administrador(email))

        assert not await _existe(email)
