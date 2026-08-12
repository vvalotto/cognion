# Plan de Implementación: US-2.1.1 - Docente da de alta una materia y su banco de preguntas

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion

---

## 0. Refactor previo — extraer JWT/RBAC a `src/shared/`

**Por qué:** la spec exige "Actor autenticado con JWT válido y claim `rol = docente`" en el
endpoint de `banco_preguntas`, pero hoy `TipoPerfil`, `JWT`/`JWTPayload`, `JWTIssuerPort`,
`PyJWTIssuer`, `get_current_user` y `require_rol` viven exclusivamente en `src/identidad`.
Importarlos directo desde `banco_preguntas` violaría la regla de `CLAUDE.md` ("nunca imports
directos entre BCs"). Decisión confirmada con Víctor: mover estas piezas a `shared/` como
infraestructura transversal, ya que el rol de un usuario y la verificación de su JWT no son
lógica de negocio de Identidad — son un cross-cutting concern que todo BC necesita.

**Diseño de la composición resultante:** cada BC arma su propio `require_docente` (etc.) en su
`frameworks/dependencies.py`, componiendo `build_get_current_user` + `require_rol` +
`PyJWTIssuer`, todos importados desde `shared`. Ningún BC importa directamente de otro —
`identidad/frameworks/dependencies.py` sigue exponiendo `require_administrador`/
`require_docente` con la misma firma que hoy (sin romper nada que ya los use), pero construidos
sobre `shared`.

- [x] `src/shared/entities/tipo_perfil.py`
  - `TipoPerfil(StrEnum)` — movido desde `src/identidad/entities/usuario.py`
- [x] `src/shared/entities/jwt.py`
  - `JWT`, `JWTPayload` — movidos desde `src/identidad/entities/jwt.py`, referencian `TipoPerfil` de `shared`
- [x] `src/shared/entities/errors.py` (nuevo)
  - `JWTInvalido`, `JWTExpirado` — movidos desde `src/identidad/entities/errors.py`
- [x] `src/shared/entities/ports/__init__.py`, `src/shared/entities/ports/jwt_issuer_port.py`
  - `JWTIssuerPort` — movido desde `src/identidad/entities/ports/jwt_issuer_port.py`
- [x] `src/shared/frameworks/security/__init__.py`, `src/shared/frameworks/security/jwt_pyjwt.py`
  - `PyJWTIssuer` — movido desde `src/identidad/frameworks/security/jwt_pyjwt.py`
- [x] `src/shared/interface_adapters/__init__.py`, `src/shared/interface_adapters/security/__init__.py`
  - `src/shared/interface_adapters/security/get_current_user.py` — `build_get_current_user`, movido
  - `src/shared/interface_adapters/security/require_rol.py` — `require_rol`, movido
- [x] Actualizar `src/identidad/entities/usuario.py`, `eventos.py`, `errors.py` (quitar lo movido, importar `TipoPerfil` desde `shared`)
- [x] Actualizar `src/identidad/frameworks/dependencies.py` para importar desde `shared` y reconstruir `get_current_user`/`require_administrador`/`require_docente` igual que hoy (misma API pública, mismo comportamiento)
- [x] Eliminar los archivos originales movidos (`identidad/entities/jwt.py`, `identidad/entities/ports/jwt_issuer_port.py`, `identidad/frameworks/security/jwt_pyjwt.py`, `identidad/interface_adapters/security/get_current_user.py`, `identidad/interface_adapters/security/require_rol.py`)
- [x] Actualizar todos los imports de `TipoPerfil`/`JWT`/`JWTPayload`/`JWTIssuerPort` en `src/identidad/**` y `tests/**` (unit, integration, step_defs — ~20 archivos, ver `grep -rl TipoPerfil`) para apuntar a `shared`
- [x] Correr la suite completa de tests de Identidad (`pytest tests/unit/inc1 tests/integration/inc1 tests/step_defs/inc1`) y confirmar que sigue en verde tras el refactor, antes de tocar nada de `banco_preguntas` — **131/131 passed**

---

## 1. Entities — BC Banco de Preguntas

- [x] `src/banco_preguntas/entities/materia.py`
  - `Materia` (dataclass): `id`, `nombre` — factory `Materia.crear(nombre)`
- [x] `src/banco_preguntas/entities/banco.py`
  - `Banco` (dataclass): `id`, `materia_id` — factory `Banco.crear(materia_id)`
- [x] `src/banco_preguntas/entities/eventos.py`
  - `MateriaCreada(materia_id, nombre, ocurrido_en)`, `BancoCreado(banco_id, materia_id, ocurrido_en)`
- [x] `src/banco_preguntas/entities/errors.py`
  - `MateriaYaExiste(nombre)` (INV-BP-00)
- [x] `src/banco_preguntas/entities/ports/__init__.py`
- [x] `src/banco_preguntas/entities/ports/materia_repository_port.py`
  - `MateriaRepositoryPort`: `guardar`, `obtener_por_nombre`
- [x] `src/banco_preguntas/entities/ports/banco_repository_port.py`
  - `BancoRepositoryPort`: `guardar`

## 2. Use Cases

- [x] `src/banco_preguntas/use_cases/crear_materia.py`
  - `CrearMateriaUseCase.execute(nombre)`: valida INV-BP-00 vía `MateriaRepositoryPort.obtener_por_nombre`, crea `Materia` + `Banco` y persiste ambos en la misma operación, devuelve `(Materia, Banco, MateriaCreada, BancoCreado)`

## 3. Interface Adapters

- [x] `src/banco_preguntas/interface_adapters/controllers/materias_controller.py`
  - `MateriasController.crear_materia(nombre)` — delega en `CrearMateriaUseCase`
- [x] `src/banco_preguntas/interface_adapters/gateways/materia_repository.py`
  - `SQLAlchemyMateriaRepository` — implementa `MateriaRepositoryPort`
- [x] `src/banco_preguntas/interface_adapters/gateways/banco_repository.py`
  - `SQLAlchemyBancoRepository` — implementa `BancoRepositoryPort`

## 4. Frameworks

- [x] `src/banco_preguntas/frameworks/db/__init__.py`, `src/banco_preguntas/frameworks/db/models.py`
  - `MateriaModel` (tabla `materia`, `nombre` unique), `BancoModel` (tabla `banco`, `materia_id` FK unique)
- [x] `migrations/versions/<hash>_materia_banco.py`
  - Migración Alembic: tablas `materia`, `banco`
- [x] `src/banco_preguntas/frameworks/api/__init__.py`, `src/banco_preguntas/frameworks/api/schemas.py`
  - `CrearMateriaRequest` (`nombre: str`, `min_length=1`), `MateriaResponse` (`id`, `nombre`, `banco_id`)
- [x] `src/banco_preguntas/frameworks/api/materias_router.py`
  - `POST /materias` — requiere `require_docente`, 201 con `MateriaResponse`; 409 si `MateriaYaExiste`; 422 si `nombre` vacío (validación Pydantic)
- [x] `src/banco_preguntas/frameworks/dependencies.py`
  - `get_materias_controller(session)`; `require_docente` propio, compuesto desde `shared` (ver Tarea 0)

## 5. Integración

- [x] `src/app.py`: registrar `materias_router` de `banco_preguntas`

**Estado:** ✅ COMPLETADO — 24/24 tareas
**Fecha completado:** 2026-08-02

## Métricas de Tiempo (tracking real, `.claude/tracking/US-2.1.1-tracking.json`)

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 14 min |
| 1 — Escenarios BDD | 1 min |
| 2 — Plan de Implementación | 6 min |
| 3 — Implementación | 11 min |
| 4 — Tests Unitarios | 2 min |
| 5 — Tests de Integración | 1 min |
| 6 — Validación BDD | 2 min |
| 7 — Quality Gates | 6 min |
| **Total** | **~43 min** |

> Nota PRIN-001: son tiempos reales de ejecución del agente, no comparables contra estimación humana.

## Lecciones Aprendidas

- ⚠️ La spec no anticipaba que el guard de rol (`require_docente`) no existía fuera de
  `identidad` — surgió como ambigüedad de diseño genuina en Fase 2, resuelta con Víctor antes
  de tocar código (Tarea 0, `ADR-019`). Quedó como precedente: toda US que sea la "primera" en
  cruzar un concern transversal entre BCs debe revisar si ese concern ya está en `shared/`
  antes de plantear el plan.
- ✅ Tener `ADR-017` como precedente directo (mismo patrón: mover infraestructura transversal a
  `shared/frameworks/`) aceleró la decisión — se pudo aplicar el mismo criterio sin abrir un
  debate de diseño desde cero.
- 💡 Migración Alembic generada con `--autogenerate` en vez de escrita a mano evitó errores de
  transcripción del modelo ORM a SQL.
