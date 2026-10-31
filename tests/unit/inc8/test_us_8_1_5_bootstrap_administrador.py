"""Bootstrap del primer Administrador: caso de uso y comando (US-8.1.5)."""

import pytest

from src.identidad.entities.errors import AdministradorYaExiste, EmailYaRegistrado
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.cli.bootstrap_administrador import (
    SALIDA_ENTRADA_INVALIDA,
    SALIDA_OK,
    SALIDA_SIN_PASSWORD,
    ejecutar,
)
from src.identidad.use_cases.bootstrap_administrador import BootstrapAdministradorUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository

PASSWORD = "Admin#2026-ok"
ENV = {"ADMIN_NOMBRE": "Ada Admin", "ADMIN_EMAIL": "ada@uner.edu.ar", "ADMIN_PASSWORD": PASSWORD}


def _admin_existente(repo: FakeUsuarioRepository, email: str = "otro@uner.edu.ar") -> Usuario:
    usuario = Usuario.crear("Otro", email, "hash", TipoPerfil.ADMINISTRADOR)
    repo.usuarios[usuario.id] = usuario
    return usuario


async def test_crea_el_primer_administrador() -> None:
    """Sin Administradores, crea uno con la contraseña hasheada."""
    repo = FakeUsuarioRepository()
    usuario = await BootstrapAdministradorUseCase(repo, FakePasswordHasher()).execute(
        "Ada", "ada@uner.edu.ar", PASSWORD
    )
    assert usuario.tipo_perfil is TipoPerfil.ADMINISTRADOR
    assert repo.usuarios[usuario.id].password_hash == f"hashed:{PASSWORD}"


async def test_no_crea_otro_si_ya_hay_un_administrador_operativo() -> None:
    """Idempotencia por existencia de Administrador, no solo por email."""
    repo = FakeUsuarioRepository()
    _admin_existente(repo)
    with pytest.raises(AdministradorYaExiste):
        await BootstrapAdministradorUseCase(repo, FakePasswordHasher()).execute(
            "Ada", "ada@uner.edu.ar", PASSWORD
        )
    assert len(repo.usuarios) == 1


async def test_email_en_uso_por_otra_cuenta_se_propaga() -> None:
    """Si el email es de una cuenta no-Administrador, el alta falla."""
    repo = FakeUsuarioRepository()
    docente = Usuario.crear("Doc", "ada@uner.edu.ar", "hash", TipoPerfil.DOCENTE)
    repo.usuarios[docente.id] = docente
    with pytest.raises(EmailYaRegistrado):
        await BootstrapAdministradorUseCase(repo, FakePasswordHasher()).execute(
            "Ada", "ada@uner.edu.ar", PASSWORD
        )


async def test_comando_crea_y_sale_con_0(capsys: pytest.CaptureFixture[str]) -> None:
    """Escenario 1: datos válidos."""
    repo = FakeUsuarioRepository()
    codigo = await ejecutar(ENV, lambda: None, repo, FakePasswordHasher())
    assert codigo == SALIDA_OK
    assert len(repo.usuarios) == 1
    assert "Administrador creado" in capsys.readouterr().out


async def test_segunda_ejecucion_con_otro_email_no_duplica(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Escenario 2: ya existe un Administrador operativo, exit 0 y sin crear nada."""
    repo = FakeUsuarioRepository()
    _admin_existente(repo)
    codigo = await ejecutar(ENV, lambda: None, repo, FakePasswordHasher())
    assert codigo == SALIDA_OK
    assert len(repo.usuarios) == 1
    assert "Ya existe" in capsys.readouterr().out


async def test_falta_una_variable(capsys: pytest.CaptureFixture[str]) -> None:
    """Escenario 3: el mensaje nombra la variable faltante."""
    env = {k: v for k, v in ENV.items() if k != "ADMIN_EMAIL"}
    codigo = await ejecutar(env, lambda: None, FakeUsuarioRepository(), FakePasswordHasher())
    assert codigo == SALIDA_ENTRADA_INVALIDA
    assert "ADMIN_EMAIL" in capsys.readouterr().out


async def test_password_debil_no_se_repite_en_el_mensaje(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Escenario 4: INV-ID-11 rechaza, y la contraseña no se imprime."""
    repo = FakeUsuarioRepository()
    codigo = await ejecutar(
        {**ENV, "ADMIN_PASSWORD": "corta"}, lambda: None, repo, FakePasswordHasher()
    )
    salida = capsys.readouterr().out
    assert codigo == SALIDA_ENTRADA_INVALIDA
    assert "12 caracteres" in salida
    assert "corta" not in salida.replace("demasiado corta", "")
    assert not repo.usuarios


async def test_sin_password_ni_terminal() -> None:
    """Escenario 5: sin ADMIN_PASSWORD y sin terminal, exit 2."""
    env = {k: v for k, v in ENV.items() if k != "ADMIN_PASSWORD"}
    codigo = await ejecutar(env, lambda: None, FakeUsuarioRepository(), FakePasswordHasher())
    assert codigo == SALIDA_SIN_PASSWORD


async def test_sin_variable_pide_la_password_por_terminal() -> None:
    """Escenario 6: con terminal, la contraseña se pide y se usa."""
    env = {k: v for k, v in ENV.items() if k != "ADMIN_PASSWORD"}
    repo = FakeUsuarioRepository()
    codigo = await ejecutar(env, lambda: PASSWORD, repo, FakePasswordHasher())
    assert codigo == SALIDA_OK
    assert len(repo.usuarios) == 1


async def test_email_de_otra_cuenta_sale_con_1(capsys: pytest.CaptureFixture[str]) -> None:
    """Un email ya usado por una cuenta no-Administrador es entrada inválida."""
    repo = FakeUsuarioRepository()
    docente = Usuario.crear("Doc", "ada@uner.edu.ar", "hash", TipoPerfil.DOCENTE)
    repo.usuarios[docente.id] = docente
    codigo = await ejecutar(ENV, lambda: None, repo, FakePasswordHasher())
    assert codigo == SALIDA_ENTRADA_INVALIDA
    assert "otra cuenta" in capsys.readouterr().out
