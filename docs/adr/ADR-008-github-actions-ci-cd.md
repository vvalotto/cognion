# ADR-008 — GitHub Actions para CI/CD (vs. Jenkins o GitLab CI)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

El escenario de calidad de Administrabilidad en `RNF_v1.md` exige que el deployment de una
nueva versión no requiera intervención manual al hacer push a `main`. El equipo es unipersonal
(driver arquitectónico 4) y el repositorio ya vive en GitHub.

## Opciones Consideradas

- **Jenkins self-hosted** — descartada: requiere mantener infraestructura propia de CI (un
  servidor adicional), overhead operacional que un equipo de una persona no puede absorber.
- **GitLab CI** — descartada: implicaría migrar el repositorio de GitHub a GitLab, sin
  beneficio que lo justifique.
- **GitHub Actions** — integrado nativamente al repositorio ya alojado en GitHub. Elegida.

## Decisión

GitHub Actions como única herramienta de CI/CD, con pipelines separados: lint + test en
`develop`, build + deploy en `main`.

## Justificación

El repositorio ya vive en GitHub — Actions no requiere infraestructura propia, se integra
directamente con Secrets y Environments para las credenciales del proveedor de hosting, y
permite separar naturalmente los pipelines de integración continua (develop) y despliegue
continuo (main) sin herramientas adicionales.

## Impacto en Configuración

- `.github/workflows/` — `lint-test.yml` (push/PR a `develop`), `build-deploy.yml` (push a
  `main`).
- `Dockerfile` — imagen multi-stage usada por el job de build.
- Secrets de GitHub (Settings → Secrets) — credenciales del proveedor de hosting (Fly.io).

## Consecuencias

- ✅ Sin infraestructura propia de CI que mantener
- ✅ Integración nativa con Secrets y Environments de GitHub
- ✅ Pipelines separados por rama sin herramientas adicionales
- ⚠️ Acoplado a GitHub como plataforma — migrar de proveedor de repositorio implicaría migrar
  también el CI/CD
