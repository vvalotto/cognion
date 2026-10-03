import uuid

import pytest

from src.identidad.entities.errors import (
    CredencialesInvalidas,
    CuentaBloqueadaError,
    CuentaDeshabilitadaError,
)
from src.identidad.entities.eventos import CuentaBloqueada, SesionIniciada
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.iniciar_sesion import IniciarSesionUseCase
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.unit.inc1._fakes import FakeJWTIssuer, FakePasswordHasher, FakeUsuarioRepository


class TestIniciarSesionUseCase:
    async def test_login_exitoso_docente(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        jwt_issuer = FakeJWTIssuer()
        usuario = Usuario.crear(
            "Docente", "docente@fiuner.edu.ar", hasher.hash("Docente#2026"), TipoPerfil.DOCENTE
        )
        usuario_repo.usuarios[usuario.id] = usuario

        use_case = IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer)
        jwt_vo, evento = await use_case.execute("docente@fiuner.edu.ar", "Docente#2026")

        assert jwt_vo.rol == TipoPerfil.DOCENTE
        assert isinstance(evento, SesionIniciada)
        assert evento.usuario_id == usuario.id
        assert evento.rol == TipoPerfil.DOCENTE
        assert jwt_issuer.emitidos == [(usuario.id, TipoPerfil.DOCENTE)]

    async def test_login_exitoso_administrador(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        jwt_issuer = FakeJWTIssuer()
        usuario = Usuario.crear(
            "Admin", "admin@fiuner.edu.ar", hasher.hash("Admin#2026"), TipoPerfil.ADMINISTRADOR
        )
        usuario_repo.usuarios[usuario.id] = usuario

        use_case = IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer)
        jwt_vo, _evento = await use_case.execute("admin@fiuner.edu.ar", "Admin#2026")

        assert jwt_vo.rol == TipoPerfil.ADMINISTRADOR

    async def test_login_exitoso_estudiante(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        jwt_issuer = FakeJWTIssuer()
        usuario = Usuario.crear_estudiante(
            "Estudiante", "estudiante@fiuner.edu.ar", hasher.hash("Estudiante#2026"), uuid.uuid4()
        )
        usuario_repo.usuarios[usuario.id] = usuario

        use_case = IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer)
        jwt_vo, _evento = await use_case.execute("estudiante@fiuner.edu.ar", "Estudiante#2026")

        assert jwt_vo.rol == TipoPerfil.ESTUDIANTE

    async def test_rechaza_password_incorrecta(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        jwt_issuer = FakeJWTIssuer()
        usuario = Usuario.crear(
            "Docente", "docente@fiuner.edu.ar", hasher.hash("Docente#2026"), TipoPerfil.DOCENTE
        )
        usuario_repo.usuarios[usuario.id] = usuario

        use_case = IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer)

        with pytest.raises(CredencialesInvalidas):
            await use_case.execute("docente@fiuner.edu.ar", "password-incorrecta")

        assert jwt_issuer.emitidos == []

    async def test_rechaza_email_inexistente(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        jwt_issuer = FakeJWTIssuer()

        use_case = IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer)

        with pytest.raises(CredencialesInvalidas):
            await use_case.execute("no-existe@fiuner.edu.ar", "cualquier-password")

        assert jwt_issuer.emitidos == []

    async def test_mensaje_identico_para_email_inexistente_y_password_incorrecta(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        jwt_issuer = FakeJWTIssuer()
        usuario = Usuario.crear(
            "Docente", "docente@fiuner.edu.ar", hasher.hash("Docente#2026"), TipoPerfil.DOCENTE
        )
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer)

        with pytest.raises(CredencialesInvalidas) as exc_password:
            await use_case.execute("docente@fiuner.edu.ar", "password-incorrecta")
        with pytest.raises(CredencialesInvalidas) as exc_email:
            await use_case.execute("no-existe@fiuner.edu.ar", "cualquier-password")

        assert str(exc_password.value) == str(exc_email.value)


