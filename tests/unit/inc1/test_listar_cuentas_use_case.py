import uuid

from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.listar_cuentas import ListarCuentasUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakeUsuarioRepository


def _usuario(nombre: str, email: str, tipo_perfil: TipoPerfil, bloqueada: bool = False) -> Usuario:
    if tipo_perfil is TipoPerfil.ESTUDIANTE:
        usuario = Usuario.crear_estudiante(nombre, email, "hash", uuid.uuid4())
    else:
        usuario = Usuario.crear(nombre, email, "hash", tipo_perfil)
    usuario.bloqueada = bloqueada
    return usuario


class TestListarCuentasUseCase:
    async def test_listado_sin_filtros_devuelve_todas_las_cuentas(self):
        repo = FakeUsuarioRepository()
        docente = _usuario("Docente", "docente@fiuner.edu.ar", TipoPerfil.DOCENTE)
        admin = _usuario("Admin", "admin@fiuner.edu.ar", TipoPerfil.ADMINISTRADOR)
        repo.usuarios[docente.id] = docente
        repo.usuarios[admin.id] = admin
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(None, None, None)

        assert {u.id for u in resultado} == {docente.id, admin.id}

    async def test_filtro_combinado_por_rol_y_estado(self):
        repo = FakeUsuarioRepository()
        estudiante_activo = _usuario(
            "Est Activo", "activo@fiuner.edu.ar", TipoPerfil.ESTUDIANTE, bloqueada=False
        )
        estudiante_bloqueado = _usuario(
            "Est Bloqueado", "bloqueado@fiuner.edu.ar", TipoPerfil.ESTUDIANTE, bloqueada=True
        )
        docente_activo = _usuario(
            "Docente Activo", "docente@fiuner.edu.ar", TipoPerfil.DOCENTE, bloqueada=False
        )
        for u in (estudiante_activo, estudiante_bloqueado, docente_activo):
            repo.usuarios[u.id] = u
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(TipoPerfil.ESTUDIANTE, "bloqueada", None)

        assert len(resultado) == 1
        assert resultado[0].id == estudiante_bloqueado.id

    async def test_busqueda_por_email_parcial(self):
        repo = FakeUsuarioRepository()
        objetivo = _usuario("Marisa Gonzalez", "mgonzalez@fiuner.edu.ar", TipoPerfil.DOCENTE)
        otro = _usuario("Juan Perez", "jperez@fiuner.edu.ar", TipoPerfil.DOCENTE)
        repo.usuarios[objetivo.id] = objetivo
        repo.usuarios[otro.id] = otro
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(None, None, "mgonzalez")

        assert len(resultado) == 1
        assert resultado[0].id == objetivo.id

    async def test_busqueda_case_insensitive_contra_nombre(self):
        repo = FakeUsuarioRepository()
        usuario = _usuario("Marisa Gonzalez", "mgonzalez@fiuner.edu.ar", TipoPerfil.DOCENTE)
        repo.usuarios[usuario.id] = usuario
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(None, None, "MARISA")

        assert len(resultado) == 1
        assert resultado[0].id == usuario.id

    async def test_sin_resultados_devuelve_lista_vacia(self):
        repo = FakeUsuarioRepository()
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(None, None, "no-existe")

        assert resultado == []
