# Changelog

Todos los cambios notables de Cognion se documentan en este archivo.

Formato: [Keep a Changelog](https://keepachangelog.com/es/1.0.0/)
Versionado: [Semantic Versioning](https://semver.org/lang/es/)

---

## [Unreleased]

### Added
- [US-ADJ-16] Subir cobertura de branches del frontend por encima del umbral global (80%)
  - 3 tests nuevos en `NuevaPreguntaTipo.test.tsx` (interacción por teclado — `Enter` sobre
    cada Card de selección de tipo, y una tecla no-`Enter` que no navega) — branches globales
    de 79.66% (517/649) a 80.12% (520/649), cerrando exactamente el gap real medido
  - Sin cambio de comportamiento — solo tests nuevos, ningún test existente modificado

### Fixed
- [US-ADJ-15] Fix de `coverage_report_path` en `[tool.architectanalyst]`
  - `pyproject.toml`: agregado `coverage_report_path = "../coverage.json"` — `CoverageAnalyzer`
    resolvía el reporte relativo a `src/` (el `PATH` posicional del CLI), no a la raíz del
    repo, y nunca encontraba `coverage.json` pese a que `pytest --cov` ya lo generaba
    correctamente
  - `CLAUDE.md`: nota operativa — generar `coverage.json` antes de correr `architectanalyst`
    al cerrar una baseline
  - Verificado con datos reales: `CoverageAnalyzer` pasa de warning a `info` con 98.9% de
    cobertura real (antes: warning vacío en 3 baselines consecutivas)

### Changed
- [US-ADJ-14] Reordenar `frontend/src/pages/` por Bounded Context
  - 33 pantallas movidas de un directorio plano a `pages/{identidad,cuentas,banco-preguntas,
    actividad-evaluativa}/`, igual que la organización ya existente de `frontend/src/lib/` y
    de `src/<bc>/` en el backend — `_placeholders.tsx` queda en la raíz (sigue con un
    consumidor activo)
  - 34 archivos con imports actualizados (`router.tsx`, `Login.tsx`, 32 tests)
  - Refactor mecánico sin cambio de comportamiento: ninguna URL cambió, `vitest run` idéntico
    al baseline (41 archivos / 229 tests), `tsc`/`oxlint` en verde

### Fixed
- [US-ADJ-13] Documentar "Zone of Pain" de ArchitectAnalyst como falso positivo aceptado +
  limpiar claves inválidas de `[tool.architectanalyst]` en `pyproject.toml`
  - `pyproject.toml`: eliminado `paths = ["src"]` (no existe en `ArchitectAnalystConfig`, el
    CLI ya recibe el path por argumento posicional) y renombrado `history_db` → `db_path`
    (campo real, mismo valor) — dejaban de emitir `[tool.architectanalyst] clave desconocida
    ignorada` en cada corrida desde hacía 3 baselines
  - `CLAUDE.md`: nota en Quality gates documentando los 5 críticos "Zone of Pain" de paquete
    raíz de BC (`identidad`, `settings`, `shared`, `banco_preguntas`, `actividad_evaluativa`)
    como falso positivo permanente — causa raíz estructural (cada BC es hoja del grafo de
    dependencias por diseño), no resuelto por `analysis_depth` (probado: sube de 5 a 15
    críticos)
  - Sin cambio de comportamiento — las claves corregidas nunca tuvieron efecto real

## [0.5.0] - 2026-09-02

### Added
- [US-3.4.7] Estudiante finaliza su evaluación y ve la revisión completa, backend + frontend —
  cierra completo el lado Estudiante de la Iteración 4 del Incremento 3
  - Backend: `DetalleCorreccionPregunta` (+`opciones: list[str] | None`, mismo criterio que
    `ContenidoPregunta.opciones`), poblado en `PreguntaConsultaPortInProcess.obtener_detalle_correccion()`
    y propagado por `DetallePreguntaRevision`/`DetallePreguntaRevisionResponse` hasta
    `GET /evaluaciones/{id}/revision`. Gap detectado en Fase 2, resuelto dentro de esta misma
    US (mismo criterio que `US-2.1.9`/`US-2.2.8`/`US-ADJ-10`): sin este campo, el detalle de
    opción múltiple solo traía `{opcion_indice: N}`, sin el texto real de la opción elegida —
    el prototipo aprobado (`#est-revision`) muestra el texto, no el índice
  - Frontend: `RevisionEvaluacion.tsx` (nueva, reemplaza el placeholder de `US-3.4.1` en
    `/mis-actividades/evaluaciones/:evaluacionId/revision`) — resumen + detalle por pregunta,
    resolviendo el texto de la respuesta propia/correcta desde `opciones`/`valor` sin conocer
    el tipo concreto de pregunta. `RendirEvaluacion.tsx`: el botón de la última pregunta pasa
    a "Confirmar y finalizar" y dispara `finalizarEvaluacion` + navegación a la revisión —
    decisión de diseño porque el prototipo no define un botón "Finalizar" separado. 2 variantes
    nuevas en `Badge` (`revision-correcta`/`revision-incorrecta`). `ActividadEvaluativaPlaceholder`
    eliminado de `_placeholders.tsx` (código obsoleto, sin más rutas que lo referencien)
  - 1 test de integración + 3 escenarios BDD nuevos backend (749→752 tests backend con
    regresiones existentes en verde), 5 tests nuevos frontend (226/226 suite completa);
    quality gates APROBADO (pylint 9.59/10, CC máx 7, MI mín 54.63, coverage 99%, codeguard
    9/9 checks full, mypy limpio sobre `src/` completo)
- [US-3.4.6] Estudiante rinde su evaluación — responde, pausa y reanuda, backend + frontend
  - Backend: `PreguntaConsultaPort.obtener_contenido()` (nuevo, texto + opciones sin marcar
    cuál es correcta — `ContenidoPregunta`), implementado en `PreguntaConsultaPortInProcess`;
    `PreguntaAsignadaResponse` (+`enunciado`/`opciones`) y `EvaluacionResponse`
    (+`preguntas_respondidas`) ampliados; `_a_response()` del router pasa a `async` y se
    enriquece vía una dependencia FastAPI nueva y separada (`get_pregunta_consulta_port`),
    no como 6ª dependencia de `EvaluacionesController` — evita repetir el patrón de CRITICAL
    de CBO ya visto varias veces en el proyecto. Desvío documentado respecto de la spec: el
    enriquecimiento vive en el router, no en `IniciarEvaluacionUseCase` (que devuelve la
    entidad de dominio pura, sin conocer texto de preguntas)
  - Frontend: `RendirEvaluacion.tsx` (nueva, reemplaza el placeholder de `US-3.4.1`) y
    `EvaluacionSuspendida.tsx` (nueva, ruta nueva) — reusan íntegro el cliente API existente
    (`iniciarEvaluacion`, `registrarRespuesta`, `suspenderEvaluacion`, `reanudarEvaluacion`),
    sin agregar endpoints. Reconexión idempotente vía `iniciarEvaluacion` en ambas pantallas
  - 7 tests unitarios + 3 integración + 5 BDD nuevos backend, 355+230+71 suites sin
    regresiones; 10 tests nuevos frontend, 221/221 suite completa frontend; quality gates
    APROBADO (pylint 9.97/10, CC máx 5, MI mín 66.68, coverage 99.78%, codeguard 9/9 checks
    full — primera corrida con vulture/codespell realmente en PATH, ver observaciones del
    reporte de calidad)
- [US-3.4.5] Estudiante ve sus materias y las actividades disponibles — backend + frontend,
  primer punto de entrada del Estudiante al frontend de Actividad Evaluativa
  - Backend Identidad: `require_estudiante` (nuevo, hasta ahora solo existía en Actividad
    Evaluativa), `ListarMateriasDelEstudianteUseCase` (resuelve `Estudiante.comision_id` →
    `Comision.materia_id` → `MateriaPort`, reutilizado desde `US-2.1.2`), `EstudianteController`,
    endpoint `GET /identidad/estudiante/materias`
  - Backend Actividad Evaluativa: puerto nuevo y separado `EvaluacionEstudianteQueryPort`
    (`existentes_finalizadas`, chequea solo el evento terminal `EvaluacionFinalizada` por
    `aggregate_id` sin replay completo — no se ensancha `EvaluacionActivaQueryPort` de
    `US-3.2.4`, mismo criterio command/query que evitó el CRITICAL de CBO en `US-2.1.2`/
    `US-2.1.5`/`US-2.1.6`), `ListarActividadesVisiblesUseCase` (extiende
    `ListarActividadesUseCase` de `US-3.4.2` con el `Badge` por-estudiante),
    `ActividadesEstudianteController` (separado del controller de consulta docente),
    `GET /actividades/mis-actividades` (rol `estudiante`, registrado antes de
    `/{actividad_id}` para no chocar con esa ruta)
  - Contradicción detectada contra el prototipo aprobado durante la implementación: el plan
    original proponía 4 estados de `Badge` (agregando `"cerrada_sin_rendir"`); el prototipo
    `actividad-evaluativa-periodo-abierto.html` (`#est-actividades`) solo define 3 — corregido
    con Víctor, sin ese 4to estado (una actividad cerrada sin rendir se muestra como
    "Pendiente de responder", mismo criterio que `EnCurso`/`Suspendida` no distinguidas; el
    422 de `FueraDePeriodo` al intentar iniciar, `US-3.4.6`, resuelve ese caso)
  - Frontend: `identidad-estudiante-api.ts` (nuevo), extensión de `actividad-evaluativa-api.ts`,
    pantallas `MisMaterias.tsx`, `MisActividades.tsx`, `FueraDePeriodo.tsx` (reemplazan 2
    placeholders de `US-3.4.1` + 1 ruta nueva), 3 variantes de `Badge` nuevas
  - 11 tests unitarios + 6 integración + 5 BDD nuevos backend, 575+227+138 suites sin
    regresiones; 10 tests nuevos frontend, 211/211 suite completa frontend; quality gates
    APROBADO (pylint 9.81/10, CC máx 5, MI 83.2, coverage 99% backend / 89-92% en las
    pantallas nuevas, oxlint 0 errores, `tsc --noEmit` 0 errores, codeguard 9/9 checks full)
- [US-3.4.4] Docente ve el detalle de una actividad, extiende el plazo y la cierra manualmente
  — backend + frontend
  - Ajuste sobre la spec detectado en Fase 2: `ActividadResumen`/`ActividadResumenResponse`
    (`US-3.4.2`) ya tenían todos los campos del detalle (preguntas, intentos, conteos) — se
    reutilizan en vez de crear un `ActividadDetalle` redundante. Solo faltaba exponer
    `cerrada_manualmente` en el borde de la API (schema + tipo TS), ya existía en el dominio.
  - Backend: `ActividadQueryPort.obtener()` (nuevo), `ObtenerActividadUseCase` (lanza
    `ActividadNoExiste` si no está, mismo patrón que `ObtenerCuentaUseCase`),
    `ActividadesQueryController` con el use case nuevo inyectado, `GET /actividades/{id}`
    (rol `docente`, 404 si no existe) — reutiliza `PATCH /periodo` (`US-3.3.1`) y
    `POST /cerrar` (`US-3.3.2`) sin cambios
  - Frontend: `obtenerActividad()`, pantallas `ActividadDetalle.tsx`, `ExtenderPlazo.tsx`,
    `CerrarActividad.tsx` — reemplazan los 3 placeholders cableados desde `US-3.4.1`;
    `CerrarActividad.tsx` sigue el mismo patrón visual que `EliminarPregunta.tsx`;
    `ExtenderPlazo.tsx` muestra el 422 `NoSePuedeAcortarConEvaluacionesActivas` inline, mismo
    criterio que `NuevaActividad.tsx`
  - 6 tests unitarios + 5 integración + 4 BDD nuevos backend, 679/679 suite completa backend
    sin regresiones; 11 tests nuevos frontend, 199/199 suite completa frontend; quality gates
    APROBADO (pylint 9.84/10, CC máx 5, MI mín 54.63, coverage 100% backend / ~90-97% en las
    pantallas nuevas, oxlint 0 errores, `tsc --noEmit` 0 errores)
- [US-3.4.3] Docente crea una nueva actividad de período abierto — frontend puro, sin cambios
  de backend (`POST /actividades` ya existía desde `US-3.1.2`)
  - `NuevaActividad.tsx`: formulario con apertura/cierre/cantidad de preguntas/intentos
    permitidos, sin campo de título (el prototipo `#doc-nueva-actividad` no lo incluye — la
    materia es implícita por la navegación); hint dinámico con `cantidadPreguntasActivas` del
    banco de la materia; validación de cliente de período (INV-AE-02) e intentos (INV-AE-03);
    422 del backend (`PreguntasInsuficientes`, `PeriodoInvalido`, `CantidadIntentosInvalida`)
    mostrado inline
  - Reemplaza el placeholder de la ruta `/actividad-evaluativa/materias/:materiaId/actividades/nueva`
    cableada desde `US-3.4.1`
  - 5 tests nuevos (`NuevaActividad.test.tsx`), 188/188 suite completa frontend sin
    regresiones, quality gates APROBADO (oxlint 0 errores, `tsc --noEmit` 0 errores, coverage
    90.24% statements en el componente nuevo / 91.51% global)
- [US-3.4.2] Docente ve sus materias y el listado de actividades de una materia — primera
  pantalla real de la Iteración 4 del Incremento 3 (backend + frontend)
  - Gap detectado y resuelto con Víctor: `titulo` (opcional, default `""`) agregado a
    `ActividadEvaluativaPeriodoAbierto`/evento/Use Case/schemas — el prototipo/wireframe lo
    pedían pero el dominio no lo tenía; opcional para no romper los fixtures de `US-3.1.2` a
    `US-3.3.2`
  - `ActividadQueryPort`/`ActividadResumen` (nuevo), `ListarActividadesUseCase`,
    `SQLAlchemyActividadQueryRepository` (agrupa `events` en memoria, reutiliza
    `ActividadEvaluativaPeriodoAbierto.reconstruir()`, cuenta evaluaciones activas y
    finalizadas), `ActividadesQueryController` separado de `ActividadesController`
    (command/query, mismo criterio ya aplicado 5 veces en el proyecto), `GET
    /actividades?materia_id=` con estado derivado (`en_curso`/`programada`/`cerrada`)
  - Frontend: `listarActividades()`, 3 variantes nuevas de `Badge`, pantallas
    `MateriasActividades.tsx`/`Actividades.tsx` reemplazando los placeholders de `US-3.4.1`
  - 293/293 tests nuevos del Incremento 3, 664/664 suite completa backend, 183/183 frontend,
    quality gates APROBADO (pylint 9.59/10, CC rank A, coverage 100% backend / 91.57%
    statements frontend)
- [US-3.4.1] Infraestructura de frontend de Actividad Evaluativa — primera US de la Iteración
  4 del Incremento 3 (frontend), bloquea `US-3.4.2` a `US-3.4.7`
  - `actividad-evaluativa-api.ts`: cliente API tipado con las 9 funciones que envuelven los
    endpoints ya implementados en las Iteraciones 1-3 (`crearActividad`,
    `modificarPeriodoDisponibilidad`, `cerrarActividad`, `iniciarEvaluacion`,
    `registrarRespuesta`, `suspenderEvaluacion`, `reanudarEvaluacion`, `finalizarEvaluacion`,
    `obtenerRevision`), reutiliza `apiFetch` (JWT/401/403 de `US-1.1.6`)
  - 10 rutas nuevas en `router.tsx`: 6 bajo `/actividad-evaluativa/*` (rol `docente`) y 4 bajo
    `/mis-actividades/*` (rol `estudiante`, primer uso de ese rol en `RequireRole`), todas con
    `ActividadEvaluativaPlaceholder` hasta que `US-3.4.2` a `US-3.4.7` las reemplacen
  - Sin gap de backend (a diferencia de `US-2.1.8`) — los 9 endpoints consumidos ya existían
  - 178/178 tests frontend, oxlint 0 errores, `tsc --noEmit` 0 errores, cobertura global 94.01%

## [0.4.0] - 2026-08-23

> Tag `v0.4.0` y merge `develop → main` ejecutados el 2026-08-24 (commit `e31ee67`), junto con
> `v0.3.0`, a pedido explícito de Víctor — deploy real a un entorno sigue pendiente de decisión
> institucional, sin relación con este merge (`cd.yml` solo construye la imagen Docker).

### Added
- **Ajuste UX en vivo post-`SP-ADJ-01`** (PRs #120/#121, sin US formal — track informal por
  tocar solo `frontend/`, comparación en navegador real contra los prototipos HTML aprobados)
  - PR #120: login con cuenta bloqueada (layout propio del prototipo, corregido en la spec en
    vez de en el código — el prototipo manda), detalle de cuenta, resetear contraseña,
    subtítulo/mayúsculas de Cuentas, pantallas de Registro (Registro/RegistroError/RegistroExito)
  - PR #121: Banco de Preguntas — bug real de breadcrumb ("Banco" hardcodeado en vez del nombre
    de la materia, en 5 pantallas), estilo de `NuevaPreguntaTipo`/carga de preguntas, y un bug
    de layout real (botón "Eliminar" cortado sin scroll) que solo se manifestó al cargar **60
    preguntas reales** desde dos `.docx` de la materia "Ingeniería de Software" — con los 3
    fixtures mínimos del prototipo el problema de ancho de columnas no se veía
  - 3 candidatas nuevas documentadas sin implementar, fuera de alcance de este cierre:
    `US-ADJ-06` (nombre real en el header), `US-ADJ-07` (`comisionId` sin resolver a nombre
    legible), `US-ADJ-08` (chip de materia/comisión en Registro antes de completar el formulario)
  - 165/165 tests frontend en verde, 0 CRITICAL DesignReviewer
