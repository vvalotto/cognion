# Plan de Implementación: US-ADJ-43 - Pantallas de autoregistro con selección de perfil

**Patrón:** Clean Architecture BC-first (`entities → use_cases → interface_adapters → frameworks`)
**Producto:** identidad (+ frontend)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-13

## Métricas de Tiempo

Tracking activo (`tracker_cli.py`) — tiempo efectivo acumulado a fases 0-7: 33 min al cierre
de Fase 7. Sin estimaciones previas comparables (perfil `clean-architecture-bc`, PRIN-001 —
los tiempos son referencias de complejidad relativa para esfuerzo humano, no comparables 1:1
con ejecución de agente).

## Lecciones Aprendidas

- ✅ El gap de backend (selector público sin JWT) se detectó en Fase 2, antes de codear —
  evitó descubrirlo a mitad de la implementación del frontend.
- ⚠️ Los escenarios BDD de Fase 1 se redactaron inicialmente como flujo de UI (clics,
  navegación) — no ejecutables con pytest-bdd en este proyecto (sin driver de navegador). Se
  corrigieron en Fase 6 al comportamiento backend testeable, siguiendo el mismo criterio ya
  establecido para US frontend-puro (`US-ADJ-24/27/28/29/30/35/36/37/40`): "No aplica — BDD",
  cubierto por Vitest con el router real. **Ajuste de proceso:** en Fase 0/1, antes de generar
  escenarios BDD para una US que toca `frontend/`, verificar primero si es frontend-puro o
  mixta — si es frontend-puro, no generar `.feature`; si es mixta (como esta), acotar BDD
  solo a la porción de backend testeable desde el inicio, no después de la aprobación.
- 💡 `codeguard`/`pylint` en corrida fría puede fallar (`vulture`/`codespell` no en PATH
  aunque estén instalados en `.venv`; `pylint` timeout >10s en archivos grandes) — reintentar
  con `PATH="$(pwd)/.venv/bin:$PATH"` antepuesto resolvió ambos casos sin cambios de código.

## Gap detectado en Fase 2 (decidido con Víctor antes de codear)

La spec asume que `AutoregistroEstudiante.tsx` puede poblar el selector Materia→Comisión con
`GET /materias` (`US-2.1.9`) y `GET /materias/{id}/comisiones` (`US-4.2.2`) — ambos exigen JWT
de rol `docente`/`administrador` (`require_docente_o_administrador`). Un Estudiante
autoregistrándose no tiene cuenta todavía, no puede tener token.

**Decisión:** dos endpoints públicos nuevos y acotados bajo el mismo prefijo de autoregistro
(`/identidad/autoregistro/materias`, `/identidad/autoregistro/materias/{id}/comisiones`), sin
`Depends(require_...)`, devolviendo solo `id`/`nombre` (materias) e `id`/`horario` (comisiones)
— sin `docentes_asignados` ni ningún otro campo de los endpoints protegidos existentes. No se
tocan `GET /materias` ni `GET /materias/{id}/comisiones` — quedan con su RBAC intacto.

Reutiliza infraestructura ya existente sin puertos nuevos entre BCs:
- `MateriaPort` (`src/identidad/entities/ports/materia_port.py`) ya existe (`obtener()`
  usado por `CrearComisionUseCase`) — se le agrega `listar()`.
- `ComisionQueryPort.listar_comisiones_por_materia()` ya existe (`US-4.2.2`) — se reutiliza
  sin cambios.

## Componentes a Implementar

### 1. Backend — endpoints públicos de consulta para autoregistro (gap de Fase 2)

- [x] `src/identidad/entities/ports/materia_port.py`
  - Agregar método abstracto `listar(self) -> list[MateriaDTO]` a `MateriaPort`
- [x] `src/identidad/frameworks/adapters/materia_port_in_process.py`
  - Implementar `listar()` sobre `MateriaRepositoryPort.listar()` directo (no
    `ListarMateriasUseCase` — ese agrega banco/conteo de preguntas por N+1 queries, datos que
    este consumidor no necesita)
- [x] `src/identidad/frameworks/api/schemas.py`
  - `MateriaAutoregistroResponse(id: UUID, nombre: str)`
  - `ComisionAutoregistroResponse(id: UUID, horario: str)`
