# Plan de Implementación: US-ADJ-36 - Contraseña segura — política ampliada

**Patrón:** Clean Architecture BC-first (`entities → use_cases → interface_adapters → frameworks`)
**Producto:** cognion (backend `src/identidad/` + frontend)
**Estado:** ✅ COMPLETADO — 2026-09-12
**Tiempo real (tracker):** ~141 min efectivos (Fases 0 a 8)

## Componentes a Implementar

### 1. Entities — `errors.py` y `usuario.py`
- [x] `src/identidad/entities/errors.py`
  - `PasswordSinComplejidadSuficiente(Exception)` (nueva) — mismo patrón que
    `PasswordDemasiadoCorta` (sin parámetros, mensaje fijo)
  - Actualizar el docstring/mensaje de `PasswordDemasiadoCorta` ("al menos 8" → "al menos 12")
- [x] `src/identidad/entities/usuario.py`
  - `_LARGO_MINIMO_PASSWORD` de `8` a `12`
  - `validar_password_nueva`: agrega chequeo de complejidad (mayúscula, dígito, símbolo no
    alfanumérico) después del chequeo de longitud — `PasswordSinComplejidadSuficiente` si
    falta alguna de las 3 reglas

### 2. Use Cases — cierre del gap real
- [x] `src/identidad/use_cases/crear_usuario.py`
  - Agrega `Usuario.validar_password_nueva(password)` antes de `self._hasher.hash(password)`
- [x] `src/identidad/use_cases/registrar_estudiante.py`
  - Agrega `Usuario.validar_password_nueva(password)` antes de `self._hasher.hash(password)`

### 3. Frameworks — routers (propagar excepciones nuevas)
- [x] `src/identidad/frameworks/api/perfil_router.py` — agrega
  `except PasswordSinComplejidadSuficiente` (mismo status 422 que `PasswordDemasiadoCorta`)
- [x] `src/identidad/frameworks/api/cuentas_router.py` — ídem
- [x] `src/identidad/frameworks/api/usuarios_router.py` — agrega import + ambas excepciones
  de password (nuevo, hoy solo captura `EmailYaRegistrado`)
- [x] `src/identidad/frameworks/api/registro_router.py` — ídem

### 4. Frontend — `PasswordInput` gana indicador de fortaleza
- [x] `frontend/src/components/PasswordInput.tsx` — prop opcional `mostrarFortaleza?: boolean`;
  cuando es `true`, renderiza 3 barras (Débil/Media/Fuerte) + checklist de las 4 reglas
  (longitud ≥12, mayúscula, número, símbolo), calculado sobre el `value` actual
- [x] `frontend/src/pages/identidad/Registro.tsx` — `minLength={12}`, activa
  `mostrarFortaleza` en `registro-password`, hint actualizado
- [x] `frontend/src/pages/identidad/CambiarPassword.tsx` — activa `mostrarFortaleza` en
  `password-nueva` (no en `password-actual`)
- [x] `frontend/src/pages/identidad/AltaDocente.tsx` — `minLength={12}`, activa
  `mostrarFortaleza` en `alta-docente-password`, hint actualizado
- [x] `frontend/src/pages/cuentas/ResetearPassword.tsx` — `minLength={12}` (nuevo), activa
  `mostrarFortaleza` en `password-nueva`, hint actualizado

### 5. Integración
- [x] Actualizar `tests/unit/inc1/test_usuario.py` (`TestUsuarioValidarPasswordNueva`) — los
  4 tests existentes asumen la regla vieja (8 caracteres, sin complejidad); actualizar valores
  de ejemplo para que sigan pasando con las reglas nuevas y agregar casos de complejidad faltante

**Estado:** 14/14 tareas completadas
