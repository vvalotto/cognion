# HITO-6 — El banco de preguntas no soporta volumen real sin paginación

> Estado documental: evidencia
> Registra un hallazgo de aprendizaje del ensayo IEDD en Cognion.
> No reemplaza a las fuentes vigentes (ADRs, arquitectura, specs).

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-6 — hallazgo de escalabilidad en UAT manual de Víctor con datos reales |
| **Fecha** | 2026-08-18 |
| **Incremento / contexto** | Incremento 2 (Banco de Preguntas), UAT manual de Víctor en navegador real, cargando el contenido real de la materia "Ingeniería de Software" (70 preguntas del banco docente + 1 previa) |
| **Relacionado** | `HITO-4`, `HITO-5`, `US-2.1.7`, `US-2.1.10`, `docs/specs/ajustes/US-ADJ-03.md`, `docs/design/ux/wireframes-banco-preguntas.md` |

---

## Contexto

`HITO-4` y `HITO-5` (2026-08-17) surgieron de un UAT ejercitando el flujo con datos mínimos —
1-2 preguntas por banco, suficientes para verificar comportamiento funcional, no volumen. El
2026-08-18, para continuar la UAT con un caso realista, se cargaron las 70 preguntas de opción
múltiple del banco docente real de Víctor (`Preguntas Evaluación Ingeniería de Software.docx`,
Módulo 1 de la materia) contra el mismo backend, vía script que reutiliza
`POST /preguntas/opcion-multiple` (sin endpoint nuevo).

## Hallazgo / Análisis

Con 71 preguntas activas en un solo banco, `Banco.tsx` (`US-2.1.10`) renderiza la tabla
completa de una sola vez — sin paginación ni virtualización, porque `GET /bancos/{id}/preguntas`
(`US-2.1.7`) nunca tuvo límite de resultados. Ningún criterio de aceptación de `US-2.1.7` o
`US-2.1.10` contempló esto: ambas specs (y el wireframe que las origina) se escribieron y
validaron contra fixtures de 1-2 preguntas, el mismo volumen que usa toda la suite de tests
automatizados del incremento — nada en el pipeline de CI ejercitó nunca un banco de tamaño
real.

A diferencia de `HITO-4` (divergencia no documentada) y `HITO-5` (recorte de alcance
documentado que igual dejó fricción), este hallazgo tiene una causa raíz distinta: no fue una
decisión de alcance ni un desvío de implementación — fue una dimensión del problema
(volumen de datos) que ninguna spec, wireframe ni test consideró, porque hasta este UAT nunca
hubo datos reales de la magnitud que un Docente realmente carga en un cuatrimestre.

**Decisión de Víctor:** paginar en el backend (no solo cortar en el cliente), tamaño de
página fijo de 20, agregar `fecha_creacion` como criterio de orden estable (no existía),
resetear a página 1 al cambiar cualquier filtro, UI de números de página + Anterior/Siguiente.
Especificado en `US-ADJ-03` — pendiente de implementación.

## Aprendizaje(s)

- **L-6.1:** Los fixtures de test y los datos de UAT con volumen mínimo (1-2 registros)
  verifican corrección funcional pero no exponen problemas de escala — un flujo puede pasar
  270+ tests automatizados y una UAT completa de cierre de iteración, y aun así no aguantar el
  primer uso con datos reales de un Docente. La brecha solo se hizo visible al cargar contenido
  real, no al escribir más tests con los mismos fixtures pequeños.
- **L-6.2:** Cuando una US-IEDD expone un endpoint de listado sin límite (`US-2.1.7`,
  `filtrar()` sin paginación), esa omisión no genera ningún error ni test roto — el sistema
  "funciona" igual con 2 preguntas que con 200. El costo de la omisión es silencioso hasta que
  el volumen real lo expone, lo que la vuelve más difícil de detectar en revisión de código que
  un bug funcional.

---

## Relación con la hipótesis del ensayo

Refuerza un punto ya señalado en `HITO-5`: los criterios de aceptación de una US, por más
completos que estén en su Gherkin, están acotados por el volumen de datos que su autor tuvo en
mente al escribirlos. Ninguna revisión de código ni suite de tests con fixtures pequeños
sustituye una UAT con datos de la escala real de uso — el ensayo IEDD asume que UAT + revisión
humana cierran ese gap, y este HITO es evidencia directa de que, en este caso, así fue: el
gap solo se hizo visible al cargar contenido real, no antes.

---

## Valoración conjunta de NC-1/NC-2/NC-3 (US-ADJ-01/02/03)

Comentario de cierre de sesión, a pedido de Víctor, comparando los tres hallazgos de ajuste
del Banco de Preguntas antes de decidir cómo seguir con el próximo incremento:

Los tres no son el mismo tipo de problema:

- **`US-ADJ-01`** (divergencia visual, `HITO-4`) es una desviación de implementación respecto
  a un prototipo ya aprobado — nadie tomó una decisión consciente, el código simplemente no
  siguió el diseño. Deuda de calidad, no urgente: no afecta funcionalidad ni datos.
- **`US-ADJ-02`** (unidad/tema texto libre, `HITO-5`) fue una decisión **consciente y
  documentada** en su momento (sin catálogo, sin endpoint) que igual dejó fricción real de
  uso. Es el caso más sano de los tres: la decisión estaba justificada, el UAT la corrigió con
  una solución barata (derivar del cliente, sin tocar el backend), y ya está resuelta.
- **`US-ADJ-03`** (paginación, este HITO) es cualitativamente distinto: no es un desvío ni una
  decisión de alcance — es una dimensión del problema que ninguna spec, wireframe ni test
  consideró, porque hasta esta UAT nunca hubo datos con volumen real corriendo contra el
  sistema. Pasó 270+ tests automatizados y una UAT completa de cierre de iteración sin que nada
  lo detectara, porque los fixtures usan 1-2 preguntas en todos lados (`L-6.1`).

El patrón que más preocupa no es ninguno de los tres individualmente, sino lo que el conjunto
— sobre todo este HITO — dice del proceso: **la UAT de cierre de iteración certificó "listo"
con datos de juguete.** Los gates automatizados (pytest, Vitest, DesignReviewer) nunca van a
atrapar esto porque no falla nada, solo degrada (`L-6.2`). Sugerencia para
`docs/plans/PROCEDIMIENTO-UAT.md`: que al menos una corrida de UAT por incremento use datos de
volumen real (no necesariamente 70+ registros, pero sí más de 2) — queda como sugerencia
abierta, no aplicada, porque es una decisión de proceso de Víctor.

Ninguno de los tres bloquea arrancar el próximo incremento — los tres son mejoras acotadas al
Banco de Preguntas existente, no defectos que invaliden lo ya cerrado.

---

## Resumen de Aprendizajes

| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-6.1 | Fixtures/UAT con volumen mínimo no exponen problemas de escala — hace falta UAT con datos reales para encontrarlos | Proceso |
| L-6.2 | Un endpoint sin límite de resultados no falla ningún test ni bloquea ningún gate — el costo es silencioso hasta que el volumen real lo expone | Arquitectura / Quality Gates |

---

*Creado: 2026-08-18*
