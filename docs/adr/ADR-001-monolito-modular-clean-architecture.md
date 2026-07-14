# ADR-001 — Monolito modular con Clean Architecture (vs. microservicios)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

El sistema es desarrollado y mantenido por un único desarrollador. Tiene un dominio de
complejidad media-alta (dos modos de sesión, event sourcing, tiempo real) pero una escala
modesta (hasta 60 usuarios simultáneos). Se necesita deployment frecuente y CI/CD sin
fricción (driver arquitectónico 4).

## Opciones Consideradas

- **Microservicios** — un servicio por Bounded Context, comunicación de red entre ellos.
  Descartada: introduce complejidad operacional (múltiples deployments, distributed tracing,
  comunicación de red) que un equipo de una persona no puede absorber, sin que la escala
  proyectada la justifique.
- **Monolito modular con Clean Architecture interna** — Bounded Contexts como módulos del
  mismo proceso, con capas internas que aíslan el dominio de la infraestructura. Elegida.

## Decisión

Monolito modular con Clean Architecture interna. Los Bounded Contexts son módulos del mismo
proceso, no servicios independientes.

## Justificación

Microservicios no están justificados para un equipo de una persona y la escala proyectada. La
modularidad por BCs dentro del monolito preserva la separación conceptual sin el overhead de
distribución. La Clean Architecture responde además a los drivers 5 (modelo de dominio
extensible) y 7 (dos modos de sesión con ciclo de vida distinto): el dominio vive aislado de la
infraestructura, los Use Cases orquestan sin saber qué framework los ejecuta, y ambos modos de
sesión pueden modelarse con pureza.

**Trade-off aceptado:** mayor estructura inicial que un monolito layered clásico. La inversión
en capas se justifica por la complejidad del dominio de Sesiones y la necesidad de
extensibilidad futura.

## Impacto en Configuración

- Estructura de paquetes `src/<bc>/{entities,use_cases,interface_adapters,frameworks}/` — regla
  de imports documentada en `CLAUDE.md`.
- `Dockerfile` — un único artefacto multi-stage, no un despliegue por servicio.
- `pyproject.toml` — un solo proyecto Python, sin monorepo de paquetes independientes por BC.

## Consecuencias

- ✅ Deployment simple: un único artefacto Docker
- ✅ Debugging local sin infraestructura de red entre servicios
- ✅ Menor latencia: comunicación en memoria entre BCs
- ⚠️ Escalar partes independientes en el futuro requerirá partir el monolito
