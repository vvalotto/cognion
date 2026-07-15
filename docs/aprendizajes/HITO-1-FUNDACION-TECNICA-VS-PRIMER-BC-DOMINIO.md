# HITO-1 — Fundación técnica vs. primer BC de dominio: el plan necesita el mismo gate que exige al código

> Estado documental: evidencia
> Registra un hallazgo de aprendizaje del ensayo IEDD en Cognion.
> No reemplaza a las fuentes vigentes (ADRs, arquitectura, specs).

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-1 — hallazgo metodológico previo al arranque del Incremento 0 |
| **Fecha** | 2026-07-15 |
| **Incremento / contexto** | Planificación del Incremento 0, antes de abrir la primera baseline (sin BL-000) |
| **Relacionado** | `docs/rf/PLAN_v1.md` (revisión 2026-07-15), `docs/plans/WORKFLOW-DESARROLLO.md` §3 y §6, precedente `vvalotto/ataraxiadive` (`docs/plans/sp1/SP1-candidatas.md`, Inc 1.1 vs 1.2) |

---

## Contexto

Con el checklist de instalación resuelto, se inició la planificación operativa del
Incremento 0 (`docs/plans/incN/incN-candidatas.md`, primer uso de ese artefacto en Cognion).
Al construir las US candidatas para la Iteración 2 del Incremento 0 original ("BC Identidad:
RF-01, RF-02, JWT, healthcheck"), surgieron dos preguntas directas de Víctor que no tenían
respuesta consistente en el plan: *"¿por qué instalar PostgreSQL en Fly.io si todavía no se va
a usar en la nube?"* y *"¿por qué decís que no hay dominio que modelar en el Incremento 0 si
ahí está el registro de usuarios y roles?"*.

---

## Hallazgo / Análisis

`docs/rf/PLAN_v1.md` definía el Incremento 0 como "Walking Skeleton", empaquetando en el mismo
incremento dos cosas de naturaleza distinta:

- **Iteración 1:** fundación técnica pura (repo, CI/CD, Docker, PostgreSQL, esqueleto de capas) — sin lógica de negocio.
- **Iteración 2:** BC Identidad completo (registro por invitación, roles, JWT) — con agregados y invariantes reales (Usuario, Rol, Invitación).

El propio plan afirmaba, en el mismo párrafo, que este incremento *"no lleva Iteración 0 —
Modelado: es deliberadamente un slice técnico sin lógica de negocio, no hay dominio que
modelar todavía"* — una afirmación cierta para la Iteración 1, pero falsa para la Iteración 2.
Nadie lo había verificado hasta que se intentó bajar el plan a candidatas concretas.

Encima, quien esto escribe (Claude) ya había construido un `inc0-candidatas.md` completo sobre
esa premisa sin cuestionarla, e incluso guardado una entrada de memoria citando el precedente de
AtaraxiaDive como si validara la mezcla — cuando en realidad ese mismo precedente
(`SP1-candidatas.md`, Inc 1.1 "Fundación técnica" vs. Inc 1.2 "El dominio habla") demuestra
justamente la separación que Cognion no había hecho. La inconsistencia se resolvió recién
cuando Víctor preguntó directamente por la infraestructura de Fly.io y por dónde estaba
modelado el dominio de Identidad — dos preguntas concretas de negocio/arquitectura que
expusieron la falla que ninguna revisión automática (lint, tests, DesignReviewer) podía
detectar, porque es una inconsistencia *conceptual* entre artefactos de planificación, no de
código.

**Anti-patrón identificado:** el mismo que el proyecto ya nombra como "spec-validatoria" para
dominio y UX (especificar mirando el código/diseño existente en vez del modelo aprobado) se
manifestó un nivel más arriba — construir candidatas de un incremento sin auditar primero la
consistencia interna del plan de origen contra sus propias reglas declaradas.

---

## Aprendizaje(s)

- **L-1.1:** Instalar y verificar son actos distintos, y el primer incremento técnico debe ser
  el segundo, no el primero. El checklist de instalación resuelve la *presencia* de
  herramientas; el incremento de fundación técnica debe demostrar, con evidencia registrada
  (log de CI, salida de `alembic upgrade head`, respuesta de `curl` a `/health`), que esas
  piezas funcionan **integradas como un pipeline real** de punta a punta en el entorno local.
  "Quedó configurado" no es un criterio de éxito válido para un incremento — "corrió y dejó
  evidencia" sí.
- **L-1.2:** Un incremento de fundación técnica pura y el primer incremento con lógica de
  negocio real nunca deben compartir número de incremento, aunque el volumen de trabajo del
  primero sea chico. Mezclarlos produce exactamente la contradicción detectada: la regla
  "modelado de dominio antes de construir, por BC" necesita una excepción ad-hoc para el
  incremento mezclado, en lugar de aplicarse sin excepciones a todo lo que sí introduce un BC.
- **L-1.3:** El plan de incrementos (`PLAN_v1.md`) necesita el mismo gate de consistencia que
  el proyecto exige para dominio y UX — auditar sus propias reglas contra su propio contenido
  antes de bajarlo a candidatas operativas, no asumir que un documento de "definición" está
  libre de inconsistencias por haber sido "verificado" en la etapa de elicitación.
- **L-1.4:** Tener un precedente validado (AtaraxiaDive) no garantiza aplicarlo correctamente —
  hay que verificar que la aplicación nueva replica la distinción real del precedente, no solo
  su vocabulario. La primera versión de `PLAN_v1.md` usó el término "Walking Skeleton" sin
  replicar la separación Inc 1.1/1.2 que el propio precedente ya modelaba.

---

## Relación con la hipótesis del ensayo

Confirma con más fuerza el punto de `docs/iedd/04-Hipotesis_Ensayo_IA_Ingenieria_Human_In_The_Loop.md`
§3.4 sobre el rol estructural (no de parche) del human-in-the-loop, específicamente en la
función de **"detectar inconsistencias entre artefactos"**: la IA (Claude) construyó y hasta
persistió en memoria un plan operativo completo sobre una premisa contradictoria del documento
fuente, sin detectarla — la revisión automática (lint/tests/DesignReviewer) no aplica a este
tipo de falla, porque es semántica entre documentos de planificación, no sintáctica en código.
Solo la pregunta de dominio de Víctor ("¿por qué Fly.io si no se despliega?", "¿dónde está
modelado Usuario?") expuso el problema.

---

## Resumen de Aprendizajes

| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-1.1 | Instalación ≠ verificación — el incremento de fundación técnica exige evidencia de pipeline integrado, no configuración declarada | Proceso |
| L-1.2 | Fundación técnica pura y primer BC de dominio nunca comparten incremento | Proceso / Arquitectura |
| L-1.3 | El plan de incrementos necesita auditoría de consistencia interna antes de bajar a candidatas | Documentación / Proceso |
| L-1.4 | Un precedente validado debe verificarse en su distinción real, no solo copiarse por vocabulario | Proceso |

---

*Creado: 2026-07-15*
