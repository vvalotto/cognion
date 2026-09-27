# Plan de Implementación: US-ADJ-58 — Cancelar, finalizar en cualquier etapa, no iniciar sin participantes

**Patrón:** clean-architecture-bc (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC `actividad_evaluativa` + `frontend/`
**Fuente UX:** `wireframes-actividad-evaluativa-en-vivo.md` §8, prototipo pantallas 20-22 (aprobado 2026-09-27)

## Decisiones de diseño (a confirmar en este checkpoint)

1. **Estado `Cancelada`** en `EstadoSesionEnVivo` (terminal). Se suma `SesionEnVivoCancelada → Cancelada` al mapa
   `_ESTADO_POR_EVENTO` del aggregate **y** al del read model `SQLAlchemySesionesEnVivoQueryRepository` (que tiene su
   propia copia). El frontend ya pide solo `EnEspera`/`EnCurso` en los listados, así que una sesión cancelada
   desaparece sin tocar las pantallas de listado.
2. **Errores nuevos:** `SesionYaCancelada` (422) y `SinParticipantes` (422).
3. **Aggregate — `cancelar()`** (INV-AEV-10), validación en función de módulo `_validar_para_cancelar` (criterio CBO
   ya usado en este archivo): `Cancelada` → `SesionYaCancelada`; distinto de `EnEspera` → `SesionYaIniciada`.
   Una sesión `Cancelada` además rechaza con `SesionYaCancelada`:
   - `validar_para_unirse()` (hoy solo rechaza `Finalizada`);
   - `iniciar()` (hoy devolvería `SesionYaIniciada`, mensaje engañoso).
   El resto de transiciones ya la rechaza con `SesionNoEnCurso` (exigen `EnCurso`).
4. **Aggregate — `finalizar()`** (INV-AEV-03 modificado): `_validar_para_finalizar` deja de exigir
   `pregunta_actual_cerrada`. La pregunta abierta queda sin cerrar: **no** se emite `PreguntaEnVivoCerrada`. El
   ranking final ya incluye las respuestas dadas, porque `ranking_por_sesion` se actualiza al responder
   (`ResponderPreguntaEnVivoUseCase` → `proyecciones.registrar_respuesta`), no al cerrar. `AvanzarSiguientePregunta`
   sigue exigiendo la pregunta cerrada.
5. **INV-AEV-11 en el Use Case, no en el aggregate:** el aggregate no conoce las participaciones (viven en
   `ParticipacionEnVivo`). `IniciarSesionEnVivoUseCase` recibe `ParticipantesSesionQueryPort` (ya existe) y rechaza
   con `SinParticipantes` si `listar()` viene vacío. Se valida **después** de `sesion.iniciar()` en memoria, para que
   una sesión ya iniciada o cancelada siga devolviendo su error propio. Mismo criterio que INV-AEV-01 en
   `CrearSesionEnVivoUseCase` (regla que necesita un puerto → Use Case). Mantiene intacta la firma de `iniciar()` y los
   ~10 tests unitarios del aggregate que la llaman.
6. **Evento `SesionEnVivoCancelada`** (`eventos_en_vivo.py`), payload `sesion_id` + `ocurrido_en`.
7. **Use Case `CancelarSesionEnVivoUseCase(event_store, canal)`:** `load` (`SesionNoExiste`) → `reconstruir` →
   `cancelar` → `append` → publica `{"tipo": "sesion_cancelada"}` después de persistir. Ante
   `ConcurrenciaOptimistaError` (carrera con un iniciar o con otro cancelar) recarga el stream y vuelve a validar, así
   el error que llega es el real (`SesionYaIniciada` o `SesionYaCancelada`).
8. **Controller:** `cancelar()` en `SesionesEnVivoController` (crear/unirse/iniciar: el ciclo de vida previo a la
   dinámica), que pasa de 3 a 4 use cases. `ConduccionEnVivoController` ya tiene 4. El CBO se mide con
   `designreviewer` antes del push; si roza 10/10, controller propio.
9. **Endpoint:** `POST /sesiones-en-vivo/{sesion_id}/cancelar`, rol `docente`, sin body, 200 `SesionEnVivoResponse`.
   `SesionNoExiste` → 404; `SesionYaIniciada`/`SesionYaCancelada` → 422. Además:
   - `iniciar` mapea `SinParticipantes` y `SesionYaCancelada` a 422;
   - `unirse` mapea `SesionYaCancelada` a 422;
   - `finalizar` deja de listar `PreguntaActualNoCerrada`.
10. **Sin migración ni puertos nuevos.** `dependencies.py`: el iniciar recibe el query de participantes; se cablea el
    cancelar.

### Frontend

11. **Cliente API** (`sesion-en-vivo-api.ts`): estado `cancelada` (`Cancelada` en la API) y `cancelarSesion(id)`.
    **Canal** (`canal-sesion-en-vivo.ts`): mensaje `sesion_cancelada`.
12. **Docente — sala** (`SalaEsperaDocente.tsx`): botón "Cancelar sesión" (rojo contorneado, al pie, junto a
    "‹ Salir") → ruta nueva `/sesiones-en-vivo/:sesionId/cancelar` → `CancelarSesionEnVivo.tsx` (pantalla 20).
    Confirmar → `cancelarSesion` → vuelve a `ComisionDetalleDocente`; en `422`, mensaje en la misma pantalla.
13. **Estudiante:** etapa nueva `cancelada` en `vista-estudiante.ts`, terminal como `finalizada`. Se llega por el
    mensaje `sesion_cancelada` o por `GET estado` con estado `cancelada` (reconexión). Componente
    `EstudianteSesionCancelada` (pantalla 21) con "Volver a mis actividades".
14. **Proyección:**
    - "Finalizar sesión" secundario en `StagePreguntaSola` y `StagePreguntaOpciones` que abre la confirmación
      `StageConfirmarFinalizar` (pantalla 22). Es un estado local del contenedor, no una etapa nueva de
      `vista-proyeccion.ts`, así la resincronización periódica no la pisa.
    - "Finalizar sesión" directo en `StageHistograma`.
    - Si la proyección carga una sesión `cancelada`, vuelve al detalle de la Comisión.

## Componentes

### Backend
- [ ] `entities/actividad_evaluativa_en_vivo.py`: `CANCELADA`, `cancelar()`, `_validar_para_cancelar`, unirse/iniciar
  sobre cancelada, `_validar_para_finalizar` sin INV de pregunta cerrada, `_ESTADO_POR_EVENTO`
- [ ] `entities/errors.py`: `SesionYaCancelada`, `SinParticipantes`
- [ ] `entities/eventos_en_vivo.py`: `SesionEnVivoCancelada`
- [ ] `use_cases/cancelar_sesion_en_vivo.py` (nuevo)
- [ ] `use_cases/iniciar_sesion_en_vivo.py`: INV-AEV-11
- [ ] `interface_adapters/controllers/sesiones_en_vivo_controller.py`: `cancelar()`
- [ ] `frameworks/api/sesiones_en_vivo_router.py`: endpoint y mapeos
- [ ] `frameworks/adapters/sesiones_en_vivo_query_repository.py`: estado `Cancelada`
- [ ] `frameworks/dependencies.py`: wiring

### Frontend
- [ ] `lib/sesion-en-vivo-api.ts`, `lib/canal-sesion-en-vivo.ts`
- [ ] `pages/actividad-evaluativa/SalaEsperaDocente.tsx`, `CancelarSesionEnVivo.tsx` (nuevo), `router.tsx`
- [ ] `pages/actividad-evaluativa/estudiante/vista-estudiante.ts` + contenedor + `EstudianteSesionCancelada.tsx`
- [ ] `pages/actividad-evaluativa/ProyeccionSesionEnVivo.tsx`, `proyeccion/StagePreguntaSola.tsx`,
  `StagePreguntaOpciones.tsx`, `StageHistograma.tsx`, `StageConfirmarFinalizar.tsx` (nuevo)

### Documentación
- [ ] `BC-actividad-evaluativa-modelo.md` §§10-18: comando, evento, estado, INV-AEV-10/11, INV-AEV-03 modificado
- [ ] `tests/features/inc6/US-6.2.7-finalizar-sesion-en-vivo.feature`: el escenario "Rechazo si la pregunta actual no
  fue cerrada" pasa a "Finalizar con la pregunta abierta" (con nota de reemplazo por `US-ADJ-58`)

## Tests

- **Unit** (se pueden correr en local):
  - aggregate: cancelar, unirse e iniciar sobre cancelada, finalizar con la pregunta abierta, `reconstruir` con
    `SesionEnVivoCancelada`;
  - `CancelarSesionEnVivoUseCase` con Fakes, incluida la carrera optimista;
  - iniciar sin participantes, sumando un Fake del query de participantes a sus tests;
  - `_resumen_de_stream` con cancelada;
  - actualizar los tests que afirmaban `PreguntaActualNoCerrada` al finalizar y los Fakes que cambian de firma.
- **Integración + BDD:**
  - `tests/integration/inc6/_helpers.iniciar_sesion` une a un estudiante nuevo **solo si** la sesión no tiene
    participantes. Así no cambian los tests que ya unen estudiantes y cuentan participantes.
  - Se ajustan los tests que llaman a `/iniciar` directo: `test_sesiones_en_vivo_iniciar_router.py` y
    `test_us_6_1_4_steps.py`.
  - Tests nuevos: router de cancelar (HTTP + `sesion_cancelada` por WebSocket), iniciar sin participantes y
    finalizar con la pregunta abierta.
  - Step defs de los 11 escenarios backend en `tests/step_defs/sp-adj-02/test_us_adj_58_steps.py`.
  - **Dónde se corren:** en una base aparte (`cognion_test_adj58`, creada y migrada con Alembic, con
    `DATABASE_URL` apuntando a ella), nunca en la base de la UAT. Si la suite no la respeta, quedan para CI.
- **Frontend:** Vitest de las pantallas y los reductores nuevos. E2E en `frontend/e2e/`:
  - circuito nuevo: cancelar desde la sala, con el Estudiante viendo la cancelación;
  - circuito nuevo: finalizar a mitad de una pregunta con confirmación;
  - repasar el circuito 7 (inicio bloqueado), que ahora también lo rechaza la API.
- **Scripts de UAT** (`tests/uat/inc6/*.sh`): se revisan para que unan a alguien antes de iniciar. El guion de la
  Iteración 2 ya lo hace.

## Estimación relativa

Tamaño medio: ~9 archivos de backend, ~12 de frontend, ~15 de tests tocados.
