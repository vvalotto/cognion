# US-ADJ-65: El comando que crea el Administrador pide la contraseña dos veces

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 8 — Despliegue y operación`, Iteración 8 (ajustes de la UAT de `v0.9.0`)
**Tipo**: `mejora de usabilidad` backend (comando operativo)
**Agregado principal afectado**: ninguno
**Bounded Context**: Identidad
**Origen**: UAT `US-8.7.2`, hallazgo #3 (`quality/reports/uat/inc8/registro-hallazgos.md`).
**Issue**: [#571](https://github.com/vvalotto/cognion/issues/571)
**Interactúa con**: `US-8.1.5` (`bootstrap_administrador`), `ADR-016`, `scripts/local/levantar.sh` (lo invoca).

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **persona que instala Cognión y crea el primer Administrador por terminal**,
quiero **escribir la contraseña dos veces y que el comando me avise si no coinciden**,
para **no quedar fuera del sistema por un error de tipeo que no veo, porque la contraseña no se muestra al escribirla**.

---

## Contexto

`python -m src.identidad.frameworks.cli.bootstrap_administrador` pide la contraseña **una sola vez y sin eco** (`getpass`). Un error de
tipeo crea un Administrador con una contraseña desconocida, sin ninguna advertencia. En la UAT de `v0.9.0` pasó exactamente eso: el login
falló con dos intentos, y la única salida fue resetear la contraseña directamente en la base. Con la recuperación por email todavía
dependiente del log (`US-ADJ-64`), no hay otro camino de recuperación para el primer Administrador.

## Especificacion del comportamiento

- Cuando la contraseña se pide por terminal, el comando la pide **dos veces** ("Contraseña del Administrador:" y "Repetí la contraseña:").
- Si no coinciden, lo dice ("Las contraseñas no coinciden.") y vuelve a pedirlas, **hasta 3 intentos**. Al tercer fallo termina con código `1` **sin crear nada**.
- Las reglas de la contraseña (`INV-ID-11`: 12 o más caracteres, mayúscula, número y símbolo) se validan sobre la que coincide, con los mensajes de siempre.
- Si `ADMIN_PASSWORD` está definida en el entorno, **no se pide nada** (comportamiento actual, para uso no interactivo).
- Sin terminal interactiva ni `ADMIN_PASSWORD`, sigue el mensaje y el código `2` actuales.
- El resto del comando (nombre, email, "ya existe un Administrador", códigos de salida) no cambia.

## Escenarios (BDD)

1. **Coinciden.** Terminal interactiva, las dos entradas iguales y válidas → se crea el Administrador, código `0`.
2. **No coinciden y luego sí.** Primera vez distintas, segunda vez iguales → mensaje de no coincidencia, se crea, código `0`.
3. **No coinciden tres veces.** → código `1`, no se crea ningún usuario, mensaje claro.
4. **Coinciden pero no cumplen las reglas.** → mensaje de contraseña rechazada de siempre, código `1`.
5. **`ADMIN_PASSWORD` definida.** → no pide nada, crea, código `0` (sin regresión).
6. **Sin terminal y sin variable.** → el mensaje y el código `2` actuales.
7. **Ya existe un Administrador operativo.** → no pide la contraseña (o termina antes de pedirla) y mantiene el mensaje y el código `0` actuales.

## Fuera de alcance

Recuperación del primer Administrador cuando se olvida la contraseña; mostrar la contraseña en pantalla; cambios en `levantar.sh` más allá de que el comando que invoca ya pide la confirmación.

## Notas para `/implement-us`

- La confirmación vive en el comando (capa `frameworks/cli`), no en el caso de uso: el dominio no sabe de terminales.
- Si el caso 7 requiere reordenar para no pedir la contraseña antes de saber que ya hay un Administrador, es parte de esta US.
