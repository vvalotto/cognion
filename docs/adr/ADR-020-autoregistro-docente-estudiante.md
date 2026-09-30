# ADR-020 — Autoregistro de Docente y Estudiante como tercera vía de alta de cuenta (RF-25)

**Estado:** Aceptado
**Fecha:** 2026-09-16

---

## Contexto

El sistema tenía, hasta el Incremento 5-ADJ, dos vías de alta de cuenta: registro de
Estudiante por invitación de una Comisión puntual (`RF-01`, `ADR-012`) y alta directa por el
Administrador para cualquier rol (`RF-03`, `US-1.1.0`/`US-1.1.9`). Víctor relevó
(`hallazgos-cognion.md`, 2026-09-12) que ninguna de las dos cubre el caso de alguien que
quiere sumarse al sistema por su cuenta, sin depender de que el docente genere un link o el
administrador cree la cuenta a mano — friccción real detectada en uso propio del sistema
(docente único, 30-60 alumnos por comisión, sin equipo de soporte que gestione altas). Esta
decisión determina si el autoregistro es una tercera vía independiente o una variante de una
de las dos existentes, y qué nivel de confianza/verificación exige.

## Opciones Consideradas

- **Extender la invitación existente** para que el link sea "abierto" (sin comisión
  predeterminada) — descartada: la invitación es intrínsecamente por Comisión (`ADR-012`,
  `Invitación.comision_id`); forzarla a cubrir también el caso sin comisión previa mezclaría
  dos conceptos de dominio distintos en un mismo aggregate.
- **Autoregistro con aprobación posterior del Administrador** (cuenta creada en estado
  "pendiente", activada recién cuando el Administrador la revisa) — descartada: agrega un
  paso manual que el propio problema (fricción de alta) buscaba eliminar, y no hay volumen
  (30-60 alumnos) que justifique un flujo de moderación.
- **Autoregistro con verificación de email** (link de confirmación antes de activar la
  cuenta) — descartada por ahora: duplicaría la infraestructura de token/expiración que ya
  existe para `Invitación` y para `TokenRecuperacionPassword` (RF-24) sin un requisito de
  seguridad que lo justifique a esta escala; **revisar si el sistema crece más allá del
  entorno controlado actual**.
- **Autoregistro activo de inmediato, sin aprobación ni verificación, como tercera vía
  independiente que convive con las otras dos** — elegida.
- **Un único comando de autoregistro parametrizado por `perfil`** (mismo patrón que
  `CrearUsuario`, que ya es parametrizado porque el actor —Administrador— está autenticado y
  autorizado para cualquier perfil) — descartada: cada perfil autoregistrado tiene su propia
  precondición de datos (`Estudiante` exige `comision_id`, `Docente` no admite ninguno);
  separar el comando (`AutoregistrarDocente`/`AutoregistrarEstudiante`) evita un parámetro
  condicional y dos ramas de validación dentro de un único handler sin actor autenticado que
  ya haya elegido el perfil de antemano.
- **Autoregistro admite perfil Administrador** — descartada: un segundo Administrador
  autocreado sin ningún control es un riesgo de seguridad que ninguna decisión de producto
  pidió resolver; el bootstrap del primer Administrador ya tiene su propio mecanismo
  (`ADR-016`).

## Decisión

Cualquier persona sin autenticar puede crear su propia cuenta de Docente o Estudiante
(`AutoregistrarDocente`/`AutoregistrarEstudiante`, `docs/design/domain/BC-identidad-modelo.md`
§13.2), quedando activa de inmediato sin aprobación del Administrador ni verificación de
email. El Estudiante que se autoregistra debe elegir su Comisión de una lista pública
(`comision_id` obligatorio, validado contra `Comisión` existente). El autoregistro **convive**
con la invitación (`RF-01`) y el alta directa por Administrador (`RF-03`) — no las reemplaza;
son tres vías de alta de cuenta independientes. El autoregistro no admite el perfil
Administrador.

## Justificación

El mismo criterio de confianza que ya rige el resto del sistema (docente único, entorno
controlado, sin equipo de soporte) hace que un paso de aprobación o verificación de email sea
fricción sin beneficio de seguridad proporcional a esta escala — el costo de una cuenta
autoregistrada indebidamente (un Estudiante que se anota en la Comisión equivocada, por
ejemplo) es bajo y corregible por el propio Administrador con las herramientas de gestión de
cuentas ya existentes (`RF-03`). Mantener las tres vías independientes en vez de fusionarlas
evita forzar un modelo de datos común (`Invitación` con o sin `comision_id`, alta directa con
o sin autenticación previa) sobre casos de uso con actores y precondiciones genuinamente
distintos.

## Impacto en Configuración

Sin impacto de stack/librería/herramienta — decisión puramente de dominio. Artefactos de
código afectados (ya implementados, `US-ADJ-41`/`US-ADJ-42`/`US-ADJ-43`):
- `src/identidad/entities/` — comandos `AutoregistrarDocente`/`AutoregistrarEstudiante`,
  evento `UsuarioAutoregistrado`, invariantes `INV-ID-14`/`INV-ID-15`/`INV-ID-16`.
- `src/identidad/interface_adapters/` — endpoints públicos (sin autenticar)
  `POST /identidad/autoregistro/docente` y `POST /identidad/autoregistro/estudiante`.
- `frontend/src/pages/` — pantalla de autoregistro con selección de perfil.

## Consecuencias

- ✅ Elimina la fricción de alta detectada en uso real, sin depender del docente ni del
  administrador para sumar una cuenta nueva.
- ✅ No introduce un modelo de datos híbrido — cada vía de alta conserva su propia forma
  (`Invitación`, alta directa, autoregistro), más simple de razonar que una unificación
  forzada.
- ⚠️ Sin verificación de email, un Docente o Estudiante puede autoregistrarse con un email que
  no controla — aceptado como trade-off consciente a la escala actual (entorno controlado);
  revisar si el sistema se abre a un contexto donde eso sea explotable.
- ⚠️ Sin aprobación, el Administrador se entera de una cuenta autoregistrada recién al verla
  en el listado de cuentas (`RF-03`), no en el momento del alta — mismo criterio que ya acepta
  el registro por invitación (RF-01), que tampoco notifica al Administrador.
