# Plan de Implementación — Cognión

> Versión: PLAN_v1
> Fecha: 2026-07-08
> Estado: borrador verificado
> Basado en: RF_v1.md · RNF_v1.md · ARQ_v1.md
> Revisión 2026-07-15: se separó la fundación técnica (Incremento 0) del primer BC de dominio
> (Identidad, ahora Incremento 1) — ningún incremento estaba aún en ejecución (sin BL-000
> abierta), por lo que esta revisión no reescribe historia, corrige el plan antes de arrancar.
> Revisión 2026-07-16: Docker no está disponible en el entorno de desarrollo actual — se decide
> usarlo más adelante en el proyecto (queda como ítem abierto, ver `CLAUDE.md`). PostgreSQL
> local para el Incremento 0 se instala vía Homebrew en lugar de Docker Compose; Alembic corre
> igual, sin cambios, contra esa instancia. Cuando se adopte Docker, se migra la infraestructura
> local a Docker Compose sin tocar Alembic ni el dominio. Tampoco reescribe historia — el
> Incremento 0 sigue sin ejecutarse (sin BL-001 abierta).

---

## Estrategia general

**Fundación técnica primero, sin lógica de negocio.** Antes de construir cualquier BC, el
Incremento 0 deja operativo el entorno de desarrollo completo: repo, CI/CD, esqueleto
de las cuatro capas de Clean Architecture (Entities → Use Cases → Adapters → Frameworks),
PostgreSQL local (vía Homebrew — Docker Compose diferido, ver revisión 2026-07-16) y Alembic.
Esto valida que el pipeline técnico funciona
antes de invertir en dominio — reduce el riesgo de integración típico en Clean Architecture
cuando se posterga. El despliegue a un entorno real (Fly.io u otro) queda deliberadamente fuera
de este incremento: depende de una decisión de infraestructura todavía pendiente (`ARQ_v1.md`)
y no debe bloquear el arranque del dominio. Recién en el **Incremento 1 (BC Identidad)** aparece
la primera lógica de negocio real — registro por invitación y roles — con su propia
Iteración 0 — Modelado, igual que cualquier otro BC.

**Orden por riesgo y dependencia, no por importancia percibida.** La sesión de período abierto
va antes que la sesión en vivo, aunque ambas sean "core": el período abierto no requiere
WebSockets ni tiene el algoritmo de puntaje sin definir (ítem pendiente en RF). La sesión en
vivo es el driver arquitectónico más exigente (broadcast ≤100ms, 60 clientes concurrentes) y
depende de una decisión de diseño que todavía no existe — conviene llegar a ella con la
arquitectura ya probada en producción con tráfico real.

**Iteraciones cortas (1 semana), incrementos de 2–4 semanas.** Dado que es un equipo unipersonal
(driver arquitectónico confirmado en ARQ), iteraciones largas no aportan — lo que sí aporta es
que cada incremento termine en un hito demostrable al docente real, porque hay múltiples ítems
que requieren su decisión (algoritmo de puntaje, mecanismo de importación PDF, comportamiento de
link vencido) y esas decisiones se destraban mejor viendo el sistema andar, no en abstracto.

**Las decisiones pendientes se resuelven con spikes dentro del incremento que las necesita**,
no bloquean el plan completo.

**Modelado de dominio antes de construir, por BC.** La experiencia previa (AtaraxiaDive) mostró
que diseñar la UX después de construir el backend contamina la revisión de specs: el código
termina especificado mirando el código existente en vez del diseño aprobado (anti-patrón
"spec-validatoria"). La misma lógica aplica al dominio — escribir specs de US sin haber resuelto
antes el modelo de agregados, eventos e invariantes del BC produce el mismo problema del lado
del backend. Por eso cada Incremento que introduce un BC nuevo, o lo extiende de forma
significativa, abre con una **Iteración 0 — Modelado**: event storming del BC (agregados,
eventos de dominio, comandos, invariantes) más — si el BC expone pantallas nuevas — el prototipo
UX correspondiente. Ambos artefactos se aprueban explícitamente con Víctor antes de escribir la
primera US-IEDD del incremento. Procedimiento operativo en `docs/cm/WORKFLOW-DESARROLLO.md` §3.

---

## Incremento 0 — Fundación Técnica

