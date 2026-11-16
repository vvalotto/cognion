"""La guarda de la base de tests acepta solo bases descartables (VT-03)."""

import pytest

from tests.guarda_base import verificar_base_descartable


def test_acepta_una_base_que_termina_en_test() -> None:
    """Una base `*_test` es descartable."""
    verificar_base_descartable("postgresql+asyncpg://user:password@localhost:5432/cognion_test")


@pytest.mark.parametrize("nombre", ["cognion", "cognion_dev", "test_cognion", ""])
def test_rechaza_una_base_que_no_termina_en_test(nombre: str) -> None:
    """Cualquier otro nombre, incluido el de desarrollo, corta la corrida."""
    with pytest.raises(RuntimeError, match="no termina en '_test'"):
        verificar_base_descartable(f"postgresql+asyncpg://user:password@localhost:5432/{nombre}")
