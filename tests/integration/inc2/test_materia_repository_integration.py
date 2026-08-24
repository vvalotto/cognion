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

    async def test_listar_incluye_materias_persistidas(self, session):
        repo = SQLAlchemyMateriaRepository(session)
        materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
        await repo.guardar(materia)

        materias = await repo.listar()

        assert any(m.id == materia.id and m.nombre == materia.nombre for m in materias)


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

    async def test_obtener_por_materia_id(self, session):
        materia_repo = SQLAlchemyMateriaRepository(session)
        banco_repo = SQLAlchemyBancoRepository(session)
        materia = Materia.crear(f"Análisis de Sistemas {uuid.uuid4()}")
        await materia_repo.guardar(materia)
        banco = Banco.crear(materia.id)
        await banco_repo.guardar(banco)

        recuperado = await banco_repo.obtener_por_materia_id(materia.id)

        assert recuperado is not None
        assert recuperado.id == banco.id

    async def test_obtener_por_materia_id_inexistente_retorna_none(self, session):
        banco_repo = SQLAlchemyBancoRepository(session)

        assert await banco_repo.obtener_por_materia_id(uuid.uuid4()) is None
