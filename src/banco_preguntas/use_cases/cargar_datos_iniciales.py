"""Caso de uso: carga de una materia y sus preguntas desde un archivo ya leído (`US-8.7.1`)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from src.banco_preguntas.entities.errors import OpcionesInvalidas
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)
from src.banco_preguntas.use_cases.cargar_pregunta_verdadero_falso import (
    CargarPreguntaVerdaderoFalsoUseCase,
)
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase


class ArchivoInvalido(Exception):
    """El archivo de datos no se puede cargar: formato incorrecto o una pregunta inválida."""


@dataclass(frozen=True)
class PreguntaACargar:
    """Una pregunta leída del archivo: opción múltiple si trae `opciones`, si no verdadero/falso."""

    metadatos: MetadatosPregunta
    opciones: tuple[Opcion, ...] | None = None
    respuesta_correcta: bool | None = None


@dataclass(frozen=True)
class ArchivoDeDatos:
    """Contenido de un archivo: la materia destino y sus preguntas, en orden."""

    origen: str
    materia: str
    preguntas: tuple[PreguntaACargar, ...]


@dataclass(frozen=True)
class ResultadoCarga:
    """Resumen de la carga de un archivo."""

    materia: str
    materia_creada: bool
    cargadas: int
    omitidas: int


def _validar(archivo: ArchivoDeDatos, banco_id: UUID) -> None:
    """Construye cada pregunta en memoria para aplicar INV-BP-02/03 antes de escribir nada."""
    for posicion, pregunta in enumerate(archivo.preguntas, start=1):
        if pregunta.opciones is None:
            continue
        try:
            PreguntaPlantillaOpcionMultiple.crear(
                banco_id, pregunta.metadatos, list(pregunta.opciones)
            )
        except OpcionesInvalidas as error:
            raise ArchivoInvalido(f"pregunta {posicion}: {error}") from error


def _sin_repetidas(
    preguntas: tuple[PreguntaACargar, ...], existentes: set[str]
) -> list[PreguntaACargar]:
    """Deja las preguntas cuyo texto no está cargado ni se repite dentro del mismo archivo."""
    vistos = set(existentes)
    nuevas: list[PreguntaACargar] = []
    for pregunta in preguntas:
        if pregunta.metadatos.texto not in vistos:
            vistos.add(pregunta.metadatos.texto)
            nuevas.append(pregunta)
    return nuevas


class CargarDatosInicialesUseCase:
    """Crea la materia si falta y carga sus preguntas, omitiendo las ya existentes."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        materia_repositorio: MateriaRepositoryPort,
        banco_repositorio: BancoRepositoryPort,
        pregunta_repositorio: PreguntaRepositoryPort,
        crear_materia: CrearMateriaUseCase,
        cargar_opcion_multiple: CargarPreguntaOpcionMultipleUseCase,
        cargar_verdadero_falso: CargarPreguntaVerdaderoFalsoUseCase,
    ) -> None:
        """Recibe los repositorios y los casos de uso de alta que reutiliza."""
        self._materias = materia_repositorio
        self._bancos = banco_repositorio
        self._preguntas = pregunta_repositorio
        self._crear_materia = crear_materia
        self._cargar_opcion_multiple = cargar_opcion_multiple
        self._cargar_verdadero_falso = cargar_verdadero_falso

    async def execute(self, archivo: ArchivoDeDatos, simular: bool = False) -> ResultadoCarga:
        """Valida el archivo completo y carga lo que falta; con `simular` no escribe nada.

        Levanta `ArchivoInvalido` (con la posición de la pregunta) si alguna es inválida,
        sin haber cargado ninguna.
        """
        materia = await self._materias.obtener_por_nombre(archivo.materia)
        banco = await self._bancos.obtener_por_materia_id(materia.id) if materia else None
        banco_id = banco.id if banco else uuid4()
        _validar(archivo, banco_id)

        existentes: set[str] = set()
        if banco is not None:
            activas = await self._preguntas.filtrar(banco_id=banco.id)
            existentes = {p.metadatos.texto for p in activas.preguntas}
        nuevas = _sin_repetidas(archivo.preguntas, existentes)

        if not simular:
            if banco is None:
                _, creado, _, _ = await self._crear_materia.execute(archivo.materia)
                banco_id = creado.id
            await self._persistir(banco_id, nuevas)
        return ResultadoCarga(
            materia=archivo.materia,
            materia_creada=materia is None,
            cargadas=len(nuevas),
            omitidas=len(archivo.preguntas) - len(nuevas),
        )

    async def _persistir(self, banco_id: UUID, preguntas: list[PreguntaACargar]) -> None:
        """Guarda cada pregunta con el caso de uso de su tipo (sin autorización por Comisión)."""
        for pregunta in preguntas:
            if pregunta.opciones is not None:
                await self._cargar_opcion_multiple.execute(
                    banco_id, pregunta.metadatos, list(pregunta.opciones)
                )
            else:
                await self._cargar_verdadero_falso.execute(
                    banco_id, pregunta.metadatos, bool(pregunta.respuesta_correcta)
                )
