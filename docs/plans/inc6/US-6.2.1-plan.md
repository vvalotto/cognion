# Plan de Implementación: US-6.2.1 - Cálculo de puntaje server-side

**Patrón:** clean-architecture, BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar)

1. **`puntaje_en_vivo.py` en `entities/`** con `NivelPregunta` (StrEnum `BAJO/MEDIO/ALTO`),
   `NivelesDePregunta` (dataclass frozen: `dificultad`, `importancia`) y `calcular_puntaje(...)`
   función pura. Sin imports de `banco_preguntas`.
2. **Fórmula con `round()` único al final**, tiempo acotado a `[0, limite]`, `limite <= 0` →
   `ValueError`, incorrecta → 0 (antes de cualquier otra validación de tiempo). Nota: `round()` de
   Python redondea half-to-even; se usa tal cual (`round`) como pide la spec. Los 3 valores de la
   spec (4000, 500, 1125) son exactos, sin ambigüedad.
3. **Puerto:** `PreguntaConsultaPort.obtener_niveles(pregunta_id) -> NivelesDePregunta`
   (abstracto). El adapter in-process mapea `Dificultad`/`Importancia` de Banco (valor
   `"alto"/"medio"/"bajo"`) a `NivelPregunta`; `pregunta is None` → `PreguntaNoAsignada(None, id)`,
   mismo criterio defensivo que los métodos hermanos.
4. **Fake:** `FakePreguntaConsultaPort.niveles: dict[UUID, NivelesDePregunta]`, default
   `BAJO/BAJO` si no se precargó (mismo criterio que `contenidos`).
5. **Sin `.feature`** (`skip_bdd`).

## Tareas

| # | Tarea | Archivo |
|---|---|---|
| 1 | `NivelPregunta`, `NivelesDePregunta`, `calcular_puntaje` | `src/actividad_evaluativa/entities/puntaje_en_vivo.py` |
| 2 | `obtener_niveles` en el puerto | `entities/ports/pregunta_consulta_port.py` |
| 3 | Adapter in-process | `frameworks/adapters/pregunta_consulta_port_in_process.py` |
| 4 | Fake con `niveles` | `tests/unit/inc3/_fakes.py` (+ chequear otros subclases del puerto con grep) |
| 5 | Unit: tabla de casos, bordes, redondeo, `ValueError` | `tests/unit/inc6/test_puntaje_en_vivo.py` |
| 6 | Integración: adapter contra DB real (OM y V/F, pregunta inexistente) | `tests/integration/inc6/test_pregunta_consulta_niveles.py` |
| 7 | Quality gates, documentación, reporte | — |

## Riesgos
- Cualquier otra implementación concreta de `PreguntaConsultaPort` se rompe al agregar el método
  abstracto → grep previo (tarea 4).
