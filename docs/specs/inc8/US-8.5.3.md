# US-8.5.3: Comando único para levantar y detener el despliegue local

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.5`
**Tipo**: `tooling operativo` (scripts, sin código de producción nuevo salvo configuración)
**Bounded Context**: transversal (`scripts/local/`)
**Issue**: #538

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba con alumnos**,
quiero **arrancar el sistema completo con un solo comando y saber a qué dirección deben entrar los alumnos**,
para **no depender de recordar una secuencia de pasos antes de una clase**.

---

## Contexto

Hoy levantar el sistema exige varios pasos manuales (base de datos, migraciones, compilar el frontend, crear el
Administrador, arrancar `uvicorn`). Para una clase con alumnos conectados por la red local hace falta además
escuchar en todas las interfaces, conocer la IP, evitar que la máquina se duerma y dejar logs para revisar después.
El servidor ya sirve la interfaz y la API desde un único origen (`US-8.1.6`), así que no hay CORS ni segundo puerto.

## Especificacion del comportamiento

`scripts/local/levantar.sh` (idempotente; volver a ejecutarlo reutiliza lo ya creado):

1. Verifica prerrequisitos (Postgres respondiendo, `.venv`, `node`/`npm`) y, si falta algo, dice qué y cómo resolverlo.
2. Primera vez: crea `.env.local` (**fuera de git**, agregado a `.gitignore`) con `ENTORNO=local`, `EMAIL_MODO=consola`,
   `SECRET_KEY` aleatoria (`openssl rand -hex 32`) y `DATABASE_URL` hacia una base **propia** `cognion_local`
   — nunca la base de desarrollo `cognion`.
3. Compila el frontend con `VITE_API_BASE_URL=/api` si `frontend/dist` falta o es más viejo que `frontend/src`.
4. Aplica las migraciones (`alembic upgrade head`).
5. Si no existe un Administrador operativo, ejecuta el bootstrap (`US-8.1.5`); la contraseña se pide por terminal sin eco.
6. Detecta la IP de la red local y el nombre `<equipo>.local`, fija `FRONTEND_URL=http://<ip>:8000` y **imprime** las URLs
   que deben usar los alumnos, junto con un recordatorio de las pruebas de red.
7. Arranca `uvicorn src.servidor:servidor --host 0.0.0.0 --port 8000` bajo `caffeinate -dims` (la máquina no se duerme
   mientras corre) y envía el log a `logs/local/uvicorn-<fecha>.log` (carpeta fuera de git) además de la terminal.

`scripts/local/detener.sh` detiene el servidor si se lo dejó en segundo plano (`levantar.sh --fondo`, guarda el PID).

## Escenarios (BDD)

1. Máquina sin `.env.local` ni base `cognion_local` → tras `levantar.sh` quedan creados, el sistema responde en
   `http://<ip>:8000/` y `http://<ip>:8000/api/health`, y el login del Administrador creado funciona.
2. Segunda ejecución → no pisa `.env.local` ni el Administrador y arranca sin errores.
3. Postgres apagado → mensaje claro y salida con código ≠ 0, sin traza.
4. La base de desarrollo `cognion` no se modifica en ningún momento.
5. Desde otro dispositivo de la misma red (o, en su defecto, usando la IP local desde esta misma máquina) la interfaz
   carga y el login contra `/api` funciona.

## Fuera de alcance

Docker (`US-8.5.5`); backup (`US-8.5.4`); guía (`US-8.5.6`); TLS (el acceso es HTTP/WS dentro de la red del aula).

## Fuente de verdad UX

No aplica — sin cambios visuales.