| Iteración | Contenido |
|---|---|
| 1 | Repo, CI/CD (GitHub Actions), esqueleto Clean Architecture, PostgreSQL local (Homebrew — Docker diferido), Alembic |

**Hito:** No es instalar herramientas — eso ya lo resolvió `docs/plans/CHECKLIST-INSTALACION.md`.
Es **verificar con evidencia que las piezas instaladas funcionan integradas como un pipeline de
construcción real**, de punta a punta, en el entorno local: push a `develop` dispara CI y
termina en verde (lint + tests + DesignReviewer); push a `main` construye la imagen Docker sin
errores (el runtime de contenedores en sí queda diferido para uso local, ver revisión
2026-07-16 — el build de imagen en CI no lo requiere); PostgreSQL local (Homebrew) recibe una
migración de Alembic aplicada con éxito; la app corre localmente y expone `GET /health` → 200.
Cada ítem con su evidencia
registrada (log de CI, salida de `alembic upgrade head`, respuesta de `curl`), no solo "quedó
configurado". El despliegue a un entorno real (testing o producción, vía Fly.io u otro) queda
pendiente de la decisión de infraestructura (`ARQ_v1.md`, ítem abierto) y se resuelve en un
incremento posterior, no acá.

*(Este incremento es deliberadamente un slice técnico sin lógica de negocio — no hay dominio
que modelar todavía, por eso no lleva Iteración 0 — Modelado. BC Identidad, que sí tiene
dominio real (Usuario, Rol, Invitación), se mueve al Incremento 1.)*

---

## Incremento 1 — BC Identidad

| Iteración | Contenido |
|---|---|
| 0 | **Modelado:** event storming BC Identidad (Usuario, Rol, Invitación — invariantes de asignación automática a comisión) + wireframes de registro y login (`docs/design/domain/BC-identidad-modelo.md`, `docs/design/ux/`) |
| 1 | RF-01, RF-02: registro por invitación, roles, JWT, healthcheck |

**Hito:** Un estudiante se registra vía link de invitación y queda asignado automáticamente a
su comisión; un docente y un administrador se autentican y reciben un JWT con su rol correcto.
Corre en el entorno local sobre la fundación técnica del Incremento 0.

*(Primer BC con lógica de negocio real — sigue la misma regla de modelado que todos los que
siguen, sin excepción.)*

---

## Incremento 2 — Banco de preguntas

| Iteración | Contenido |
|---|---|
| 0 | **Modelado:** event storming BC Banco de Preguntas (agregados Pregunta/Banco, invariantes de metadatos) + wireframes de carga y filtrado (`docs/design/domain/BC-banco-preguntas-modelo.md`, `docs/design/ux/`) |
| 1 | RF-04, RF-05, RF-06: carga, tipos (opción múltiple / V-F), metadatos y filtrado |
| 2 | RF-03: gestión de cuentas por administrador |

**Hito:** El docente arma y mantiene el banco de preguntas completo, filtrable por
materia/unidad/tema/dificultad/importancia. El administrador resuelve problemas de cuentas sin
depender del docente.

*(RF-07, migración desde PDF, se pospone al final — no bloquea nada y su mecanismo aún no está
decidido).*

---

## Incremento 3 — Sesión de período abierto (primer flujo de valor real)

| Iteración | Contenido |
|---|---|
| 0 | **Modelado:** event storming completo BC Sesiones (agregado Sesion, eventos SesionCreada/RespuestaRegistrada/SesionCerrada, invariantes de persistencia atómica — Core Domain con Event Sourcing + CQRS, ADR-002) + wireframes del flujo de período abierto (`docs/design/domain/BC-sesiones-modelo.md`, `docs/design/ux/`) |
| 1 | RF-11, RF-12: creación de sesión y set aleatorio por estudiante |
| 2 | Persistencia respuesta a respuesta (confiabilidad — escenario RNF), RF-13: revisión al finalizar |
| 3 | RF-11b: modificación del período de disponibilidad en caliente |

**Hito:** Un estudiante completa una evaluación de período abierto de principio a fin — incluida
una desconexión simulada para validar cero pérdida de respuestas — y el docente puede extender
el plazo de una sesión activa. Es el primer flujo con valor real para ambos actores.

*(Primer incremento con datos reales de estudiantes en juego — los ítems abiertos de
infraestructura de producción y backup de `ARQ_v1.md` deben resolverse antes de arrancarlo.)*

