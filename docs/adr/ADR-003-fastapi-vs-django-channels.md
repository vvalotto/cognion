# ADR-003 — FastAPI como framework backend (vs. Django + Channels)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

El sistema requiere WebSockets para sesiones en vivo y REST para las demás operaciones. El
lenguaje es Python. Se necesita un framework que soporte async nativo, WebSockets, y que no
imponga estructura que conflictúe con Clean Architecture.

## Opciones Consideradas

- **Django + Channels** — requiere un channel layer (típicamente Redis) y workers separados
  para soportar WebSockets. Descartada: añade complejidad operacional que el driver 4 (equipo
  unipersonal) no puede absorber, y Django impone una estructura de proyecto que fricciona con
  Clean Architecture.
- **FastAPI** — async nativo, WebSockets en el mismo proceso, sin imponer estructura de
  directorios. Elegida.

## Decisión

FastAPI como único framework backend.

## Justificación

FastAPI es async nativo y soporta WebSockets en el mismo proceso sin infraestructura adicional.
Es delgado: no impone modelo de datos ni estructura de directorios, lo que permite implementar
Clean Architecture sin fricciones.

## Impacto en Configuración

- `pyproject.toml` — dependencias `fastapi`, `uvicorn[standard]`.
- `Dockerfile` — comando de arranque `uvicorn` en el stage final.
- `src/<bc>/frameworks/` — routers FastAPI (REST) y endpoints WebSocket conviven en la misma
  capa de frameworks, sin infraestructura de mensajería adicional.

## Consecuencias

- ✅ WebSockets y REST en el mismo proceso async
- ✅ Sin infraestructura adicional de mensajería
- ✅ Pydantic integrado para validación en Interface Adapters
- ✅ OpenAPI/Swagger automático
- ⚠️ Sin admin integrado (no es necesario para este sistema)
