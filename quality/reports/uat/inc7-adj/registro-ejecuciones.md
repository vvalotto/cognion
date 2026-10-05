# Registro de ejecuciones — UAT de cierre del Incremento 7-ADJ

Bitácora de lo ejecutado, en orden. Plan: `plan-de-pruebas.md`. Hallazgos: `registro-hallazgos.md`.
Ejecutor: Víctor (decisión y supervisión) · Conductor y escritor: sesión de Claude Code.
Navegador usado: **navegador integrado de Claude Desktop (Chromium)**, no el navegador propio de Víctor.

## 2026-10-05 — Bloque 0: preparación del entorno

| Paso | Qué se hizo | Resultado |
|---|---|---|
| 0.0 | Estado inicial de la base `cognion`: 0 usuarios, 1 materia ("Materia - UAT7"), 3 preguntas, 42 eventos huérfanos (restos de la UAT v1), migración en `a6c2d4f8b1e3` | Se hizo `pg_dump` antes de tocar nada (respaldo en el scratchpad de la sesión) |
| 0.1 | `alembic upgrade head` | `c4d1f9a27b60` (`usuario.bloqueada_hasta`) aplicada — **sin ella `US-ADJ-60` no funcionaba en esta base** |
| 0.2 | `DELETE FROM events` (42 eventos huérfanos de la UAT v1, sin usuarios asociados; ya rompieron consultas de Analytics antes) y `tests/uat/datos-reales/sembrar.py` | 20 usuarios (1 Administrador, 2 Docentes, 17 Estudiantes), 3 materias, 1 comisión, 110 preguntas, 85 eventos. Login del Administrador `200` |
| 0.3 | Backend (`:8000`) y frontend dev (`:5173`) levantados con `preview_start` | `/docs` `200` |

Cuentas de la siembra: `admin@fiuner.edu.ar`, `victor.valotto@fiuner.edu.ar` (Docente Ing. de Software), `alejandra.morales@fiuner.edu.ar` (Docente Gestión de Proyectos); contraseñas en `tests/uat/datos-reales/usuarios.md` (fuera de git). Estudiantes: contraseña única de la siembra.

## 2026-10-05 — Bloque 1: spike del hallazgo #1 (autoregistro `201` sin persistir)

Método: cada intento se hizo desde el navegador (formulario real), y se contrastó el log del backend (`POST` y status) con `psql` (fila en `usuario`). Cuentas de prueba `spike.*@fiuner.edu.ar`.

| Caso | Entorno | Intentos | `POST` con 201 | Filas nuevas | Resultado |
|---|---|---|---|---|---|
| 1.2 Autoregistro de Docente | **Dev** (`npm run dev`, StrictMode activo) | 5 | 5 | 5 | ✅ Cada 201 persistió; 0 duplicados |
| 1.1 Autoregistro de Docente | **Build de producción** (`vite build` + `vite preview`, mismo puerto 5173 por el CORS) | 5 | 5 | 5 | ✅ Idem |
| 1.3a Autoregistro de Estudiante (Materia → Comisión) | Dev | 1 | 1 | 1 (con comisión) | ✅ |
| 1.3b Recuperación de contraseña completa (solicitar → token de `psql` → definir contraseña → login) | Build | 1 | `202` + `200` | token usado | ✅ Login `200` con la contraseña nueva; sin `422` |
| 1.3c Ídem | Dev | 1 | `202` + `200` | token usado | ✅ Idem |

Observaciones:
- El intento 2 de la primera tanda en dev no llegó a enviarse (sin `POST`, sin fila): fue un artefacto de **mi** automatización (un lote interrumpido por un error de coordenadas). Repetido en limpio, persistió.
- Lectura del código: `AutoregistroDocente.tsx` y `RecuperarPasswordNueva.tsx` crean el `AbortController` dentro del `useEffect` (corrección de `US-ADJ-20`); no hay doble envío posible desde ahí. Los mensajes de política de contraseña del backend empiezan con "La contraseña debe", así que el frontend los distingue del token inválido.
- Limpieza: las 11 cuentas `spike.*` y sus tokens se borraron de la base (volvió a 20 usuarios).

**Resultado del spike:** no reproduce en 13 envíos (modo dev y build). Ver hallazgo #1.