- [US-ADJ-05] Paginar el listado de cuentas — mismo criterio que `US-ADJ-03`, sin migración
  (`Usuario.creado_en` ya existía desde `US-2.2.3`)
  - A diferencia de `US-ADJ-03`, `CuentaQueryPort.listar()` tiene un único consumidor a cada
    lado (verificado por grep) — no hizo falta el diseño opt-in, `pagina`/`tamanio_pagina`
    con default fijo (1/20) siempre aplicado
  - `GET /usuarios` devuelve `{ cuentas, total }` (antes lista plana), orden estable por
    `creado_en, id`, `LIMIT`/`OFFSET`
  - `Cuentas.tsx` reutiliza `components/ui/pagination.tsx` de `US-ADJ-03` sin duplicarlo
  - 374/374 tests backend (306 unit/integración + 68 BDD, incluye 4 escenarios nuevos con
    steps reales de `pytest-bdd`), 165/165 tests frontend, pylint 9.56/10, coverage 98%
    backend / 91.95% frontend. Verificación visual en navegador real con 26 cuentas reales
    confirmando paginación, cambio de página y reset por filtro. **Cierra completa la
    iteración de ajuste conjunta `SP-ADJ-01`** (`US-ADJ-01`, `US-ADJ-03`, `US-ADJ-04`,
    `US-ADJ-05`)
