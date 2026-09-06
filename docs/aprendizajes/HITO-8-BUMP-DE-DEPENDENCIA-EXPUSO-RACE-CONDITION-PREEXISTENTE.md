# HITO-8 — Un bump de dependencia expuso una condición de carrera real, preexistente en 21 componentes del frontend

> Estado documental: evidencia
> Registra un hallazgo de aprendizaje del ensayo IEDD en Cognion.
> No reemplaza a las fuentes vigentes (ADRs, arquitectura, specs).

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-8 — un bump de dependencia rutinario como instrumento de diagnóstico de deuda técnica |
| **Fecha** | 2026-09-02 |
| **Incremento / contexto** | Incremento 3-ADJ (Adecuación Técnica) — triage de PRs de Dependabot, tarea de mantenimiento sin relación aparente con `src/`/`frontend/src/` |
| **Relacionado** | `US-ADJ-20`, Issue [#205](https://github.com/vvalotto/cognion/issues/205), PR [#206](https://github.com/vvalotto/cognion/pull/206), PRs de Dependabot [#126](https://github.com/vvalotto/cognion/pull/126)/[#129](https://github.com/vvalotto/cognion/pull/129) |

---

## Contexto

La tarea era rutinaria: mergear los PRs abiertos de Dependabot en `develop`. Uno de ellos
bumpeaba `vitest` de 4.1.10 a 4.1.11 (`#126`) y su CI fallaba con un `unhandled rejection`
(`TypeError: Cannot read properties of undefined (reading 'status')` / `ECONNREFUSED` en otros
casos). La primera hipótesis razonable — "el bump de vitest rompió algo" — resultó incorrecta:
el mismo patrón de fallo apareció también en `#129`, un bump de `@tailwindcss/vite` sin ninguna
relación con vitest ni con tests, y desapareció al reintentar el mismo job de CI sin cambiar una
sola línea de código. Eso descartó la hipótesis inicial y abrió la pregunta real: ¿qué código de
producción tenía un bug de timing preexistente que un cambio de tooling apenas volvió más
visible?

---

## Hallazgo / Análisis

### La causa no estaba en ninguna dependencia — estaba en el patrón de fetch del frontend

21 componentes de `frontend/src/pages/` usaban el mismo guard desde hacía varios incrementos:

```ts
useEffect(() => {
  let cancelado = false
  algunaLlamadaApi().then((datos) => {
    if (!cancelado) setEstado(datos)
  })
  return () => { cancelado = true }
}, [dep])
```

Ese guard evita el `setState` sobre un componente ya desmontado (silencia el warning típico de
React), pero **no cancela el `fetch` en sí** — la promesa de red sigue en vuelo después del
desmontaje, sin ningún `.catch`. En producción esto casi nunca se nota (el resultado
simplemente se descarta). En tests se vuelve visible porque cada archivo reemplaza
`global.fetch` con un mock nuevo en su propio `beforeEach`: si la promesa de un componente ya
desmontado se resuelve *después* de que el siguiente test instaló su propio mock vacío,
`fetch()` devuelve `undefined` y el código explota, o cae al `fetch` real de Node en CI.

`vitest 4.1.11` no introdujo el bug — introdujo (o volvió más estricta) la detección de
promesas sin manejar entre tests, exponiendo algo que `4.1.10` dejaba pasar en silencio. El
bump fue el instrumento que hizo visible un defecto que ya estaba ahí desde que se escribió el
primer componente con ese patrón, varios incrementos atrás.

### El fix de producción y el fix del flake de test necesitaron mecanismos distintos

El fix "correcto" — reemplazar el guard `cancelado` por `AbortController` real — funciona en
producción porque el `fetch` nativo del navegador sí respeta `AbortSignal` y rechaza la promesa
al abortar. Pero el mock de test (`vi.fn()`) **no interpreta `signal` en absoluto** — es una
función mockeada genérica, no una reimplementación de la Fetch API. Llamar
`controller.abort()` en el cleanup del efecto no detiene la promesa mockeada ya en vuelo. La
solución robusta terminó siendo doble: `AbortController` real (correcto para producción) más un
chequeo explícito de `signal.aborted` en cada punto de resolución/error (correcto para el caso
de test, y también más robusto en producción: cubre cualquier resolución tardía, no solo la que
llega como `AbortError`).

---

## Aprendizaje(s)

- **L-8.1:** Un bump de dependencia que "rompe algo" no siempre rompió nada — a veces expone
  algo que ya estaba roto. La forma barata de distinguir ambos casos es comparar contra otro
  PR/cambio sin relación bajo la misma condición (acá: dos bumps de Dependabot sin relación
  entre sí mostrando el mismo síntoma) y contra el propio `develop` sin cambios
  (`git stash`/`git worktree` + reintentar). Si el síntoma aparece en ambos, la causa está en
  el código base, no en la dependencia bajo sospecha.
- **L-8.2:** Un patrón repetido mecánicamente en muchos archivos (acá: el guard `cancelado` en
  21 componentes) tiende a acumular el mismo defecto en todos a la vez, porque se copia por
  precedente ("así está hecho en los demás") en vez de revisarse cada vez desde cero. Cuando
  aparece un bug de ese tipo, vale la pena preguntar de entrada "¿este patrón se repite en otro
  lado?" antes de arreglar solo el archivo donde se lo vio primero — acá el `grep` inicial ya
  encontró los 21 casos antes de escribir una sola línea de fix.
- **L-8.3:** Un mock de test no reimplementa semántica de plataforma que no se le pidió
  explícitamente — `vi.fn()` no sabe qué es `AbortSignal` aunque la firma de `fetch` lo
  acepte. El fix "correcto" para producción y el fix que hace pasar la suite de tests no son
  necesariamente el mismo mecanismo — hay que verificar ambos por separado, no asumir que uno
  implica el otro.

---

## Relación con la hipótesis del ensayo

Coincide con el patrón de `HITO-7` (docstring que ya documentaba la intención, nunca conectado
a una verificación real) pero desde un ángulo distinto: acá no había ninguna intención
documentada que señalara el problema — fue una tarea de mantenimiento rutinaria (Dependabot) la
que, por casualidad de que una herramienta de terceros se puso más estricta, sirvió de sensor
de deuda técnica preexistente. Es evidencia adicional de que el proceso IEDD no depende
únicamente de UAT planificada para encontrar bugs reales: tareas de bajo perfil como actualizar
dependencias también pueden — y en este caso lo hicieron — disparar una investigación de causa
raíz genuina si no se descartan sus fallos como "ruido" sin antes comparar contra una condición
de control.

---

## Resumen de Aprendizajes

| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-8.1 | Un bump de dependencia que rompe CI puede estar exponiendo un bug preexistente, no causándolo — comparar contra otro cambio sin relación y contra el baseline sin tocar antes de asumir causalidad | Proceso / Debugging |
| L-8.2 | Un patrón repetido mecánicamente en muchos archivos acumula el mismo defecto en todos — buscar el alcance completo (grep) antes de arreglar solo el primer caso visto | Quality / Arquitectura |
| L-8.3 | El fix correcto para producción y el fix que estabiliza los tests no son necesariamente el mismo mecanismo cuando un mock no reimplementa toda la semántica de la plataforma real | Testing / Quality Gates |

---

*Creado: 2026-09-02*
