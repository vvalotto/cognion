# Evidencia UAT — Incremento 0 "Fundación Técnica"

| Campo | Valor |
|-------|-------|
| Fecha | 2026-07-16 |
| Entorno | Propio (local, PostgreSQL vía Homebrew) |

---

## Alembic

```
$ uv run alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
696c5efea732 (head)
```

`alembic_version` en la base `cognion` local coincide con la única migración existente
(`696c5efea732 — fundacion tecnica - primera migracion vacia`).

---

## Capa 2 — HTTP

```
$ uv run uvicorn src.app:app --host 0.0.0.0 --port 8000 &
$ curl -s -w "\nHTTP %{http_code}\n" http://127.0.0.1:8000/health
{"status":"ok"}
HTTP 200
```

---

## Resultado

Sin hallazgos 🔴 Bloqueantes. Criterio de aceptación de `design.md` cumplido.
Capa 1 (dominio) y checkpoint de staging: no aplican / diferidos — ver `design.md`.

**UAT: ✅ Aprobado.**
