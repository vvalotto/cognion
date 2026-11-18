# Incremento 12 — Calidad de diseño

**Estado: aprobado por Víctor el 2026-11-15. Iteración 1 en curso** (Milestone [21](https://github.com/vvalotto/cognion/milestone/21)): cerrados #647, #645, #654 (`US-12.1.2`) y #646; pendientes #658 (`US-12.1.3`, de `AQ-04`), #648 y #649. Los Issues de las demás iteraciones se crean al abrirlas, después de su paso de confirmar.
**Origen:** [`docs/revision-diseno-2026-11/`](../../revision-diseno-2026-11/README.md), 60 hallazgos sobre la `1.0.0` (11 de severidad Alta, 35 Media, 14 Baja).
**Proceso:** [`inc12-proceso.md`](inc12-proceso.md).
**Cierre previsto:** `BL-018` con `v1.0.1` (Iteraciones 1 y 2) y `BL-019` con `v1.1.0` (Iteraciones 3 y 4).
**Política:** sin funcionalidad nueva ni cambios visibles para el usuario. Congelación funcional hasta `v1.1.0` estable; el Incremento 11 (#616 a #619) espera y pasa a apuntar a `v1.2.0`.

## Alcance

| # | Iteración | Qué resuelve | Hallazgos | Track principal |
|---|---|---|---|---|
| 1 | Cierres rápidos y operación | Riesgos que se cierran en horas, sin decisiones de diseño | 11 | Herramientas y documental; 1 o 2 historias formales |
| 2 | Los bordes de cada contexto | Transacción, errores, controllers, ubicación de repositorios | 12 | Formal (`/implement-us`) |
| — | **`BL-018` · `v1.0.1`** | | | |
| 3 | Los eventos | Versión, tipos y responsabilidad de los eventos; tipo de pregunta | 7 | Formal |
| 4 | Las fronteras entre contextos | Interfaz pública, dirección de dependencias, Analytics, contrato con el frontend | 10 | Formal; frontend informal |
| — | **`BL-019` · `v1.1.0`** | | | |
| T | Transversal | Requerimientos renegociados, proceso, instrumentos y documentación | 11 | Documental y herramientas |

Los 9 hallazgos restantes son de severidad Baja y no tienen iteración asignada (ver [Hallazgos de severidad Baja sin iteración](#hallazgos-de-severidad-baja-sin-iteración)).

El orden sale del [capítulo 13](../../revision-diseno-2026-11/13-plan-priorizado.md) del informe, con dos cambios:

- La red de seguridad (`VT-01`, `VT-02`) abre la Iteración 2 en lugar de cerrarla, porque protege a las historias que siguen.
- Los hallazgos de severidad Media que el capítulo 13 no ubicaba en ninguna etapa quedaron asignados, porque el criterio de versión estable los exige resueltos o decididos.

Los identificadores `US-12.M.K` de abajo son tentativos. La agrupación busca pocas historias por iteración, juntando lo que se prueba junto.

## Iteración 1 — Cierres rápidos y operación

Issues: [#645](https://github.com/vvalotto/cognion/issues/645) `IM-04`, [#646](https://github.com/vvalotto/cognion/issues/646) `DO-02`/`DO-01`/`DO-04`, [#647](https://github.com/vvalotto/cognion/issues/647) `CA-02`/`IQ-04`/`DO-05`/`VT-03`, [#648](https://github.com/vvalotto/cognion/issues/648) `DC-01`/`DC-02`, [#649](https://github.com/vvalotto/cognion/issues/649) `AQ-04`, [#654](https://github.com/vvalotto/cognion/issues/654) hueco de `IM-04` (`US-12.1.2`), [#658](https://github.com/vvalotto/cognion/issues/658) `AQ-04` (`US-12.1.3`).

Sin ADR. Cada punto es de horas.

| Hallazgo | Acción | Track |
|---|---|---|
| `DO-02` (Alta) | `cognion.sh` programa el respaldo al desplegar y `cognion.sh salud` avisa si el último está vencido. La copia fuera del servidor pasa a ser un paso verificado de la guía | Herramientas |
| `IM-04` | El canal en vivo verifica que el usuario sea docente de la comisión o participante de la sesión antes de conectar | Formal, **con BDD** (cambia comportamiento): `US-12.1.1` |
| `VT-03` | `conftest.py` aborta si `DATABASE_URL` no apunta a una base de prueba | Herramientas (`tests/`) |
| `AQ-04` | Probar en navegador el vencimiento del token durante una sesión en vivo. Si se confirma, ajustar la duración | Verificación; si hay cambio en `settings.py`, historia formal chica: `US-12.1.3` |
| `DO-01`, `DO-04` | Usuario sin privilegios y versión fija de `uv` en la imagen; `--forwarded-allow-ips` acotado; `healthcheck` contra `/api/health/ready`; medir cuánto duran 30 MB de registros | Herramientas |
| `CA-02`, `IQ-04`, `DO-05` | Una sola versión de Python en `pyproject.toml`, CI, imagen y `CLAUDE.md`; el CI corre `tsc -b`; borrar `fly.toml` y sus tests; renombrar el job del CD | Herramientas |
| `DC-01`, `DC-02` | Reescribir `README.md`; corregir en `CLAUDE.md` lo que el código desmiente | Documental |

**Resultado del paso 1 (2026-11-15).** Los 11 hallazgos se verificaron leyendo el código. Ninguno se descartó; no se ejecutó nada.

| Hallazgo | Resultado | Qué cambia en el alcance |
|---|---|---|
| `VT-03` | Ajustado | El CI usa una base llamada `cognion`. La guarda por sufijo `_test` la rechazaría: hay que renombrar la base del CI o elegir otro criterio |
| `IM-04` | Ajustado | El código dice en el docstring que no hay verificación de rol por decisión de diseño. Hay que decidir con Víctor quién puede conectarse antes de escribir la spec |
| `AQ-04` | Confirmado en código | Probado en navegador el 2026-11-17: se confirma; hay `US-12.1.3` |
| `DO-02` | Confirmado | La guía documenta `cron` a mano; `salud.sh` no mira los respaldos |
| `DO-05` | Confirmado | El borrado alcanza a 3 tests, el comentario del `Dockerfile` y el `needs:` del CD |
| `CA-02`, `IQ-04`, `DO-01`, `DO-04`, `DC-01`, `DC-02` | Confirmado | Sin cambios; `CA-02` suma `.pre-commit-config.yaml` y `DC-02` tiene las líneas corridas |
| `IQ-05`, `IQ-06` | No verificados | Baja, sin iteración; se ven si queda tiempo |

**Criterio de salida:**

1. En una instalación de prueba, el respaldo corre sin intervención y `cognion.sh salud` informa su antigüedad.
2. `pytest tests/integration` con la base de desarrollo en `DATABASE_URL` termina sin tocarla.
3. Un usuario autenticado que no pertenece a la sesión recibe un rechazo al abrir el canal en vivo.
4. `pyproject.toml`, el CI y el `Dockerfile` declaran la misma versión de Python.

## Iteración 2 — Los bordes de cada contexto

**Paso 1, confirmar:** `IM-03` (buscar si alguna de las 8 operaciones de dos escrituras puede fallar a mitad de camino y qué deja) e `IM-06` (medir el costo real de `NullPool`).

**Paso 2, ADR:**

| ADR | Decide | Hallazgos |
|---|---|---|
| Unidad de trabajo | Quién abre, confirma y revierte la transacción | `IM-03`, `DM-04` |
| Errores de dominio | Categorías, base común y correspondencia con códigos HTTP | `IM-02` |
| Destino de los controllers | Darles la traducción de salida o eliminarlos | `IM-01`, `CA-03` |
| Ubicación de los repositorios SQL | Una sola convención; corrige también el perfil de `/implement-us` | `CA-01` |

**Paso 3, guardas y red de seguridad** (track de herramientas, antes de cualquier historia):

| Hallazgo | Guarda |
|---|---|
| `VT-01` | La cobertura deja de omitir `src/*/frameworks/*` y `fail_under` se fija en el valor real medido |
| `VT-02` | El CI corre el umbral de cobertura del frontend y los circuitos de Playwright |
| `DO-03` | `imagen-smoke.yml` levanta `deploy/servidor/`, que es la variante que se entrega (relacionado con el Issue #624) |
| `IM-03` | Test que falla si hay un `commit()` fuera de la unidad de trabajo; los 21 actuales entran como excepciones |
| `IM-02` | Test que cuenta los `raise HTTPException` de los routers y no deja que el número suba |
| `CA-01` | La excepción del contrato de capas ya existe; es la lista a vaciar |

**Paso 4, historias:**

| Historia | Título | Hallazgos |
|---|---|---|
| `US-12.2.1` | Cada caso de uso se confirma o se revierte entero | `IM-03`, `DM-04` |
| `US-12.2.2` | Los errores de dominio tienen categoría y se traducen a HTTP en un solo lugar | `IM-02` |
| `US-12.2.3` | Los repositorios SQL de Identidad y Banco viven en `frameworks/` | `CA-01` |
| `US-12.2.4` | Los controllers quedan según el ADR; los routers no leen entidades | `IM-01`, `CA-03` |
| `US-12.2.5` | El pool de conexiones sale de la configuración y el verificador de vencimientos corre una sola vez | `IM-06`, `IM-05` |
| `US-12.2.6` | Umbral de CBO recalibrado y tipos `object` revertidos | `IQ-01` |

`US-12.2.2` puede partirse por contexto si el volumen lo pide (138 traducciones en 21 routers). `US-12.2.6` va al final: después de `US-12.2.2` el umbral deja de apretar.

**Criterio de salida:**

1. Ningún `commit()` fuera de la unidad de trabajo, con la lista de excepciones vacía.
2. El contrato de capas no tiene `ignore_imports`.
3. Los routers no importan `entities/errors.py` para traducir errores. El número objetivo de `HTTPException` se fija al confirmar.
4. La cobertura informada incluye `frameworks/`.

**Cierre:** `BL-018`, `v1.0.1`, con UAT de regresión.

## Iteración 3 — Los eventos

**Paso 1, confirmar:** `AQ-01`, con un spike. En una rama descartable se agrega un tercer tipo de pregunta y se cuentan archivos tocados por contexto y horas. El resultado fija el alcance de `DM-05`.

**Paso 2, ADR:** actualizar `ADR-002` con lo que se decide sobre event sourcing (`DM-07`): hasta dónde llega, quién arma los eventos y cómo se versionan. Va primero porque ordena las tres historias.

**Paso 3, guardas:**

| Hallazgo | Guarda |
|---|---|
| `DM-02` | Test que falla si un evento se persiste sin versión de esquema |
| `DM-01`, `DM-03` | Test que falla si un payload se arma o se lee fuera del módulo de eventos del agregado |

**Paso 4, historias:**

| Historia | Título | Hallazgos |
|---|---|---|
| `US-12.3.1` | Cada evento lleva la versión de su esquema | `DM-02` |
| `US-12.3.2` | Los eventos son tipos; el agregado los emite y los aplica, con reloj inyectado | `DM-01`, `DM-03`, `DM-06` |
| `US-12.3.3` | El tipo de pregunta se resuelve en Banco de Preguntas | `DM-05` (alcance según el spike) |

`US-12.3.1` va primero: es barata hoy y cara cuando haya datos reales acumulados. Requiere decidir qué versión reciben los eventos ya guardados.

**Criterio de salida:**

1. Todos los eventos de la base, viejos y nuevos, tienen versión.
2. El formato de un evento se conoce en un solo módulo por agregado.
3. El resultado del spike de `AQ-01` está documentado, con archivos tocados antes y después de `US-12.3.3`.

## Iteración 4 — Las fronteras entre contextos

**Paso 1, confirmar:** el impacto de `AC-03` (medir un reporte con historial sembrado) y el reparto real de código dentro de Identidad (`AC-04`).

**Paso 2, ADR:**

| ADR | Decide | Hallazgos |
|---|---|---|
| Interfaz pública por contexto | Dónde vive `publico`, qué puede exponer y el orden permitido entre contextos | `AC-01`, `AC-02` |
| Lectura de Analytics | Filtro en SQL con test de contrato, o proyección de desempeño. Revisa `ADR-026` | `AC-03` |
| Estructura académica | Deja registrada la observación y el criterio para extraerla. No se extrae | `AC-04` |

**Paso 3, guardas:**

| Hallazgo | Guarda |
|---|---|
| `AC-01` | El contrato de aislamiento solo acepta imports a `src.<bc>.publico`; cada contexto proveedor sin migrar entra como excepción |
| `AC-01` | Test que revisa que las funciones de `publico` no exponen tipos de `entities/` |
| `AC-02` | Contrato `layers` entre contextos, con las tres dependencias invertidas como excepciones |
| `AC-03` | Test de contrato con las claves del payload que Analytics lee |
| `AQ-03` | Escenario de historial escrito y prueba con datos sembrados |

**Paso 4, historias:**

| Historia | Título | Hallazgos |
|---|---|---|
| `US-12.4.1` | Banco de Preguntas publica su interfaz y Actividad Evaluativa la usa | `AC-01`, `IM-07` |
| `US-12.4.2` | Identidad publica su interfaz y deja de depender de los contextos de negocio | `AC-01`, `AC-02` |
| `US-12.4.3` | Actividad Evaluativa y Notificaciones publican su interfaz | `AC-01`, `AC-02` |
| `US-12.4.4` | Analytics deja de recorrer todos los eventos | `AC-03`, `AQ-03` (alcance según el ADR) |

Frontend, por track informal y con verificación en navegador real:

| Hallazgo | Acción |
|---|---|
| `FE-01` | Tipos generados desde OpenAPI y verificación en el CI de que están al día |
| `FE-03` | El cliente HTTP recibe un manejador de sesión perdida y deja de importar el router |
| `FE-02` | Un hook propio de consulta; migrar primero las páginas con supresiones de dependencias |
| `FE-04` | Riesgo aceptado asentado en `ADR-013` y cabecera `Content-Security-Policy` en Caddy |

**Criterio de salida:**

1. El contrato de aislamiento no tiene excepciones pendientes; solo las que el ADR acepta.
2. El contrato de dirección entre contextos se cumple sin excepciones.
3. El reporte de una comisión, con el historial sembrado que fije el escenario, responde dentro del tiempo acordado.
4. Un campo renombrado en un esquema de la API rompe la compilación del frontend.

**Cierre:** `BL-019`, `v1.1.0`, con UAT de regresión y uso en una clase real o un ensayo completo.

## Transversal

No tocan `src/`. Avanzan en paralelo y se asignan a la iteración donde molestan menos. Condicionan la versión estable igual que los demás.

| Hallazgo | Acción | Cuándo |
|---|---|---|
| `AQ-02`, `DO-06` | `RNF_v2.md` (o un ADR que enmiende) con los dos escenarios de administrabilidad renegociados | Con la Iteración 1, junto con `DO-02` |
| `IQ-03` | Retirar del cierre de baseline los instrumentos que no informan | Antes de `BL-018` |
| `IQ-02` | Trinquete de advertencias de DesignReviewer | Después de `US-12.2.6` |
| `PR-04` | Convertir en mecanismo las reglas escritas que lo admitan | Con las Iteraciones 1 y 2 (varias salen de `VT-03` e `IQ-04`) |
| `PR-01`, `PR-05` | Clasificar los ajustes por causa y retomar las métricas del proceso | Iteración 3 |
| `PR-02` | Revisión independiente automatizada en cada PR | Iteración 3 |
| `PR-03`, `DC-04` | Separar evidencia de documentación viva; una sola fuente por tema | Iteración 4, antes de `BL-019` |
| `VT-04` | **No se reorganizan los tests.** Índice de qué prueba cada carpeta y ubicación correcta de los nuevos | Iteración 2 |

## Candidatos nuevos

| Candidato | Origen | Qué falta |
|---|---|---|
| `UnirseASesionEnVivoUseCase` no comprueba que la comisión del estudiante sea la de la sesión, y `GET /sesiones-en-vivo/{id}` tampoco autoriza por comisión | `US-12.1.1`, 2026-11-16 | **Decidido 2026-11-16 (Víctor): se corrige en la Iteración 1** como `US-12.1.2`, Issue [#654](https://github.com/vvalotto/cognion/issues/654). Incluye también `GET /{id}/ranking`, que tampoco autoriza por comisión |
| Avisar en `/login` que la sesión venció, y volver a la página de origen después de re-ingresar (hoy no dice nada y cae en Inicio) | `AQ-04`, 2026-11-17 | Toca `frontend/`: gate de diseño UX primero. Sin decidir iteración |
| Renovación automática del token | `AQ-04`, 2026-11-17 | ADR nuevo; Incremento 11 (`v1.2.0`) por la congelación funcional |

## Hallazgos de severidad Baja sin iteración

No condicionan la versión estable. Se cierran si una historia pasa por ahí.

| Hallazgo | Dónde podría entrar |
|---|---|
| `VT-05` Prueba repetible de carga e historial | Iteración 4, sirve a `AQ-03` e `IM-06` |
| `IQ-05` Análisis automático de seguridad | Iteración 1 |
| `IQ-06` Activación del hook de push | Iteración 1 |
| `FE-05` Rutas en un solo archivo | Iteración 4 |
| `FE-06` Formularios parecidos entre alta y edición | Revisar antes del Incremento 11 (`US-11.1.1` agrega otra vía de alta de preguntas) |
| `PR-06` Nomenclatura del plan original | Con `DC-04` |
| `DC-03` Mapa documental | Al cierre de cada baseline |
| `DC-05`, `DC-06` Nombres de carpeta y citas a documentos ausentes | Con `DC-04` |

## Qué no se hace

Decisiones del informe que este incremento respeta:

- No se extrae "Estructura académica" de Identidad (`AC-04`): solo el ADR.
- No se automatiza el despliegue (`DO-06`): se renegocia el requerimiento.
- No se reorganizan los tests existentes (`VT-04`).
- No se agregan gates al commit ni al push.

## A tener en cuenta

- **El informe habla de `RF-07` como importación desde PDF.** El Incremento 11 lo reemplazó por importación desde JSON (`US-11.1.1`, #616). Donde el informe dice "antes de `RF-07`", vale para esa historia.
- **`RF-18` (KPIs históricos) sigue diferido y sin incremento.** La proyección de desempeño de `AC-03` es su requisito previo; el ADR de la Iteración 4 decide si se hace ahora o se deja la solución corta.
- **Lo que el informe no revisó sigue sin revisar**: seguridad en profundidad, modelos ORM y migraciones, Notificaciones y la mayor parte de los casos de uso de Identidad y Banco. El paso de confirmar de cada iteración puede descubrir trabajo que hoy no está en esta lista.

## Seguimiento por hallazgo

Estados: *Pendiente*, *Confirmado*, *En curso*, *Cerrado*, *Descartado*, *No se hace*. La columna Confianza marca con **I** los hallazgos que el informe dejó total o parcialmente inferidos.

| Hallazgo | Severidad | Confianza | Iteración | Estado | Historia / PR / decisión |
|---|---|---|---|---|---|
| `CA-01` | Media | | 2 | Pendiente | |
| `CA-02` | Baja | | 1 | Cerrado | #647, PR [#650](https://github.com/vvalotto/cognion/pull/650) |
| `CA-03` | Media | | 2 | Pendiente | |
| `AC-01` | Alta | | 4 | Pendiente | |
| `AC-02` | Media | | 4 | Pendiente | |
| `AC-03` | Alta | I | 4 | Pendiente | |
| `AC-04` | Media | I | 4 | Pendiente | |
| `DM-01` | Alta | | 3 | Pendiente | |
| `DM-02` | Alta | | 3 | Pendiente | |
| `DM-03` | Media | | 3 | Pendiente | |
| `DM-04` | Media | | 2 | Pendiente | |
| `DM-05` | Alta | | 3 | Pendiente | |
| `DM-06` | Media | | 3 | Pendiente | |
| `DM-07` | Media | | 3 | Pendiente | |
| `IM-01` | Media | | 2 | Pendiente | |
| `IM-02` | Alta | | 2 | Pendiente | |
| `IM-03` | Alta | I | 2 | Pendiente | |
| `IM-04` | Media | | 1 | Cerrado | `US-12.1.1`, Issue [#645](https://github.com/vvalotto/cognion/issues/645), PR [#652](https://github.com/vvalotto/cognion/pull/652). Regla A (decisión de Víctor, 2026-11-15). Sin el ticket de un solo uso para el token |
| `IM-05` | Media | | 2 | Pendiente | |
| `IM-06` | Media | I | 2 | Pendiente | |
| `IM-07` | Baja | | 4 | Pendiente | |
| `AQ-01` | Alta | I | 3 | Pendiente | |
| `AQ-02` | Media | | T | Pendiente | |
| `AQ-03` | Media | | 4 | Pendiente | |
| `AQ-04` | Media | I | 1 | En curso | Issue [#649](https://github.com/vvalotto/cognion/issues/649). **Confirmado en navegador el 2026-11-17**: sin tocar nada, la sala de espera recibe 401 al vencer el token y la app manda a `/login` sin aviso. Decisión de Víctor (2026-11-18): 8 horas por defecto. `US-12.1.3`, Issue [#658](https://github.com/vvalotto/cognion/issues/658) |
| `VT-01` | Media | | 2 | Pendiente | |
| `VT-02` | Media | | 2 | Pendiente | |
| `VT-03` | Media | | 1 | Cerrado | #647, PR [#650](https://github.com/vvalotto/cognion/pull/650) |
| `VT-04` | Media | | T | Pendiente | |
| `VT-05` | Baja | | — | Pendiente | |
| `IQ-01` | Alta | | 2 | Pendiente | |
| `IQ-02` | Media | | T | Pendiente | |
| `IQ-03` | Media | | T | Pendiente | |
| `IQ-04` | Baja | | 1 | Cerrado | #647, PR [#650](https://github.com/vvalotto/cognion/pull/650) |
| `IQ-05` | Baja | | — | Pendiente | |
| `IQ-06` | Baja | | — | Pendiente | |
| `FE-01` | Media | | 4 | Pendiente | |
| `FE-02` | Media | I | 4 | Pendiente | |
| `FE-03` | Media | | 4 | Pendiente | |
| `FE-04` | Media | | 4 | Pendiente | |
| `FE-05` | Baja | | — | Pendiente | |
| `FE-06` | Baja | I | — | Pendiente | |
| `DO-01` | Media | | 1 | Cerrado | Issue [#646](https://github.com/vvalotto/cognion/issues/646). Imagen con usuario `cognion` (UID 10001), `uv==0.9.18`, bases con versión de parche, `FORWARDED_ALLOW_IPS` acotado a la red interna (también en `deploy/gcp`). **Sin ensayar con Docker real** (Issue #624) |
| `DO-02` | Alta | | 1 | Cerrado | Issue [#646](https://github.com/vvalotto/cognion/issues/646). `iniciar` y `desplegar` programan el cron; `estado` informa la antigüedad del último respaldo y avisa; la copia externa es un paso verificado de la guía (sección 7) |
| `DO-03` | Media | I | 2 | Pendiente | |
| `DO-04` | Media | | 1 | Cerrado | Issue [#646](https://github.com/vvalotto/cognion/issues/646). `healthcheck` a `/api/health/ready`. Registros: 30 MB por servicio, ~151 B por línea; con los chequeos de salud cada 15 s alcanzan para ~4 a 5 semanas (estimado) |
| `DO-05` | Baja | | 1 | Cerrado | #647, PR [#650](https://github.com/vvalotto/cognion/pull/650) |
| `DO-06` | Media | | T | Pendiente | |
| `PR-01` | Alta | I | T | Pendiente | |
| `PR-02` | Media | | T | Pendiente | |
| `PR-03` | Media | | T | Pendiente | |
| `PR-04` | Media | | T | Pendiente | |
| `PR-05` | Baja | | T | Pendiente | |
| `PR-06` | Baja | | — | Pendiente | |
| `DC-01` | Media | | 1 | Confirmado | Issue [#648](https://github.com/vvalotto/cognion/issues/648). Confirmado |
| `DC-02` | Media | | 1 | Confirmado | Issue [#648](https://github.com/vvalotto/cognion/issues/648). Confirmado, con líneas corridas: Python en 47, regla entre contextos en 85, "0–6" en 98, deploy automático en 106 y 159 |
| `DC-03` | Baja | | — | Pendiente | |
| `DC-04` | Media | | T | Pendiente | |
| `DC-05` | Baja | | — | Pendiente | |
| `DC-06` | Baja | | — | Pendiente | |
