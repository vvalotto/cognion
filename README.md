# Cognión

> Plataforma web de evaluación universitaria con cuestionarios gamificados.

Cognión es una aplicación web de evaluación de conocimiento inspirada en la dinámica de Kahoot!, pensada para la Facultad de Ingeniería de la UNER. Un docente arma un banco de preguntas por materia y propone actividades a su comisión; los alumnos responden con corrección automática y reciben resultados inmediatos. Está pensada para materias de Ingeniería de Software y Gestión de Proyectos, con comisiones de 30 a 60 alumnos.

## Qué hace

- **Sesión en vivo:** el docente conduce una sesión en clase, pregunta por pregunta; los alumnos responden desde el celular y ven el ranking.
- **Período abierto:** una actividad evaluativa con apertura y cierre, que cada alumno resuelve por su cuenta.
- **Banco de preguntas** por materia (verdadero/falso y opción múltiple).
- **Cuentas y roles:** administrador, docente y estudiante, con alta por invitación a la comisión.
- **Notificaciones** por email y **analytics** del docente sobre el desempeño de sus comisiones.

## Estado

**Versión `1.0.0`** (ver [`CHANGELOG.md`](CHANGELOG.md)). Las funciones de arriba están validadas (matriz en [`docs/traceability/matrix.md`](docs/traceability/matrix.md)). Quedan sin implementar la importación de preguntas desde PDF y los KPIs históricos.

Se está trabajando en la calidad de diseño de cara a la `1.1.0`: hasta entonces no entra funcionalidad nueva (detalle en [`CLAUDE.md`](CLAUDE.md)).

## Instalación

La guía única es [`docs/INSTALACION.md`](docs/INSTALACION.md). Hay tres caminos: un servidor Linux con Docker, una sola máquina sin Docker (para una clase), o una VM en Google Cloud. El del servidor con Docker lo prueba el CI contra Docker real en `localhost`; en un servidor con dominio y certificado todavía no se ensayó (Issue #624).

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI (async), SQLAlchemy y Alembic |
| Base de datos | PostgreSQL; los eventos de las sesiones en vivo en una tabla append-only |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS y shadcn/ui |
| Autenticación | JWT (PyJWT) con roles |
| Entrega | Docker multi-stage, GitHub Actions (CI/CD) |

## Arquitectura

Monolito modular con Clean Architecture dentro de cada contexto (Identidad, Banco de Preguntas, Actividad Evaluativa, Notificaciones y Analytics). Las reglas de dependencia las verifica `import-linter` en el CI.

- Descripción vigente, contrastada con el código de la `1.0.0`: [`docs/architecture/`](docs/architecture/README.md).
- Decisiones y su porqué: [`docs/adr/`](docs/adr/).
- Requerimientos y plan originales: [`docs/rf/`](docs/rf/).
- Mapa de toda la documentación: [`docs/inventario/DOCUMENTATION-MAP.md`](docs/inventario/DOCUMENTATION-MAP.md).

## Desarrollo

Backend con `uv`, frontend con `npm`. Los tests de integración y BDD vacían la base a la que apunte `DATABASE_URL`: usá siempre una base descartable cuyo nombre termine en `_test`. Las reglas del flujo de trabajo y de los quality gates están en [`CLAUDE.md`](CLAUDE.md).

## Contexto

Proyecto desarrollado en la Facultad de Ingeniería — UNER, por un docente único. Público: docentes y alumnos de carreras de ingeniería.
