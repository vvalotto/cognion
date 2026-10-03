"""US-ADJ-60 — política de bloqueo y vencimiento perezoso de `Usuario` (INV-ID-19/20/21)."""

from datetime import UTC, datetime, timedelta

from src.identidad.entities.errors import CuentaBloqueadaTemporalmenteError
from src.identidad.entities.usuario import Usuario
from src.shared.entities.tipo_perfil import TipoPerfil

AHORA = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
DURACION = timedelta(minutes=15)


def _usuario(perfil: TipoPerfil = TipoPerfil.ADMINISTRADOR) -> Usuario:
    return Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", perfil)


class TestEsAdministradorOperativo:
    def test_administrador_activo_es_operativo(self):
        assert _usuario().es_administrador_operativo() is True

    def test_deshabilitado_o_bloqueado_no_es_operativo(self):
        deshabilitado = _usuario()
        deshabilitado.deshabilitar()
        bloqueado = _usuario()
        bloqueado.bloqueada = True

        assert deshabilitado.es_administrador_operativo() is False
        assert bloqueado.es_administrador_operativo() is False

    def test_docente_no_es_administrador_operativo(self):
        assert _usuario(TipoPerfil.DOCENTE).es_administrador_operativo() is False


class TestBloquearPorIntentosFallidos:
    def test_ultimo_administrador_queda_bloqueado_hasta_ahora_mas_duracion(self):
        usuario = _usuario()

        usuario.bloquear_por_intentos_fallidos(True, AHORA, DURACION)

        assert usuario.bloqueada is True
        assert usuario.bloqueada_hasta == AHORA + DURACION

    def test_cualquier_otro_caso_es_permanente(self):
        usuario = _usuario(TipoPerfil.DOCENTE)

        usuario.bloquear_por_intentos_fallidos(False, AHORA, DURACION)

        assert usuario.bloqueada is True
        assert usuario.bloqueada_hasta is None


class TestVencimientoPerezoso:
    def _bloqueado_temporal(self) -> Usuario:
        usuario = _usuario()
        usuario.intentos_fallidos_login = 3
        usuario.bloquear_por_intentos_fallidos(True, AHORA, DURACION)
        return usuario

    def test_bloqueo_vigente_no_se_levanta(self):
        usuario = self._bloqueado_temporal()
        antes = AHORA + timedelta(minutes=5)

        assert usuario.tiene_bloqueo_temporal_vigente(antes) is True
        assert usuario.levantar_bloqueo_si_vencio(antes) is False
        assert usuario.bloqueada is True

    def test_bloqueo_vencido_se_levanta_y_resetea_contadores(self):
        usuario = self._bloqueado_temporal()
        despues = AHORA + DURACION

        assert usuario.tiene_bloqueo_temporal_vigente(despues) is False
        assert usuario.levantar_bloqueo_si_vencio(despues) is True
        assert usuario.bloqueada is False
        assert usuario.bloqueada_hasta is None
        assert usuario.intentos_fallidos_login == 0

    def test_bloqueo_permanente_nunca_se_levanta_solo(self):
        usuario = _usuario(TipoPerfil.DOCENTE)
        usuario.bloquear_por_intentos_fallidos(False, AHORA, DURACION)

        assert usuario.levantar_bloqueo_si_vencio(AHORA + timedelta(days=30)) is False
        assert usuario.bloqueada is True

    def test_resetear_password_limpia_bloqueada_hasta(self):
        usuario = self._bloqueado_temporal()

        usuario.resetear_password("hash-nuevo")

        assert usuario.bloqueada is False
        assert usuario.bloqueada_hasta is None


class TestSegundosRestantes:
    def test_redondea_hacia_arriba_y_nunca_baja_de_uno(self):
        exc = CuentaBloqueadaTemporalmenteError(_usuario().id, AHORA + timedelta(seconds=90.2))

        assert exc.segundos_restantes(AHORA) == 91
        assert exc.segundos_restantes(AHORA + timedelta(hours=1)) == 1
