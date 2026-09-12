# BC Analytics — Wireframes: Portal de Desempeño

> Estado documental: **vigente — §2, §3.0 y §3.1 (RF-15/16/17) aprobados por Víctor en el
> cierre del Issue [#228](https://github.com/vvalotto/cognion/issues/228), US-4.0.2,
> Incremento 4. §3.2 a §3.5 (RF-20 a 23) son ampliación nueva, ver nota abajo.**
> Alcance: RF-15 (vista de estudiante, acotada a evaluaciones de período abierto — sin
> sesiones en vivo, que no existen todavía), RF-16 (docente por alumno), RF-17 (docente por
> curso y tema).
>
> Fuente: `docs/rf/RF_v1.md` (RF-15, RF-16, RF-17), `docs/design/domain/BC-analytics-modelo.md`
> (queries `ObtenerDesempenoPorEvaluacion`, `ObtenerDesempenoAcumuladoPorMateria`,
> `ObtenerTasaErrorPorTema` — §4).
>
> Prototipo: `docs/design/ux/prototipos/analytics-portal-desempeno.html` — navegable, 7
> pantallas (3 de RF-15/16/17 + 4 de la ampliación de abajo).
>
> **Ampliación 2026-09-12 — pendiente de aprobación** (`US-ADJ-34`, Incremento 5-ADJ,
> `docs/plans/inc5-adj/inc5-adj-candidatas.md`): se agrega el §3.2 a §3.5 con las pantallas de
> RF-20 a RF-23, sobre el modelo ya aprobado en `BC-analytics-modelo.md` §8 (`US-ADJ-33`). No
> reemplaza nada de lo ya aprobado en `US-4.0.2` — solo agrega.

---

## 1. Identidad visual

Misma paleta y tipografía que `wireframes-actividad-evaluativa.md` §1,
`wireframes-banco-preguntas.md` §1 y `wireframes-cuentas-administracion.md` §1 (azul
institucional `#1D75B5`, verde de acento `#53AA74`, Roboto) — continuidad visual entre BCs e
iteraciones, sin redefinir tokens nuevos. Primitivas reutilizadas: `Card`, `Badge`,
`Breadcrumb`, `.summary-bar` (de la revisión de evaluación, `wireframes-actividad-evaluativa.md`
§3.5), `.progress-bar`. Primitivas **nuevas** de este BC: `.eval-item` (fila de evaluación con
resultado, más compacta que `.card` — no es clicable, no navega a ningún detalle adicional) y
`.tema-row` (fila de tema con barra de tasa de error, tres niveles de color según severidad).
Primitivas **nuevas de la ampliación RF-20 a 23**: `table.data-table` (mismo componente que
`Cuentas.tsx`/`Comisiones.tsx`, filas clicables cuando hay drill-down), `.line-chart-card`
(gráfico de línea en SVG, sin librería — dos series: individual y promedio de comisión),
`.ranking-row` (mismo esqueleto visual que `.tema-row`, adaptado a pregunta+enunciado) y
`.state-badge`/`.completitud-summary` (badge de estado con 4 variantes de color, resumen
numérico por estado).

---

## 2. Pantallas — Estudiante

### 2.0 Mi desempeño (`#est-desempeno`)

**Actor:** Estudiante.
**Query:** `ObtenerDesempenoAcumuladoPorMateria` (resumen) + `ObtenerDesempenoPorEvaluacion`
(detalle), ambas con el propio `estudiante_id` del token de sesión — RF-15.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Analytics › Mi desempeño" — entry point del BC para el estudiante |
| Selector | `Materia` — solo si el estudiante cursa más de una; si cursa una sola, sin selector (mismo criterio que el selector de materia ya evaluado en Actividad Evaluativa) |
| Resumen acumulado | `.summary-bar`: correctas, incorrectas, % de acierto y cantidad de evaluaciones finalizadas — todas acumuladas en la materia elegida |
| Detalle por evaluación | Una `.eval-item` por `Evaluacion` finalizada: título de la actividad, fecha de finalización, correctas/incorrectas de esa evaluación puntual |
| Estado vacío | Si el estudiante no tiene ninguna `Evaluacion` finalizada en la materia: mensaje simple ("Todavía no finalizaste ninguna evaluación de esta materia"), sin `.summary-bar` ni lista |
| Fuera de alcance | Ninguna acción — pantalla de solo lectura. Sin navegación a la revisión pregunta por pregunta de una evaluación puntual (esa ya existe en Actividad Evaluativa, `#est-revision`, `wireframes-actividad-evaluativa.md` §3.5) — Analytics no la duplica |

---

## 3. Pantallas — Docente

### 3.0 Desempeño por alumno (`#doc-desempeno-alumno`)

**Actor:** Docente.
**Query:** mismas dos que §2.0, con `estudiante_id` elegido por el docente en vez del propio —
RF-16.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Analytics › Desempeño por alumno" |
| Selectores | `Materia` → `Comisión` → `Estudiante` (en cascada: elegir materia acota las comisiones, elegir comisión acota el roster de estudiantes) |
| Resumen acumulado + detalle | Idéntico a §2.0 — mismo componente, mismos datos, distinto `estudiante_id` de origen. No se duplica la implementación visual entre esta pantalla y "Mi desempeño" |
| Estado vacío | Mismo criterio que §2.0, aplicado al estudiante elegido |
| Estado inicial (sin selección) | Antes de elegir un estudiante: mensaje de placeholder ("Elegí un estudiante para ver su desempeño"), sin resumen ni lista |

### 3.1 Desempeño por tema (`#doc-desempeno-tema`)

**Actor:** Docente.
**Query:** `ObtenerTasaErrorPorTema(materia_id, comision_id?)` — RF-17.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Analytics › Desempeño por tema" |
| Selectores | `Materia` (siempre) → `Comisión` (opcional, default "Toda la materia" — agrega todas las comisiones de esa materia) |
| Listado | Una `.tema-row` por `(unidad_tematica, tema)`, ordenado por tasa de error descendente (los temas más problemáticos primero — RF-17, "identificar qué temas concentran más errores") |
| Cada fila | Unidad (rótulo pequeño) + nombre del tema, barra de progreso coloreada por severidad, % de tasa de error, cantidad de respuestas/incorrectas totales |
| Color de severidad | Umbrales de referencia del prototipo (no invariante de dominio, ajustable en la spec de implementación): ≥ 50% alta (rojo), 20–49% media (ámbar), < 20% baja (verde) |
| Estado vacío | Si la materia (o comisión elegida) no tiene ninguna `Evaluacion` finalizada: mensaje simple, sin listado |

### 3.2 Desempeño por comisión (`#doc-desempeno-comision`)

**Actor:** Docente.
**Query:** `ObtenerDesempenoPorComision(comision_id)` — RF-20.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Analytics › Desempeño por comisión" |
| Selectores | `Materia` → `Comisión` (cascada, mismo patrón que §3.0) |
| Tabla | Una fila por estudiante: Nombre, % Aciertos acumulado (`Sin datos` en cursiva si `null`, nunca "0%"), Actividades pendientes (resaltado en ámbar si > 0) — ordenable por columna |
| Drill-down | Fila clicable → detalle del estudiante, mismo componente visual que §3.0/§3.1 (resumen + `.eval-item` por evaluación) — no se duplica una pantalla nueva |
| Drill-down 2° nivel | Desde una `.eval-item` del detalle del estudiante → revisión completa de esa evaluación puntual — **reusa la pantalla de revisión ya existente en Actividad Evaluativa** (`#est-revision`, `wireframes-actividad-evaluativa.md` §3.5), sin pantalla nueva; requiere el guard de rol ampliado ya documentado en `BC-analytics-modelo.md` §8.3, hot spot 3 |
| Estado vacío | Comisión sin ningún estudiante con evaluaciones finalizadas: la tabla se muestra igual, todos en "Sin datos" (mismo criterio que `RF-20` "casos límite") |

### 3.3 Evolución temporal (`#doc-evolucion-temporal`)

**Actor:** Docente.
**Query:** `ObtenerEvolucionTemporalEstudiante`/`ObtenerEvolucionTemporalComision` — RF-21.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb con 3 niveles: "Analytics › Desempeño por comisión › {Estudiante} — Evolución temporal" — accesible únicamente desde el drill-down de §3.2, no como entrada directa del menú |
| Gráfico | Línea en SVG, eje Y 0-100%, eje X = actividades rendidas en orden cronológico (etiquetadas por título de actividad) — dos series simultáneas: el estudiante elegido (línea sólida, azul) y el promedio de la comisión (línea punteada, verde) |
| Caso límite — 1 sola evaluación | Un solo punto, sin línea (ni para el estudiante ni para el promedio si solo una actividad tiene datos) — mismo criterio que RF-21 "casos límite" |
| Caso límite — actividad sin rendir | La actividad simplemente no aparece en el eje X para ese estudiante — nunca un punto en 0% ni un hueco marcado |
| Leyenda | Debajo del gráfico, color + nombre de cada serie |

### 3.4 Preguntas más falladas (`#doc-ranking-preguntas`)

**Actor:** Docente.
**Query:** `ObtenerRankingPreguntasFalladas(materia_id, comision_id?)` — RF-22.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Analytics › Preguntas más falladas" |
| Selectores | `Materia` (siempre) → `Comisión` (opcional, default "Toda la materia") — mismo patrón que §3.1 |
| Listado | Una `.ranking-row` por pregunta, numerada (posición del ranking), ordenada por tasa de error descendente: enunciado (truncado a una línea), unidad/tema, cantidad de presentaciones, % de tasa de error con el mismo código de color de severidad que `.tema-row` (§3.1: ≥50% rojo, 20-49% ámbar, <20% verde) |
| Alcance | Solo preguntas que ya fueron presentadas al menos una vez — sin denominador cero, mismo criterio que RF-22 "casos límite" |
| Estado vacío | Materia (o comisión elegida) sin ninguna pregunta presentada todavía: mensaje simple, sin listado |

### 3.5 Completitud por actividad (`#doc-completitud-actividad`)

**Actor:** Docente.
**Query:** `ObtenerCompletitudPorActividad(actividad_id)` — RF-23.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Actividades › {título de la actividad} › Completitud" — accesible desde el detalle de una actividad ya existente (`ActividadDetalle.tsx`, `US-3.4.4`), no como entrada directa del menú de Analytics |
| Resumen | `.completitud-summary`: 4 números (Finalizadas, En curso, Suspendidas, Sin iniciar) |
| Tabla | Una fila por estudiante: Nombre, Comisión, Estado (`.state-badge` con 4 variantes de color) — roster de la(s) comisión(es) a la(s) que la actividad está restringida, o de toda la materia si no hay restricción (`BC-analytics-modelo.md` §8.4, hot spot 4) |
| Columna Comisión | Solo relevante/visible cuando la tabla mezcla más de una comisión (actividad sin restricción) — si está restringida a una sola, se puede omitir en la implementación |
| Estado vacío | Actividad sin ningún estudiante en el roster aplicable: no debería ocurrir en la práctica (una actividad siempre pertenece a una materia con al menos una comisión), sin caso especial diseñado |

---

## 4. Hot spots resueltos con Víctor

1. **¿Hace falta una pantalla de entrada "elegí una materia" separada, como en Actividad
   Evaluativa (`#doc-materias`/`#est-materias`)?** Resuelto — no. En Analytics el selector de
   materia vive como filtro dentro de cada pantalla de reporte (`<select>` en el propio
   toolbar), no como un nivel de navegación previo con tarjetas — no hay nada que mostrar por
   materia antes de elegir un reporte (a diferencia de Actividad Evaluativa, donde la tarjeta de
   materia ya anticipa "cantidad de actividades en curso"). Mismo patrón que los filtros de
   `Banco.tsx` (`US-ADJ-02`).
2. **¿La vista de estudiante y la de "docente por alumno" son pantallas distintas o el mismo
   componente?** Resuelto — mismo componente visual (resumen + detalle), la única diferencia es
   el origen del `estudiante_id` (propio vs. elegido) y los selectores adicionales de
   comisión/estudiante que solo ve el docente.
3. **¿La fila de evaluación (`.eval-item`) navega a la revisión pregunta por pregunta?**
   Resuelto — no. Esa pantalla ya existe en Actividad Evaluativa (`#est-revision`) para el
   propio estudiante mientras cursa; Analytics no la reimplementa ni la expone al docente en
   este incremento (fuera de alcance de RF-15/16/17, que piden agregados, no el detalle
   pregunta por pregunta de una evaluación ajena).

**Pendiente de definir en la spec de implementación (no bloquea la aprobación de los
wireframes):**
- Umbrales exactos de color de `.tema-row` (§3.1) — los del prototipo (50%/20%) son de
  referencia, a confirmar o ajustar con datos reales de la materia piloto.
- Si "Desempeño por alumno" (§3.0) pagina el selector de estudiantes cuando la comisión es
  grande — a esta escala (30-60 alumnos) un `<select>` simple probablemente alcance.

---

## 5. Próximo paso

Wireframes de RF-15/16/17 (§2, §3.0, §3.1) completos y ya aprobados por Víctor en el cierre del
Issue #228 (`US-4.0.2`, Incremento 4).

**Ampliación RF-20 a 23 (§3.2 a §3.5)** — pasa a aprobación explícita de Víctor en el
comentario de cierre del Issue [#320](https://github.com/vvalotto/cognion/issues/320)
(`US-ADJ-34`, DoD tipo `Modelado`, `WORKFLOW-DESARROLLO.md` §2). Una vez aprobada, es el input
de las specs US-IEDD de la Iteración 4 de `docs/plans/inc5-adj/inc5-adj-candidatas.md`.
