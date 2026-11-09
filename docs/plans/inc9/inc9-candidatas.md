# Incremento 9 — Correcciones y robustez

**Estado: en planificación (2026-11-07).** Propuesta aprobada por Víctor el 2026-11-07.
**Milestone:** [Incremento 9 — Correcciones y robustez](https://github.com/vvalotto/cognion/milestone/18)
**Cierre previsto:** `BL-015`, tag `v0.10.0` (MINOR: incluye una funcionalidad nueva, el link de invitación grupal).
**Política:** sin BC nuevo ni RF funcional nuevo. Abre con una iteración de **decisiones** (con Víctor presente), porque las Iteraciones 1 a 3 dependen de ellas. Las US que tocan `src/` van por el track formal (`/implement-us`); las de `frontend/` necesitan wireframes aprobados antes (gate UX).

## Origen

1. **La prueba real con estudiantes sobre la VM de GCP (2026-11-06)**, revisada el 2026-11-07: el sistema aguantó (0 respuestas 5xx, 7 evaluaciones finalizadas, una sesión en vivo con 6 participantes), pero dejó hallazgos:
   - un link de invitación de un solo uso compartido con toda la clase falló 14 veces con `422` (#590);
   - los tokens de invitación quedan en claro en el log de acceso (#594);
   - el hash de contraseñas bloquea el event loop (325 ms por verificación en la VM, #562);
   - 8 registros rechazados con `422` antes de 7 exitosos (#595), 3 conexiones WebSocket rechazadas con `403` (#596) y 253 MB de swap en uso con 7 alumnos (#597);
   - una estudiante vio cambiar el enunciado pero no las opciones tras reanudar: causa probable, traducción automática del navegador; ya corregido con `lang="es"` y recreación del bloque de la pregunta (PR #591), sin confirmar.
2. **Deuda técnica pendiente** desde `BL-012`/`BL-013`: guardas de arquitectura (#496, #497, #498), observabilidad (#526), un bug de migraciones verificado el 2026-11-07 (#527: `alembic downgrade base` falla con `Can't emit DROP CONSTRAINT ... it has no name` en `estudiante`) y una decisión de producto de la UAT del 7-ADJ (#502).

## Alcance

| # | Iteración | Qué | Track |
|---|---|---|---|
| 0 | Decisiones y spikes | Sesión de decisiones con Víctor, ADR del acoplamiento entre BC, 3 spikes sobre la prueba real | Spike (`tipo:spike`), sin código |
| 1 | Correcciones con impacto en el uso real | Enmascarar tokens en el log, bcrypt asíncrono, `downgrade base` | Formal (`/implement-us`), backend |
| 2 | Link de invitación grupal | Invitación reutilizable con vencimiento corto, revocable | Formal, backend + gate UX + frontend |
| 3 | Guardas de arquitectura y observabilidad | `import-linter` en el CI, logs estructurados y `readiness`, bug upstream | Formal / tooling |
| 4 | Migración de adaptadores que leen tablas de otro BC | Tres adaptadores dejan de leer modelos ORM ajenos (`ADR-026`) | Formal (`/implement-us`), backend |

## Iteración 0 — Decisiones y spikes

| Issue | Qué |
|---|---|
| [#593](https://github.com/vvalotto/cognion/issues/593) `US-9.0.0` | Sesión de decisiones: #502 (aviso del 3.er intento), las 4 decisiones de #590, bloquear o no la traducción automática, consolidar duplicados de nube, confirmar #500 fuera |
| [#498](https://github.com/vvalotto/cognion/issues/498) | ADR: acoplamiento de los adaptadores in-process a internals de otro BC |
| [#502](https://github.com/vvalotto/cognion/issues/502) | Decisión de producto: 3.er intento fallido de login |
| [#595](https://github.com/vvalotto/cognion/issues/595) `US-9.0.1` | Spike: fricción en el registro de estudiantes |
| [#596](https://github.com/vvalotto/cognion/issues/596) `US-9.0.2` | Spike: rechazos `403` del canal WebSocket (hipótesis: JWT de 60 min, `ADR-013`) |
| [#597](https://github.com/vvalotto/cognion/issues/597) `US-9.0.3` | Spike: memoria y swap de la VM con una clase completa (**después** de #562) |

**Salida:** decisiones escritas en cada Issue y el ADR de #498. Si #596 concluye que hay que renovar el token, o #595 que hay que cambiar la política, se abren Issues nuevos y entran en la Iteración 1 o 2 según su tamaño.

## Iteración 1 — Correcciones con impacto en el uso real (backend)

Orden por riesgo:

1. [#594](https://github.com/vvalotto/cognion/issues/594) `US-ADJ-68` — el log de acceso enmascara `/invitaciones/<token>`. Chica; va primero porque la Iteración 2 vuelve reutilizable el token.
2. [#562](https://github.com/vvalotto/cognion/issues/562) `US-ADJ-63` — el hash de contraseñas deja de bloquear el event loop (`PasswordHasherPort` asíncrono, bcrypt en un hilo; 9 puntos de uso en 8 casos de uso; spec en `docs/specs/ajustes/US-ADJ-63.md`). Con 30 a 60 alumnos entrando a la vez frena también los WebSockets de una sesión en vivo.
3. [#527](https://github.com/vvalotto/cognion/issues/527) `US-8.3.4` — `alembic downgrade base` funcional: corregir la migración y sumar el chequeo a `tests/uat/inc8/verificar_migraciones.sh`. Falta escribir la spec.

**Verificación al cerrar la iteración:** prueba de carga de logins (`US-6.2.9` tiene scripts) antes y después de #562, y `downgrade base` + `upgrade head` en una base descartable.

## Iteración 2 — Link de invitación grupal

- [#590](https://github.com/vvalotto/cognion/issues/590) `US-ADJ-67` — invitación **grupal** (reutilizable hasta su vencimiento, duración elegible, revocable, con conteo de registros) que **reemplaza** a la individual en la UI. Decisiones de #593 (2026-11-08): duraciones 15 min / 1 h / 1 día (por defecto 1 h), sin cupo y un solo link grupal vigente por comisión (generar uno nuevo revoca el anterior). Verificar en la spec si el flujo también da de alta Docentes. Además entra [#604](https://github.com/vvalotto/cognion/issues/604) `US-ADJ-69` — el login avisa "te queda 1 intento" tras el 2.º fallo (#502, opción 3; backend + gate UX + frontend, con el trade-off de que el aviso revela que la cuenta existe). Cierra #502 al mergear. Toca `src/` (Identidad: agregado Invitación, casos de uso, endpoints, migración) y `frontend/` (`ComisionDetalleDocente.tsx`, `InvitacionPreview.tsx`, `Registro.tsx`).
- [#605](https://github.com/vvalotto/cognion/issues/605) — correcciones de frontend de la prueba real (registro de estudiantes que exige la política de contraseña y enfoca el error; canal en vivo que detecta el JWT vencido). Solo `frontend/`, track informal; decididas en los spikes #595 y #596.
- **Gate UX:** actualizar `wireframes-identidad*.md` y el prototipo, y que Víctor los apruebe **antes** de escribir el frontend.
- **Documentación:** nota o ADR que matice `ADR-012` (hoy un solo uso y 7 días) y ampliación de `BC-identidad-modelo.md` (`INV-ID-13`).
- Es la única funcionalidad nueva: por eso el cierre es `v0.10.0` (MINOR).

## Iteración 3 — Guardas de arquitectura y observabilidad

- [#497](https://github.com/vvalotto/cognion/issues/497) — **hecho (2026-11-08)**: `import-linter` en el CI con cuatro contratos (capas, aislamiento entre BC, `shared` y `ADR-026`); descubrió que 9 gateways SQL importan los modelos ORM de `frameworks`, declarados como excepción. Los tres originales: capas dentro de cada BC, aislamiento entre BC (solo desde `frameworks/adapters/`) y `shared` sin importar de ningún BC. Hoy se cumple solo por revisión humana.
- [#526](https://github.com/vvalotto/cognion/issues/526) `US-8.3.3` — observabilidad mínima: logs estructurados y `healthcheck` de `readiness`.
- [#498](https://github.com/vvalotto/cognion/issues/498) — el ADR está escrito (`ADR-026`, 2026-11-08): Analytics es la única excepción a leer datos de otro BC; los tres casos restantes se migran en la Iteración 4. El contrato de `import-linter` (#497) debe codificar esa excepción.
- [#496](https://github.com/vvalotto/cognion/issues/496) — corregir `DependencyGraphBuilder` en `software_limpio` (otro repositorio, mismo autor; acotado en tiempo) para reactivar `LayerViolationsAnalyzer` y quitar los falsos "Zone of Pain".

## Iteración 4 — Migración de adaptadores que leen tablas de otro BC

**Estado: implementada (2026-11-09)** en `feature/inc-9-iter-4-adaptadores-sin-orm-ajeno`; las tres US están commiteadas y el PR único sale al cierre. Specs en `docs/specs/inc9/US-9.4.1.md` a `US-9.4.3.md`. Desvío registrado: en `US-9.4.2` el método se puso en un puerto propio y no en `CuentaQueryPort`, porque subía su CBO a 11.

Según `ADR-026`. Depende de #497, **ya hecho** (el contrato de `import-linter` impide que vuelva a aparecer; cada migración borra su línea de `ignore_imports` en `pyproject.toml`). Una US por adaptador; cada una empieza con un test de caracterización y no puede cambiar el comportamiento.

1. [#600](https://github.com/vvalotto/cognion/issues/600) `US-9.4.1` — `banco_preguntas` deja de leer modelos de `identidad` (consulta de comisiones).
2. [#601](https://github.com/vvalotto/cognion/issues/601) `US-9.4.2` — `actividad_evaluativa` deja de leer modelos de `identidad` (consulta de estudiantes).
3. [#602](https://github.com/vvalotto/cognion/issues/602) `US-9.4.3` — `identidad` deja de leer modelos de `actividad_evaluativa` (consulta de evaluaciones); crea un puerto de consulta en el proveedor. Probablemente la más grande.

El orden es provisional y se confirma al escribir cada spec.

## Fuera de alcance

- **Nube:** #520 a #525, #528 y #549 a #552 siguen en el Milestone "Incremento 8 — Despliegue en la nube (diferido)". Dependen de elegir la nube y de reescribir los que asumen Fly.io (#520 a #523).
- **#532 (`RF-07`):** funcionalidad nueva (importar preguntas desde PDF); su spike de mecanismo sigue pendiente.
- **#500:** revisar si `actividad_evaluativa` (184 clases) debe dividirse. Revisión de diseño sin urgencia; se retoma después de #496 para medir con datos confiables.

## Dependencias y orden

```
Iter 0 (decisiones) ──► Iter 2 (link grupal)
                   └──► Iter 3 (#498 ADR → implementar)
#594 (token en log) ──► Iter 2     (el token pasa a ser reutilizable)
#497 ──► Iter 4 (migración de adaptadores, ADR-026)   (#497 no depende de #496: el Issue lo dice)
#562 (bcrypt async) ──► #597       (la medición de memoria queda distorsionada si bcrypt bloquea)
#596 (¿JWT vencido?) ──► posible Issue nuevo en Iter 1 o 2
```

## Cierre

- `BL-015`: DesignReviewer y ArchitectAnalyst sobre `src/` completo, `coverage.json` generado antes del `architectanalyst`, UAT (Capa 1 y Capa 2) y una pasada en navegador real del flujo de invitación grupal con celular.
- Merge `develop → main` y tag `v0.10.0`.
- Antes de que empiece el incremento se puede sacar un `v0.9.2` con el arreglo de `lang="es"` (PR #591), ya en `develop`, si se quiere desplegar sin esperar.
