# HITO-9 — El portal de entrada (Docente/Estudiante) nunca tuvo dueño de producto

> Estado documental: evidencia
> Registra un hallazgo de aprendizaje del ensayo IEDD en Cognion.
> No reemplaza a las fuentes vigentes (ADRs, arquitectura, specs).

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-9 — hallazgo de gestión de producto, detectado por pregunta directa de Víctor, no por UAT ni por ningún quality gate |
| **Fecha** | 2026-09-07 |
| **Incremento / contexto** | Sesión posterior al cierre de `BL-006` (Incremento 4), al responder una pregunta directa de Víctor: "¿a dónde va cada usuario una vez que se loguea?" |
| **Relacionado** | `US-1.1.7` (origen del placeholder), `CLAUDE.md` §"Gate de diseño UX", `docs/rf/RF_v1.md`, `HITO-6` (mismo patrón de omisión silenciosa) |

---

## Contexto

Al cerrar `BL-006` (Incremento 4 — Portal del Estudiante y Analytics), Víctor preguntó
directamente si las páginas de entrada de los portales de Docente y Estudiante estaban
diseñadas o previstas. La pregunta no vino de una UAT, de una spec, ni de ningún reporte de
cierre — fue una pregunta de producto hecha fuera del loop de implementación. La investigación
encontró que ambos roles caen, después del login, en `InicioPlaceholder`:

```tsx
export function InicioPlaceholder() {
  return <p>Sesión iniciada — pendiente de pantalla propia</p>
}
```

Ese placeholder se introdujo en `US-1.1.7` (Incremento 1, Iteración 2, julio 2026) como
destino temporal de la ruta `index` de `AppLayout`, con la intención explícita de que una US
posterior lo reemplazara. Cuatro incrementos y seis baselines después (`BL-002` a `BL-006`),
seguía intacto — y `AppLayout.tsx` tampoco tiene ningún menú de navegación persistente, solo
un header con logo y badge de rol. En la práctica, hoy ningún Docente ni Estudiante autenticado
puede llegar a ninguna pantalla funcional sin conocer la URL de memoria.

## Hallazgo / Análisis

**Causa raíz:** ninguno de los 18 RF de `RF_v1.md` es dueño de "cómo llega el usuario a la
pantalla que necesita". Cada RF describe una capacidad puntual (RF-01 registro, RF-04 carga de
preguntas, RF-11 crear actividad, RF-15 desempeño del estudiante...), y cada incremento agregó
pantallas nuevas *detrás* de rutas protegidas por rol — pero la navegación de entrada en sí
misma nunca fue el criterio de aceptación de ninguna US, porque no pertenece a ningún RF
individual. Es una capacidad transversal de producto, no una capacidad de dominio.

Esto tiene una consecuencia concreta sobre los mecanismos de control de calidad del proyecto:

- **El gate de UX** (`CLAUDE.md`: "ninguna línea de `frontend/` sin wireframe aprobado")
  funcionó exactamente como está diseñado para cada pantalla individual que sí se especificó
  — pero el gate solo se activa cuando una spec *nombra* una pantalla. Nadie escribió nunca una
  spec que nombrara "home"/"menú principal" como pantalla a diseñar, así que el gate nunca tuvo
  oportunidad de dispararse para esto.
- **La matriz de trazabilidad** está indexada por RF → BC → Incremento → US. Una capacidad sin
  RF dueño no tiene fila, y sin fila no hay "Planificado" que nunca pase a "Especificado" — es
  invisible al mecanismo de seguimiento, no solo está en un estado temprano de él.
- **La UAT tampoco lo detectó**, y esto es lo más significativo: los 4 incrementos con UAT
  manual en navegador real (Identidad, Banco de Preguntas, Actividad Evaluativa, Analytics)
  tienen guiones (`tests/uat/inc*/guion_manual_iteracion*.sh`) que navegan **directo a la URL
  bajo prueba** para ejercitar la pantalla que cierra esa iteración — ninguno arranca desde un
  login limpio y navega haciendo clic como lo haría un usuario real. Cuatro rondas de UAT con
  Víctor mirando el navegador en vivo nunca pasaron por el punto de entrada real, porque
  ninguna estaba diseñada para hacerlo.

