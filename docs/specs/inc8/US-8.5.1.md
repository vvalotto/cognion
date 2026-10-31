# US-8.5.1: Entorno local: `ENTORNO=local` con secreto fuerte para uso en red

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.5`
**Tipo**: `infra backend` (técnica — sin comando de negocio)
**Bounded Context**: transversal (`src/settings.py`)
**Issue**: #536

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **un modo de configuración pensado para correr el sistema en mi máquina y exponerlo a la red del aula**,
para **no usar el modo desarrollo (sin ninguna validación) cuando alumnos reales se conectan, ni el modo producción (que rechaza todo lo local)**.

---

## Contexto

`US-8.1.3` creó `ENTORNO` con `desarrollo` (sin validación) y `staging`/`produccion` (rechazan `localhost`, SMTP local,
etc.). Para una prueba con alumnos en la red local ninguno sirve: `desarrollo` permitiría arrancar con la `SECRET_KEY`
de ejemplo, que firma sesiones válidas para cualquiera que la conozca (está en el repositorio), y `produccion` rechaza
una base en `localhost`. El riesgo real es exponer a la red un servidor con un secreto público.

## Especificacion del comportamiento

- `Settings.entorno` admite un cuarto valor: `local`.
- En `local` se valida **solo** el secreto: `SECRET_KEY` de al menos 32 caracteres y distinta del valor de ejemplo
  (mismo criterio y mismo mensaje que en staging/producción; nunca imprime el valor).
- En `local` se permite `localhost`/IP en base de datos, SMTP, `FRONTEND_URL` y CORS.
- `desarrollo`, `staging` y `produccion` no cambian.
- `.env.example` documenta el valor y para qué sirve.

## Escenarios (BDD)

1. `ENTORNO=local` con `SECRET_KEY` de 40 caracteres y base en `localhost` → arranca.
2. `ENTORNO=local` con el secreto de ejemplo → falla nombrando `SECRET_KEY`, sin imprimir el valor.
3. `ENTORNO=local` con secreto corto → falla.
4. `ENTORNO=desarrollo` con el secreto de ejemplo → arranca (sin cambios).
5. `ENTORNO=produccion` sigue rechazando `localhost` (sin cambios).

## Fuera de alcance

Generar el secreto (`US-8.5.3`); canal de email (`US-8.5.2`).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
