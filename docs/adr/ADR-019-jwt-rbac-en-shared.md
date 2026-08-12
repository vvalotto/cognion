# ADR-019 — JWT y RBAC movidos de `src/identidad` a `src/shared` (vs. import directo entre BC)

**Estado:** Aceptado
**Fecha:** 2026-08-02

---

## Contexto

`US-2.1.1` (BC Banco de Preguntas) es la primera US fuera de `src/identidad` cuya spec exige
"Actor autenticado con JWT válido y claim `rol = docente`" en un endpoint. Hasta esa US,
`TipoPerfil`, `JWT`/`JWTPayload`, `JWTIssuerPort`, `PyJWTIssuer`, `get_current_user` y
`require_rol` vivían exclusivamente en `src/identidad` (entities, ports, frameworks e
interface_adapters). Importarlos directo desde `banco_preguntas` hubiera violado la regla de
`CLAUDE.md` ("nunca imports directos entre BC — solo por puertos en `entities/ports/`").

`CLAUDE.md` reconoce `shared/entities/` como única excepción transversal, y `ADR-017` ya la
extendió en la práctica a `shared/frameworks/` para el engine/sesión de SQLAlchemy. Esta ADR
extiende el mismo criterio a `shared/entities/ports/`, `shared/frameworks/security/` y
`shared/interface_adapters/security/`.

## Opciones Consideradas

- **Import directo desde `identidad`** (`banco_preguntas` importa
  `identidad.frameworks.dependencies.require_docente`) — descartada: viola la regla de
  `CLAUDE.md` de forma explícita y crea acoplamiento estructural entre BC por un concern que no
  es de negocio de Identidad.
- **Duplicar el guard en cada BC** (cada BC arma su propio `TipoPerfil`/`JWTIssuerPort`) —
  descartada: el rol de un usuario y la validez de su JWT son un único concepto en todo el
  sistema: duplicarlo arriesga que diverjan (ej. un BC valida un rol que en otro ya no existe).
- **Mover a `src/shared`** — elegida.

## Decisión

- `TipoPerfil` (antes en `identidad/entities/usuario.py`) → `shared/entities/tipo_perfil.py`.
- `JWT`, `JWTPayload` (antes `identidad/entities/jwt.py`) → `shared/entities/jwt.py`.
- `JWTInvalido`, `JWTExpirado` (antes en `identidad/entities/errors.py`) →
  `shared/entities/errors.py`.
- `JWTIssuerPort` (antes `identidad/entities/ports/jwt_issuer_port.py`) →
  `shared/entities/ports/jwt_issuer_port.py`.
- `PyJWTIssuer` (antes `identidad/frameworks/security/jwt_pyjwt.py`) →
  `shared/frameworks/security/jwt_pyjwt.py`.
- `build_get_current_user`, `require_rol` (antes `identidad/interface_adapters/security/`) →
  `shared/interface_adapters/security/`.

Cada BC sigue armando su propio composition root: `identidad/frameworks/dependencies.py` y
`banco_preguntas/frameworks/dependencies.py` importan estas piezas desde `shared` y componen
su propio `require_docente`/`require_administrador` localmente. Ningún BC importa de otro BC —
todos importan de `shared`.

## Justificación

El rol de un usuario (`TipoPerfil`) y la verificación de su JWT no son lógica de negocio de
Identidad — son infraestructura de seguridad transversal que cualquier BC necesita para proteger
sus propios endpoints, igual que el engine de base de datos (`ADR-017`) es infraestructura
transversal y no lógica de negocio de ningún BC en particular.

## Impacto en Configuración

- `shared/entities/tipo_perfil.py`, `jwt.py`, `errors.py`, `ports/jwt_issuer_port.py` — nuevos.
- `shared/frameworks/security/jwt_pyjwt.py` — nuevo.
- `shared/interface_adapters/security/get_current_user.py`, `require_rol.py` — nuevos;
  `shared/interface_adapters/` es una capa nueva en `shared/` (antes solo tenía
  `entities/`+`frameworks/`, ver `ADR-017`).
- `identidad/frameworks/dependencies.py` — reconstruye `get_current_user`/
  `require_administrador`/`require_docente` importando de `shared`, misma API pública.
- `banco_preguntas/frameworks/dependencies.py` — arma su propio `require_docente` con el mismo
  patrón, sin import cruzado a `identidad`.
- Los 5 archivos originales en `src/identidad` se eliminaron (movidos, no duplicados).

## Consecuencias

- ✅ Ningún BC importa directamente a otro — la regla de `CLAUDE.md` se mantiene intacta.
- ✅ Un único punto de verdad para el rol de un usuario y la validación de su JWT en todo el
  sistema.
- ✅ Cada BC sigue controlando su propia política de acceso (qué roles exige cada endpoint) sin
  depender del composition root de otro BC.
- ⚠️ `shared/interface_adapters/` es una capa nueva no prevista literalmente en `CLAUDE.md` (que
  solo menciona `shared/entities/`) — mismo tipo de excepción documentada ya en `ADR-017` para
  `shared/frameworks/`. Actualizar `CLAUDE.md` §"Arquitectura interna" para reflejar que
  `shared/` puede tener las 4 capas cuando el contenido es genuinamente transversal (sin lógica
  de negocio de un BC específico), no solo `entities/`.