A diferencia de `HITO-6` (paginación — un límite de escala que ningún test con fixtures
chicos podía exponer), acá no hace falta volumen de datos para exponer el problema: alcanzaba
con loguearse y no escribir una URL de memoria. El gap fue invisible no porque fuera sutil,
sino porque ningún artefacto del proceso (RF, spec, UAT) estaba organizado para preguntarlo.

## Aprendizaje(s)

- **L-9.1:** Una capacidad transversal que no pertenece a ningún RF individual (navegación de
  entrada, en este caso) puede atravesar sin ser detectada por *todos* los mecanismos de
  control de calidad del proyecto a la vez — porque el gate de UX, la matriz de trazabilidad y
  la UAT están los tres indexados por RF/US-IEDD. Un hueco de producto sin RF dueño no tiene
  disparador natural en ninguno de los tres. Hace falta preguntar explícitamente "¿qué le falta
  al producto que no le falta a ningún RF individual?" en algún punto del proceso — hoy ese
  punto no existe.
- **L-9.2:** Un guion de UAT manual que navega directo a la URL bajo prueba (en vez de arrancar
  desde un login limpio y navegar por clics) valida la pantalla, pero nunca valida el *camino*
  hasta ella. Las 4 rondas de UAT de este proyecto comparten ese mismo punto ciego. Recomendado
  para `docs/plans/PROCEDIMIENTO-UAT.md`: al menos un paso por incremento debería arrancar
  desde el login, no desde la URL de destino.
- **L-9.3:** El hallazgo no salió de ningún artefacto del proceso IEDD — salió de una pregunta
  de producto hecha por Víctor fuera del loop de implementación, sin spec ni US detrás. Es
  evidencia directa de que el rol del `human-in-the-loop` en este proyecto no se agota en
  aprobar wireframes o revisar UAT: incluye **reformular qué pregunta habría que estar
  haciéndose** — algo que ningún gate automatizado, por diseño, puede iniciar por sí mismo.

---

## Relación con la hipótesis del ensayo

Confirma dos puntos de `docs/iedd/04-Hipotesis_Ensayo_IA_Ingenieria_Human_In_The_Loop.md`:

- **§3.2** ("una mala decisión arquitectónica puede replicarse a gran escala"): acá la
  decisión implícita — nunca asignar dueño de producto a la navegación de entrada — no fue una
  decisión consciente de nadie, pero se replicó silenciosamente en 4 incrementos: cada uno
  agregó pantallas nuevas detrás de la misma puerta rota sin que nada lo señalara.
- **§3.4** ("el `human-in-the-loop` ... su papel es irreductible ... en reformular el
  problema"): este hallazgo es el ejemplo más claro hasta ahora en el proyecto de ese papel.
  No fue una corrección de un error del modelo ni un hallazgo de una UAT estructurada — fue una
  pregunta que solo un humano con visión de producto (no de RF ni de US) podía pensar en hacer,
  y que ningún mecanismo del proceso IEDD (gate de UX, matriz, UAT) estaba diseñado para
  generar por sí mismo.

---

## Resumen de Aprendizajes

| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-9.1 | Una capacidad sin RF dueño puede atravesar sin ser detectada los tres mecanismos de control de calidad del proyecto a la vez (gate UX, matriz, UAT), porque los tres están indexados por RF/US | Proceso / Gestión de producto |
| L-9.2 | Un guion de UAT que navega directo a la URL bajo prueba nunca valida el camino real (login → pantalla) — punto ciego repetido en las 4 rondas de UAT del proyecto | Proceso / UAT |
| L-9.3 | El hallazgo se originó en una pregunta de producto humana fuera del loop de implementación, no en ningún artefacto ni gate del proceso IEDD — evidencia del rol irreductible del human-in-the-loop en reformular el problema | Human-in-the-loop / Gestión de producto |

---

*Creado: 2026-09-07*
