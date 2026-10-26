"""El comando que crea el Administrador pide la contraseña dos veces (US-ADJ-65)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.cli.bootstrap_administrador import (
    MAX_INTENTOS_PASSWORD,
    SALIDA_ENTRADA_INVALIDA,
    SALIDA_OK,
    SALIDA_SIN_PASSWORD,
    ContrasenasNoCoinciden,
    ejecutar,
    pedir_password_confirmada,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakePasswordHasher, FakeUsuarioRepository

VALIDA = "Admin#2026-ok"
OTRA = "Otra#2026-clave"
CORTA = "Ab#1"
ENV_SIN_PASSWORD = {"ADMIN_NOMBRE": "Ada Admin", "ADMIN_EMAIL": "ada@uner.edu.ar"}


def _teclado(*entradas: str) -> tuple[Callable[[str], str], list[str]]:
    """Un `leer` que devuelve las entradas en orden y anota cada pedido que se le hizo."""
    pendientes = list(entradas)
    pedidos: list[str] = []

    def leer(pedido: str) -> str:
        pedidos.append(pedido)
        return pendientes.pop(0)

    return leer, pedidos


# ---------------------------------------------------------------- pedir_password_confirmada


def test_si_las_dos_entradas_coinciden_la_devuelve_y_pide_dos_veces() -> None:
    """Escenario 1: una contraseña y su repetición."""
    leer, pedidos = _teclado(VALIDA, VALIDA)
    avisos: list[str] = []
    assert pedir_password_confirmada(leer, avisos.append) == VALIDA
    assert pedidos == ["Contraseña del Administrador: ", "Repetí la contraseña: "]
    assert avisos == []


def test_si_no_coinciden_avisa_y_vuelve_a_pedir() -> None:
    """Escenario 2: distinta la primera vez, igual la segunda."""
    leer, pedidos = _teclado(VALIDA, OTRA, VALIDA, VALIDA)
    avisos: list[str] = []
    assert pedir_password_confirmada(leer, avisos.append) == VALIDA
    assert len(pedidos) == 4
    assert avisos == ["Las contraseñas no coinciden. Te quedan 2 intentos."]


def test_tres_desencuentros_levantan_el_error_y_cuentan_los_intentos_restantes() -> None:
    """Escenario 3: al tercer intento fallido deja de pedir."""
    leer, pedidos = _teclado(VALIDA, OTRA, VALIDA, OTRA, VALIDA, OTRA)
    avisos: list[str] = []
    with pytest.raises(ContrasenasNoCoinciden):
        pedir_password_confirmada(leer, avisos.append)
    assert len(pedidos) == 2 * MAX_INTENTOS_PASSWORD
    assert avisos == [
        "Las contraseñas no coinciden. Te quedan 2 intentos.",
        "Las contraseñas no coinciden. Te quedan 1 intento.",
        "Las contraseñas no coinciden.",
    ]


def test_los_avisos_no_revelan_la_contraseña() -> None:
    """Ningún aviso contiene lo que se escribió."""
    leer, _ = _teclado(VALIDA, OTRA, VALIDA, OTRA, VALIDA, OTRA)
    avisos: list[str] = []
    with pytest.raises(ContrasenasNoCoinciden):
        pedir_password_confirmada(leer, avisos.append)
    assert not any(VALIDA in aviso or OTRA in aviso for aviso in avisos)


# ---------------------------------------------------------------- ejecutar


async def test_tres_desencuentros_salen_con_1_sin_crear_nada(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Escenario 3: salida 1, ningún usuario, mensaje claro."""
    repo = FakeUsuarioRepository()

    def pedir() -> str:
        raise ContrasenasNoCoinciden

    codigo = await ejecutar(ENV_SIN_PASSWORD, pedir, repo, FakePasswordHasher())
    assert codigo == SALIDA_ENTRADA_INVALIDA
    assert not repo.usuarios
    salida = capsys.readouterr().out
    assert "no se creó el Administrador" in salida and f"{MAX_INTENTOS_PASSWORD} intentos" in salida


async def test_coinciden_pero_no_cumplen_las_reglas(capsys: pytest.CaptureFixture[str]) -> None:
    """Escenario 4: la regla INV-ID-11 se aplica sobre la contraseña confirmada."""
    repo = FakeUsuarioRepository()
    codigo = await ejecutar(ENV_SIN_PASSWORD, lambda: CORTA, repo, FakePasswordHasher())
    assert codigo == SALIDA_ENTRADA_INVALIDA
    assert not repo.usuarios
    salida = capsys.readouterr().out
    assert "Contraseña rechazada" in salida and CORTA not in salida


async def test_con_admin_password_no_pide_nada() -> None:
    """Escenario 5: la variable de entorno evita todo pedido por terminal."""
    repo = FakeUsuarioRepository()
    pedidos = 0

    def pedir() -> str | None:
        nonlocal pedidos
        pedidos += 1
        return None

    codigo = await ejecutar(
        {**ENV_SIN_PASSWORD, "ADMIN_PASSWORD": VALIDA}, pedir, repo, FakePasswordHasher()
    )
    assert codigo == SALIDA_OK and pedidos == 0 and len(repo.usuarios) == 1


async def test_sin_terminal_ni_variable_sale_con_2(capsys: pytest.CaptureFixture[str]) -> None:
    """Escenario 6: el mensaje y el código de siempre."""
    codigo = await ejecutar(
        ENV_SIN_PASSWORD, lambda: None, FakeUsuarioRepository(), FakePasswordHasher()
    )
    assert codigo == SALIDA_SIN_PASSWORD
    assert "ADMIN_PASSWORD" in capsys.readouterr().out


async def test_si_ya_hay_un_administrador_no_pide_la_contraseña(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Escenario 7: se consulta antes de pedir y se termina con 0."""
    repo = FakeUsuarioRepository()
    existente = Usuario.crear("Otro", "otro@uner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
    repo.usuarios[existente.id] = existente
    pedidos = 0

    def pedir() -> str | None:
        nonlocal pedidos
        pedidos += 1
        return VALIDA

    codigo = await ejecutar(ENV_SIN_PASSWORD, pedir, repo, FakePasswordHasher())
    assert codigo == SALIDA_OK and pedidos == 0 and len(repo.usuarios) == 1
    assert "Ya existe un Administrador operativo" in capsys.readouterr().out


async def test_las_variables_faltantes_se_validan_antes_que_nada() -> None:
    """Sin nombre o email falla antes de consultar el repositorio o pedir la contraseña."""
    pedidos = 0

    def pedir() -> str | None:
        nonlocal pedidos
        pedidos += 1
        return VALIDA

    codigo = await ejecutar(
        {"ADMIN_EMAIL": "ada@uner.edu.ar"}, pedir, FakeUsuarioRepository(), FakePasswordHasher()
    )
    assert codigo == SALIDA_ENTRADA_INVALIDA and pedidos == 0