- [US-ADJ-04] Alinear visualmente las pantallas de Cuentas/Contraseñas con el prototipo
  aprobado — refactor de presentación puro, sin cambios de comportamiento ni de backend
  - Mismo gap que resolvió `US-ADJ-01` para Banco de Preguntas, esta vez en
    `Cuentas.tsx`, `CuentaDetalle.tsx`, `ResetearPassword.tsx`, `CuentaReseteada.tsx`,
    `CambiarPassword.tsx` — implementadas antes de que existieran `Card`/`Badge`/`Breadcrumb`
  - Reutiliza las primitivas de `US-ADJ-01` sin agregar componentes nuevos; `Badge` gana 5
    variantes (`rol-docente`/`rol-estudiante`/`rol-admin`/`estado-activa`/`estado-bloqueada`)
  - `Cuentas.tsx` suma columna/botón "Ver" por fila (antes solo la fila entera navegaba)
  - `ResetearPassword.tsx` pasa el botón de reseteo a `destructive-solid` (antes soft)
  - `CuentaReseteada.tsx`/`CambiarPassword.tsx` (pantalla de éxito) pasan a `Card` centrada
    con ícono de éxito, en vez de texto suelto
  - 160/160 tests frontend, oxlint 0 errores, `tsc --noEmit` 0 errores, cobertura global
    92.09%/85%/90.76%/93.71%. Verificación visual en navegador real confirmada en 3 de las 5
    pantallas (Cuentas, CuentaDetalle, ResetearPassword); las 2 restantes comparten el mismo
    patrón ya validado y quedan cubiertas por tests de Vitest dedicados
- [US-ADJ-03] Paginar el listado del banco de preguntas — página fija de 20, orden estable
  por fecha de creación, reset a página 1 al cambiar filtros
  - Backend: `PreguntaPlantilla*.fecha_creacion` (nuevo, inmutable), migración con backfill
    automático (`server_default=now()`, mismo patrón que `usuario_creado_en`)
  - `GET /bancos/{id}/preguntas` acepta `pagina`/`tamanio_pagina` **opt-in**: si el cliente no
    los manda, sigue devolviendo el banco completo sin truncar — decisión de diseño detectada
    en Fase 2 (4 pantallas más consumen este endpoint para buscar una pregunta por id o
    derivar sugerencias, y se hubieran roto silenciosamente con paginación forzada). Contrato
    de respuesta pasa a `{ preguntas, total }` siempre (antes lista plana)
  - `frontend/src/components/ui/pagination.tsx` (nuevo, reusable) — controles de números de
    página + Anterior/Siguiente en `Banco.tsx`
  - `docs/design/ux/wireframes-banco-preguntas.md` §2.3 actualizado (gate UX) antes de tocar
    `frontend/`
  - 368/368 tests backend (300 unit/integración + 68 BDD, incluye 4 escenarios nuevos con
    steps reales de `pytest-bdd`), 156/156 tests frontend, pylint 9.16/10, coverage 100%
    backend / 92.04% frontend. Verificación visual en navegador real con 25 preguntas reales
    confirmando paginación, cambio de página y reset por filtro
- [US-ADJ-01] Alinear visualmente las pantallas de Banco de Preguntas con el prototipo
  aprobado — refactor de presentación puro (SP-ADJ-01), sin cambios de comportamiento ni de
  backend
  - Detectado en el UAT de cierre de la Iteración 1 (`HITO-4`): las pantallas de Banco de
    Preguntas no reproducían el lenguaje visual de
    `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`
  - `frontend/src/components/ui/card.tsx` y `badge.tsx` (nuevos), `Breadcrumb.tsx` (nuevo,
    propio no-shadcn), variante `destructive-solid` agregada a `button.tsx` sin tocar la
    variante `destructive` existente (usada por pantallas de Identidad ya aprobadas)
  - Aplicado a las 8 pantallas de `US-2.1.9` a `US-2.1.13`: breadcrumb, cards con sombra, tags
    de color por tipo/dificultad/importancia, resaltado de la opción/respuesta correcta, botón
    "Eliminar" sólido destructivo
  - Verificación visual en navegador real (Chrome vía claude-in-chrome) contra el prototipo
    aprobado, sin hallazgos — mismo criterio que el gate de diseño UX de `CLAUDE.md`
  - 150/150 tests frontend (2 nuevos + ajustes de selectors por el cambio de estructura DOM),
    oxlint 0 errores, `tsc --noEmit` 0 errores, cobertura global 92.49%/84.85%/91.3%/94.08%
    (statements/branches/functions/lines)
- [US-2.2.9] Login refleja el estado de cuenta bloqueada — frontend puro, sin cambios de
  backend (`POST /identidad/login` ya distinguía 403/401 desde `US-2.2.1`)
  - Gap detectado en Fase 2: la spec asumía `frontend/src/lib/auth-api.ts`, que no existe —
    `Login.tsx` distingue el caso inspeccionando `ApiError.status === 403` directamente
  - `frontend/src/pages/LoginCuentaBloqueadaError.tsx` (nuevo) — alerta destructiva "Cuenta
    bloqueada", dirige a contactar a un Administrador
  - `frontend/src/pages/Login.tsx` (extendido) — estado `bloqueada`, formulario completo
    (`fieldset`) deshabilitado cuando la cuenta está bloqueada
  - 4 tests nuevos + 2 escenarios BDD (validados con Vitest, sin pytest-bdd, mismo criterio de
    `US-2.2.6`/`7`/`8`) — 148/148 tests frontend, oxlint 0 errores, `tsc --noEmit` 0 errores.
    Cierra completa la Iteración 2 del Incremento 2 (backend y frontend)
- [US-2.2.8] Cualquier usuario autenticado cambia su propia contraseña — accesible a los tres
  roles, sin `RequireRole`
  - Backend (extensión mínima sobre `US-2.2.5`, gap detectado en Fase 2): `PUT
    /usuarios/me/password` expone `intentos_restantes` (401) o `bloqueada` (401/403) en el
    `detail` del error, en vez de un string genérico — `Usuario.intentos_restantes_cambio_password()`,
    `PasswordActualIncorrecta.intentos_restantes`; sin cambio de status codes existentes
  - `frontend/src/lib/api-client.ts` (extendido) — `ApiError.detail`, opción
    `handleUnauthorized` en `apiFetch` para que un 401 puntual (contraseña actual incorrecta)
    no dispare el logout global
  - `frontend/src/lib/cuentas-api.ts` (extendido) — `cambiarPassword(passwordActual,
    passwordNueva)`, `CambiarPasswordError`
  - `frontend/src/pages/CambiarPassword.tsx` (nuevo) — un solo componente con los 3 estados
    del wireframe (formulario/error/éxito), sin ruta separada para el error
  - `/mi-cuenta/cambiar-password` en `router.tsx`
  - 15 tests nuevos (3 backend + 12 frontend) + 3 escenarios BDD (validados con Vitest, sin
    pytest-bdd) — 357/357 tests backend, 145/145 tests frontend, oxlint 0 errores,
    `tsc --noEmit` 0 errores
