# US-ADJ-07: Mostrar la comisión de una cuenta de Estudiante con un nombre legible

**Estado**: `Especificada`
**Iteracion / Sprint**: `SP-ADJ-01` (misma iteración de ajuste que `US-ADJ-01`/`03`/`04`/`05`/`06`)
**Tipo**: `feature backend + frontend`
**Agregado principal afectado**: — (consulta de solo lectura, sin cambios de Aggregate)
**Bounded Context**: Identidad (consulta cruzada de solo lectura hacia Banco de Preguntas, vía
puerto — mismo patrón que `Comisión.materia_id` resuelto en `US-2.1.2`)

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **ver el nombre legible de la comisión de una cuenta de Estudiante en su Detalle** (ej.
"Ingeniería de Software — Com. A")
para **identificar la comisión sin tener que buscar el UUID en la base de datos**.

---

## Contexto del dominio

### Problema

Encontrado leyendo código durante UAT/UX en vivo (2026-08-23) — no reproducible en el entorno
de prueba actual porque no hay ninguna cuenta de perfil Estudiante en la base. `CuentaDetalle
.tsx` (`US-2.2.7`) renderiza `cuenta.comisionId` tal cual llega de
`GET /usuarios/{id}` (`US-2.2.3`) — un UUID crudo, no un nombre. El prototipo
(`identidad-cuentas-administracion.html`, pantalla `#cuenta-detalle`) muestra "Ingeniería de
Software — Com. A".

Causa raíz: `ObtenerCuentaUseCase` (`src/identidad/use_cases/obtener_cuenta.py`) solo consulta
`UsuarioRepositoryPort`, sin resolver `comision_id` contra ninguna otra fuente. Y no hay forma
de resolverlo del lado del cliente tampoco — no existe `GET /comisiones/{id}` (solo
`POST /comisiones` y `POST /comisiones/{id}/docentes`, ver `comisiones_router.py`).

### Modelo involucrado

Mismo patrón que `US-2.1.2` (`Comisión.materia_id` resuelto contra `MateriaPort`, sin imports
directos entre BCs): agregar un puerto de solo lectura que permita a Identidad resolver
`comision_id` → una etiqueta legible, sin acoplarse directamente al modelo interno de
`Comisión`/`Materia` del BC Banco de Preguntas.

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Puerto nuevo (o extensión) | `ComisionPort` (o extender el existente si ya hay uno de `US-2.1.2`) | Resolver `comision_id` → etiqueta legible ("{materia} — Com. {letra/número}") |
| Extendido | `ObtenerCuentaUseCase` | Resuelve la etiqueta antes de devolver el detalle, si `perfil == estudiante` |

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — cómo resolver el nombre de la comisión sin acoplar Identidad al modelo interno de
  Comisión/Materia. Evaluar si reutiliza el puerto ya creado por `US-2.1.2` o si hace falta uno
  nuevo específico de lectura (`ComisionQueryPort`), mismo criterio command/query que
  `US-2.2.2` (`CuentaQueryPort`).

**Capa(s) afectadas:**
- [x] Backend — `entities/ports/` (puerto nuevo o extendido), `use_cases/obtener_cuenta.py`,
  posible endpoint `GET /comisiones/{id}` si se decide resolverlo del lado del cliente en vez
  del servidor.
- [x] Frontend — `frontend/src/pages/CuentaDetalle.tsx` (deja de mostrar el UUID crudo una vez
  que el backend devuelva la etiqueta).

---

## Fuente de verdad UX

`docs/design/ux/prototipos/identidad-cuentas-administracion.html`, pantalla `#cuenta-detalle`
— fila "Comisión": "Ingeniería de Software — Com. A".

---

## Referencias

- Relacionada con: `US-2.1.2` (mismo patrón de resolución cross-BC por puerto, sin imports
  directos), `US-2.2.3` (`GET /usuarios/{id}`, endpoint que esta US extiende), `US-2.2.7`
  (`CuentaDetalle.tsx`, pantalla que esta US corrige)
- Candidatas: sin incremento asignado — hallazgo de UAT/UX en vivo 2026-08-23, no implementada
  ni reproducida en vivo (no hay cuenta Estudiante en la base de prueba actual); toca `src/`,
  requiere track formal según `CLAUDE.md` §"Clasificación de hallazgos en UAT"

---

*Basado en el template de `docs/specs/ajustes/US-ADJ-01.md`. US de ajuste (`SP-ADJ-01`,
`docs/plans/PLAN-CM.md` §12) — sin Issue de GitHub ni branch hasta que se decida el incremento
de implementación.*
