# Procedimiento de Pruebas de Aceptación (UAT) — Cognion

> Estado documental: vigente
> Fuente de verdad para: estrategia y procedimiento de pruebas de aceptación
> Última actualización: 2026-07-13
> Fuente normativa relacionada: `docs/cm/PLAN-CM.md` §10 (Quality Gates), §11 (Versionado, Entregas y Builds)

---

## 1. Propósito

El pipeline de `/implement-us` ya cubre pruebas unitarias, de integración y funcionales (BDD)
por US. Este documento define lo que faltaba: la estrategia de **pruebas de aceptación**
(UAT) — que verifican el DoD completo de un Incremento de punta a punta, no una US aislada.

---

## 2. Entornos — esquema híbrido

Cognion usa dos entornos con roles distintos, no uno solo:

| Entorno | Rol | Cuándo se usa |
|---|---|---|
| **Entorno propio de pruebas** (máquina propia simulando servidor) | Entorno de aceptación **por defecto** | Cierre de la mayoría de los Incrementos — rápido, sin costo, permite iterar con vibe coding en etapas tempranas |
| **Staging (Fly.io)** | Checkpoint puntual, no continuo | Solo en los dos momentos del §4 — valida lo que el entorno propio no puede: WebSocket detrás de un proxy real (WSS), conexión real a PostgreSQL administrado, y el pipeline de CI/CD/deploy en sí |

Esta distinción existe porque el entorno de producción es un oráculo distinto al de
desarrollo — no una versión "final" de lo mismo. El entorno propio valida el dominio; el
staging valida las condiciones reales de infraestructura que el dominio no puede ejercitar
por sí solo.

---

## 3. Estrategia de dos capas

```
Capa 1 — Automatizada (pytest)
  Ejecuta el flujo DoD del incremento vía use_cases/ directamente.
  Verifica invariantes, persistencia y read models desde el código.
  Evidencia: salida de pytest -v

Capa 2 — HTTP / WebSocket
  Verifica los endpoints/canales reales contra el entorno correspondiente
  (propio por defecto, staging en los checkpoints del §4), con datos sembrados.
  Evidencia: respuestas capturadas (JSON / log de mensajes WS)
```

Usar Capa 1 sola cuando un comando todavía no está expuesto vía HTTP/WS. Usar ambas capas
cuando el incremento ya expone el flujo completo por API.

---

## 4. Cuándo usar staging (checkpoints puntuales)

| Momento | Qué valida | Por qué no alcanza el entorno propio |
|---|---|---|
| Cierre del incremento de infraestructura que monta el pipeline de CI/CD (§11 de PLAN-CM.md) | Que el pipeline de build + deploy + healthcheck funciona de punta a punta | El pipeline en sí no existe en el entorno propio — ejercitarlo recién en el go-live es el riesgo que este checkpoint evita |
| Antes de cerrar el Incremento 5 — Sesión en vivo | RNF de rendimiento (≤100ms server-side, 60 clientes concurrentes) bajo WebSocket real detrás de un proxy/edge, con PostgreSQL administrado | WSS con keepalive/timeouts de un balanceador real y la latencia real a una DB administrada no son replicables en el entorno propio |
| Antes de promover cualquier Baseline a producción real (con docente/estudiantes reales) | Condiciones reales de despliegue previas a exponer usuarios reales | Es la última verificación antes de que haya datos y usuarios reales en juego |

Fuera de estos momentos, todo el UAT corre contra el entorno propio.

---

## 5. Diseño por Incremento

Antes de ejecutar el UAT de un incremento, crear `quality/reports/uat/incN/design.md`:

```markdown
# Diseño de Pruebas UAT — Incremento N "<nombre>"

| Campo | Valor |
|-------|-------|
| Incremento | N |
| Baseline | BL-NNN |
| US cubiertas | US-N.1.1 a US-N.M.K |
| Entorno | Propio / Staging (según §4) |
| Fecha diseño | AAAA-MM-DD |

## Objetivo
<Qué DoD del incremento se verifica de punta a punta>

## Estrategia
<Capa 1 sola / Capa 1 + Capa 2 — justificar>

## Escenario DoD
<Descripción concreta y realista — ej. un docente + N estudiantes completando un flujo real>

## Capa 1 — Tests Automatizados
| ID | Test | Qué verifica |

## Capa 2 — Verificación HTTP/WS
| ID | Endpoint/Canal | Verificación | Resultado esperado |

## Criterio de aceptación
<Cuántos casos deben pasar para dar el UAT por aprobado>
```

---

## 6. Seeds y orquestación

```
tests/uat/incN/
├── seed_incN.py        ← siembra datos realistas del escenario DoD
└── run_uat.sh           ← orquesta Capa 1 + seed + Capa 2, deposita evidencia
```

`run_uat.sh` corre pytest (Capa 1), siembra la base con `seed_incN.py`, y verifica
endpoints/canales (Capa 2) contra `UAT_URL` (por defecto el entorno propio; se sobreescribe
con la URL de staging en los checkpoints del §4). Deposita toda la evidencia en
`quality/reports/uat/incN/`.

---

## 7. Simulación de concurrencia — Incremento 5 (sesión en vivo)

Este incremento requiere un script adicional que no existe en incrementos anteriores: un
simulador de **N clientes WebSocket concurrentes** contra el entorno correspondiente, para
validar el RNF de rendimiento (Escenario 1 de `RNF_v1.md` — ranking en vivo, ≤100ms
server-side, hasta 60 alumnos):

```
tests/uat/inc5/simular_concurrencia.py
  → Abre N conexiones WS simultáneas (empezar con N=10, escalar a N=60)
  → Cada cliente simula un alumno respondiendo una pregunta
  → Mide el tiempo entre el cierre de pregunta (docente) y el broadcast del ranking
  → Registra: latencia por cliente, latencia server-side aislada, mensajes perdidos
```

Este script corre **contra staging** (checkpoint del §4), no contra el entorno propio — es
precisamente el caso que el entorno propio no puede validar con realismo.

---

## 8. Clasificación de severidad

| Severidad | Definición | Acción |
|---|---|---|
| 🔴 Bloqueante | Impide continuar · pérdida de datos · flujo roto | Detener — registrar — no cerrar el incremento hasta resolver |
| 🟡 Observación | Incorrecto pero el flujo puede continuar | Registrar — continuar, clasificar track (frontend/backend) según PLAN-CM.md §4 |
| ⚪ Estético | Texto, color, alineación | Registrar para después, no bloquea el cierre |

---

## 9. Gate de cierre

Un Incremento **no cierra su baseline** (`docs/cm/WORKFLOW-DESARROLLO.md` §7) hasta que su
UAT esté aprobado — Capa 1 + Capa 2 con el criterio de aceptación de `design.md` cumplido, y
sin hallazgos 🔴 Bloqueantes sin resolver.

---

## 10. Artefactos generados

| Archivo | Contenido |
|---|---|
| `quality/reports/uat/incN/design.md` | Diseño de las pruebas de este incremento |
| `quality/reports/uat/incN/capa1-pytest.txt` | Salida completa de pytest -v |
| `quality/reports/uat/incN/capa2-http.json` | Respuestas capturadas de Capa 2 |
| `quality/reports/uat/incN/report.md` | Reporte de ejecución con resultado final y hallazgos clasificados |
| `tests/uat/incN/seed_incN.py` | Script de siembra de datos realistas |
| `tests/uat/incN/run_uat.sh` | Orquestación completa |
| `tests/uat/inc5/simular_concurrencia.py` | Solo Incremento 5 — simulador de clientes WS concurrentes |