- [US-2.2.7] Administrador ve el detalle de una cuenta y resetea/desbloquea — frontend puro,
  sin cambios de backend
  - `frontend/src/lib/cuentas-api.ts` (extendido) — `obtenerCuenta(id)`,
    `resetearPassword(id, passwordNueva)`, mapeo snake_case↔camelCase para `CuentaDetalleResponse`
  - `frontend/src/pages/CuentaDetalle.tsx` (nuevo) — reemplaza el placeholder de `US-2.2.6`;
    alerta de bloqueo, datos de la cuenta, botón único "Resetear contraseña y desbloquear"
  - `frontend/src/pages/ResetearPassword.tsx` (nuevo) — formulario con validación de cliente
    (≥8 caracteres, coincidencia), "Resetear contraseña"/"Cancelar"
  - `frontend/src/pages/CuentaReseteada.tsx` (nuevo) — confirmación de éxito
  - `/cuentas/:usuarioId/resetear-password` y `/cuentas/:usuarioId/reseteada` en `router.tsx`,
    protegidas con `RequireRole rol="administrador"`
  - 16 tests nuevos + 3 escenarios BDD (validados con Vitest, sin pytest-bdd) — 134/134 tests
    frontend en verde, oxlint 0 errores, `tsc --noEmit` 0 errores
- [US-2.2.6] Administrador ve y filtra el listado de cuentas — frontend puro, sin cambios de
  backend
  - `frontend/src/lib/cuentas-api.ts` (nuevo) — `listarCuentas(filtros)`, reutiliza el tipo
    `Rol` de `session.ts`
  - `frontend/src/pages/Cuentas.tsx` (nuevo) — tabla + filtros de rol/estado/búsqueda, fila
    navega al detalle (`/cuentas/{id}`, placeholder hasta `US-2.2.7`)
  - `/cuentas` y `/cuentas/:usuarioId` en `router.tsx`, protegidas con
    `RequireRole rol="administrador"`
  - 13 tests nuevos + 2 escenarios BDD (validados con Vitest, sin pytest-bdd) — 119/119 tests
    frontend en verde, oxlint 0 errores, `tsc --noEmit` 0 errores
- [US-2.2.5] Usuario autenticado cambia su propia contraseña — backend puro (RF-19)
  - `src/identidad/entities/usuario.py` — `Usuario.cambiar_password()` y
    `Usuario.registrar_fallo_cambio_password()`, contador propio `intentos_fallidos_password`
    independiente del de login (INV-ID-10)
  - `src/identidad/use_cases/cambiar_password.py` (nuevo) — `CambiarPasswordUseCase`
  - `PUT /usuarios/me/password` (cualquier rol autenticado) en `perfil_router.py` (nuevo) —
    `PerfilController` nuevo, separado de `CuentasController` por actor (self-service vs.
    administración)
  - 14 tests unitarios nuevos + 7 tests de integración nuevos + 5 escenarios BDD — 354/354
    tests del proyecto en verde, quality gates APROBADO (pylint 9.80/10, coverage 99% en
    `src/identidad`)
  - Cierra el backend completo de la Iteración 2 (`US-2.2.1` a `US-2.2.5`)
- [US-2.2.4] Administrador resetea la contraseña de una cuenta, con desbloqueo incluido —
  backend puro (RF-03)
  - `src/identidad/entities/usuario.py` — `Usuario.validar_password_nueva()` (INV-ID-11,
    primera vez que se enforza del lado del dominio) y `usuario.resetear_password()`
  - `src/identidad/use_cases/resetear_password.py` (nuevo) — `ResetearPasswordUseCase`, emite
    `PasswordReseteada` siempre y `CuentaDesbloqueada` solo si la cuenta estaba bloqueada
  - `POST /usuarios/{id}/resetear-password` (rol `administrador`) en `cuentas_router.py` —
    tercer método de `CuentasController`, junto a `listar_cuentas`/`obtener_cuenta`
    (`US-2.2.2`/`US-2.2.3`)
  - 9 tests unitarios nuevos + 5 tests de integración nuevos + 3 escenarios BDD — 329/329 tests
    del proyecto en verde, quality gates APROBADO (pylint 9.95/10, coverage 99% en
    `src/identidad`)
- [US-2.1.13] Docente elimina una pregunta desde la UI, con confirmación previa — frontend
  puro, sin cambios de backend
  - `frontend/src/pages/EliminarPregunta.tsx` (nuevo) — resuelve la pregunta a eliminar con
    `filtrarBanco()` (`US-2.1.7`), muestra su texto y aclara explícitamente que es baja lógica
    (INV-BP-04) antes de confirmar; ejecuta con `eliminarPregunta()` (`US-2.1.8`/`US-2.1.6`)
  - `frontend/src/router.tsx` — nueva ruta
    `/materias/:materiaId/banco/preguntas/:preguntaId/eliminar`
  - `frontend/src/pages/Banco.tsx` — habilita el botón "Eliminar" de la tabla (deshabilitado
    desde `US-2.1.10`)
  - 4 tests nuevos (Vitest) + 1 test de integración de router + 1 test nuevo en `Banco.tsx` —
    coverage 96.87%/77.77%/100% (statements/branches/functions) en `EliminarPregunta.tsx`.
    Cierra completa la Iteración 1 del Incremento 2 (`US-2.1.10` a `US-2.1.13`)
- [US-2.1.12] Docente edita una pregunta existente desde la UI — frontend puro, sin cambios de
  backend
  - `frontend/src/pages/EditarPregunta.tsx` (nuevo) — resuelve la pregunta a editar con
    `filtrarBanco()` (`US-2.1.7`, sin endpoint `GET /preguntas/{id}` nuevo), reutiliza los
    campos/validación de `NuevaPreguntaOpcionMultiple.tsx`/`NuevaPreguntaVerdaderoFalso.tsx`
    prellenados según el tipo concreto, sin selector de tipo; guarda con `editarPregunta()`
    (`US-2.1.8`/`US-2.1.5`)
  - `frontend/src/router.tsx` — reemplaza el placeholder de
    `/materias/:materiaId/banco/preguntas/:preguntaId/editar` por la pantalla real
  - 8 tests nuevos (Vitest) + 1 test de integración de router — coverage 90.52%/85.18%/92.1%
    (statements/branches/functions) en `EditarPregunta.tsx`
- [US-2.1.11] Docente carga una pregunta eligiendo su tipo — frontend puro, sin cambios de
  backend
  - `frontend/src/pages/NuevaPreguntaTipo.tsx` (nuevo) — selección de tipo (dos tarjetas
    clicables), navega al formulario correspondiente; aclara que el tipo no se puede cambiar
    después
  - `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx` (nuevo) — texto, opciones dinámicas
    (mínimo 2, radio de correcta, agregar/quitar), unidad temática y tema (texto libre —
    sin catálogo ni endpoint de origen, mismo criterio de `US-2.1.8`), dificultad/importancia;
    validación de cliente (INV-BP-02/03) antes de llamar a `cargarPreguntaOpcionMultiple()`
    (`US-2.1.8`)
  - `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx` (nuevo) — texto, selector V/F sin
    default, mismos metadatos; consume `cargarPreguntaVerdaderoFalso()` (`US-2.1.8`)
  - `frontend/src/router.tsx` — reemplaza los 3 placeholders de `/materias/:id/banco/preguntas/
    nueva*` por las pantallas reales
  - 9 tests nuevos (Vitest) + 3 tests de integración de router — coverage 100%/83.33%/90.47%
    (statements) en las 3 pantallas nuevas
- [US-2.1.10] Docente ve y filtra el banco de preguntas de una materia — frontend puro, sin
  cambios de backend
  - `frontend/src/pages/Banco.tsx` (nuevo) — resuelve `materiaId` contra `listarMaterias()`
    (`US-2.1.9`) para obtener nombre y `bancoId`, sin endpoint nuevo; filtros de unidad/tema
    (texto libre) y dificultad/importancia (`<select>` nativo, sin dependencia nueva de
    shadcn/ui); refresca la tabla al cambiar cualquier filtro consumiendo `filtrarBanco()`
    (`US-2.1.7`); acciones "Editar"/"+ Nueva pregunta" navegan a las rutas placeholder ya
    existentes (`US-2.1.8`), que reemplazarán `US-2.1.11`–`US-2.1.13`
  - `frontend/src/router.tsx` — reemplaza el placeholder de `/materias/:materiaId/banco` por
    la pantalla real
  - 7 tests nuevos (Vitest, `Banco.test.tsx`) + 1 test de integración de router actualizado —
    coverage 95.55%/89.28%/89.47% (statements/branches/functions) en `Banco.tsx`
