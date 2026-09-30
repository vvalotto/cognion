# Plan de Implementación: US-ADJ-54 - Esperas asincrónicas correctas en los tests del frontend

## Barrido (Fase 0-2)

Dos patrones buscados en `frontend/src/**/*.test.tsx`:

- **A** — `expect(await screen.findBy…(…)).toHave…` (espera el elemento y verifica una sola vez): **32 casos**.
- **B** — `await screen.findBy…` seguido, sin otro `await`, de `expect(...)` sincrónico sobre valor, texto, cantidad o
  estado: **16 casos** (heurística sobre todos los `findBy` de cada test, ventana de 6 líneas).

Criterio de cada caso: ¿el elemento esperado puede existir **antes** que el dato verificado? Se miró el componente.

### Carreras reales — se corrigen (6)

| Test | Por qué es una carrera |
|---|---|
| `cuentas/EditarCuenta.test.tsx:51` | El formulario se dibuja vacío; `setNombre` llega después con la cuenta |
| `banco-preguntas/EditarMateria.test.tsx:46` | Igual: formulario sin esperar la materia |
| `identidad/EditarComision.test.tsx:49` | Igual: formulario sin esperar la comisión |
| `actividad-evaluativa/MateriasActividades.test.tsx:99` | La fila sale con `…` y los conteos llegan en otro pedido (`cargarResumen`) |
| `actividad-evaluativa/ComisionesDeMateria.test.tsx:107` | Igual: fila con `…`, resumen por comisión en pedidos aparte |
| `actividad-evaluativa/RendirEvaluacion.test.tsx:214` | "Finalizar evaluación" existe siempre (deshabilitado); `findByRole` lo encuentra antes de que la respuesta confirmada lo habilite |

### Descartados — seguros (42)

- **Patrón A — 28 `findByRole("alert")` + `toHaveTextContent`**: el alerta aparece recién con el error y ya trae su texto.
- **Patrón B — `EditarTituloActividad.test.tsx:88`**: el formulario espera `actividad` y `materia` (`Cargando…`); el título
  se setea junto con la actividad.
- **`EvolucionTemporal.test.tsx` (95, 114)**: las dos series llegan en un único `Promise.all`; el SVG se dibuja
  recién con ambas.
- **`ProyeccionSesionEnVivo.test.tsx` (306, 337, 456)**: lo esperado y lo verificado salen del mismo render
  (misma etapa); el indicador de conexión es síncrono.
- **`RendirEvaluacion.test.tsx` (185, 323, 370)**: enunciado, botón y radios dependen del mismo payload o del mismo
  cambio de estado.
- **`DesempenoPorAlumno.test.tsx:210`, `Banco.test.tsx:214`**: el estado verificado se resetea sincrónicamente con la
  acción del usuario.
- **`DesempenoPorComision.test.tsx:168`**: filas y nombre esperado salen de la misma respuesta.
- **`NuevaPreguntaOpcionMultiple.test.tsx:145`, `AutoregistroEstudiante.test.tsx:83`**: verifican el estado inicial
  (deshabilitado), que ya es el correcto al primer render.

Total: 32 (A) + 16 (B) = 48 = 6 corregidos + 28 descartados de A + 14 descartados de B.

**Límite del barrido:** es heurístico (dos patrones de texto + revisión manual). No garantiza que no haya otras carreras
con formas distintas (por ejemplo, `getBy` sin ningún `findBy` antes). Las 6 corridas repetidas de la verificación son
la segunda red.

## Corrección

```ts
const campo = await screen.findByLabelText("Nombre completo")
await waitFor(() => expect(campo).toHaveValue("Ana Docente"))
```

En las tablas, esperar el dato de la celda (`await waitFor(() => expect(celdas[1]).toHaveTextContent("2"))`) en vez de
solo la fila. En `RendirEvaluacion`, `await waitFor(() => expect(boton).toBeEnabled())`. **Sin cambios en componentes.**

## Tareas

- [ ] Corregir los 6 tests
- [ ] Verificación: `npm run test` × 3 y `npm run test:coverage` × 3 seguidas, en verde; `tsc -b`, `oxlint`
- [ ] Confirmar con `git diff --stat` que solo cambian archivos `*.test.tsx`
