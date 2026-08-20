import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil


class TestUsuariosAPIIntegration:
    async def test_crear_usuario_devuelve_201(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/usuarios",
                json={
                    "nombre": "Ana Docente",
                    "email": "ana.api@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "ana.api@fiuner.edu.ar"
        assert body["perfil"] == "docente"

    async def test_crear_usuario_email_duplicado_devuelve_409(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "nombre": "Ana",
                "email": "duplicado@fiuner.edu.ar",
                "password": "claveSegura1",
                "perfil": "docente",
            }
            await client.post("/usuarios", json=payload, headers=admin_headers)
            response = await client.post("/usuarios", json=payload, headers=admin_headers)

        assert response.status_code == 409


class TestListarCuentasAPIIntegration:
    """US-2.2.2: listado de cuentas con filtros por rol/estado/búsqueda."""

    async def test_listado_sin_filtros_devuelve_todas_las_cuentas(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Listado Uno",
                    "email": "listado.uno@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            response = await client.get("/usuarios", headers=admin_headers)

        assert response.status_code == 200
        emails = [c["email"] for c in response.json()]
        assert "listado.uno@fiuner.edu.ar" in emails

    async def test_filtro_por_rol_y_busqueda_por_email_parcial(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Marisa Gonzalez",
                    "email": "mgonzalez.api@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Admin Distinto",
                    "email": "admin.distinto@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "administrador",
                },
                headers=admin_headers,
            )

            response = await client.get(
                "/usuarios",
                params={"rol": "docente", "busqueda": "mgonzalez"},
                headers=admin_headers,
            )

        assert response.status_code == 200
        cuentas = response.json()
        assert len(cuentas) == 1
        assert cuentas[0]["email"] == "mgonzalez.api@fiuner.edu.ar"
        assert cuentas[0]["perfil"] == "docente"
        assert cuentas[0]["bloqueada"] is False

    async def test_filtro_por_estado_activa(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/usuarios",
                json={
                    "nombre": "Cuenta Activa",
                    "email": "activa.api@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )

            response = await client.get(
                "/usuarios", params={"estado": "activa"}, headers=admin_headers
            )

        assert response.status_code == 200
        emails = [c["email"] for c in response.json()]
        assert "activa.api@fiuner.edu.ar" in emails
        assert all(c["bloqueada"] is False for c in response.json())

    async def test_requiere_rol_administrador(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/usuarios")

        assert response.status_code == 401


class TestObtenerCuentaAPIIntegration:
    """US-2.2.3: detalle de una cuenta puntual."""

    async def test_detalle_de_un_docente(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            creado = await client.post(
                "/usuarios",
                json={
                    "nombre": "Detalle Docente",
                    "email": "detalle.docente@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            usuario_id = creado.json()["id"]

            response = await client.get(f"/usuarios/{usuario_id}", headers=admin_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "detalle.docente@fiuner.edu.ar"
        assert body["perfil"] == "docente"
        assert body["comision_id"] is None
        assert "creado_en" in body

    async def test_detalle_de_un_estudiante_incluye_comision_id(self, session, admin_headers):
        hasher = BcryptPasswordHasher()
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Admin Detalle",
            f"admin.detalle.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        estudiante = Usuario.crear_estudiante(
            "Estudiante Detalle",
            f"estudiante.detalle.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("Estudiante#2026"),
            comision.id,
        )
        await usuario_repo.guardar(estudiante)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/usuarios/{estudiante.id}", headers=admin_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["perfil"] == "estudiante"
        assert body["comision_id"] == str(comision.id)

    async def test_cuenta_inexistente_devuelve_404(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/usuarios/{uuid.uuid4()}", headers=admin_headers)

        assert response.status_code == 404

    async def test_requiere_rol_administrador(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/usuarios/{uuid.uuid4()}")

        assert response.status_code == 401


class TestResetearPasswordAPIIntegration:
    """US-2.2.4: reseteo de contraseña de una cuenta, con desbloqueo si corresponde."""

    async def test_reseteo_de_cuenta_bloqueada_la_desbloquea(self, session, admin_headers):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        usuario = Usuario.crear(
            "Bloqueado Reseteo",
            f"bloqueado.reseteo.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("claveVieja1"),
            TipoPerfil.DOCENTE,
        )
        usuario.bloqueada = True
        usuario.intentos_fallidos_login = 3
        await usuario_repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/usuarios/{usuario.id}/resetear-password",
                json={"password_nueva": "claveNueva123"},
                headers=admin_headers,
            )

        assert response.status_code == 200
        body = response.json()
        assert body["bloqueada"] is False

    async def test_password_reseteada_habilita_login(self, session, admin_headers):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        hasher = BcryptPasswordHasher()
        email = f"login.reseteo.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear(
            "Login Reseteo", email, hasher.hash("claveVieja1"), TipoPerfil.DOCENTE
        )
        await usuario_repo.guardar(usuario)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                f"/usuarios/{usuario.id}/resetear-password",
                json={"password_nueva": "claveNueva123"},
                headers=admin_headers,
            )
            response = await client.post(
                "/identidad/login", json={"email": email, "password": "claveNueva123"}
            )

        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_reseteo_de_cuenta_activa_no_la_bloquea(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            creado = await client.post(
                "/usuarios",
                json={
                    "nombre": "Activa Reseteo",
                    "email": f"activa.reseteo.{uuid.uuid4()}@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            usuario_id = creado.json()["id"]

            response = await client.post(
                f"/usuarios/{usuario_id}/resetear-password",
                json={"password_nueva": "claveNueva123"},
                headers=admin_headers,
            )

        assert response.status_code == 200
        assert response.json()["bloqueada"] is False

    async def test_password_demasiado_corta_devuelve_422(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            creado = await client.post(
                "/usuarios",
                json={
                    "nombre": "Corta Reseteo",
                    "email": f"corta.reseteo.{uuid.uuid4()}@fiuner.edu.ar",
                    "password": "claveSegura1",
                    "perfil": "docente",
                },
                headers=admin_headers,
            )
            usuario_id = creado.json()["id"]

            response = await client.post(
                f"/usuarios/{usuario_id}/resetear-password",
                json={"password_nueva": "corta"},
                headers=admin_headers,
            )

        assert response.status_code == 422

    async def test_cuenta_inexistente_devuelve_404(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/usuarios/{uuid.uuid4()}/resetear-password",
                json={"password_nueva": "claveNueva123"},
                headers=admin_headers,
            )

        assert response.status_code == 404

    async def test_requiere_rol_administrador(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/usuarios/{uuid.uuid4()}/resetear-password",
                json={"password_nueva": "claveNueva123"},
            )

        assert response.status_code == 401
