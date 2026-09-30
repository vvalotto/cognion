# Reporte de Implementación: US-ADJ-36 - Contraseña segura — política ampliada

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-36 |
| **Título** | Contraseña segura — política ampliada |
| **Producto** | cognion |
| **Prioridad** | Alta — cierra un gap de seguridad real |
| **Puntos estimados** | 2 |
| **Fecha inicio** | 2026-09-12 |
| **Fecha fin** | 2026-09-12 |
| **Tiempo real** | ~143 min de tracking (Fases 0 a 9, todas las fases del skill) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Segunda US de la Iteración 1 del Incremento 5-ADJ: amplía `INV-ID-11` (política de contraseña
de `Usuario`) de "mínimo 8 caracteres" a "mínimo 12 caracteres + mayúscula + número + símbolo",
y **cierra un gap de seguridad real detectado en el relevamiento**: `CrearUsuarioUseCase`
(alta de Docente por Administrador) y `RegistrarEstudianteUseCase` (registro vía invitación)
nunca invocaban `Usuario.validar_password_nueva` — solo `CambiarPassword`/`ResetearPassword`
lo hacían. Antes de esta US, `POST /usuarios` y `POST /identidad/registro` aceptaban
cualquier contraseña del lado del dominio, protegidos únicamente por `minLength` HTML del
cliente (trivial de saltear con un `curl` directo). El cierre del gap propagó el efecto a
~19 archivos de fixtures de tests preexistentes en todo el proyecto, que usaban contraseñas
que dejaron de cumplir la política ampliada.

En frontend, `PasswordInput` (`US-ADJ-35`) gana el indicador de fortaleza + checklist de
reglas, activado en los 4 campos de contraseña nueva del sistema.

---

## Componentes Implementados

### Código Fuente (Backend)

- ✅ `src/identidad/entities/errors.py` — `PasswordSinComplejidadSuficiente` (nueva excepción)
- ✅ `src/identidad/entities/usuario.py` — `_LARGO_MINIMO_PASSWORD` 8→12,
  `validar_password_nueva` agrega chequeo de mayúscula/dígito/símbolo
- ✅ `src/identidad/use_cases/crear_usuario.py` — cierra el gap, agrega
  `Usuario.validar_password_nueva(password)`
- ✅ `src/identidad/use_cases/registrar_estudiante.py` — cierra el gap, misma llamada
- ✅ `src/identidad/frameworks/api/perfil_router.py` — propaga `PasswordSinComplejidadSuficiente`
- ✅ `src/identidad/frameworks/api/cuentas_router.py` — ídem
- ✅ `src/identidad/frameworks/api/usuarios_router.py` — nuevo manejo de ambas excepciones
  de password (antes solo capturaba `EmailYaRegistrado`)
- ✅ `src/identidad/frameworks/api/registro_router.py` — ídem

### Código Fuente (Frontend)

- ✅ `frontend/src/components/PasswordInput.tsx` — prop `mostrarFortaleza`, indicador de 3
  niveles (Débil/Media/Fuerte) + checklist de las 4 reglas
- ✅ `frontend/src/pages/identidad/Registro.tsx` — `minLength={12}`, activa `mostrarFortaleza`,
  mensaje de error actualizado
- ✅ `frontend/src/pages/identidad/CambiarPassword.tsx` — activa `mostrarFortaleza` en
  "nueva" (no en "actual"), mensaje actualizado
- ✅ `frontend/src/pages/identidad/AltaDocente.tsx` — `minLength={12}`, activa
  `mostrarFortaleza`, mensaje actualizado
- ✅ `frontend/src/pages/cuentas/ResetearPassword.tsx` — `minLength={12}` (nuevo), activa
  `mostrarFortaleza`, mensaje actualizado

**Total archivos de producción:** 13 (8 backend, 5 frontend)

### Fixtures de tests actualizados (efecto del cierre del gap)

~19 archivos en `tests/unit/inc1/`, `tests/integration/inc1/`, `tests/step_defs/inc1/`,
`tests/step_defs/inc2/` y `tests/features/inc2/` — contraseñas de ejemplo que antes del
cierre del gap se aceptaban sin control (`"claveSegura1"`, `"claveNueva123"`,
`"nuevaClave123"`, `"password123"`, etc.) actualizadas para cumplir INV-ID-11 ampliada.

