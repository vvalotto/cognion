"""Ayudas compartidas por los tests de la carga de datos iniciales (US-8.7.1)."""

from __future__ import annotations

from pathlib import Path

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.use_cases.cargar_datos_iniciales import (
    ArchivoDeDatos,
    CargarDatosInicialesUseCase,
    PreguntaACargar,
)
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)
from src.banco_preguntas.use_cases.cargar_pregunta_verdadero_falso import (
    CargarPreguntaVerdaderoFalsoUseCase,
)
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase
from tests.unit.inc2._fakes import (
    FakeBancoRepository,
    FakeComisionConsultaPort,
    FakeMateriaRepository,
    FakePreguntaRepository,
)


class Entorno:
    """Casos de uso reales sobre repositorios en memoria."""

    def __init__(self) -> None:
        """Arma los repositorios falsos y el caso de uso a probar."""
        self.materias = FakeMateriaRepository()
        self.bancos = FakeBancoRepository()
        self.preguntas = FakePreguntaRepository()
        comisiones = FakeComisionConsultaPort()
        self.caso_de_uso = CargarDatosInicialesUseCase(
            self.materias,
            self.bancos,
            self.preguntas,
            CrearMateriaUseCase(self.materias, self.bancos),
            CargarPreguntaOpcionMultipleUseCase(self.bancos, self.preguntas, comisiones),
            CargarPreguntaVerdaderoFalsoUseCase(self.bancos, self.preguntas, comisiones),
        )


def metadatos(texto: str) -> MetadatosPregunta:
    """Metadatos de prueba con el texto indicado."""
    return MetadatosPregunta(texto, "Unidad", "Tema", Dificultad.MEDIO, Importancia.MEDIO)


def opcion_multiple(texto: str, correctas: int = 1) -> PreguntaACargar:
    """Pregunta de opción múltiple con 3 opciones y `correctas` marcadas como correctas."""
    opciones = tuple(Opcion(f"op{i}", i < correctas) for i in range(3))
    return PreguntaACargar(metadatos=metadatos(texto), opciones=opciones)


def verdadero_falso(texto: str) -> PreguntaACargar:
    """Pregunta de verdadero/falso."""
    return PreguntaACargar(metadatos=metadatos(texto), respuesta_correcta=True)


def archivo(*preguntas: PreguntaACargar, materia: str = "Materia") -> ArchivoDeDatos:
    """Archivo de datos con las preguntas dadas."""
    return ArchivoDeDatos(origen="a.json", materia=materia, preguntas=tuple(preguntas))


CUESTIONARIO = """# Cuestionario — Riesgos

**Unidad temática:** 09 – Incertidumbre
**Preguntas:** 2

---

**Pregunta 1.** ¿Qué es un riesgo?

a) Un problema que ya ocurrió.
b) Una condición incierta con efecto en los objetivos.
c) Un cambio aprobado.
d) Un error de planificación.

✅ **Respuesta correcta: b)** — Justificación. *(Nivel: Fácil)*

---

**Pregunta 2.** ¿Qué significa VUCA?

a) Valor, uso, calidad y alcance.
b) Volatilidad, incertidumbre, complejidad y ambigüedad.
c) Variación, urgencia, costo y alcance.

✅ **Respuesta correcta: b)** — Justificación. *(Nivel: Difícil)*
"""


def escribir(carpeta: Path, nombre: str, contenido: str) -> Path:
    """Escribe un archivo de prueba y devuelve su ruta."""
    ruta = carpeta / nombre
    ruta.write_text(contenido, encoding="utf-8")
    return ruta
