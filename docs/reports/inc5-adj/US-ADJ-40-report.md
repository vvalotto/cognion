# Reporte de Implementación: US-ADJ-40 - Pantallas de recuperación de contraseña

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-40 |
| **Título** | Pantallas de recuperación de contraseña |
| **Producto** | cognion |
| **Prioridad** | Última US de la Iteración 2 del Incremento 5-ADJ — la cierra completa |
| **Puntos estimados** | 3 |
| **Fecha inicio** | 2026-09-13 |
| **Fecha fin** | 2026-09-13 |
| **Tiempo real** | ~36 min de tracking (Fases 0, 2-5, 7-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Última US de la Iteración 2 del Incremento 5-ADJ: agrega las 5 pantallas del flujo de
recuperación de contraseña ("Olvidé mi contraseña") que consumen los endpoints ya cerrados en
`US-ADJ-38` (solicitar) y `US-ADJ-39` (confirmar) — hasta ahora esos endpoints solo eran
accesibles por HTTP directo. Frontend puro, sin cambios de backend. Cierra completa la
Iteración 2 (`US-ADJ-38` a `40`).

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro.

### Código Fuente (Frontend)

- ✅ `frontend/src/lib/cuentas-api.ts` — `solicitarRecuperacionPassword(email)` y
  `confirmarNuevaPassword(token, passwordNueva)`, ambas sobre `apiFetch` sin sesión
  (endpoints públicos). `confirmarNuevaPassword` propaga `ApiError` tal cual — el 422 del
  backend trae `detail` como string plano, no un objeto estructurado
- ✅ `frontend/src/pages/identidad/RecuperarPasswordSolicitar.tsx` (nuevo, 68 líneas) — ruta
  `/recuperar-password`
- ✅ `frontend/src/pages/identidad/RecuperarPasswordSolicitado.tsx` (nuevo, 29 líneas) — ruta
  `/recuperar-password/solicitado`
- ✅ `frontend/src/pages/identidad/RecuperarPasswordNueva.tsx` (nuevo, 124 líneas) — ruta
  `/recuperar-password/:token`; distingue error de política de contraseña (inline) de error
  de token (navega a pantalla dedicada) por el prefijo del mensaje, vía helper local
  `esErrorPoliticaPassword()`
- ✅ `frontend/src/pages/identidad/RecuperarPasswordTokenInvalido.tsx` (nuevo, 42 líneas) —
  ruta `/recuperar-password/invalido`
- ✅ `frontend/src/pages/identidad/RecuperarPasswordExito.tsx` (nuevo, 25 líneas) — ruta
  `/recuperar-password/exito`
- ✅ `frontend/src/pages/identidad/Login.tsx` — agrega el link "¿Olvidaste tu contraseña?"
  (único cambio a este archivo)
- ✅ `frontend/src/router.tsx` — 5 rutas nuevas bajo el `AuthLayout` público, mismo patrón que
  `/registro`/`/registro/error`/`/registro/exito`

**Total archivos:** 8 (0 backend, 8 frontend — 5 nuevos, 3 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `RecuperarPasswordSolicitar.test.tsx` (nuevo) — 2 tests: envía el email y navega a
  confirmación, link "Volver a iniciar sesión"
- ✅ `RecuperarPasswordSolicitado.test.tsx` (nuevo) — 2 tests: mensaje genérico + vigencia,
  botón vuelve a `/login`
- ✅ `RecuperarPasswordNueva.test.tsx` (nuevo) — 5 tests: éxito → pantalla de éxito, contraseña
  corta rechazada sin llamar al backend, confirmación no coincide rechazada sin llamar al
  backend, error de política de contraseña del backend → inline sin navegar, token
  vencido/inválido/ya usado → navega a pantalla de link no válido
- ✅ `RecuperarPasswordTokenInvalido.test.tsx` (nuevo) — 1 test: mensaje + sin formulario +
  link "Pedir un nuevo link"
- ✅ `RecuperarPasswordExito.test.tsx` (nuevo) — 1 test: confirmación + link a `/login`
- ✅ `cuentas-api.test.ts` — +4 tests: `solicitarRecuperacionPassword` (POST correcto),
  `confirmarNuevaPassword` (POST correcto, propaga mensaje de error de token tal cual, propaga
  mensaje de error de política tal cual)
- ✅ `Login.test.tsx` — +1 test: el link "¿Olvidaste tu contraseña?" navega a
  `/recuperar-password`

#### Tests de Integración
- ✅ `router.test.tsx` — +3 tests (con el `router` real, no mocks manuales): Login → clic en
  el link → pantalla de solicitud dentro del layout de auth; flujo completo solicitar → email
  enviado → abrir link con token → guardar → éxito → login; token vencido/inválido/ya usado →
  pantalla de link no válido → "Pedir un nuevo link" vuelve a solicitar

#### Escenarios BDD

No aplica — frontend puro, mismo criterio que `US-ADJ-24`/`27`/`28`/`29`/`30`/`35`/`36`/`37`.

**Total tests nuevos/actualizados:** 35 nuevos · **Estado:** 417/417 frontend pasando en la
corrida final (con `testTimeout` elevado a 20000ms para absorber la contención de CPU de
correr la suite completa con `--coverage`); en corridas previas con el timeout por defecto de
5000ms se observaron fallos intermitentes por contención de CPU en archivos no tocados por
esta US (`NuevaPreguntaOpcionMultiple.test.tsx`, `NuevaPreguntaVerdaderoFalso.test.tsx`,
`MateriasActividades.test.tsx`, `ResetearPassword.test.tsx`, `Registro.test.tsx`,
`NuevaPreguntaTipo.test.tsx`) — mismo patrón de flake ya documentado en `US-ADJ-24`/`37`,
confirmado ajeno a esta US corriendo los archivos nuevos en aislamiento (38/38 verdes en
todas las corridas).

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (6 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa) | 417/417 | Sin regresiones | ✅ |
| **Coverage global** | 91.28% stmts / 81.35% branches / 86.89% functions / 94% lines | ≥80% (umbral del proyecto, `vite.config.ts`) | ✅ |
| **Coverage archivos nuevos** | 92-100% stmts/functions/lines en las 5 pantallas | — | ✅ |

Fuente: `quality/reports/inc5-adj/US-ADJ-40-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] Navegar desde el login: clic en "¿Olvidaste tu contraseña?" lleva a `/recuperar-password`
- [x] Solicitar recuperación con cualquier email muestra siempre el mensaje genérico
- [x] Definir nueva contraseña con un token vigente → pantalla de éxito, login posterior
  exitoso con la contraseña nueva
- [x] Token vencido/inválido/ya usado → "Este link ya no es válido", sin formulario, link
  "Pedir un nuevo link"
- [x] Contraseña nueva que no cumple la política → error inline, sin navegar

**Estado:** 5/5 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Frontend puro, mismo patrón de pantallas públicas ya usado en `Login.tsx`/`Registro.tsx`/
`RegistroExito.tsx`/`RegistroError.tsx` bajo `AuthLayout`. Sin capas de dominio — no aplica
Clean Architecture backend a esta US.

### Decisión de diseño — distinguir errores sin código de error estructurado

`POST /identidad/recuperar-password/confirmar` responde 422 con `detail` como string plano
(`str(exc)` de la excepción de dominio), no como objeto `{mensaje, ...}` (a diferencia de
`CambiarPasswordError`, que sí tiene ese objeto). Las excepciones de política de contraseña
siempre arrancan con `"La contraseña debe..."`; las de token mencionan
`"El token de recuperación '...'..."`. Sin agregar una clase de error nueva al cliente API —
`RecuperarPasswordNueva.tsx` decide la navegación con un helper local
`esErrorPoliticaPassword(mensaje)` que chequea ese prefijo.

### Flujo de Pantallas

```
Login (link "¿Olvidaste tu contraseña?")
  → RecuperarPasswordSolicitar (/recuperar-password)
      → RecuperarPasswordSolicitado (/recuperar-password/solicitado)
          → Login

(desde el email) RecuperarPasswordNueva (/recuperar-password/:token)
  → éxito → RecuperarPasswordExito (/recuperar-password/exito) → Login
  → error de política → inline, mismo formulario
  → error de token → RecuperarPasswordTokenInvalido (/recuperar-password/invalido)
      → RecuperarPasswordSolicitar
```

---

## Cambios no Previstos

Ninguno — implementación siguió el plan aprobado sin desviaciones. La spec mencionaba "3
rutas nuevas" para 5 pantallas listadas; se registró una ruta por pantalla (5 rutas), mismo
criterio que `/registro`/`/registro/error`/`/registro/exito`, documentado explícitamente en el
plan como una aclaración menor, no una desviación de diseño.

---

## Testing Manual Realizado

Ninguno — sin servidor de backend corriendo en esta sesión (US previamente cerradas
`US-ADJ-38`/`39` ya verificaron los endpoints reales por HTTP directo y en navegador). La
verificación de esta US se apoyó en los tests de integración con el `router` real
(`router.test.tsx`), que ejercitan el flujo completo de navegación por clic sin mocks
manuales de rutas.

---

## Deuda Técnica

Ninguna introducida por esta US. Se detectó (sin acción, fuera de alcance) que `US-ADJ-39` no
tiene entrada propia en `CHANGELOG.md` — mencionada solo de pasada dentro de la entrada de
`US-ADJ-38`.

---

## Próximos Pasos

### Historias Relacionadas

Ninguna — `US-ADJ-40` cierra completa la Iteración 2 del Incremento 5-ADJ (`US-ADJ-38` a
`40`, recuperación de contraseña). Siguen la Iteración 3 (autoregistro, `US-ADJ-41` a `43`) y
la Iteración 4 (Analytics RF-20/23), independientes entre sí según
`docs/plans/inc5-adj/inc5-adj-candidatas.md`.

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 72s |
| Plan | 130s |
| Implementación | 138s |
| Tests Unitarios | 730s |
| Tests de Integración | 185s |
| Quality Gates | N/D — gap de bookkeeping: `start-phase 7` no se invocó antes de `end-phase 7` por error de secuencia de esta sesión, el trabajo de la fase sí se ejecutó y verificó completo (ver Métricas de Calidad) |
| Documentación | 91s |
| **TOTAL** | **~36 min** (`tracker_cli.py status`, incluye el tiempo de Quality Gates no registrado por fase) |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`). La mayor parte del tiempo (Tests Unitarios) correspondió
a corridas repetidas de la suite completa de Vitest con `--coverage` para descartar que los
fallos observados fueran una regresión real, afectadas por contención de CPU — mismo patrón ya
documentado en `US-ADJ-24`/`35`/`36`/`37`.

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Verificar la propagación de errores del backend (`ApiError.message` con el string plano de
   `detail`) en el cliente API antes de escribir la pantalla evitó descubrir el gap de diseño
   (sin código de error estructurado) a mitad de la implementación — se documentó como
   decisión explícita en el plan antes de codear.
2. Los tests de integración sobre el `router` real (`router.test.tsx`) detectaron un bug de
   timing en el primer intento del test de flujo completo (el `router.navigate()` a
   `/recuperar-password/tok-abc` no había terminado de re-renderizar antes de que el test
   intentara tipear en el campo de contraseña nueva) — corregido agregando un
   `await screen.findByRole("heading", ...)` antes de interactuar, mismo patrón ya usado en
   otros tests de ese archivo.

### Recomendaciones para Próximas Historias

1. Mismo patrón que `US-ADJ-24`/`35`/`36`/`37`: evitar lanzar más de un proceso de Vitest en
   paralelo al correr la suite completa con `--coverage` — la contención de CPU produce
   timeouts falsos en archivos no relacionados al cambio; subir `testTimeout` (20000ms) para
   la corrida de verificación final evita repetir el diagnóstico cada vez.
2. Recordar invocar `start-phase` antes de `end-phase` en cada fase — esta sesión saltó
   `start-phase 7` por apuro al pasar de Fase 5 a Fase 7, y el tracking de esa fase quedó sin
   tiempo registrado (el trabajo en sí no se vio afectado).
