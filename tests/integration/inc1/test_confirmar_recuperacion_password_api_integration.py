import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update

from src.app import app
from src.identidad.frameworks.db.models import TokenRecuperacionPasswordModel, UsuarioModel


async def _crear_docente_y_token(client: AsyncClient, admin_headers: dict[str, str]) -> tuple[str, str]:
    """Crea un docente, solicita recuperación y devuelve (email, token generado)."""
    email = f"docente.confirmar.{uuid.uuid4()}@fiuner.edu.ar"
    await client.post(
        "/usuarios",
        json={
            "nombre": "Docente Confirmación",
            "email": email,
            "password": "claveVieja1#xyz",
            "perfil": "docente",
        },
        headers=admin_headers,
    )
    await client.post("/identidad/recuperar-password/solicitar", json={"email": email})
    return email


class TestConfirmarRecuperacionPasswordAPIIntegration:
    async def test_confirmar_con_token_vigente_actualiza_password_y_permite_login(
        self, admin_headers, session
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            email = await _crear_docente_y_token(client, admin_headers)
            resultado = await session.execute(select(TokenRecuperacionPasswordModel))
            token_str = resultado.scalar_one().token

            response = await client.post(
                "/identidad/recuperar-password/confirmar",
                json={"token": token_str, "password_nueva": "NuevaClave2#xyz"},
            )
            assert response.status_code == 200

            login_response = await client.post(
                "/identidad/login",
                json={"email": email, "password": "NuevaClave2#xyz"},
            )
            assert login_response.status_code == 200

        resultado = await session.execute(
            select(TokenRecuperacionPasswordModel).where(
                TokenRecuperacionPasswordModel.token == token_str
            )
        )
        token_en_db = resultado.scalar_one()
        assert token_en_db.usado_en is not None

    async def test_confirmar_con_token_ya_usado_responde_422_y_no_cambia_password(
        self, admin_headers, session
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            email = await _crear_docente_y_token(client, admin_headers)
            resultado = await session.execute(select(TokenRecuperacionPasswordModel))
            token_str = resultado.scalar_one().token

            primera = await client.post(
                "/identidad/recuperar-password/confirmar",
                json={"token": token_str, "password_nueva": "NuevaClave2#xyz"},
            )
            assert primera.status_code == 200

            segunda = await client.post(
                "/identidad/recuperar-password/confirmar",
                json={"token": token_str, "password_nueva": "OtraClave3#xyz"},
            )
            assert segunda.status_code == 422

            login_con_password_vieja = await client.post(
                "/identidad/login",
                json={"email": email, "password": "OtraClave3#xyz"},
            )
            assert login_con_password_vieja.status_code == 401

    async def test_confirmar_con_token_vencido_responde_422(self, admin_headers, session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _crear_docente_y_token(client, admin_headers)
            resultado = await session.execute(select(TokenRecuperacionPasswordModel))
            token_str = resultado.scalar_one().token

            await session.execute(
                update(TokenRecuperacionPasswordModel)
                .where(TokenRecuperacionPasswordModel.token == token_str)
                .values(expira_en=datetime.now(UTC) - timedelta(seconds=1))
            )
            await session.commit()

            response = await client.post(
                "/identidad/recuperar-password/confirmar",
                json={"token": token_str, "password_nueva": "NuevaClave2#xyz"},
            )

        assert response.status_code == 422

    async def test_confirmar_con_token_inexistente_responde_422(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/recuperar-password/confirmar",
                json={"token": "token-que-no-existe", "password_nueva": "NuevaClave2#xyz"},
            )

        assert response.status_code == 422

    async def test_confirmar_con_password_debil_responde_422(self, admin_headers, session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            email = await _crear_docente_y_token(client, admin_headers)
            resultado = await session.execute(select(TokenRecuperacionPasswordModel))
            token_str = resultado.scalar_one().token

            response = await client.post(
                "/identidad/recuperar-password/confirmar",
                json={"token": token_str, "password_nueva": "debilsinmayus1"},
            )
            assert response.status_code == 422

            login_con_password_vieja = await client.post(
                "/identidad/login",
                json={"email": email, "password": "claveVieja1#xyz"},
            )
            assert login_con_password_vieja.status_code == 200

    async def test_confirmar_no_desbloquea_una_cuenta_bloqueada(self, admin_headers, session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            email = await _crear_docente_y_token(client, admin_headers)

            for _ in range(3):
                await client.post(
                    "/identidad/login", json={"email": email, "password": "password-incorrecta"}
                )

            resultado = await session.execute(select(TokenRecuperacionPasswordModel))
            token_str = resultado.scalar_one().token
            usuario_bloqueado = await session.execute(
                select(UsuarioModel).where(UsuarioModel.email == email)
            )
            assert usuario_bloqueado.scalar_one().bloqueada is True

            response = await client.post(
                "/identidad/recuperar-password/confirmar",
                json={"token": token_str, "password_nueva": "NuevaClave2#xyz"},
            )
            assert response.status_code == 200

            login_response = await client.post(
                "/identidad/login",
                json={"email": email, "password": "NuevaClave2#xyz"},
            )
            assert login_response.status_code == 403

        resultado = await session.execute(select(UsuarioModel).where(UsuarioModel.email == email))
        assert resultado.scalar_one().bloqueada is True
