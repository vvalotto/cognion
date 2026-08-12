import uuid

from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.identidad.frameworks.adapters.materia_port_in_process import MateriaPortInProcess


class TestMateriaPortInProcessIntegration:
    async def test_obtener_resuelve_materia_persistida_por_banco_preguntas(self, session):
        materia_repo = SQLAlchemyMateriaRepository(session)
        materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
        await materia_repo.guardar(materia)

        puerto = MateriaPortInProcess(session)
        resultado = await puerto.obtener(materia.id)

        assert resultado is not None
        assert resultado.id == materia.id
        assert resultado.nombre == materia.nombre

    async def test_obtener_materia_inexistente_retorna_none(self, session):
        puerto = MateriaPortInProcess(session)

        assert await puerto.obtener(uuid.uuid4()) is None
