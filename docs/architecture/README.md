# Documentación de arquitectura — Cognión

> Contrastada con el código de la versión `1.0.0` (Incremento 10.1, 2026-11). Marco: C4 más vistas de datos, runtime, transversal, desarrollo y despliegue.

## Propósito

Esta carpeta es la **descripción arquitectónica vigente** de Cognión: cómo está estructurada, cómo colaboran sus partes, qué reglas la sostienen y cómo se instala. Está escrita para tres lectores: quien **instala y opera**, quien **mantiene el código** y la **materia** (como material para explicar un sistema real).

No reemplaza a `docs/rf/ARQ_v1.md` (arquitectura inicial, histórica) ni a `docs/adr/` (el *por qué* de cada decisión), ni al modelo de dominio por BC (`docs/design/domain/`). Si una vista contradice al código, **se corrige la vista**: el código y los tests mandan.

## Por dónde empezar

| Si querés… | Leé |
|---|---|
| Entender qué es Cognión y con quién habla | `01-system-context.md` |
| Instalar y operar | `60-deployment-view.md`, luego `docs/INSTALACION.md` |
| Ver cómo se divide el sistema | `02-container-view.md`, `03-bounded-contexts.md` |
| Tocar un Bounded Context | `10` a `14-componentes-*.md` (el que corresponda) |
| Seguir un flujo de punta a punta | `30-runtime-interactions.md` |
| Saber qué reglas no romper | `40-cross-cutting-concerns.md`, `50-development-view.md` |
| Saber qué calidad se cumple de verdad | `70-trazabilidad-rnf-vistas.md` |

## Las vistas

| Vista | Documento | Pregunta que responde |
|---|---|---|
| C4-1 Contexto | `01-system-context.md` | ¿Qué es y con quién habla? |
| C4-2 Contenedores | `02-container-view.md` | ¿Qué procesos y almacenes hay? |
| Catálogo de BC | `03-bounded-contexts.md` | ¿Cómo se parte el dominio? |
| C4-3 Componentes | `10-componentes-identidad.md`, `11-componentes-banco-preguntas.md`, `12-componentes-actividad-evaluativa.md`, `13-componentes-analytics.md`, `14-componentes-notificaciones.md` | ¿Cómo está armado cada BC por dentro? |
| Mapa de contexto | `20-context-map-integrations.md` | ¿Cómo se relacionan los BC y por qué puertos? |
| Datos | `24-modelo-datos-postgresql.md`, `24a`, `24b`, `24c` | ¿Qué tablas hay y quién las escribe? |
| Runtime | `30-runtime-interactions.md` | ¿Qué pasa en los flujos críticos? |
| Transversal | `40-cross-cutting-concerns.md` | Seguridad, configuración, logging, salud, errores |
| Desarrollo | `50-development-view.md` | Estructura, dependencias, calidad, CI/CD, versionado |
| Despliegue | `60-deployment-view.md` | ¿Dónde corre y cómo se instala y opera? |
| Calidad | `70-trazabilidad-rnf-vistas.md` | ¿Qué escenario de `RNF_v1.md` se cumple y con qué evidencia? |

Plantilla común de las vistas: `_plantilla-vista.md`.

## Cómo se mantiene

Cada vista termina con tres secciones que son su contrato de mantenimiento:
- **Cómo verificar contra el código:** comandos o archivos concretos para comprobar que sigue siendo cierta.
- **Cuándo hay que actualizarla:** qué tipo de cambio obliga a tocarla.
- **Sin verificar:** lo que no se pudo contrastar, marcado con ⚠. Una vista no afirma lo que no comprobó.

Al cerrar una baseline se corre `/docs-audit` y se revisan las vistas que el incremento haya invalidado.

## Principios
- **Descriptivas, no aspiracionales.** Lo que no existe se marca como pendiente.
- **No duplicar.** Se enlaza a los ADR y a `docs/design/domain/` en vez de repetirlos.
- **Un diagrama por pregunta.** Cada caja y flecha se puede rastrear a un archivo o a un ADR.
- **Separar** lo estático (estructura), lo dinámico (flujos) y lo transversal.

## Cómo se produjo esta versión
El plan, las brechas y la auditoría del dominio están en `docs/plans/inc10-1/` (Incremento 10.1, documental, sin US). La baseline es `BL-017`.
