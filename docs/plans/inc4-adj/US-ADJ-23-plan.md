# Plan de Implementación: US-ADJ-23 - Administrador ve el listado de Comisiones de una Materia

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion
**BC:** Identidad + frontend

## Componentes a Implementar

### 1. Entities — sin cambios

`Comisión.docentes_asignados` (`entities/comision.py`) ya existe como `list[UUID]` — nada que
tocar en esta capa.

### 2. Use Cases — sin cambios

`ComisionesQueryController.listar_comisiones_por_materia`/`listar_estudiantes`
(`interface_adapters/controllers/comisiones_query_controller.py`) ya delegan correctamente al
puerto — nada que tocar en esta capa.

### 3. Interface Adapters (Backend)

- [x] `src/identidad/interface_adapters/gateways/comision_query_repository.py`
  - `listar_comisiones_por_materia`: reemplazar `docentes_asignados=[]` hardcodeado por
    `[d.id for d in modelo.docentes]` (la relación `ComisionModel.docentes` ya existe,
    `frameworks/db/models.py:85`)
  - Actualizar el docstring que hoy documenta el `[]` como deliberado

### 4. Frameworks (Backend)

- [x] `src/identidad/frameworks/dependencies.py`
  - Nueva dependency `require_docente_o_administrador = require_rol([TipoPerfil.DOCENTE,
    TipoPerfil.ADMINISTRADOR], get_current_user)`, junto a las 3 existentes (líneas 171-177)
- [x] `src/identidad/frameworks/api/materias_comisiones_router.py`
  - `GET /materias/{id}/comisiones`: `require_docente` → `require_docente_o_administrador`
- [x] `src/identidad/frameworks/api/comisiones_router.py`
  - `GET /comisiones/{id}/estudiantes`: `require_docente` → `require_docente_o_administrador`
- [x] `src/identidad/frameworks/api/schemas.py`
  - `ComisionResumenResponse` gana `docentes_asignados: list[UUID]`

### 5. Frontend — Cliente API

- [x] `frontend/src/lib/identidad-comisiones-api.ts` (ya existía, ver "Cambios no Previstos" — extendido, no reemplazado)
  - `listarComisionesPorMateria(materiaId, signal?)` → `GET /materias/{id}/comisiones`,
    mapea `docentes_asignados` (snake_case → camelCase)
  - `listarEstudiantesDeComision(comisionId, signal?)` → `GET /comisiones/{id}/estudiantes`
  - Reutiliza `apiFetch` de `api-client.ts` (mismo patrón que `banco-preguntas-api.ts`)
  - Reutiliza `listarMaterias()` de `banco-preguntas-api.ts` (ya existe, sin cambios) y
    `listarCuentas({ rol: "docente" })` de `cuentas-api.ts` (ya existe, sin cambios) para
    resolver nombres de Docente por id

### 6. Frontend — Pantalla

- [x] `frontend/src/pages/identidad/Comisiones.tsx` (nuevo)
  - Selector de Materia (`listarMaterias()`)
  - Tabla: horario, Docentes asignados (cruza `docentes_asignados` contra
    `listarCuentas({rol:"docente"})` por id → nombre; badge "Sin docente asignado" si vacío),
    cantidad de Estudiantes (`listarEstudiantesDeComision(id).length` por fila)
  - Botón "+ Nueva Comisión" (placeholder de ruta hasta `US-ADJ-24`, mismo criterio que
    placeholders temporales de incrementos anteriores)
  - Estado vacío si la Materia no tiene Comisiones
  - Wireframe: `docs/design/ux/wireframes-portal-entrada.md` §3.1

### 7. Integración

- [x] `frontend/src/router.tsx`
  - Ruta `/comisiones`, protegida con `RequireRole rol="administrador"`
- [x] Verificar manualmente contra el prototipo (`docs/design/ux/prototipos/portal-entrada.html`,
  pantalla 4) antes de dar la US por terminada

### 8. Ajuste detectado en Fase 3 — gap adicional en `GET /materias`

- [x] `GET /materias` (Banco de Preguntas) también era `require_docente` únicamente — el
  Administrador no podía ni siquiera poblar el selector de Materia de esta misma pantalla.
  Detectado al verificar en navegador real contra el backend real (403 en consola). Ampliado
  con el mismo patrón: `require_docente_o_administrador` nuevo en
  `src/banco_preguntas/frameworks/dependencies.py`, aplicado solo a `GET /materias`
  (`POST /materias` sigue exclusivo de Docente)

**Estado:** ✅ COMPLETADO — 8/8 tareas, verificado end-to-end en navegador real (login
Administrador, selector de Materia, tabla de Comisiones con Docente asignado y conteo de
Estudiantes correctos).

## Métricas de Tiempo (`tracker_cli.py status`)

Tiempo real acumulado: ~25 min efectivos hasta el cierre de Fase 7 — sin estimación previa
por fase (US-ADJ, no sigue el desglose de estimación humana de `PRIN-001`).

## Lecciones Aprendidas

- 💡 La verificación manual en navegador real (Fase 3) detectó un segundo endpoint
  (`GET /materias` de Banco de Preguntas) con el mismo problema de guard de rol que el plan
  original no había cubierto — ningún test automatizado lo habría atrapado porque no existía
  ningún test que ejercitara "Administrador ve el selector de Materia" antes de esta US.
- ✅ Reutilizar `listarMaterias()`/`listarCuentas({rol:"docente"})` ya existentes evitó
  duplicar clientes API — el único archivo nuevo de frontend fue el propio de Comisiones.
