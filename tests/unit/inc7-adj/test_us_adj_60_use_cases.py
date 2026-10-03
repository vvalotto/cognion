"""US-ADJ-60 — los use cases aplican INV-ID-19/20/21."""

from datetime import UTC, datetime, timedelta

import pytest

from src.identidad.entities.bloqueo_cuenta import es_administrador_operativo
from src.identidad.entities.errors import (
    CredencialesInvalidas,
    CuentaBloqueadaError,
    CuentaBloqueadaTemporalmenteError,
    PasswordActualIncorrecta,
    UltimoAdministradorOperativoError,
)
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.cambiar_password import CambiarPasswordUseCase
from src.identidad.use_cases.eliminar_cuenta import EliminarCuentaUseCase
from src.identidad.use_cases.iniciar_sesion import IniciarSesionUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import (
    FakeComisionQueryRepository,
    FakeEvaluacionConsultaPort,
    FakeJWTIssuer,
    FakePasswordHasher,
    FakeTokenRecuperacionPasswordRepository,
    FakeUsuarioRepository,
)

PASSWORD = "Admin#2026-ok"


def _alta(repo: FakeUsuarioRepository, perfil: TipoPerfil, n: int = 0) -> Usuario:
    usuario = Usuario.crear(
        f"U{n}", f"u{n}@fiuner.edu.ar", FakePasswordHasher().hash(PASSWORD), perfil
    )
    repo.usuarios[usuario.id] = usuario
    return usuario


def _eliminar(repo: FakeUsuarioRepository) -> EliminarCuentaUseCase:
    return EliminarCuentaUseCase(
        repo,
        FakeComisionQueryRepository(),
        FakeEvaluacionConsultaPort(),
        FakeTokenRecuperacionPasswordRepository(),
    )


class TestEliminarAdministrador:
    async def test_con_otro_operativo_es_baja_logica_nunca_fisica(self):
        repo = FakeUsuarioRepository()
        a = _alta(repo, TipoPerfil.ADMINISTRADOR, 1)
        _alta(repo, TipoPerfil.ADMINISTRADOR, 2)

        resultado = await _eliminar(repo).execute(a.id)

        assert resultado is a
        assert a.deshabilitada is True
        assert a.id in repo.usuarios

    async def test_el_ultimo_operativo_no_se_puede_dar_de_baja(self):
        repo = FakeUsuarioRepository()
        a = _alta(repo, TipoPerfil.ADMINISTRADOR)

        with pytest.raises(UltimoAdministradorOperativoError):
            await _eliminar(repo).execute(a.id)

        assert a.deshabilitada is False

    async def test_otro_bloqueado_no_cuenta_como_operativo(self):
        repo = FakeUsuarioRepository()
        a = _alta(repo, TipoPerfil.ADMINISTRADOR, 1)
        b = _alta(repo, TipoPerfil.ADMINISTRADOR, 2)
        b.bloqueada = True

        with pytest.raises(UltimoAdministradorOperativoError):
            await _eliminar(repo).execute(a.id)

    async def test_ya_deshabilitado_es_idempotente(self):
        repo = FakeUsuarioRepository()
        a = _alta(repo, TipoPerfil.ADMINISTRADOR, 1)
        a.deshabilitar()
        b = _alta(repo, TipoPerfil.ADMINISTRADOR, 2)

        resultado = await _eliminar(repo).execute(a.id)

        assert resultado is a
        assert es_administrador_operativo(b)

    async def test_docente_sin_datos_sigue_borrandose_fisicamente(self):
        repo = FakeUsuarioRepository()
        d = _alta(repo, TipoPerfil.DOCENTE)

        assert await _eliminar(repo).execute(d.id) is None
        assert d.id not in repo.usuarios


def _login(repo: FakeUsuarioRepository) -> IniciarSesionUseCase:
    return IniciarSesionUseCase(repo, FakePasswordHasher(), FakeJWTIssuer(), timedelta(minutes=15))


