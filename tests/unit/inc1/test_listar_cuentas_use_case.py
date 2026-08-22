import uuid

from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.listar_cuentas import ListarCuentasUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakeCuentaQueryRepository


def _usuario(nombre: str, email: str, tipo_perfil: TipoPerfil, bloqueada: bool = False) -> Usuario:
    if tipo_perfil is TipoPerfil.ESTUDIANTE:
        usuario = Usuario.crear_estudiante(nombre, email, "hash", uuid.uuid4())
    else:
        usuario = Usuario.crear(nombre, email, "hash", tipo_perfil)
    usuario.bloqueada = bloqueada
    return usuario


class TestListarCuentasUseCase:
    async def test_listado_sin_filtros_devuelve_todas_las_cuentas(self):
        repo = FakeCuentaQueryRepository()
        docente = _usuario("Docente", "docente@fiuner.edu.ar", TipoPerfil.DOCENTE)
        admin = _usuario("Admin", "admin@fiuner.edu.ar", TipoPerfil.ADMINISTRADOR)
        repo.usuarios[docente.id] = docente
        repo.usuarios[admin.id] = admin
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(None, None, None)

        assert {u.id for u in resultado.cuentas} == {docente.id, admin.id}
        assert resultado.total == 2

    async def test_filtro_combinado_por_rol_y_estado(self):
        repo = FakeCuentaQueryRepository()
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

        assert len(resultado.cuentas) == 1
        assert resultado.cuentas[0].id == estudiante_bloqueado.id

    async def test_busqueda_por_email_parcial(self):
        repo = FakeCuentaQueryRepository()
        objetivo = _usuario("Marisa Gonzalez", "mgonzalez@fiuner.edu.ar", TipoPerfil.DOCENTE)
        otro = _usuario("Juan Perez", "jperez@fiuner.edu.ar", TipoPerfil.DOCENTE)
        repo.usuarios[objetivo.id] = objetivo
        repo.usuarios[otro.id] = otro
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(None, None, "mgonzalez")

        assert len(resultado.cuentas) == 1
        assert resultado.cuentas[0].id == objetivo.id

    async def test_busqueda_case_insensitive_contra_nombre(self):
        repo = FakeCuentaQueryRepository()
        usuario = _usuario("Marisa Gonzalez", "mgonzalez@fiuner.edu.ar", TipoPerfil.DOCENTE)
        repo.usuarios[usuario.id] = usuario
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(None, None, "MARISA")

        assert len(resultado.cuentas) == 1
        assert resultado.cuentas[0].id == usuario.id

    async def test_sin_resultados_devuelve_lista_vacia(self):
        repo = FakeCuentaQueryRepository()
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(None, None, "no-existe")

        assert resultado.cuentas == []
        assert resultado.total == 0

    async def test_pagina_y_tamanio_pagina_limitan_el_resultado_pero_no_el_total(self):
        repo = FakeCuentaQueryRepository()
        for i in range(5):
            u = _usuario(f"Docente {i}", f"docente{i}@fiuner.edu.ar", TipoPerfil.DOCENTE)
            repo.usuarios[u.id] = u
        use_case = ListarCuentasUseCase(repo)

        resultado = await use_case.execute(None, None, None, pagina=1, tamanio_pagina=2)

        assert len(resultado.cuentas) == 2
        assert resultado.total == 5