- [US-2.1.9] Docente ve el listado de materias y da de alta una nueva — backend + frontend
  - `GET /materias` (nuevo, `src/banco_preguntas/frameworks/api/materias_router.py`) — lista
    materias con `id`, `nombre`, `banco_id` y `cantidad_preguntas_activas`, rol `docente`
  - `ListarMateriasUseCase` (nuevo) — orquesta `MateriaRepositoryPort.listar()` (nuevo),
    `BancoRepositoryPort.obtener_por_materia_id()` (nuevo) y reutiliza
    `PreguntaRepositoryPort.filtrar()` (`US-2.1.7`) para el conteo, sin ensanchar ese puerto
  - `frontend/src/lib/banco-preguntas-api.ts` — `listarMaterias()` (excluida de `US-2.1.8`
    por este mismo gap: el backend nunca expuso `GET /materias`)
  - `frontend/src/pages/Materias.tsx` (nuevo) — grilla de materias con conteo de preguntas
    activas, tarjeta "Nueva materia"
  - `frontend/src/pages/NuevaMateria.tsx` (nuevo) — formulario de alta, error inline por
    nombre duplicado (409), vuelve al listado en éxito
  - 24 tests nuevos (backend: 6 unitarios de use case, 1 unitario de controller, 5 de
    integración de gateways/API, 1 escenario BDD; frontend: 11 unitarios/integración de
    Vitest) — coverage 100% en entities/use_cases/interface_adapters del BC, 100%/93.33% en
    las 2 pantallas nuevas
- [US-2.1.8] Infraestructura de frontend del Banco de Preguntas — sin cambios de backend
  - `frontend/src/lib/banco-preguntas-api.ts` (nuevo) — cliente API tipado del BC (reutiliza
    `apiFetch`/JWT/401/403 de `US-1.1.6`, sin duplicar esa lógica): `crearMateria`,
    `filtrarBanco`, `cargarPreguntaOpcionMultiple`, `cargarPreguntaVerdaderoFalso`,
    `editarPregunta`, `eliminarPregunta`; mapea explícitamente snake_case (schemas Pydantic)
    ↔ camelCase (TS)
  - `frontend/src/pages/_placeholders.tsx` — `BancoPreguntasPlaceholder`, destino temporal de
    las rutas nuevas hasta que `US-2.1.9` a `US-2.1.13` las reemplacen
  - `frontend/src/router.tsx` — 7 rutas nuevas bajo `AppLayout`, protegidas con
    `RequireRole rol="docente"` (`US-1.1.9`): `/materias`, `/materias/nueva`,
    `/materias/:materiaId/banco` y sus subrutas de carga/edición de preguntas
  - **Gap detectado en Fase 2 (planificación):** el backend no expone `GET /materias`
    (listado) — solo `POST /materias` de `US-2.1.1`. La spec de `US-2.1.9` asumía que ya
    existía. Decisión de Víctor: excluir `listarMaterias` de esta US; `US-2.1.9` queda
    bloqueada hasta que ese endpoint se implemente
  - 19 tests nuevos (12 unitarios de `banco-preguntas-api.ts`, 7 de integración de router) —
    100% cobertura en `banco-preguntas-api.ts`
- [US-2.1.7] Docente filtra el banco por materia, unidad, tema, dificultad e importancia —
  BC Banco de Preguntas
  - `src/banco_preguntas/entities/ports/pregunta_repository_port.py` — método abstracto
    `filtrar(banco_id, unidad?, tema?, dificultad?, importancia?)`, solo preguntas `activa = true`
  - `src/banco_preguntas/use_cases/filtrar_banco.py` — `FiltrarBancoUseCase`, valida que el
    `Banco` exista y delega el filtro combinado (AND) en el repositorio
  - `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` — implementación
    SQLAlchemy de `filtrar()` con `WHERE` dinámico; mapeo a entidad extraído a `_a_entidad()`
    para reutilizarlo con `obtener_por_id()`
  - `src/banco_preguntas/interface_adapters/controllers/bancos_controller.py` (nuevo) —
    `BancosController`, separado de `PreguntasController` para no repetir el patrón de
    CRITICAL de CBO ya visto en `US-2.1.2`/`US-2.1.5`/`US-2.1.6` (`PreguntasController` estaba
    en CBO=10/10, el umbral duro, tras `US-2.1.6`)
  - `GET /bancos/{banco_id}/preguntas` (`src/banco_preguntas/frameworks/api/bancos_router.py`,
    nuevo) — requiere rol `docente`, filtros opcionales por query params, 404 si `BancoNoExiste`
  - 21 tests nuevos (6 unitarios de use case, 2 unitarios de controller, 4 integración de
    repositorio, 6 integración de API, 3 escenarios BDD) — 99% cobertura del BC completo
- [US-2.1.6] Docente elimina (baja lógica) una pregunta — BC Banco de Preguntas
  - `src/banco_preguntas/entities/pregunta_plantilla.py` — método `eliminar()` en
    `PreguntaPlantillaOpcionMultiple` y `PreguntaPlantillaVerdaderoFalso`, marca
    `activa = false` (INV-BP-04, baja lógica, no física)
  - `src/banco_preguntas/entities/errors.py` — `PreguntaYaEliminada`
  - `src/banco_preguntas/entities/eventos.py` — `PreguntaEliminada`
  - `src/banco_preguntas/use_cases/eliminar_pregunta.py` — `EliminarPreguntaUseCase`,
    reutiliza `obtener_por_id()`/`actualizar()` del puerto (sin cambios de puerto)
  - `DELETE /preguntas/{pregunta_id}` (`src/banco_preguntas/frameworks/api/preguntas_router.py`)
    — requiere rol `docente`, 204 sin body en éxito, 404 si `PreguntaNoExiste`, 409 si
    `PreguntaYaEliminada`
  - Cuarto use case inyectado en `PreguntasController`; evento tipado `object` en esa capa,
    mismo criterio preventivo de CBO ya aplicado en `US-2.1.5`
  - 15 tests nuevos (6 unitarios de entities, 4 unitarios de use case, 1 unitario de
    controller, 4 integración, 3 escenarios BDD) — 99% cobertura del BC completo
- [US-2.1.5] Docente edita una pregunta existente — BC Banco de Preguntas
  - `src/banco_preguntas/entities/pregunta_plantilla.py` — método `editar()` en
    `PreguntaPlantillaOpcionMultiple` y `PreguntaPlantillaVerdaderoFalso`, reaplica INV-BP-02/03
    en el primero (validación extraída a `_validar_opciones()`, compartida con `crear()`); el
    tipo de la pregunta no es editable
  - `src/banco_preguntas/entities/errors.py` — `PreguntaNoExiste`, `PreguntaInactiva`
  - `src/banco_preguntas/entities/eventos.py` — `PreguntaEditada`
  - `src/banco_preguntas/use_cases/editar_pregunta.py` — `EditarPreguntaUseCase`, dispatch por
    tipo concreto sin lógica de negocio propia
  - `PUT /preguntas/{pregunta_id}` (`src/banco_preguntas/frameworks/api/preguntas_router.py`) —
    requiere rol `docente`, 200 con la respuesta según el tipo real, 404 si `PreguntaNoExiste`,
    409 si `PreguntaInactiva`, 422 si `OpcionesInvalidas`
  - `PreguntaRepositoryPort` extendido con `obtener_por_id()` y `actualizar()` (separado de
    `guardar()`, que es alta)
  - RF-05 pasa a "Implementado (backend) — frontend Especificado" en la matriz de
    trazabilidad — las tres US-IEDD de backend (`US-2.1.3`, `US-2.1.4`, `US-2.1.5`) ya están
    implementadas
  - 25 tests nuevos (10 unitarios, 12 integración, 3 escenarios BDD) — 100% cobertura en
    entities/use_cases/interface_adapters del código nuevo
  - Bug encontrado y corregido en Fase 5: `SQLAlchemyPreguntaRepository.actualizar()` no
    persistía la columna `activa`, expuesto por el test de rechazo de edición sobre pregunta
    inactiva
- [US-2.1.4] Docente carga una pregunta de Verdadero/Falso en un banco — BC Banco de Preguntas
  - `src/banco_preguntas/entities/pregunta_plantilla.py` — aggregate `PreguntaPlantillaVerdaderoFalso`,
    segundo tipo de pregunta, sin invariantes de negocio adicionales sobre `respuesta_correcta`
    (garantizado por tipado)
  - `src/banco_preguntas/use_cases/cargar_pregunta_verdadero_falso.py` —
    `CargarPreguntaVerdaderoFalsoUseCase`, mismo flujo que `CargarPreguntaOpcionMultipleUseCase`
  - `POST /preguntas/verdadero-falso`
    (`src/banco_preguntas/frameworks/api/preguntas_router.py`) — requiere rol `docente`, 201
    con `PreguntaVerdaderoFalsoResponse`, 404 si `BancoNoExiste`
  - `PreguntaRepositoryPort.guardar()` y `SQLAlchemyPreguntaRepository` extendidos para
    aceptar ambos tipos de pregunta (opción múltiple y verdadero/falso), sin generalizar entre
    ellos (`BC-banco-preguntas-modelo.md` §4)
  - Migración Alembic `6f523d16bf1c_pregunta_plantilla_respuesta_correcta.py` — columna
    `respuesta_correcta` (nullable) en `pregunta_plantilla`
  - RF-04 pasa a "Implementado (backend) — frontend Especificado" en la matriz de
    trazabilidad — las tres US-IEDD de backend (`US-2.1.1`, `US-2.1.3`, `US-2.1.4`) ya están
    implementadas
  - 25 tests nuevos (13 unitarios, 10 integración, 2 escenarios BDD) — 100% cobertura en
    entities/use_cases/interface_adapters del código nuevo