- [x] `src/identidad/interface_adapters/controllers/autoregistro_controller.py`
  - `listar_materias() -> list[MateriaDTO]` — pass-through fino sobre `MateriaPort.listar()`,
    mismo criterio sin Use Case dedicado que `ComisionesQueryController.obtener_comision`
    (`US-ADJ-25`)
  - `listar_comisiones_por_materia(materia_id: UUID) -> list[Comision]` — pass-through fino
    sobre `ComisionQueryPort.listar_comisiones_por_materia(materia_id)`
  - Constructor gana `materia_port: MateriaPort` y `comision_query: ComisionQueryPort`
- [x] `src/identidad/frameworks/api/autoregistro_router.py`
  - `GET /identidad/autoregistro/materias` → `list[MateriaAutoregistroResponse]`, sin
    `Depends`, público
  - `GET /identidad/autoregistro/materias/{materia_id}/comisiones` →
    `list[ComisionAutoregistroResponse]`, sin `Depends`, público
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_autoregistro_controller` cablea `MateriaPortInProcess(session)` y
    `SQLAlchemyComisionQueryRepository(session)` (ya se usa en otros controllers)

### 2. Frontend — cliente API

- [x] `frontend/src/lib/identidad-autoregistro-api.ts`
  - `autoregistrarDocente(nombre, email, password): Promise<{id, nombre, email}>` → POST
    `/identidad/autoregistro/docente`
  - `autoregistrarEstudiante(nombre, email, password, comisionId): Promise<{id, nombre, email}>`
    → POST `/identidad/autoregistro/estudiante`
  - `listarMateriasAutoregistro(signal?): Promise<{id, nombre}[]>` → GET
    `/identidad/autoregistro/materias`
  - `listarComisionesAutoregistro(materiaId, signal?): Promise<{id, horario}[]>` → GET
    `/identidad/autoregistro/materias/{id}/comisiones`
  - Mapeo snake_case↔camelCase mismo patrón que `identidad-comisiones-api.ts`

### 3. Frontend — pantallas nuevas (`frontend/src/pages/identidad/`)

- [x] `AutoregistroPerfil.tsx` (`/autoregistro`)
  - Dos `.profile-card` ("Soy Docente" → `/autoregistro/docente`, "Soy Estudiante" →
    `/autoregistro/estudiante`), link "¿Ya tenés cuenta? Iniciar sesión" → `/login`
- [x] `AutoregistroDocente.tsx` (`/autoregistro/docente`)
  - Tag "Perfil: Docente", campos Nombre/Email/`PasswordInput` (mostrarFortaleza)/Confirmar,
    copy "Tu cuenta queda activa de inmediato", submit → `autoregistrarDocente(...)`
  - Éxito → navigate a `/autoregistro/exito`
  - 409 → error inline "Ese email ya está registrado."; 422 → `err.message` inline (password
    insegura, ya viene en lenguaje de negocio desde el backend)
  - Mismo patrón `AbortController` en `useEffect` que `Registro.tsx`/`Login.tsx` (`US-ADJ-20`)
  - Link "‹ Elegir otro perfil" → `/autoregistro`
- [x] `AutoregistroEstudiante.tsx` (`/autoregistro/estudiante`)
  - Al montar: `listarMateriasAutoregistro()` puebla el `<select>` de Materia
  - Al elegir Materia: `listarComisionesAutoregistro(materiaId)` puebla el `<select>` de
    Comisión (deshabilitado/vacío mientras no hay Materia elegida)
  - Orden de campos: Materia → Comisión → Nombre → Email → Contraseña → Confirmar (spec §5.3)
  - Submit → `autoregistrarEstudiante(nombre, email, password, comisionId)`
  - Mismos criterios de error/abort/navegación que `AutoregistroDocente.tsx`
- [x] `AutoregistroExito.tsx` (`/autoregistro/exito`)
  - Pantalla única para ambos perfiles: "Cuenta creada. Tu cuenta ya está activa. Iniciá
    sesión para continuar.", botón "Iniciar sesión" → `/login` (mismo patrón que
    `RegistroExito.tsx`, sin login automático)

### 4. Integración

- [x] `frontend/src/pages/identidad/Login.tsx`
  - Link nuevo "¿No tenés cuenta? Registrate" → `/autoregistro`, mismo patrón visual que
    "¿Olvidaste tu contraseña?" (`US-ADJ-38`)
- [x] `frontend/src/router.tsx`
  - 4 rutas nuevas, públicas, dentro de `AuthLayout` (sin `RequireRole`):
    `/autoregistro`, `/autoregistro/docente`, `/autoregistro/estudiante`,
    `/autoregistro/exito`

**Estado:** 0/15 tareas completadas
