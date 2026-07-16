# HITO-2 — Un skill de auditoría documental se deriva del procedimiento manual, no al revés

> Estado documental: evidencia
> Registra un hallazgo de aprendizaje del ensayo IEDD en Cognion.
> No reemplaza a las fuentes vigentes (ADRs, arquitectura, specs).

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-2 — hallazgo metodológico sobre cómo empaquetar una práctica de gobernanza documental en un skill |
| **Fecha** | 2026-07-16 |
| **Incremento / contexto** | Sesión de trabajo sobre estrategia documental, previa al arranque operativo del Incremento 0 |
| **Relacionado** | `.claude/commands/docs-audit.md`, `.claude/commands/checkpoint.md`, `docs/inventario/FUENTES-DE-VERDAD-DOCUMENTAL.md`, `docs/inventario/DOCUMENTATION-MAP.md`, precedente `vvalotto/ataraxiadive` (deriva documental por acumulación de activos sin indexar) |

---

## Contexto

Al revisar dónde correspondía tener `README.md` vs. `CLAUDE.md` en la estructura del
repositorio, Víctor trajo la experiencia de AtaraxiaDive: a medida que avanzaba ese
proyecto se generaban nuevos activos documentales (ADRs, specs, procedimientos) que no
quedaban indexados, produciendo deriva y pérdida de trazabilidad. La pregunta concreta fue
si convenía resolver eso con un skill o con un agente dedicado, para detectar ese tipo de
gaps de forma proactiva en Cognion antes de que se repitiera el problema.

---

## Hallazgo / Análisis

Antes de decidir "skill vs. agente", se hizo primero el chequeo a mano: se leyeron
completas `docs/inventario/FUENTES-DE-VERDAD-DOCUMENTAL.md` y
`docs/inventario/DOCUMENTATION-MAP.md`, se inventariaron los archivos reales de
`docs/plans/` y `docs/iedd/`, y se cruzó archivo por archivo contra las tablas. Esa
pasada manual encontró dos huérfanos reales (`PROCEDIMIENTO-UAT.md` y
`CHECKLIST-INSTALACION.md`, sin ninguna fila que los declarara como fuente de verdad) y,
en una segunda pasada ya con el skill recién escrito, otros dos más
(`escenarios-calidad-draft.md` y `sesion-rnf.md` en `docs/rf/`, borradores de elicitación
sin marcar como históricos).

Recién con ese procedimiento ya ejecutado y verificado a mano se escribió
`/docs-audit` como skill — el algoritmo del skill es literalmente la secuencia de pasos
que se siguió manualmente (inventariar filesystem → leer tablas completas, no grep →
cruzar archivo por archivo → filtrar falsos positivos con un criterio explícito de
ambigüedad real → proponer la fila, no aplicarla). No se diseñó el skill primero para
después probarlo: se probó el procedimiento primero, con casos reales, y el skill quedó
como la cristalización de esa experiencia.

Dos decisiones de diseño quedaron resueltas por el mismo motivo — evitar que el skill
introdujera un riesgo nuevo en vez de mitigar el que resolvía:

- **Solo reporta, nunca edita** `FUENTES-DE-VERDAD-DOCUMENTAL.md` ni
  `DOCUMENTATION-MAP.md` — son documentos de autoridad; la decisión editorial de cómo
  indexar cada gap (fila nueva vs. ampliar una fila de carpeta) es de Víctor.
- **No se creó un hook de harness ni un agente en background** para dispararlo
  automáticamente. `/docs-audit` requiere criterio (distinguir cobertura a nivel de
  archivo vs. de carpeta, filtrar falsos positivos) — eso es razonamiento de Claude, no
  un chequeo determinístico ejecutable por un script de shell. El punto de enganche
  quedó dentro de `/checkpoint`, el ritual manual que ya existía para cerrar sesión,
  como paso condicional ("si se tocó `docs/` esta sesión, correr `/docs-audit` antes de
  guardar") — no un mecanismo nuevo.

---

## Aprendizaje(s)

- **L-2.1:** Un skill de gobernanza documental se diseña *después* de correr el
  procedimiento a mano al menos una vez con casos reales del propio proyecto — el
  algoritmo del skill debe ser la experiencia distillada, no una hipótesis de cómo
  debería funcionar la auditoría.
- **L-2.2:** Un skill que audita documentos de autoridad debe reportar, no aplicar —
  la corrección de un documento que rige trazabilidad es una decisión editorial humana,
  no una acción mecánica.
- **L-2.3:** No toda detección proactiva necesita un agente en background o un hook de
  harness. Cuando la tarea requiere juicio (no es determinística) y el proyecto ya tiene
  un ritual manual de cierre de sesión, el punto de enganche correcto es ese ritual
  existente, no un mecanismo de automatización nuevo — menos piezas móviles para un
  equipo unipersonal.
- **L-2.4:** El criterio de "¿es esto realmente un gap?" no es "¿aparece en la tabla?"
  sino "¿hay ambigüedad real sobre la autoridad de este tema si surge una duda o
  conflicto?" — aplicar ese filtro evitó que el skill señalara como huérfanos archivos
  únicos y autoevidentes (ej. `docs/traceability/matrix.md`) que no necesitan fila
  propia.

---

## Relación con la hipótesis del ensayo

Se relaciona con `docs/iedd/04-Hipotesis_Ensayo_IA_Ingenieria_Human_In_The_Loop.md` §3.4
sobre el rol estructural del human-in-the-loop: acá el rol no fue detectar una
inconsistencia ya cometida (como en HITO-1), sino decidir, antes de automatizar nada,
que la automatización debía derivarse de la práctica verificada y no al revés — una
función preventiva de diseño, no solo correctiva.

---

## Resumen de Aprendizajes

| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-2.1 | Un skill de auditoría se diseña después de correr el procedimiento a mano con casos reales | Proceso / Documentación |
| L-2.2 | Un skill sobre documentos de autoridad reporta, no aplica ediciones | Documentación / Quality |
| L-2.3 | La detección proactiva se engancha en rituales manuales existentes antes que en hooks o agentes nuevos | Proceso / Workflow |
| L-2.4 | El criterio de gap es "ambigüedad real de autoridad", no "ausencia en la tabla" | Documentación |

---

*Creado: 2026-07-16*