async def _fallar_login(use_case: IniciarSesionUseCase, email: str, veces: int) -> None:
    for _ in range(veces):
        with pytest.raises((CredencialesInvalidas, CuentaBloqueadaError)):
            await use_case.execute(email, "incorrecta")


class TestLoginBloqueoTemporal:
    async def test_el_ultimo_administrador_queda_bloqueado_temporalmente(self):
        repo = FakeUsuarioRepository()
        a = _alta(repo, TipoPerfil.ADMINISTRADOR)
        use_case = _login(repo)

        await _fallar_login(use_case, a.email, 3)

        assert a.bloqueada is True
        assert a.bloqueada_hasta is not None
        with pytest.raises(CuentaBloqueadaTemporalmenteError) as info:
            await use_case.execute(a.email, PASSWORD)
        assert info.value.segundos_restantes(datetime.now(UTC)) > 0

    async def test_con_otro_administrador_el_bloqueo_es_permanente(self):
        repo = FakeUsuarioRepository()
        a = _alta(repo, TipoPerfil.ADMINISTRADOR, 1)
        _alta(repo, TipoPerfil.ADMINISTRADOR, 2)
        use_case = _login(repo)

        await _fallar_login(use_case, a.email, 3)

        assert a.bloqueada is True
        assert a.bloqueada_hasta is None
        with pytest.raises(CuentaBloqueadaError):
            await use_case.execute(a.email, PASSWORD)

    async def test_docente_conserva_el_bloqueo_permanente(self):
        repo = FakeUsuarioRepository()
        d = _alta(repo, TipoPerfil.DOCENTE)

        await _fallar_login(_login(repo), d.email, 3)

        assert d.bloqueada is True
        assert d.bloqueada_hasta is None

    async def test_bloqueo_vencido_se_levanta_y_el_login_continua(self):
        repo = FakeUsuarioRepository()
        a = _alta(repo, TipoPerfil.ADMINISTRADOR)
        a.bloqueada = True
        a.intentos_fallidos_login = 3
        a.bloqueada_hasta = datetime.now(UTC) - timedelta(seconds=1)

        jwt_vo, _ = await _login(repo).execute(a.email, PASSWORD)

        assert jwt_vo.rol == TipoPerfil.ADMINISTRADOR
        assert a.bloqueada is False
        assert a.bloqueada_hasta is None


class TestCambiarPasswordBloqueoTemporal:
    def _use_case(self, repo: FakeUsuarioRepository) -> CambiarPasswordUseCase:
        return CambiarPasswordUseCase(repo, FakePasswordHasher(), timedelta(minutes=15))

    async def test_el_ultimo_administrador_queda_bloqueado_temporalmente(self):
        repo = FakeUsuarioRepository()
        a = _alta(repo, TipoPerfil.ADMINISTRADOR)
        use_case = self._use_case(repo)

        for _ in range(3):
            with pytest.raises(PasswordActualIncorrecta):
                await use_case.execute(a.id, "incorrecta", "Nueva#Pass2026")

        assert a.bloqueada is True
        assert a.bloqueada_hasta is not None
        with pytest.raises(CuentaBloqueadaTemporalmenteError):
            await use_case.execute(a.id, PASSWORD, "Nueva#Pass2026")

    async def test_docente_queda_bloqueado_de_forma_permanente(self):
        repo = FakeUsuarioRepository()
        d = _alta(repo, TipoPerfil.DOCENTE)
        use_case = self._use_case(repo)

        for _ in range(3):
            with pytest.raises(PasswordActualIncorrecta):
                await use_case.execute(d.id, "incorrecta", "Nueva#Pass2026")

        assert d.bloqueada is True
        assert d.bloqueada_hasta is None

    async def test_bloqueo_vencido_se_levanta_y_el_cambio_continua(self):
        repo = FakeUsuarioRepository()
        a = _alta(repo, TipoPerfil.ADMINISTRADOR)
        a.bloqueada = True
        a.bloqueada_hasta = datetime.now(UTC) - timedelta(seconds=1)

        await self._use_case(repo).execute(a.id, PASSWORD, "Nueva#Pass2026")

        assert a.bloqueada is False
