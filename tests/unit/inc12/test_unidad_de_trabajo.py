"""Unidad de trabajo por request (`US-12.2.1`, `ADR-028` y su enmienda del 2026-11-26).

Se confirma al terminar bien o ante un error controlado (el resultado de una regla de negocio o de un control de
seguridad) y se revierte ante uno no controlado (una falla técnica). Sin base de datos: la sesión es un doble.
"""

from __future__ import annotations

import asyncio
from typing import Annotated, get_args

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError

from src.actividad_evaluativa.entities.errors import ConcurrenciaOptimistaError
from src.identidad.entities.errors import CredencialesInvalidas, EmailYaRegistrado
from src.shared.entities.errors import JWTExpirado
from src.shared.frameworks import db


class SesionFalsa:
    """Registra qué se le pidió a la sesión; `commit_falla` hace fallar la confirmación."""

    def __init__(self, commit_falla: bool = False) -> None:
        self.llamadas: list[str] = []
        self._commit_falla = commit_falla

    async def __aenter__(self) -> SesionFalsa:
        return self

    async def __aexit__(self, *_: object) -> None:
        self.llamadas.append("close")

    async def commit(self) -> None:
        self.llamadas.append("commit")
        if self._commit_falla:
            raise RuntimeError("commit falló")

    async def rollback(self) -> None:
        self.llamadas.append("rollback")


@pytest.fixture
def sesion(monkeypatch: pytest.MonkeyPatch) -> SesionFalsa:
    falsa = SesionFalsa()
    monkeypatch.setattr(db, "SessionLocal", lambda: falsa)
    return falsa


class TestEsErrorControlado:
    @pytest.mark.parametrize(
        "error",
        [
            HTTPException(status_code=400),
            HTTPException(status_code=404),
            HTTPException(status_code=422),
            CredencialesInvalidas(),
            EmailYaRegistrado("a@b.c"),
            ConcurrenciaOptimistaError("T", "id", 1, 2),
            JWTExpirado(),
        ],
    )
    def test_el_resultado_de_una_regla_es_controlado(self, error: BaseException) -> None:
        assert db.es_error_controlado(error) is True

    @pytest.mark.parametrize(
        "error",
        [
            RuntimeError("error del código"),
            ValueError("x"),
            OperationalError("select 1", {}, Exception("se perdió la conexión")),
            IntegrityError("insert", {}, Exception("violación")),
            asyncio.TimeoutError(),
            ConnectionError("sin red"),
            HTTPException(status_code=500),
            HTTPException(status_code=503),
        ],
    )
    def test_una_falla_tecnica_no_es_controlada(self, error: BaseException) -> None:
        assert db.es_error_controlado(error) is False


class TestUnidadDeTrabajo:
    async def test_confirma_al_salir_bien(self, sesion: SesionFalsa) -> None:
        async with db.unidad_de_trabajo():
            pass

        assert sesion.llamadas == ["commit", "close"]

    async def test_confirma_ante_un_error_controlado_y_lo_propaga(
        self, sesion: SesionFalsa
    ) -> None:
        with pytest.raises(CredencialesInvalidas):
            async with db.unidad_de_trabajo():
                raise CredencialesInvalidas()

        assert sesion.llamadas == ["commit", "close"]

    async def test_revierte_ante_una_falla_tecnica_y_la_propaga(self, sesion: SesionFalsa) -> None:
        with pytest.raises(RuntimeError):
            async with db.unidad_de_trabajo():
                raise RuntimeError("se cayó la base")

        assert sesion.llamadas == ["rollback", "close"]

    async def test_un_commit_fallido_se_propaga(self, monkeypatch: pytest.MonkeyPatch) -> None:
        falsa = SesionFalsa(commit_falla=True)
        monkeypatch.setattr(db, "SessionLocal", lambda: falsa)

        with pytest.raises(RuntimeError, match="commit falló"):
            async with db.unidad_de_trabajo():
                pass


class TestGetSession:
    async def test_entrega_la_sesion_y_confirma_al_terminar(self, sesion: SesionFalsa) -> None:
        generador = db.get_session()
        entregada = await generador.__anext__()
        assert entregada is sesion

        with pytest.raises(StopAsyncIteration):
            await generador.__anext__()

        assert sesion.llamadas == ["commit", "close"]

    async def test_revierte_si_el_request_termina_con_una_falla_tecnica(
        self, sesion: SesionFalsa
    ) -> None:
        generador = db.get_session()
        await generador.__anext__()

        with pytest.raises(RuntimeError):
            await generador.athrow(RuntimeError("falla"))

        assert sesion.llamadas == ["rollback", "close"]

    async def test_confirma_si_el_request_termina_con_un_error_controlado(
        self, sesion: SesionFalsa
    ) -> None:
        generador = db.get_session()
        await generador.__anext__()

        with pytest.raises(HTTPException):
            await generador.athrow(HTTPException(status_code=401))

        assert sesion.llamadas == ["commit", "close"]


class TestSessionDep:
    def test_declara_scope_function(self) -> None:
        """Sin `scope="function"`, un commit fallido ocurre después de enviar el 200 (FastAPI 0.139)."""
        dependencia = get_args(db.SessionDep)[1]
        assert isinstance(dependencia, type(Depends(db.get_session)))
        assert dependencia.scope == "function"
        assert dependencia.dependency is db.get_session

    def test_un_commit_fallido_llega_al_cliente_como_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(db, "SessionLocal", lambda: SesionFalsa(commit_falla=True))
        app = FastAPI()

        @app.post("/x")
        async def x(session: db.SessionDep) -> dict[str, bool]:  # noqa: ARG001
            return {"ok": True}

        respuesta = TestClient(app, raise_server_exceptions=False).post("/x")

        assert respuesta.status_code == 500

    def test_un_error_controlado_no_revierte_y_responde_su_codigo(
        self, sesion: SesionFalsa
    ) -> None:
        app = FastAPI()

        @app.post("/x")
        async def x(session: db.SessionDep) -> None:  # noqa: ARG001
            raise HTTPException(status_code=401, detail="credenciales inválidas")

        respuesta = TestClient(app, raise_server_exceptions=False).post("/x")

        assert respuesta.status_code == 401
        assert sesion.llamadas == ["commit", "close"]

    def test_una_falla_tecnica_revierte_y_responde_500(self, sesion: SesionFalsa) -> None:
        app = FastAPI()

        @app.post("/x")
        async def x(session: db.SessionDep) -> None:  # noqa: ARG001
            raise RuntimeError("falla")

        respuesta = TestClient(app, raise_server_exceptions=False).post("/x")

        assert respuesta.status_code == 500
        assert sesion.llamadas == ["rollback", "close"]
