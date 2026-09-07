# US-ADJ-23: Administrador ve el listado de Comisiones de una Materia

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 4-ADJ — Portal de Entrada y Validación E2E`, Iteración 1a
**Tipo**: `feature` (backend + frontend)
**Agregado principal afectado**: `Comisión` (lectura, sin cambio de invariantes)
**Bounded Context**: Identidad
**Origen**: `docs/aprendizajes/HITO-9-PORTAL-DE-ENTRADA-SIN-DUENO-DE-PRODUCTO.md` — no existe
ninguna pantalla para que el Administrador vea o gestione Comisiones. Precondición de
`US-ADJ-24`/`25`/`26` (crear Comisión, asignar Docente, generar invitación).

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **ver el listado de Comisiones de una Materia elegida, con su horario, los Docentes
asignados y la cantidad de Estudiantes inscriptos**
para **poder gestionar Comisiones (crear una nueva, asignar Docente) y verificar el estado de
alta de Estudiantes de una Materia sin depender de consultas manuales en la base de datos**.

---

## Contexto del dominio

### Problema

`GET /materias/{id}/comisiones` (`US-4.2.2`) y `GET /comisiones/{id}/estudiantes` (`US-4.2.2`)
existen desde el Incremento 4, pero **exigen rol `docente` únicamente** (`require_docente`) —
se construyeron para el selector en cascada de Analytics (`Desempeño por alumno`), donde el
actor siempre es un Docente. El Administrador no tiene forma de consultar Comisiones desde la
UI.

Además, `SQLAlchemyComisionQueryRepository.listar_comisiones_por_materia` devuelve
`docentes_asignados=[]` **siempre**, de forma deliberada:

```python
# src/identidad/interface_adapters/gateways/comision_query_repository.py
"""Lista las comisiones de una materia. Materia sin comisiones → lista vacía.

No carga los docentes asignados (`docentes_asignados=[]`) — esta consulta solo se
usa para poblar el selector de comisiones (id, horario), sin necesitar ese dato.
"""
```

Esa decisión fue correcta para su único consumidor de entonces (un selector que solo necesita
`id`/`horario`), pero esta US sí necesita el dato real — la tabla del Administrador debe
mostrar qué Docente(s) tiene asignado cada Comisión, o que no tiene ninguno.

`ComisionModel.docentes` (relación `many-to-many` vía `comision_docentes`) ya persiste esa
información — el gateway simplemente no la carga.

### Alcance del fix

1. **Backend — ampliar el guard de rol** de los dos endpoints de consulta
   (`materias_comisiones_router.py`, `comisiones_router.py`) de `require_docente` a un nuevo
   `require_docente_o_administrador` (`require_rol([TipoPerfil.DOCENTE,
   TipoPerfil.ADMINISTRADOR], get_current_user)`, mismo patrón que las 3 dependencies ya
   existentes en `dependencies.py:171-177`).
2. **Backend — cargar `docentes_asignados` real** en
   `SQLAlchemyComisionQueryRepository.listar_comisiones_por_materia`: mapear
   `[d.id for d in modelo.docentes]` en vez de `[]`. `Comision.docentes_asignados` ya es
   `list[UUID]` en la entidad (`entities/comision.py:16`) — el cambio es solo en el gateway.
3. **Backend — exponer `docentes_asignados`** en `ComisionResumenResponse`
   (`frameworks/api/schemas.py:91-96`), hoy solo `id`/`horario`.
4. **Frontend — pantalla nueva** `/comisiones` (Administrador): selector de Materia
   (`GET /materias`, ya existente) → tabla con horario, Docentes asignados (nombres,
   resueltos cruzando `docentes_asignados` contra `GET /usuarios?rol=docente`, `US-2.2.2`) o
   badge "Sin docente asignado", y cantidad de Estudiantes (`GET /comisiones/{id}/estudiantes`
   por cada Comisión listada, `.length` — aceptable a esta escala, pocas Comisiones por
   Materia, mismo criterio de simplicidad que `US-3.2.4`).

**Fuera de alcance de esta US:**
- Crear Comisión (`US-ADJ-24`), asignar Docente (`US-ADJ-25`), generar invitación
  (`US-ADJ-26`) — pantallas separadas, esta US es de solo lectura.
- Cambiar el comportamiento del selector de Analytics que ya consume estos endpoints
  (`US-4.2.2`, `US-4.2.5`) — sigue funcionando igual, `docentes_asignados` es un campo nuevo
  que antes no se leía ahí, no rompe ningún consumidor existente.
- Endpoint dedicado de conteo de Estudiantes por Comisión — se resuelve componiendo el
  endpoint ya existente, no se agrega uno nuevo.

---

## Especificacion del comportamiento

### Precondicion

- Al menos una Materia existe (`GET /materias`, `US-2.1.9`).
- `GET /materias/{id}/comisiones` y `GET /comisiones/{id}/estudiantes` solo aceptan rol
  `docente`.
- `docentes_asignados` de `ComisionResumenResponse` no existe como campo.

### Postcondicion

- Un Administrador autenticado puede elegir una Materia y ver la tabla de sus Comisiones, con
  horario, Docentes asignados por nombre (o "Sin docente asignado") y cantidad de Estudiantes.
- Un Docente autenticado sigue pudiendo usar los mismos endpoints sin cambio de comportamiento
  (regresión: `US-4.2.2`/`US-4.2.5` en verde).
- Un Estudiante autenticado sigue recibiendo 403 en ambos endpoints (sin cambio).

### Invariantes

Ninguna nueva — `Comisión` no cambia sus invariantes de escritura (`INV-ID-*`), esta US es de
lectura.

---

## Criterios de aceptacion

```gherkin
Feature: Administrador ve el listado de Comisiones de una Materia (US-ADJ-23)

  Scenario: Administrador ve las Comisiones de una Materia con Docente asignado
    Given una Materia con una Comisión que tiene un Docente asignado y 3 Estudiantes inscriptos
    When el Administrador consulta las Comisiones de esa Materia
    Then ve la Comisión con su horario, el nombre del Docente asignado y "3" estudiantes

  Scenario: Administrador ve una Comisión sin Docente asignado
    Given una Materia con una Comisión sin ningún Docente asignado
    When el Administrador consulta las Comisiones de esa Materia
    Then ve la Comisión con el badge "Sin docente asignado"

  Scenario: Materia sin Comisiones
    Given una Materia sin ninguna Comisión
    When el Administrador la consulta
    Then ve el estado vacío con la acción "+ Nueva Comisión"

  Scenario: Docente sigue teniendo acceso (regresión)
    Given un Docente autenticado
    When consulta GET /materias/{id}/comisiones o GET /comisiones/{id}/estudiantes
    Then recibe 200, mismo comportamiento que antes de esta US

  Scenario: Estudiante sigue sin acceso
    Given un Estudiante autenticado
    When consulta GET /materias/{id}/comisiones
    Then recibe 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — amplía un guard de rol ya existente (`require_rol` acepta una lista, patrón ya
  usado) y corrige un gateway para dejar de descartar un dato que la entidad ya modela.

