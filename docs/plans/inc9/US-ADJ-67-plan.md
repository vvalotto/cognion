# Plan de Implementación: US-ADJ-67 - El Docente genera un link de invitación grupal con vencimiento corto

**Patrón:** clean-architecture-bc · **Producto:** cognion · **BC:** Identidad · **Capas:** `entities`, `use_cases`, `interface_adapters`, `frameworks` y `frontend/`

## Diseño
`Invitacion` pasa a modelar dos clases de link sobre el mismo agregado: la **individual** (un uso, 7 días, sin cambios) y la **grupal** (varios usos hasta que venza o se desactive). Los estados salen del agregado, no del router.

```
Invitacion   grupal: bool · usos: int · revocada_en: datetime | None
   estado(ahora) ──► vigente | vencida | revocada | usada(solo individual)
   verificar_vigente(ahora) lanza InvitacionRevocada / InvitacionVencida / InvitacionYaUsada
   aceptar(ahora): individual marca usada_en · grupal no la marca
   revocar(ahora): idempotente

POST /comisiones/{id}/invitaciones-grupales   {duracion_minutos: 15|60|1440, default 60}
   GenerarInvitacionGrupalUseCase ── repo.reemplazar(anterior_vigente, nueva)   (una sola transacción)
GET  /comisiones/{id}/invitaciones-grupales/ultima        → estado, token (solo vigente), expira_en, usos | null
   ObtenerUltimaInvitacionGrupalUseCase
POST /comisiones/{id}/invitaciones-grupales/{inv_id}/revocar   → 204 (idempotente)
   RevocarInvitacionGrupalUseCase

GET  /invitaciones/{token} y POST /registro  →  detail = {"codigo", "mensaje"}
   invitacion_invalida (404) · invitacion_vencida / invitacion_revocada / invitacion_usada / password_invalida (422)
RegistrarEstudianteUseCase: grupal → repo.incrementar_usos(id)  (UPDATE usos = usos + 1, atómico)
                            individual → aceptar + repo.actualizar (como hoy)
```

- **Contrato de errores:** los status no cambian; el `detail` pasa de texto a objeto. El mapeo error → (status, código) vive en el router (`frameworks`), no en las entidades.
- **Reemplazo en una transacción:** `repo.reemplazar` revoca la anterior y guarda la nueva con un solo `commit`.
- **El individual se conserva en el backend:** `POST /comisiones/{id}/invitaciones` no cambia; solo desaparece de la pantalla.
- **Controllers separados** (CBO, regla del pre-push): el actual sigue con la invitación individual y el preview; uno nuevo reúne las tres operaciones del link grupal.

## Componentes a Implementar

### 1. Entidades (`src/identidad/entities/`)
- [ ] `invitacion.py`: campos `grupal`, `usos`, `revocada_en`; `crear_grupal(comision_id, docente_id, duracion_minutos)` con `DURACIONES_GRUPALES_MINUTOS = (15, 60, 1440)` y por defecto 60; `estado(ahora)`, `revocar(ahora)`; `verificar_vigente` y `aceptar` adaptados; enum `EstadoInvitacion`. Docstring actualizado.
- [ ] `errors.py`: `InvitacionRevocada`, `DuracionInvitacionInvalida`.
- [ ] `eventos.py`: `InvitacionGrupalGenerada`, `InvitacionRevocada` (evento).
- [ ] `ports/invitacion_repository_port.py`: `obtener_por_id`, `obtener_grupal_vigente`, `obtener_ultima_grupal`, `reemplazar`, `incrementar_usos`; `actualizar` también guarda `revocada_en`.

### 2. Casos de uso (`src/identidad/use_cases/`)
- [ ] `generar_invitacion_grupal.py`, `revocar_invitacion_grupal.py`, `obtener_ultima_invitacion_grupal.py` (autorización: Docente asignado a la comisión, `ComisionNoAutorizada`; comisión inexistente, `ComisionNoExiste`).
- [ ] `registrar_estudiante.py`: usa la vigencia ampliada; grupal incrementa `usos`; un rechazo no cuenta como uso.
- [ ] `obtener_invitacion.py`: el preview informa también revocada.

