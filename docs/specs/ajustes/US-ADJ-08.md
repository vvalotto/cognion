# US-ADJ-08: Mostrar la comisión de destino antes de completar el registro

**Estado**: `Especificada`
**Iteracion / Sprint**: `SP-ADJ-01` (misma iteración de ajuste que `US-ADJ-01`/`03`/`04`/`05`/`06`/`07`)
**Tipo**: `feature backend + frontend`
**Agregado principal afectado**: — (consulta de solo lectura, sin cambios de Aggregate)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Estudiante que abre un link de invitación**,
quiero **ver a qué materia/comisión me voy a unir antes de completar el formulario de
registro**
para **confirmar que el link es el correcto antes de crear mi cuenta**.

---

## Contexto del dominio

### Problema

Detectado en UAT/UX en vivo (2026-08-23) comparando `Registro.tsx` contra el prototipo
aprobado (`identidad-registro-login.html`, pantalla "2. Registro (link válido)"): el
prototipo muestra un chip informativo antes del formulario — "● Te vas a unir a Ingeniería
de Software — Comisión A" — que la pantalla real no tiene.

Causa raíz: `POST /identidad/registro` (`US-1.1.8`) valida el token y crea la cuenta en la
misma operación — no existe ningún endpoint de solo lectura que permita al frontend
pre-consultar los datos de la invitación (materia, comisión) antes de que el Estudiante
complete y envíe el formulario. `Registro.tsx` no tiene forma de obtener esos datos hoy.

### Modelo involucrado

Sin cambios de invariantes de dominio — consulta de solo lectura sobre una `Invitacion`
vigente, expuesta antes del comando `Registrar`.

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint nuevo | `GET /identidad/invitaciones/{token}` | Devuelve materia/comisión de una invitación vigente, sin consumirla ni validar datos de registro — 404/422 si el token no existe o venció (mismo criterio sin distinguir causa que `US-1.1.8`) |
| Query nueva | `ObtenerInvitacionPorTokenUseCase` (o similar) | Resuelve `Invitacion.comision_id` → nombre de materia (mismo puerto cross-BC que ya usa `RegistrarEstudianteUseCase`) |

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — nuevo endpoint público (sin autenticación, como el propio registro) que expone
  datos de una invitación por token; evaluar que no filtre información sensible más allá de
  materia/comisión (no exponer `docente_id`, email destinatario, etc.).
- [ ] No es un cambio de contrato hacia otros BCs — reutiliza la misma resolución cross-BC
  (`MateriaPort`) que ya usa el flujo de registro actual.

**Capa(s) afectadas:**
- Backend — nuevo endpoint de solo lectura en `identidad/frameworks/api/`, use case nuevo o
  extensión del existente, controller.
- Frontend — `frontend/src/pages/Registro.tsx` (fetch al montar con el `token` de la URL,
  chip `.comision-tag` del prototipo, estado de carga/error si el token ya es inválido antes
  de completar el formulario — coordinar con el manejo de error que ya tiene el submit).

**Nota de diseño:** el prototipo etiqueta la comisión como "Comisión A" (letra) — ese
identificador no existe en el dominio real (`Comisión` se identifica por `materia_id` +
`horario`, sin letra). La implementación deberá decidir qué mostrar en su lugar (ej. el
`horario`, o solo el nombre de la materia) — no inventar un dato que no existe.

---

## Fuente de verdad UX

`docs/design/ux/prototipos/identidad-registro-login.html`, pantalla "2. Registro (link
válido)" — bloque `.comision-tag`: "● Te vas a unir a **{materia} — {comisión}**".

---

## Referencias

- Relacionada con: `US-1.1.8` (`POST /identidad/registro`, flujo que esta US complementa sin
  modificar)
- Candidatas: sin incremento asignado — hallazgo de UAT/UX en vivo 2026-08-23; toca `src/`,
  requiere track formal según `CLAUDE.md` §"Clasificación de hallazgos en UAT"

---

*Basado en el template de `docs/specs/ajustes/US-ADJ-06.md`. US de ajuste (`SP-ADJ-01`,
`docs/plans/PLAN-CM.md` §12) — sin Issue de GitHub ni branch hasta que se decida el incremento
de implementación.*