---

### Tests

#### Tests Unitarios
- ✅ `tests/unit/inc1/test_usuario.py` — `TestUsuarioValidarPasswordNueva` reescrita: 8 tests
  (4 preexistentes actualizados + 4 nuevos: sin mayúscula, sin número, sin símbolo, orden
  longitud-antes-que-complejidad)
- ✅ `tests/unit/inc1/test_crear_usuario_use_case.py` — +1 test (gap cerrado)
- ✅ `tests/unit/inc1/test_registrar_estudiante_use_case.py` — +1 test (gap cerrado, verifica
  que la invitación no se consume)
- ✅ `frontend/src/components/PasswordInput.test.tsx` — +5 tests de `mostrarFortaleza`
  (oculto por defecto, Débil/Media/Fuerte, checklist)

#### Tests de Integración
- ✅ `tests/integration/inc1/test_usuarios_api_integration.py` — +1 test (`POST /usuarios`
  con password débil → 422)
- ✅ `tests/integration/inc1/test_registro_api_integration.py` — +1 test (`POST
  /identidad/registro` con password débil → 422)

#### Escenarios BDD
- ✅ `tests/features/inc5-adj/US-ADJ-36-contrasena-segura.feature` — 9 escenarios (5 de
  dominio puro sobre `Usuario.validar_password_nueva`, 4 de los dos gaps cerrados a nivel HTTP)
- ✅ `tests/step_defs/inc5-adj/test_us_adj_36_steps.py` (nuevo) — incluye stub SMTP propio
  (mismo patrón que `US-ADJ-26`) porque generar la invitación de los escenarios de Estudiante
  dispara un email real

**Total tests nuevos:** 20 (backend: 2 unit use case + 8 unit entity ampliados + 2 integration
+ 9 BDD; frontend: 5 unit) · **Estado:** 986/986 backend (unit+integration+BDD), 385/389
frontend (4 fallos de flake preexistente de `banco-preguntas`, confirmado ajeno en aislamiento)

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (8 archivos backend) | 9.83/10 | ≥ 8.0 | ✅ |
| **CC máximo** | 8 (`Usuario.validar_password_nueva`) | ≤ 10 | ✅ |
| **MI mínimo** | 63.89 | > 20 | ✅ |
| **Coverage backend** (entities + use_cases tocados) | 98% | ≥ 95% | ✅ |
| **oxlint** | 0 errores | 0 errores | ✅ |
| **tsc -b** | 0 errores | 0 errores | ✅ |
| **Coverage `PasswordInput.tsx`** | 100% stmts/branches/functions/lines | — | ✅ |

Fuente: `quality/reports/inc5-adj/US-ADJ-36-quality.json`,
`quality/reports/inc5-adj/US-ADJ-36-codeguard.json` (9/9 checks, `--analysis-type full`).
Los 18 "errors" de CodeGuard son fallos de herramienta no instalada en el entorno
(vulture/codespell) + timeout de mypy (bug conocido, `vvalotto/software_limpio#70`) — ninguno
es un hallazgo de código real, mismo patrón ya documentado en US-5.1.1/2/3.

---

## Criterios de Aceptación

- [x] `Usuario.validar_password_nueva` exige mínimo 12 caracteres + mayúscula + número + símbolo
- [x] Los 4 comandos/endpoints que fijan contraseña aplican la misma regla
- [x] **Gap cerrado**: `CrearUsuario` y `RegistrarEstudiante` ahora llaman
  `validar_password_nueva`
- [x] Frontend: indicador de fortaleza + checklist en los campos de contraseña nueva

**Estado:** 4/4 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Ampliación de una invariante de dominio ya existente (`INV-ID-11`), sin aggregate ni comando
nuevo. El cierre del gap es agregar una llamada ya usada en otros 2 Use Cases del mismo BC —
mismo patrón, sin decisión arquitectónica nueva.

