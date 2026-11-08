"""El 2.º fallo de login avisa que queda 1 intento, y solo ese (US-ADJ-69)."""

from __future__ import annotations

import pytest

from src.identidad.entities.errors import CredencialesInvalidas
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.iniciar_sesion import IniciarSesionUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakeJWTIssuer, FakePasswordHasher, FakeUsuarioRepository

PASSWORD = "Docente#2026"
INCORRECTA = "otra-contraseña"


def _caso_de_uso(
    tipo: TipoPerfil = TipoPerfil.DOCENTE,
) -> tuple[IniciarSesionUseCase, FakeUsuarioRepository, Usuario]:
    repo = FakeUsuarioRepository()
    hasher = FakePasswordHasher()
    usuario = Usuario.crear("Persona", "persona@fiuner.edu.ar", hasher.hash(PASSWORD), tipo)
    repo.usuarios[usuario.id] = usuario
    return IniciarSesionUseCase(repo, hasher, FakeJWTIssuer()), repo, usuario


async def _fallar(caso: IniciarSesionUseCase, email: str = "persona@fiuner.edu.ar") -> int | None:
    with pytest.raises(CredencialesInvalidas) as info:
        await caso.execute(email, INCORRECTA)
    return info.value.intentos_restantes


class TestAvisoUltimoIntento:
    """El caso de uso avisa del último intento solo en el 2.º fallo."""

    def test_la_excepcion_no_lleva_aviso_por_defecto(self):
        """`CredencialesInvalidas` nace sin `intentos_restantes`."""
        assert CredencialesInvalidas().intentos_restantes is None

    async def test_el_primer_fallo_no_avisa(self):
        """El 1.er fallo es genérico."""
        caso, _repo, _usuario = _caso_de_uso()

        assert await _fallar(caso) is None

    async def test_el_segundo_fallo_avisa_que_queda_un_intento(self):
        """El 2.º fallo informa `intentos_restantes = 1`."""
        caso, _repo, _usuario = _caso_de_uso()
        await _fallar(caso)

        assert await _fallar(caso) == 1

    async def test_el_tercer_fallo_bloquea_y_no_lleva_aviso(self):
        """El 3.er fallo bloquea la cuenta y no lleva aviso."""
        caso, _repo, usuario = _caso_de_uso()
        await _fallar(caso)
        await _fallar(caso)

        with pytest.raises(CredencialesInvalidas) as info:
            await caso.execute("persona@fiuner.edu.ar", INCORRECTA)

        assert info.value.intentos_restantes is None
        assert info.value.evento_cuenta_bloqueada is not None
        assert usuario.bloqueada is True

    async def test_un_email_inexistente_nunca_recibe_el_aviso(self):
        """Un email inexistente nunca lleva el aviso, por más intentos que haga."""
        caso, _repo, _usuario = _caso_de_uso()

        avisos = [await _fallar(caso, "no-existe@fiuner.edu.ar") for _ in range(4)]

        assert avisos == [None, None, None, None]

    async def test_un_login_correcto_reinicia_el_contador(self):
        """Un login correcto reinicia el contador: el fallo siguiente es el 1.º."""
        caso, _repo, usuario = _caso_de_uso()
        await _fallar(caso)
        await caso.execute("persona@fiuner.edu.ar", PASSWORD)

        assert usuario.intentos_fallidos_login == 0
        assert await _fallar(caso) is None

    async def test_el_unico_administrador_tambien_recibe_el_aviso(self):
        """El último Administrador operativo recibe el aviso como cualquier cuenta."""
        caso, _repo, _usuario = _caso_de_uso(TipoPerfil.ADMINISTRADOR)
        await _fallar(caso)

        assert await _fallar(caso) == 1
