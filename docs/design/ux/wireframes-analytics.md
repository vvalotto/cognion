# BC Analytics — Wireframes: Portal de Desempeño

> Estado documental: **borrador — pendiente de aprobación explícita de Víctor en el comentario
> de cierre del Issue [#228](https://github.com/vvalotto/cognion/issues/228) (US-4.0.2,
> Iteración 0, Incremento 4).**
> Alcance: RF-15 (vista de estudiante, acotada a evaluaciones de período abierto — sin
> sesiones en vivo, que no existen todavía), RF-16 (docente por alumno), RF-17 (docente por
> curso y tema).
>
> Fuente: `docs/rf/RF_v1.md` (RF-15, RF-16, RF-17), `docs/design/domain/BC-analytics-modelo.md`
> (queries `ObtenerDesempenoPorEvaluacion`, `ObtenerDesempenoAcumuladoPorMateria`,
> `ObtenerTasaErrorPorTema` — §4).
>
> Prototipo: `docs/design/ux/prototipos/analytics-portal-desempeno.html` — navegable, 3
> pantallas.

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

Wireframes completos, sin hot spots abiertos (§4) — pasan a aprobación explícita de Víctor en
el comentario de cierre del Issue #228 (DoD tipo `Modelado`, `WORKFLOW-DESARROLLO.md` §2). Una
vez aprobados, son el input de las specs US-IEDD de las Iteraciones 1 y 2
(`docs/plans/inc4/inc4-candidatas.md`).