### 3. Persistencia (`interface_adapters/gateways/`, `frameworks/db/`, `migrations/`)
- [ ] `models.py`: `InvitacionModel.grupal` (`server_default false`), `usos` (`server_default 0`), `revocada_en`.
- [ ] `invitacion_repository.py`: los métodos nuevos; `incrementar_usos` con una sola sentencia `UPDATE`.
- [ ] Migración nueva con las tres columnas y `downgrade` que las quita; cumple la guarda de `US-8.3.4`.

### 4. API (`interface_adapters/controllers/`, `frameworks/api/`, `frameworks/dependencies.py`)
- [ ] `invitaciones_grupales_controller.py` y `invitaciones_grupales_router.py` (registrado en `src/app.py`); schemas de request y response en `schemas.py`.
- [ ] `registro_router.py`: `detail` con `codigo` en el preview y el registro; mapeo de errores en un helper del router; `password_invalida` para la contraseña.
- [ ] `dependencies.py`: `get_invitaciones_grupales_controller`.
- [ ] Revisar el `409` del email repetido simultáneo (nota de la spec): si hoy sale un `500`, traducirlo a `EmailYaRegistrado`.

### 5. Frontend (`frontend/src/`)
- [ ] `lib/identidad-comisiones-api.ts`: `generarInvitacionGrupal`, `obtenerUltimaInvitacionGrupal`, `desactivarInvitacionGrupal`.
- [ ] `pages/actividad-evaluativa/ComisionDetalleDocente.tsx`: la tarjeta "Invitación" según el wireframe §3.4 (selector de duración, link con "Copiar", estado, "Desactivar link", leyenda de reemplazo, avisos de vencido y desactivado).
- [ ] `pages/identidad/RegistroError.tsx`: motivo por `?motivo=` con los cuatro textos del wireframe §2.4.
- [ ] `pages/identidad/Registro.tsx`: elige el motivo con `detail.codigo`; `password_invalida` se muestra en el formulario, no como link inválido.

### 6. Sin cambios
`POST /comisiones/{id}/invitaciones`, el autoregistro, `Usuario`, el notificador.

## Tests (Fases 4 a 6)
- **Unitarios (sin base):** `Invitacion` (estados, `crear_grupal`, duraciones, revocar idempotente, `aceptar` grupal e individual), los tres casos de uso nuevos y los modificados con `FakeInvitacionRepository` ampliado en `tests/unit/inc1/_fakes.py`, mapeo de errores.
- **Integración (base descartable inline):** los tres endpoints nuevos, el preview y el registro con códigos, **20 registros simultáneos** contra la base (contador exacto), un solo link vigente, la migración (`upgrade` y `downgrade`).
- **BDD (`tests/step_defs/inc9/test_us_adj_67_steps.py`):** los 13 escenarios aprobados.
- **Frontend (Vitest):** `ComisionDetalleDocente` (estados, generar, copiar, desactivar), `RegistroError` (cuatro motivos), `Registro` (motivo y contraseña en el formulario), cliente de API.
- **Que los tests detectan el error:** con el código anterior deben fallar los escenarios nuevos; el del individual y los de regresión pasan en ambos.
- `tests/uat/inc8/verificar_migraciones.sh` sigue en verde; ajustar los tests existentes que leen `detail` como texto.

## Documentación (Fase 8)
- `ADR-027` (nuevo: invitación grupal; matiza el uso único y los 7 días de `ADR-012`) y una nota en `ADR-012`.
- `docs/design/domain/BC-identidad-modelo.md`: agregado `Invitacion`, enmienda de `INV-ID-01` e `INV-ID-03` y el invariante de vigencia grupal.
- Docstrings de `Invitacion` y de los routers.
