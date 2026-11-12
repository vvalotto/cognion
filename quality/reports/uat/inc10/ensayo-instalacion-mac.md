# Ensayo de instalación limpia — Mac sin Docker (`US-10.3.1`, 2026-11-11)

**Versión:** `1.0.0` (`develop` en `b5bf485`, exportada con `git archive` a una carpeta vacía, sin `.venv`, `.env` ni `frontend/dist`).
**Método:** solo `docs/INSTALACION.md`, camino B, con base propia (`cognion_ensayo`) y puerto 8765; no se tocó `cognion`, `cognion_local` ni `cognion_uat`.
**Resultado:** ✅ La instalación funciona. 1 hallazgo 🟡 corregido en la guía.

| Verificación | Resultado |
|---|---|
| `uv sync` en carpeta limpia | ✅ 10 s |
| `levantar.sh --fondo` crea base, compila frontend, migra, crea el primer Administrador e imprime la dirección para alumnos | ✅ (tras crear `.env`, ver H-1) |
| `GET /api/health` → `{"status":"ok","version":"1.0.0"}`, `/` sirve el frontend | ✅ |
| Recorrido HTTP (`tests/uat/inc10/capa2_http.py`) contra esta instalación: docente, link grupal, 3 estudiantes, errores del registro, bloqueo de login, log sin token | ✅ 27/27 |
| `respaldar.sh` (dump verificado) y ensayo de `restaurar.sh` (conteos coinciden) | ✅ |
| `restaurar.sh --sobre-local` con confirmación `RESTAURAR`: un docente creado después del respaldo desaparece (6 → 5 usuarios), el servidor vuelve a levantar y el login del admin responde 200 | ✅ |
| Actualización simulada (VERSION 1.0.1, `levantar.sh` otra vez): conserva datos (5 usuarios), no recrea el Administrador, `/api/health` informa `1.0.1` | ✅ |

## Hallazgos
| # | Sev. | Descripción | Resolución |
|---|---|---|---|
| H-1 | 🟡 | La guía no decía que `levantar.sh` necesita un `.env` (de ahí toma usuario y host de PostgreSQL). En una carpeta recién descomprimida se detenía con "No encuentro un DATABASE_URL de origen". | Se agregó el paso `cp .env.example .env` y se documentó la actualización local. |

## No verificado
- Recorrido en navegador y celular reales: el ensayo fue por HTTP.
- La actualización se simuló cambiando `VERSION` en la misma carpeta; no se probó descomprimir una versión nueva y copiar `.env.local`.
- Rol de PostgreSQL con contraseña distinta a la del ejemplo: aquí coincide con el del ejemplo.