- [US-2.1.3] Docente carga una pregunta de opción múltiple en un banco — BC Banco de Preguntas
  - `src/banco_preguntas/entities/pregunta_plantilla.py` — aggregate `PreguntaPlantillaOpcionMultiple`,
    factory `crear()` valida INV-BP-02 (exactamente una opción correcta) e INV-BP-03 (mínimo 2
    opciones), levanta `OpcionesInvalidas`
  - `src/banco_preguntas/entities/opcion.py`, `dificultad.py`, `importancia.py` — value objects
    `Opcion` y enums `Dificultad`/`Importancia` (Alto/Medio/Bajo)
  - `src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py` —
    `CargarPreguntaOpcionMultipleUseCase`, valida precondición de `Banco` existente
    (`BancoNoExiste`)
  - `POST /preguntas/opcion-multiple`
    (`src/banco_preguntas/frameworks/api/preguntas_router.py`) — requiere rol `docente`, 201
    con `PreguntaOpcionMultipleResponse`, 404 si `BancoNoExiste`, 422 si `OpcionesInvalidas`
  - `BancoRepositoryPort.obtener_por_id` — agregado al puerto existente para soportar la
    validación de precondición
  - Migración Alembic `b0e03a73f699_pregunta_plantilla.py` — tabla `pregunta_plantilla`
    (`opciones` como `JSONB`, columna discriminadora `tipo` para `US-2.1.4`)
  - 22 tests nuevos (11 unitarios, 11 integración incluyendo 4 escenarios BDD) — 100%
    cobertura en entities/use_cases/interface_adapters del código nuevo
- [US-2.1.2] `ObtenerMateriaUseCase` de solo lectura (`src/banco_preguntas/use_cases/`) y
  `MateriaRepositoryPort.obtener_por_id` — soportan la consulta de `Materia` desde otros BCs.
- [US-2.1.1] Docente da de alta una materia y su banco de preguntas — BC Banco de Preguntas
  - `src/banco_preguntas/entities/materia.py`, `banco.py` — aggregates `Materia` (`nombre`
    único, INV-BP-00) y `Banco` (1:1 con `Materia`, INV-BP-01)
  - `src/banco_preguntas/use_cases/crear_materia.py` — `CrearMateriaUseCase` crea `Materia` +
    `Banco` en la misma operación
  - `POST /materias` (`src/banco_preguntas/frameworks/api/materias_router.py`) — requiere rol
    `docente`, 201 con `MateriaResponse`, 409 si `MateriaYaExiste`, 422 si `nombre` vacío
  - Migración Alembic `099d86aa5d0d_materia_banco.py` — tablas `materia`, `banco`
  - 16 tests nuevos (5 unitarios, 8 integración, 3 BDD) — 100% cobertura en
    entities/use_cases/interface_adapters

### Changed
- [US-2.1.2] `Comisión` referencia `Materia` por puerto en vez de un `string` libre — BC
  Identidad
  - `Comision.materia: str` → `Comision.materia_id: UUID` (`src/identidad/entities/comision.py`)
  - `MateriaPort`/`MateriaDTO` nuevos (`src/identidad/entities/ports/materia_port.py`) —
    Identidad consulta `Materia` sin importar `src/banco_preguntas` directamente
  - `MateriaPortInProcess` (`src/identidad/frameworks/adapters/`) — adaptador in-process, mismo
    criterio que `ADR-006`; único punto de Identidad que importa `src.banco_preguntas`
  - `CrearComisionUseCase` valida `materia_id` contra el puerto (`MateriaNoExiste` si no
    existe); `RegistrarEstudianteUseCase` resuelve el nombre para `RegistroResponse.materia`
    (contrato existente sin cambios para el Estudiante)
  - `POST /comisiones` ahora recibe `materia_id: UUID` en vez de `materia: str`; responde 422
    con `MateriaNoExiste`
  - Migración `295bc74948c3_comision_materia_id.py` — backfill de `comision.materia` (string)
    a `materia_id` (UUID) por nombre, verificada con round-trip real contra Postgres local
  - Documentado en `docs/architecture/20-context-map-integrations.md`: nueva relación
    Identidad → Banco de Preguntas (`Materia`), patrón Customer-Supplier
  - 25 tests nuevos/actualizados (6 unitarios, 8 integración, 4 BDD nuevos + 7 preexistentes de
    Identidad ajustados) — 100% cobertura en entities/use_cases/interface_adapters, 158/158
    tests del proyecto en verde
- **Refactor (`ADR-019`):** `TipoPerfil`, `JWT`/`JWTPayload`, `JWTIssuerPort`, `PyJWTIssuer`,
  `get_current_user`, `require_rol` movidos de `src/identidad` a `src/shared` — necesario para
  que `banco_preguntas` pudiera exigir rol `docente` en su endpoint sin importar directo de
  `identidad` (regla de `CLAUDE.md`: nunca imports entre BCs). `identidad` sigue exponiendo
  `require_administrador`/`require_docente` con la misma API pública; `banco_preguntas` arma su
  propio `require_docente` componiendo las mismas piezas de `shared`. 148/148 tests del
  proyecto verificados en verde tras el refactor.

## [0.3.0] - 2026-07-29

> Tag `v0.3.0` taggeado retroactivamente el 2026-08-24 sobre el commit real de cierre
> (`75e0de9`), junto con el merge `develop → main` que también cerró `v0.4.0` — ver nota en
> `[0.4.0]`.

### Added
- [US-1.1.9] Administrador da de alta un Docente desde la UI — BC Identidad
  - `frontend/src/components/RequireRole.tsx` — guard de ruta por rol (componente nuevo,
    reutilizable): sin sesión → redirige a `/login`; sesión con rol distinto del requerido →
    mensaje inline "Acceso denegado"; rol correcto → renderiza. Gap detectado en Fase 2 —
    `router.tsx`/`AppLayout.tsx` (`US-1.1.6`) no tenían guard client-side, solo el manejo
    reactivo de 401/403 de `apiFetch`; decisión de Víctor: componente reutilizable en vez de
    chequeo inline, pensando en próximas rutas protegidas por rol
  - `frontend/src/pages/AltaDocente.tsx` — formulario controlado (nombre/email/contraseña/
    confirmar contraseña), perfil fijo en "Docente" sin selector (§2.6
    `wireframes-identidad.md`), consume `POST /usuarios` (`US-1.1.0`, protegido por
    `US-1.1.5`) vía `apiFetch`; 201 → `/docentes/nuevo/exito`; 409 (email ya registrado) →
    error inline en el propio formulario
  - `frontend/src/pages/AltaDocenteExito.tsx` — confirmación con nombre/email del Docente
    creado y aclaración explícita de que todavía no está asignado a ninguna comisión (§2.7);
    acción "Dar de alta otro Docente" vuelve al formulario (flujo de altas en lote)
  - `frontend/src/router.tsx` — rutas nuevas `/docentes/nuevo` y `/docentes/nuevo/exito` bajo
    `AppLayout`, protegidas con `RequireRole rol="administrador"`
  - **Corrección de UAT acordada con Víctor** (hallazgo de un smoke test manual en navegador
    real, fuera del alcance original de la spec): el estilo de la app no respetaba el
    prototipo aprobado (`US-1.0.2`) desde `US-1.1.6` — una regla CSS heredada sin `@layer` en
    `frontend/src/index.css` pisaba las utilities de Tailwind (afectaba tamaño/alineación de
    todos los `<h1>` y angostaba la app a 1126px centrada), y la paleta/tipografía eran las de
    shadcn por defecto en vez de las institucionales (azul `#1D75B5`, verde `#53AA74`, Roboto).
    Se reescribió `index.css`, se agregaron `Logo.tsx`/`TopStrip.tsx` (marca + barra
    institucional) y se actualizaron `AuthLayout.tsx`/`AppLayout.tsx` — afecta a todas las
    pantallas de Identidad, no solo a esta US
  - Cierra la Iteración 2 (Frontend de Identidad) del Incremento 1 — habilita la apertura de
    BL-002
  - 16 tests nuevos (`RequireRole.test.tsx`, `AltaDocente.test.tsx`, `AltaDocenteExito.test.tsx`,
    `AuthLayout.test.tsx`) + `router.test.tsx`/`AppLayout.test.tsx` actualizados; 46/46 tests
    frontend, cobertura ≥85% sobre los 3 archivos nuevos de esta US (umbral de referencia 80%)
    (`quality/reports/inc1/US-1.1.9-quality.json`)
