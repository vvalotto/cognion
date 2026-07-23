import uuid

import pytest

from src.identidad.entities.usuario import Administrador, Docente, Estudiante, TipoPerfil, Usuario


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