**Capa(s) afectadas:**
- [x] Backend — `entities` (ninguna, sin cambios), `interface_adapters/gateways` (gateway de
  query), `frameworks` (dependency de rol, schema, 2 routers)
- [x] Frontend — pantalla nueva `Comisiones.tsx`

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/frameworks/dependencies.py` | Nueva dependency `require_docente_o_administrador = require_rol([TipoPerfil.DOCENTE, TipoPerfil.ADMINISTRADOR], get_current_user)` |
| `src/identidad/frameworks/api/materias_comisiones_router.py` | `GET /materias/{id}/comisiones` usa `require_docente_o_administrador` |
| `src/identidad/frameworks/api/comisiones_router.py` | `GET /comisiones/{id}/estudiantes` usa `require_docente_o_administrador` |
| `src/identidad/interface_adapters/gateways/comision_query_repository.py` | `listar_comisiones_por_materia` mapea `docentes_asignados` real desde `modelo.docentes` |
| `src/identidad/frameworks/api/schemas.py` | `ComisionResumenResponse` gana `docentes_asignados: list[UUID]` |
| `frontend/src/lib/identidad-comisiones-api.ts` (nuevo) | `listarComisionesPorMateria(materiaId)`, `listarEstudiantesDeComision(comisionId)` — reutiliza `apiFetch` |
| `frontend/src/pages/identidad/Comisiones.tsx` (nuevo) | Pantalla del listado, ruta `/comisiones` (rol `administrador`) |
| `frontend/src/router.tsx` | Ruta `/comisiones` nueva, protegida con `RequireRole rol="administrador"` |

---

## Referencias

- Incremento: 4-ADJ
- `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1a
- `docs/design/ux/wireframes-portal-entrada.md` §3.1
- `docs/design/domain/portal-entrada-modelo.md` §2 (gap real detectado)
- Issue: [#268](https://github.com/vvalotto/cognion/issues/268)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
