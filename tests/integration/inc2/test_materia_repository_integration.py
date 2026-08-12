import uuid

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.interface_adapters.gateways.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)


class TestSQLAlchemyMateriaRepositoryIntegration:
    async def test_guardar_y_obtener_por_nombre(self, session):
        repo = SQLAlchemyMateriaRepository(session)
        materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")

        await repo.guardar(materia)
        recuperada = await repo.obtener_por_nombre(materia.nombre)

        assert recuperada is not None
        assert recuperada.id == materia.id
        assert recuperada.nombre == materia.nombre

    async def test_obtener_por_nombre_inexistente_retorna_none(self, session):
        repo = SQLAlchemyMateriaRepository(session)

        assert await repo.obtener_por_nombre("No existe") is None


class TestSQLAlchemyBancoRepositoryIntegration:
    async def test_guardar_banco_asociado_a_materia(self, session):
        materia_repo = SQLAlchemyMateriaRepository(session)
        banco_repo = SQLAlchemyBancoRepository(session)
        materia = Materia.crear(f"Gestión de Proyectos {uuid.uuid4()}")
        await materia_repo.guardar(materia)

        banco = Banco.crear(materia.id)
        await banco_repo.guardar(banco)

        recuperada = await materia_repo.obtener_por_nombre(materia.nombre)
        assert recuperada is not None