### Flujo de Datos (gap cerrado)

```
CrearUsuarioUseCase.execute(...)
  1. Verificar email no duplicado
  2. Usuario.validar_password_nueva(password)   ← nuevo — antes se saltaba directo al hash
  3. hasher.hash(password)
  4. Usuario.crear(...)

RegistrarEstudianteUseCase.execute(...)
  1. Buscar y validar vigencia de la Invitación
  2. Verificar email no duplicado
  3. Usuario.validar_password_nueva(password)   ← nuevo — antes de invitacion.aceptar()
  4. hasher.hash(password)
  5. Usuario.crear_estudiante(...)
  6. invitacion.aceptar(...)                     ← la invitación no se consume si el password falla
```

---

## Cambios no Previstos

- **Corrección del `.feature`** (Fase 6): tres contraseñas de ejemplo usadas al redactar los
  escenarios en Fase 1 no cumplían realmente las 4 reglas (`"Segura#2026"` = 11 caracteres,
  `"Segura2026"` = 10) — detectado al ejecutar los steps, corregido en la misma fase.
- **Propagación a fixtures de tests preexistentes** (Fase 3, no estaba en el plan original con
  este alcance): el cierre del gap rompió ~19 archivos de tests de otros incrementos que
  usaban contraseñas ahora inválidas (`"claveSegura1"`, `"claveNueva123"`, etc.) — corregido
  en la misma US en vez de dejarlo para después, consistente con "no fragmentar en
  mini-ajustes".
- **Stub SMTP en el step_defs nuevo** (Fase 6, no estaba explícito en el plan): los escenarios
  de registro de Estudiante generan una invitación real, que dispara un email — se agregó el
  mismo fixture `fake_smtp_server` ya usado en `test_us_adj_26_steps.py`.

---

## Testing Manual Realizado

No se hizo un recorrido en navegador real dedicado a esta US — verificado con la suite
automatizada completa (unit + integración + BDD backend, unit + integración frontend).
Recomendado un recorrido visual del indicador de fortaleza en conjunto con `US-ADJ-35`
cuando ambos cambios ya estén desplegados juntos.

---

## Deuda Técnica

Ninguna introducida por esta US. Persiste la deuda ya documentada de CodeGuard (vulture/
codespell no instalados, timeout de mypy) — ajena a esta US, ya reportada upstream.

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-37` — Descubribilidad (menú de usuario con "Cambiar contraseña" y "Cerrar
  sesión") — independiente, sin dependencia de esta US. Cierra la Iteración 1 del
  Incremento 5-ADJ.

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 35s |
| BDD (escenarios) | 1370s |
| Plan | 3732s |
| Implementación | 1073s |
| Tests Unitarios | 137s |
| Tests de Integración | 932s |
| Validación BDD | 313s |
| Quality Gates | 352s |
| Documentación | 112s |
| **TOTAL** | **~8610s (~143 min)** |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`). La mayor parte del tiempo (Plan, Implementación,
Integración) correspondió a diagnosticar y corregir el efecto en cascada del cierre del gap
sobre fixtures de tests preexistentes en todo el proyecto, no anticipado en el plan original.

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Relevar el código real de los 2 use cases antes de escribir la spec (Fase 0 del `/pr`
   anterior) permitió detectar el gap de seguridad real en vez de asumir que la invariante ya
   se aplicaba en los 4 puntos documentados.
2. Corregir el efecto en cascada sobre fixtures de tests en la misma US, en vez de abrir un
   ticket aparte, evitó dejar la suite del proyecto en un estado roto entre incrementos.

### Recomendaciones para Próximas Historias

1. Cuando una US amplía una invariante de dominio ya usada en múltiples flujos, relevar de
   entrada cuántos archivos de fixtures usan valores que podrían dejar de cumplirla — el
   impacto en `US-ADJ-36` fue ~19 archivos, mucho más grande que los 8 archivos de producción
   tocados.
2. Escribir las contraseñas de ejemplo del `.feature` verificando manualmente que cumplen
   todas las reglas antes de la aprobación de Fase 1 — tres no cumplían por 1-2 caracteres.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-12.
