import uuid

import pytest

from src.identidad.entities.errors import PasswordDemasiadoCorta
from src.identidad.entities.usuario import Administrador, Docente, Estudiante, Usuario
from src.shared.entities.tipo_perfil import TipoPerfil


class TestUsuarioCrear:
    def test_crea_docente_con_perfil_atomico(self):
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)

        assert isinstance(usuario.perfil, Docente)
        assert usuario.perfil.id == usuario.id
        assert usuario.tipo_perfil == TipoPerfil.DOCENTE

    def test_crea_administrador(self):
        usuario = Usuario.crear("Vic", "vic@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)

        assert isinstance(usuario.perfil, Administrador)
        assert usuario.tipo_perfil == TipoPerfil.ADMINISTRADOR

    def test_rechaza_estudiante_por_via_generica(self):
        with pytest.raises(ValueError):
            Usuario.crear("Est", "est@fiuner.edu.ar", "hash", TipoPerfil.ESTUDIANTE)

    def test_cada_usuario_tiene_id_propio(self):
        u1 = Usuario.crear("A", "a@x.com", "h", TipoPerfil.DOCENTE)
        u2 = Usuario.crear("B", "b@x.com", "h", TipoPerfil.DOCENTE)

        assert u1.id != u2.id


class TestUsuarioCrearEstudiante:
    def test_crea_estudiante_con_comision_asignada(self):
        comision_id = uuid.uuid4()
        usuario = Usuario.crear_estudiante("Est", "est@fiuner.edu.ar", "hash", comision_id)

        assert isinstance(usuario.perfil, Estudiante)
        assert usuario.perfil.comision_id == comision_id
        assert usuario.tipo_perfil == TipoPerfil.ESTUDIANTE


class TestUsuarioValidarPasswordNueva:
    def test_acepta_password_de_8_caracteres(self):
        Usuario.validar_password_nueva("12345678")

    def test_acepta_password_larga(self):
        Usuario.validar_password_nueva("unaContraseñaBienLarga123")

    def test_rechaza_password_de_menos_de_8_caracteres(self):
        with pytest.raises(PasswordDemasiadoCorta):
            Usuario.validar_password_nueva("corta")

    def test_rechaza_password_vacia(self):
        with pytest.raises(PasswordDemasiadoCorta):
            Usuario.validar_password_nueva("")


class TestUsuarioResetearPassword:
    def test_actualiza_el_hash(self):
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash-viejo", TipoPerfil.DOCENTE)

        usuario.resetear_password("hash-nuevo")

        assert usuario.password_hash == "hash-nuevo"

    def test_resetea_bloqueada_y_contadores_de_una_cuenta_bloqueada(self):
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        usuario.bloqueada = True
        usuario.intentos_fallidos_login = 3
        usuario.intentos_fallidos_password = 2

        usuario.resetear_password("hash-nuevo")

        assert usuario.bloqueada is False
        assert usuario.intentos_fallidos_login == 0
        assert usuario.intentos_fallidos_password == 0

    def test_devuelve_true_si_estaba_bloqueada(self):
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        usuario.bloqueada = True

        resultado = usuario.resetear_password("hash-nuevo")

        assert resultado is True

    def test_devuelve_false_si_no_estaba_bloqueada(self):
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)

        resultado = usuario.resetear_password("hash-nuevo")

        assert resultado is False

    def test_resetea_contadores_de_una_cuenta_activa_tambien(self):
        usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        usuario.intentos_fallidos_login = 2

        usuario.resetear_password("hash-nuevo")

        assert usuario.bloqueada is False
        assert usuario.intentos_fallidos_login == 0
