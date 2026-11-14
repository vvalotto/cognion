# Revisión de calidad de diseño — Cognión `1.0.0`

> Fecha: 2026-11-14 · Código revisado: rama `develop` en `8906211` (posterior a `BL-017`)
> Destinatario: Víctor Valotto, como mantenedor
> Naturaleza: revisión independiente. No reemplaza ni corrige a `docs/architecture/`; la contrasta.

## Qué es este informe

Una revisión del proyecto con mirada de ingeniería de software, guiada por la calidad de diseño, desde la arquitectura hasta las decisiones de implementación, el despliegue, el proceso IEDD y la documentación.

Usa dos varas, y cada hallazgo dice con cuál se midió:

- **Conformidad:** ¿el proyecto cumple las reglas que él mismo se impuso (`ARQ_v1.md`, ADR, `RNF_v1.md`, `CLAUDE.md`)?
- **Decisión:** ¿la regla o la decisión es buena para este sistema y esta escala?

## Capítulos

| # | Capítulo | Pregunta que responde |
|---|---|---|
| 01 | [Resumen ejecutivo](01-resumen-ejecutivo.md) | ¿Cuál es el juicio global y qué atacar primero? |
| 02 | [Conformidad arquitectónica](02-conformidad-arquitectonica.md) | ¿El código cumple las reglas de capas? |
| 03 | [Acoplamiento entre contextos](03-acoplamiento-entre-contextos.md) | ¿Los cinco contextos son independientes? |
| 04 | [Dominio y event sourcing](04-dominio-y-event-sourcing.md) | ¿Agregados, eventos e invariantes están bien diseñados? |
| 05 | [Implementación por capa](05-implementacion-por-capa.md) | ¿Cada capa hace lo que le corresponde? |
| 06 | [Atributos de calidad](06-atributos-de-calidad.md) | ¿Qué escenarios de `RNF_v1.md` se sostienen? |
| 07 | [Verificación y testeabilidad](07-verificacion-y-testeabilidad.md) | ¿Los tests y la cobertura dicen la verdad? |
| 08 | [Instrumentos de calidad](08-instrumentos-de-calidad.md) | ¿Los gates miden bien o moldean el diseño? |
| 09 | [Frontend](09-frontend.md) | ¿El cliente está bien estructurado? |
| 10 | [Despliegue y operación](10-despliegue-y-operacion.md) | ¿Se puede instalar y operar con confianza? |
| 11 | [Proceso IEDD](11-proceso-iedd.md) | ¿El proceso produce calidad a un costo razonable? |
| 12 | [Documentación](12-documentacion.md) | ¿La documentación es confiable y sostenible? |
| 13 | [Plan priorizado](13-plan-priorizado.md) | ¿En qué orden conviene actuar y qué quedó sin revisar? |

## Método

1. **Mediciones sobre todo `src/`:** tamaño por contexto y capa, imports entre contextos, `import-linter`, cobertura por capa, y búsquedas de patrones (`commit()`, `HTTPException`, `datetime.now`, `isinstance`, `dict[str, Any]`).
2. **Lectura por muestreo:** el flujo de sesión en vivo de punta a punta (router, controller, caso de uso, agregado, event store, adaptador entre contextos), el arranque de la aplicación, la configuración, y casos de uso de Identidad y Banco de Preguntas con más de una escritura.
3. **Reportes existentes:** `BL-016-designreviewer.json`, `BL-016-arquitectura.json`, `coverage.json` y la vista `70-trazabilidad-rnf-vistas.md`.
4. **Proceso y documentación:** historia de git, specs, baselines, métricas de `implement-us` y los documentos de inventario.

No se ejecutó la suite de tests ni la aplicación. Lo que quedó fuera está en el [capítulo 13](13-plan-priorizado.md#no-revisado).

## Cómo leer un hallazgo

Cada hallazgo tiene un identificador con el prefijo de su capítulo (`AC-01`, `DM-02`…) y estos campos:

| Campo | Valores |
|---|---|
| **Vara** | *Conformidad* (incumple una regla propia) o *Decisión* (la regla o la elección es discutible) |
| **Severidad** | *Alta*: puede dejar datos inconsistentes, compromete un escenario de `RNF_v1.md` o rompe una regla declarada no negociable. *Media*: encarece el cambio o esconde defectos. *Baja*: higiene |
| **Confianza** | *Verificado*: medido o leído en el código. *Inferido*: deducido, falta confirmarlo ejecutando o leyendo más |
| **Esfuerzo** | *S* (horas), *M* (días), *L* (una iteración o más) |

## Sistema revisado, en números

| Dimensión | Valor |
|---|---|
| Backend (`src/`) | 22.696 líneas en 329 archivos Python |
| Contextos | Actividad Evaluativa 9.156 · Identidad 6.391 · Banco de Preguntas 3.144 · Analytics 2.777 · Shared 565 · Notificaciones 347 |
| Frontend (`frontend/src/`) | 263 archivos; 16.763 líneas sin contar tests |
| Tests de backend | 1.197 unitarios · 674 de integración · 636 escenarios BDD en 113 features |
| Tests de frontend | 112 archivos de Vitest · 9 circuitos de Playwright |
| Documentación (`docs/`) | 766 archivos Markdown, 85.089 líneas |
| Historia | 1.204 commits entre 2026-06-24 y 2026-11-13 · 27 ADR · 17 baselines |