---

## Incremento 4 — Portal del estudiante y Analytics

| Iteración | Contenido |
|---|---|
| 0 | **Modelado (liviano):** diseño de read models de Analytics sobre el event store del BC Sesiones ya modelado en el Incremento 3 + wireframes del portal del estudiante (`docs/design/domain/BC-analytics-modelo.md`, `docs/design/ux/`) |
| 1 | RF-15: vista de desempeño individual del estudiante |
| 2 | RF-16, RF-17: seguimiento por alumno y por curso/tema (primeros read models de Analytics sobre el event store) |

**Hito:** Docente y estudiante tienen visibilidad de desempeño histórico basado en sesiones
reales ya corridas en el incremento anterior.

---

## Incremento 5 — Notificaciones

| Iteración | Contenido |
|---|---|
| 0 | **Modelado (liviano):** contrato de eventos consumidos por BC Notificaciones desde BC Sesiones (integración directa, ADR-006) — no requiere prototipo UX nuevo (`docs/design/domain/BC-notificaciones-modelo.md`) |
| 1 | RF-14: email de apertura/cierre de sesión de período abierto |

**Hito:** El ciclo de la sesión de período abierto queda completo, incluida la comunicación
automática al estudiante.

*(Es un incremento corto y deliberadamente aislado: valida la integración BC Sesiones → BC
Notificaciones documentada en ADR-006 con el menor acoplamiento posible antes de seguir
agregando funcionalidad.)*

---

## Incremento 6 — Sesión en vivo (Kahoot!-style)

| Iteración | Contenido |
|---|---|
| 0 | **Modelado:** extensión del agregado Sesion existente (nuevos eventos de tiempo real, invariantes de ranking) + wireframes de pantalla en vivo/proyección. El spike del algoritmo de puntaje (RF-10, ítem pendiente) se resuelve dentro de esta iteración, junto al docente, antes de tocar código (`docs/design/domain/BC-sesiones-modelo.md` actualizado, `docs/design/ux/`) |
| 1 | RF-08: creación de sesión en vivo + infraestructura WebSockets |
| 2 | RF-09, RF-10: dinámica en tiempo real, ranking, cálculo de puntaje con el algoritmo cerrado en la iteración 0 |

**Hito:** El docente conduce una sesión en vivo completa en el aula, con ranking actualizado en
tiempo real dentro del umbral de ≤100ms server-side acordado en RNF.

*(Este es el incremento de mayor riesgo técnico — se llega a él con el resto de la arquitectura
ya validada en producción.)*

---

## Incremento 7 — Cierre de alcance v1

| Iteración | Contenido |
|---|---|
| 1 | RF-18: KPIs históricos (definidos incrementalmente junto al docente, según lo diferido en RF) |
| 2 | **Spike + implementación:** RF-07, mecanismo de importación desde PDF (automático vs. asistido — decisión pendiente) |

**Hito:** Sistema completo según el alcance v1 acordado en RF_v1.md, con el historial de
preguntas del docente migrado.

---

## Resumen de la estrategia

- **8 incrementos**, cada uno termina en un hito demostrable (desplegado, una vez resuelta la
  decisión de infraestructura — ver Incremento 0).
- El **orden sigue el riesgo real**: fundación técnica sin dominio → primer BC de dominio
  (identidad) → dominio estable (banco de preguntas) → primer flujo de valor sin tiempo real
  (período abierto) → observabilidad de ese flujo (analytics/notificaciones) → el flujo más
  exigente técnicamente (en vivo) → cierre de ítems diferidos.
- **Todo incremento que introduce o extiende un BC abre con una Iteración 0 — Modelado**
  (event storming + UX si corresponde), aprobada por Víctor antes de escribir la primera
  US-IEDD — sin excepciones. El Incremento 0 (fundación técnica) es el único que no aplica esta
  regla, precisamente porque no introduce ningún BC.
- Las **decisiones pendientes del RF** (algoritmo de puntaje, mecanismo PDF, comportamiento de
  link vencido) se resuelven como spikes al inicio del incremento que las necesita, con el
  docente presente — no se posponen indefinidamente ni se inventan.
- Los **ítems abiertos del ARQ** (infraestructura de producción, backup) se resuelven antes del
  Incremento 3, porque ya hay datos reales de estudiantes en juego a partir de ahí.
