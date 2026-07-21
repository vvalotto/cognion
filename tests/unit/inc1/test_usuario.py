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

    def test_crea_estudiante(self):
        usuario = Usuario.crear("Est", "est@fiuner.edu.ar", "hash", TipoPerfil.ESTUDIANTE)

        assert isinstance(usuario.perfil, Estudiante)
        assert usuario.tipo_perfil == TipoPerfil.ESTUDIANTE

    def test_cada_usuario_tiene_id_propio(self):
        u1 = Usuario.crear("A", "a@x.com", "h", TipoPerfil.DOCENTE)
        u2 = Usuario.crear("B", "b@x.com", "h", TipoPerfil.DOCENTE)

        assert u1.id != u2.id
