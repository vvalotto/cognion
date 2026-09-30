# Plan de Implementación: US-ADJ-35 - Toggle mostrar/ocultar contraseña

**Patrón:** Frontend puro — sin capas de Clean Architecture (no aplica `entities/use_cases/
interface_adapters/frameworks`)
**Producto:** cognion (frontend)
**Estado:** ✅ COMPLETADO — 2026-09-12
**Tiempo real (tracker):** ~24 min efectivos (Fases 0 a 8)

## Componentes a Implementar

### 1. Componente compartido `PasswordInput`
- [x] `frontend/src/components/PasswordInput.tsx` (nuevo)
  - Envuelve `Input` (`@/components/ui/input`) agregando un botón de toggle posicionado
    dentro del campo (íconos `Eye`/`EyeOff` de `lucide-react`)
  - Props: mismas que `Input` vía spread (`id`, `value`, `onChange`, `minLength`, etc.) — sin
    prop propio obligatorio, el estado de visibilidad es interno (`useState`)
  - `data-slot="password-input"` en el wrapper, mismo criterio de `data-slot` que ya usa
    `Input`

### 2. Integración — reemplazo en los 5 formularios existentes
- [x] `frontend/src/pages/identidad/Login.tsx` — reemplaza `login-password`
- [x] `frontend/src/pages/identidad/Registro.tsx` — reemplaza `registro-password` y
  `registro-confirmar-password`
- [x] `frontend/src/pages/identidad/CambiarPassword.tsx` — reemplaza `password-actual`,
  `password-nueva` y `password-confirmacion`
- [x] `frontend/src/pages/identidad/AltaDocente.tsx` — reemplaza `alta-docente-password` y
  `alta-docente-confirmar-password`
- [x] `frontend/src/pages/cuentas/ResetearPassword.tsx` — reemplaza `password-nueva` y
  `password-confirmacion`

Cada reemplazo es: cambiar `<Input type="password" .../>` por `<PasswordInput .../>` (mismos
props) e importar `PasswordInput` en vez de (o además de) `Input` — sin tocar ningún otro
elemento del formulario (labels, validación, handlers `onChange`, `minLength`).

**Estado:** 6/6 tareas completadas