- [US-1.1.8] Estudiante se registra desde la UI con un link de invitación — BC Identidad
  - `frontend/src/pages/Registro.tsx` — formulario controlado (nombre/email/contraseña/
    confirmar contraseña), lee `token` de query param, consume `POST /identidad/registro`
    (`US-1.1.2`/`US-1.1.3`) vía `apiFetch`; 201 → `/registro/exito`; 422 (invitación
    inválida/vencida/ya usada, sin distinguir motivo) → `/registro/error`; 409 (email ya
    registrado) → error inline en el propio formulario
  - `frontend/src/pages/RegistroError.tsx` / `RegistroExito.tsx` — pantallas completas
    (§2.4/§2.5 `wireframes-identidad.md`); éxito muestra el nombre de la comisión asignada,
    sin autenticar automáticamente (sin login automático post-registro en v1)
  - **Ampliación de backend acordada con Víctor** (fuera del alcance original "sin cambios de
    backend" de la spec, documentada como adenda): `RegistroResponse.materia` — nuevo campo,
    poblado con un lookup a `ComisionRepositoryPort.obtener_por_id` (puerto ya existente)
    dentro de `RegistrarEstudianteUseCase`, para poder mostrar el nombre de la comisión en la
    pantalla de éxito (el wireframe lo requiere; antes solo se exponía `comision_id`, un UUID)
  - `frontend/src/router.tsx` — `/registro` deja de ser placeholder; rutas nuevas
    `/registro/error`, `/registro/exito`
  - 9 tests nuevos (`Registro.test.tsx`, `RegistroError.test.tsx`, `RegistroExito.test.tsx`) +
    `router.test.tsx` actualizado; 30/30 tests frontend, cobertura 91.66% sobre las pantallas
    nuevas (umbral de referencia 80%); backend 71/71 unitarios + 38/38 integración, mypy y
    codeguard sin errores (`quality/reports/inc1/US-1.1.8-quality.json`)
- [US-1.1.7] Docente/Administrador/Estudiante inicia sesión desde la UI — BC Identidad
  - `frontend/src/pages/Login.tsx` — formulario controlado (email/contraseña, shadcn
    `Input`/`Label`), consume `POST /identidad/login` (`US-1.1.4`) vía `apiFetch`; éxito guarda
    la sesión y redirige por rol (`administrador` → `/docentes/nuevo`, cubierta por
    `US-1.1.9`; `docente`/`estudiante` → placeholder post-login)
  - `frontend/src/pages/LoginError.tsx` — alerta inline con el mensaje genérico que no
    distingue email inexistente de contraseña incorrecta (mismo criterio del backend,
    `US-1.1.4`) — no es una ruta separada, es el mismo `/login` con un estado de error
  - `frontend/src/components/ui/{input,label}.tsx` — agregados vía `npx shadcn add`, primeros
    campos de formulario del proyecto (antes solo existía `Button`)
  - `frontend/src/router.tsx` — `/login` deja de ser placeholder; ruta `index` bajo
    `AppLayout` para el destino post-login de docente/estudiante
  - 5 tests nuevos (`Login.test.tsx`, `LoginError.test.tsx`) + `router.test.tsx` actualizado;
    21/21 tests frontend, cobertura 96.9% (umbral de referencia 80%,
    `quality/reports/inc1/US-1.1.7-quality.json`)
  - **RF-02 pasa a Implementado** (backend + frontend) — `docs/traceability/matrix.md`
- [US-1.1.6] Infraestructura de frontend — routing, cliente API y manejo de sesión — BC Identidad
  - `frontend/src/lib/session.ts` — guardar/leer/limpiar `{token, rol}` en `localStorage`
    (trade-off XSS documentado, suficiente para un JWT sin refresh/blacklist, `ADR-013`)
  - `frontend/src/lib/api-client.ts` — `apiFetch<T>()` adjunta `Authorization: Bearer` si hay
    sesión; 401 limpia la sesión y navega a `/login`; 403 propaga el mensaje genérico que ya
    devuelve el backend (`US-1.1.5`) sin agregar detalle del recurso
  - `frontend/src/router.tsx` — React Router v7 (modo data, `createBrowserRouter`), rutas
    placeholder `/login` y `/registro` (pantallas reales en `US-1.1.7`/`US-1.1.8`)
  - `frontend/src/layouts/{AuthLayout,AppLayout}.tsx` — tarjeta centrada para auth, header de
    aplicación para pantallas post-login (`wireframes-identidad.md` §3)
  - Decisión tomada con Víctor en Fase 0: se agrega **Vitest + React Testing Library** al
    proyecto — no existía ninguna estrategia de testing de frontend (`package.json` sin test
    runner, CI solo corría ESLint). Gate de cobertura de referencia 80%, alcanzado con 100%
    líneas/statements/funcs, 87.5% branches
    (`quality/reports/inc1/US-1.1.6-quality.json`)
  - `npm run test` (`tsc --noEmit` + `vitest run`) agregado al job `lint-frontend` de CI —
    mismo nombre de job para no romper el required status check de branch protection
  - Limpieza: 5 archivos del scaffold demo de Vite sin referencias (`App.css`, `react.svg`,
    `vite.svg`, `hero.png`, `public/icons.svg`)
  - 16 tests (10 unitarios + 6 de integración), suite frontend completa en verde
- [US-1.1.5] El sistema restringe el acceso a funcionalidades según el rol del usuario autenticado — BC Identidad
  - `JWTPayload` (VO) — `usuario_id` + `rol` resueltos al decodificar un JWT válido, sin
    volver a consultar la base (ADR-013, sin refresh/blacklist)
  - `JWTIssuerPort.verificar(token)` — nuevo método sobre el puerto existente (`US-1.1.4`);
    `PyJWTIssuer.verificar()` decodifica con PyJWT, `JWTExpirado`/`JWTInvalido` según el caso
  - `get_current_user` (`interface_adapters/security/get_current_user.py`) — dependency FastAPI
    que extrae y valida el JWT del header `Authorization: Bearer`; 401 si falta o no es válido
  - `require_rol(roles_permitidos, get_current_user)` (`interface_adapters/security/require_rol.py`)
    — dependency que compone sobre `get_current_user` y exige el rol; 403 si no está permitido.
    Ambos builders reciben la abstracción como parámetro (no importan `frameworks/`) — el wiring
    con `PyJWTIssuer` ocurre en el composition root (`frameworks/dependencies.py`)
  - Endpoints protegidos: `POST /usuarios` y `POST /comisiones`, `POST /comisiones/{id}/docentes`
    con `require_administrador` (`US-1.1.0`); `POST /comisiones/{id}/invitaciones` con
    `require_docente` (`US-1.1.1`). `POST /identidad/login` y `POST /identidad/registro`
    permanecen públicos (precondición de tener un JWT)
  - RF-02 pasa a Implementado — las dos US-IEDD que requería (`US-1.1.4`, `US-1.1.5`) están
    cerradas en backend
  - 12 tests unitarios nuevos + 6 de integración + 6 escenarios BDD; se actualizaron los
    `step_defs` y tests de integración de `US-1.1.0` a `US-1.1.4` para autenticarse contra los
    endpoints ahora protegidos (helper compartido `tests/step_defs/inc1/_auth_headers.py` y
    fixtures `admin_headers`/`docente_headers` en `tests/integration/conftest.py`) — el primer
    Administrador se emite directo con `PyJWTIssuer`, sin pasar por la API (huevo-y-gallina,
    igual que en un despliegue real)
  - Suite total del proyecto: 132/132 tests, cobertura 100% en los componentes nuevos
    (`entities/`, `interface_adapters/security/`)
- [US-1.1.4] Docente, administrador y estudiante se autentican y reciben un JWT con su rol — BC Identidad
  - `IniciarSesionUseCase` — verifica email/password contra el hash bcrypt guardado; emite un
    JWT vía `JWTIssuerPort` con claim `rol` derivado de `Usuario.tipo_perfil` (`TipoPerfil`,
    ya existente — no se creó un VO `Rol` adicional por ser una envoltura redundante sobre
    `TipoPerfil`, decisión aprobada antes de implementar, ver `docs/plans/inc1/US-1.1.4-plan.md`)
  - VO `JWT` (`token`, `rol`, `expira_en`) y puerto `JWTIssuerPort`; `PyJWTIssuer` — adaptador
    PyJWT (`ADR-007`), firma con `settings.secret_key`/`algorithm`, `exp` a 60 minutos desde
    la emisión (`ADR-013`)
  - `CredencialesInvalidas` — mismo error genérico tanto si el email no existe como si la
    contraseña no verifica, para no filtrar existencia de cuentas; evento `SesionIniciada`
  - `UsuarioRepositoryPort.obtener_por_email` nuevo (puerto y gateway SQLAlchemy)
  - Endpoint público `POST /identidad/login` — 200 con `access_token`/`rol`/`expira_en`, 401
    genérico ante credenciales inválidas
  - Corrección de configuración: `ACCESS_TOKEN_EXPIRE_MINUTES` estaba en 30 desde el walking
    skeleton, desalineado con `ADR-013` (60 min) — alineado en `settings.py`, `.env` y
    `.env.example`
  - Alcance: solo backend — `Login.tsx`/`LoginError.tsx`/`frontend/src/lib/auth.ts` quedan
    diferidos a la misma US-IEDD de frontend que ya diferían las US anteriores de Identidad
    (`frontend/src` sigue sin routing ni cliente API), ver `docs/plans/inc1/US-1.1.4-context.md`
  - 10 tests unitarios nuevos + 7 de integración + 5 escenarios BDD; suite total del proyecto
    107/107, coverage 100% en entities/use_cases/interface_adapters, 99% total del proyecto
- [US-1.1.3] Estudiante intenta registrarse con link vencido o inválido — BC Identidad
  - `InvitacionNoValida` (guard genérico de `US-1.1.2`) refinada en tres excepciones
    específicas: `InvitacionInvalida` (token inexistente), `InvitacionVencida`
    (`expira_en` pasado), `InvitacionYaUsada` (`usada_en` no null)
  - `Invitacion.verificar_vigente(ahora)` — nuevo método que distingue el motivo del
    rechazo (INV-ID-01, INV-ID-03); `Invitacion.aceptar()` lo reutiliza
  - `RegistrarEstudianteUseCase._buscar_invitacion_vigente` distingue token inexistente de
    invitación vencida/ya usada
  - `POST /identidad/registro` sigue devolviendo 422 para los tres casos (mismo mensaje al
    Estudiante; el backend distingue internamente solo para logging/debug, según wireframe)
  - Alcance: solo backend — la pantalla `RegistroError.tsx` (`#registro-error`) queda
    diferida a la misma US-IEDD de frontend que ya difería `Registro.tsx`/`RegistroExito.tsx`
    desde `US-1.1.2` (ver `docs/plans/inc1/US-1.1.3-context.md`)
  - 3 tests unitarios nuevos + 1 de integración + 3 escenarios BDD backend; suite total del
    proyecto 85/85 (excluyendo el escenario de UI diferido), coverage 100% en los archivos
    modificados
- [US-1.1.2] Estudiante se registra con un link de invitación válido — BC Identidad
  - `Estudiante` gana `comision_id` (INV-ID-05: nunca existe sin comisión); nueva factory
    `Usuario.crear_estudiante` — único camino de construcción de un `Estudiante`.
    `Usuario.crear()` genérico ya no admite `TipoPerfil.ESTUDIANTE`
  - `Invitacion.es_vigente`/`Invitacion.aceptar` (INV-ID-01, INV-ID-03); error
    `InvitacionNoValida` (guard genérico de esta US — `US-1.1.3` lo refina en las tres
    excepciones específicas de su propio alcance); eventos `InvitacionAceptada`,
    `UsuarioRegistrado`
  - `RegistrarEstudianteUseCase` — valida invitación vigente, valida email libre, crea
    Usuario+Estudiante y consume la invitación en la misma operación
  - Endpoint público `POST /identidad/registro` (sin guard JWT, mismo criterio que
    `US-1.1.1` — el Estudiante todavía no tiene sesión al registrarse)
  - Migración Alembic: columna `comision_id` en `estudiante`
  - Alcance: solo backend — el frontend de registro (`Registro.tsx`, `RegistroExito.tsx`)
    queda diferido a una US-IEDD separada, dado que `frontend/src` no tenía routing ni
    cliente API todavía (ver `docs/plans/inc1/US-1.1.2-context.md`)
  - 15 tests nuevos (10 unitarios + 3 integración + 2 BDD), coverage 100% en
    entities/use_cases/interface_adapters; suite total del proyecto 77/77
- [US-1.1.1] Docente genera link de invitación para una comisión — BC Identidad
  - `Invitación` (aggregate) con token único (`secrets.token_urlsafe`) y expiración a 7 días
    (`ADR-012`), evento `InvitacionGenerada`
  - `GenerarInvitacionUseCase` — valida INV-ID-08 (docente asignado a la comisión), genera
    token, persiste, envía email, emite evento
  - Endpoint `POST /comisiones/{id}/invitaciones` (sin guard de rol todavía, mismo criterio
    que US-1.1.0 — se agrega en `US-1.1.5`); `docente_id` y `email_destinatario` explícitos
    en el body (ajuste de alcance sobre la spec original, ver `docs/plans/inc1/US-1.1.1-plan.md`)
  - `SmtpNotificador` — adaptador SMTP propio de Identidad (`ADR-012`), `smtplib` en
    `asyncio.to_thread`; variables `SMTP_*` nuevas en `.env.example`
  - Migración Alembic: tabla `invitacion`
  - 16 tests nuevos (9 unitarios + 4 integración + 2 BDD via `step_defs` + 1 gateway),
    coverage 100% en entities/use_cases/interface_adapters; suite total del proyecto 53/53
- [US-1.1.0] Administrador da de alta cuentas de usuario, crea una comisión y asigna docentes
  — BC Identidad, precondición del resto de la Iteración 1
  - `Usuario` (aggregate) + entities subordinadas `Docente`/`Administrador`/`Estudiante`,
    `Comisión` (aggregate), eventos `UsuarioCreado`/`ComisionCreada`/`DocenteAsignado`
  - `CrearUsuarioUseCase`, `CrearComisionUseCase`, `AsignarDocenteAComisionUseCase`
  - Endpoints `POST /usuarios`, `POST /comisiones`, `POST /comisiones/{id}/docentes` (sin
    guard de rol todavía — se agrega en `US-1.1.5`)
  - `scripts/seed_admin.py` — bootstrap del primer Administrador (`ADR-016`)
  - Migración Alembic: tablas `usuario`, `docente`, `administrador`, `estudiante`, `comision`,
    `comision_docentes`
  - 37 tests (20 unitarios + 9 integración + 5 BDD via `step_defs`), coverage 100% en
    entities/use_cases/interface_adapters
  - `ADR-016` (bootstrap admin), `ADR-017` (DB session compartida `shared/frameworks/db.py`),
    `ADR-018` (`NullPool` en el engine SQLAlchemy)

### Fixed
- `passlib` incompatible con `bcrypt>=4.1` — reemplazado por `bcrypt` directo
- Orden de inserción `Usuario`/perfil sin `relationship()` ORM causaba violación de FK —
  corregido con flush intermedio en `SQLAlchemyUsuarioRepository`
- `pytest-asyncio` sin `loop_scope` explícito rompía el engine compartido entre tests con
  distintos event loops — fijado a `session` scope

## [0.2.0] - 2026-07-16

### Added
- PostgreSQL local (vía Homebrew) y Alembic inicializado (`alembic.ini`, `migrations/`)
- `src/settings.py` — configuración desde `.env` con pydantic-settings
- Primer test real del proyecto (`tests/unit/inc0/test_health.py`)
- `.claude/commands/docs-audit.md` — skill de auditoría de trazabilidad documental
- HITO-2 y HITO-3 (`docs/aprendizajes/`)
- BL-001 — cierre del Incremento 0 (`.cm/baselines/BL-001-fundacion-tecnica.md`)

### Changed
- CI ya no tolera "0 tests" — retirado tras agregar el primer test real
- `docs/rf/PLAN_v1.md`: Docker local diferido a un incremento posterior; PostgreSQL local
  corre vía Homebrew mientras tanto
- `CLAUDE.md`: corregido el "próximo paso" — el Incremento 0 no usa `incN-candidatas.md`

## [0.1.0] - 2026-07-15

### Added
- Fundación documental: RF_v1, RNF_v1, ARQ_v1, PLAN_v1
- Plan de Gestión de Configuración (`docs/plans/PLAN-CM.md`), checklist de instalación y
  workflow de desarrollo
- ADRs 001-011 ratificados y matriz de trazabilidad inicial
- Primer HITO de aprendizaje (`docs/aprendizajes/HITO-1-*.md`)
- BL-000 — cierre de la fundación documental (`.cm/baselines/BL-000-fundacion-documental.md`)

### Changed
- Plan de incrementos (`PLAN_v1.md`) reestructurado: Incremento 0 pasa a ser fundación técnica
  pura, BC Identidad se mueve a un nuevo Incremento 1, resto renumerado (2-7)
- `docs/cm/` renombrado a `docs/plans/`