class TestBloqueoCuentaLogin:
    """US-2.2.1: bloqueo automático por 3 intentos fallidos consecutivos de login."""

    def _crear_usuario(self, hasher: FakePasswordHasher, **overrides: object) -> Usuario:
        usuario = Usuario.crear(
            "Docente", "docente@fiuner.edu.ar", hasher.hash("Docente#2026"), TipoPerfil.DOCENTE
        )
        for campo, valor in overrides.items():
            setattr(usuario, campo, valor)
        return usuario

    async def test_fallo_que_no_llega_al_limite(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, intentos_fallidos_login=1)
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, FakeJWTIssuer())

        with pytest.raises(CredencialesInvalidas) as exc:
            await use_case.execute("docente@fiuner.edu.ar", "password-incorrecta")

        actualizado = usuario_repo.usuarios[usuario.id]
        assert actualizado.intentos_fallidos_login == 2
        assert actualizado.bloqueada is False
        assert exc.value.evento_cuenta_bloqueada is None

    async def test_tercer_fallo_consecutivo_bloquea_la_cuenta(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, intentos_fallidos_login=2)
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, FakeJWTIssuer())

        with pytest.raises(CredencialesInvalidas) as exc:
            await use_case.execute("docente@fiuner.edu.ar", "password-incorrecta")

        actualizado = usuario_repo.usuarios[usuario.id]
        assert actualizado.intentos_fallidos_login == 3
        assert actualizado.bloqueada is True
        assert isinstance(exc.value.evento_cuenta_bloqueada, CuentaBloqueada)
        assert exc.value.evento_cuenta_bloqueada.usuario_id == usuario.id

    async def test_acierto_resetea_el_contador(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, intentos_fallidos_login=2)
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, FakeJWTIssuer())

        await use_case.execute("docente@fiuner.edu.ar", "Docente#2026")

        assert usuario_repo.usuarios[usuario.id].intentos_fallidos_login == 0

    async def test_intento_sobre_cuenta_ya_bloqueada(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, bloqueada=True, intentos_fallidos_login=3)
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, FakeJWTIssuer())

        with pytest.raises(CuentaBloqueadaError) as exc:
            await use_case.execute("docente@fiuner.edu.ar", "cualquier-password")

        assert exc.value.usuario_id == usuario.id
        assert usuario_repo.usuarios[usuario.id].intentos_fallidos_login == 3


class TestCuentaDeshabilitadaLogin:
    """US-ADJ-59 (INV-ID-18): una cuenta deshabilitada no puede iniciar sesión."""

    def _crear_usuario(self, hasher: FakePasswordHasher, **overrides: object) -> Usuario:
        usuario = Usuario.crear(
            "Docente", "docente@fiuner.edu.ar", hasher.hash("Docente#2026"), TipoPerfil.DOCENTE
        )
        for campo, valor in overrides.items():
            setattr(usuario, campo, valor)
        return usuario

    async def test_rechaza_con_la_contrasena_correcta_y_no_emite_jwt(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        jwt_issuer = FakeJWTIssuer()
        usuario = self._crear_usuario(hasher, deshabilitada=True)
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer)

        with pytest.raises(CuentaDeshabilitadaError) as exc:
            await use_case.execute("docente@fiuner.edu.ar", "Docente#2026")

        assert exc.value.usuario_id == usuario.id
        assert jwt_issuer.emitidos == []

    async def test_el_rechazo_no_depende_de_la_contrasena_ni_consume_intentos(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, deshabilitada=True)
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, FakeJWTIssuer())

        with pytest.raises(CuentaDeshabilitadaError):
            await use_case.execute("docente@fiuner.edu.ar", "password-incorrecta")

        actualizado = usuario_repo.usuarios[usuario.id]
        assert actualizado.intentos_fallidos_login == 0
        assert actualizado.bloqueada is False

    async def test_el_mensaje_invita_a_contactar_a_un_administrador(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher, deshabilitada=True)
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, FakeJWTIssuer())

        with pytest.raises(CuentaDeshabilitadaError) as exc:
            await use_case.execute("docente@fiuner.edu.ar", "Docente#2026")

        assert "deshabilitada" in str(exc.value)
        assert "administrador" in str(exc.value)

    async def test_deshabilitada_tiene_prioridad_sobre_bloqueada(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(
            hasher, deshabilitada=True, bloqueada=True, intentos_fallidos_login=3
        )
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, FakeJWTIssuer())

        with pytest.raises(CuentaDeshabilitadaError):
            await use_case.execute("docente@fiuner.edu.ar", "Docente#2026")

        assert usuario_repo.usuarios[usuario.id].intentos_fallidos_login == 3

    async def test_reactivar_la_cuenta_restituye_el_acceso(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        jwt_issuer = FakeJWTIssuer()
        usuario = self._crear_usuario(hasher, deshabilitada=True)
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer)

        usuario.activar()
        jwt_vo, _evento = await use_case.execute("docente@fiuner.edu.ar", "Docente#2026")

        assert jwt_vo.rol == TipoPerfil.DOCENTE
        assert len(jwt_issuer.emitidos) == 1

    async def test_una_cuenta_activa_no_cambia_de_comportamiento(self):
        usuario_repo = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        usuario = self._crear_usuario(hasher)
        usuario_repo.usuarios[usuario.id] = usuario
        use_case = IniciarSesionUseCase(usuario_repo, hasher, FakeJWTIssuer())

        jwt_vo, evento = await use_case.execute("docente@fiuner.edu.ar", "Docente#2026")

        assert jwt_vo.rol == TipoPerfil.DOCENTE
        assert evento.usuario_id == usuario.id
