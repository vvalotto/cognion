# Despliegue local — instalar y operar Cognión en tu Mac

> Estado documental: operativo
> Alcance: correr el sistema completo en una sola máquina y exponerlo a la red local (por ejemplo, el aula).
> Origen: `US-8.5.1` a `US-8.5.4` (Incremento 8, Iteración 5). Reemplaza para este caso el alcance "solo desarrollo"
> de `docs/plans/CHECKLIST-INSTALACION.md`.
> Última actualización: 2026-10-18

---

## 1. Qué es y qué no es

Un único proceso (`uvicorn`) sirve la interfaz y la API desde el mismo origen (`http://<ip>:8000/`), contra una
base PostgreSQL **propia** (`cognion_local`), separada de la de desarrollo. Todo se maneja con scripts de
`scripts/local/`.

**No cubre:**
- HTTPS/TLS: el acceso es HTTP/WS dentro de la red local.
- Alta disponibilidad: si la máquina o el servidor se caen, el sistema se cae.
- Acceso desde fuera de la red local (internet).
- Envío real de emails: `EMAIL_MODO=consola` deja el contenido en el log (ver sección 7).
- Docker: no se usa en este modo.
- Subir respaldos a Drive o a la nube.

---

## 2. Marca de estado de cada paso

Cada paso dice si fue **probado** o está **sin probar**. Lo sin probar figura en la sección 11.

---

## 3. Prerrequisitos

| Herramienta | Para qué | Cómo comprobar |
|---|---|---|
| PostgreSQL 14+ corriendo | base `cognion_local` | `pg_isready` |
| Herramientas cliente de PostgreSQL | `psql`, `pg_dump`, `pg_restore` | `psql --version` |
| Un rol con `CREATEDB` | crear la base | en Mac suele alcanzar tu usuario; si no, `PGADMIN_USER=<rol>` |
| `uv` y la `.venv` del proyecto | backend | `uv sync` crea `.venv` |
| Node.js + npm | compilar el frontend | `node --version` |
| `.env` en la raíz con `DATABASE_URL` | solo se toma de ahí usuario, clave y host de PostgreSQL | copiar de `.env.example` |
| `openssl`, `curl`, `caffeinate` | secreto, comprobaciones, evitar suspensión | vienen con macOS |

Instalar PostgreSQL con Homebrew: `brew install postgresql@16 && brew services start postgresql@16`.

---

## 4. Primera vez (estado: probado, también sobre `cognion_local` real el 2026-10-18)

Desde la raíz del repositorio, sobre la branch que contiene los scripts:

```bash
scripts/local/levantar.sh
```

Qué hace, en orden:
1. Verifica prerrequisitos; si falta algo, dice qué y cómo resolverlo (sin trazas).
2. Crea la base `cognion_local` y el archivo `.env.local` (fuera de git, permisos 600) con `ENTORNO=local`,
   `EMAIL_MODO=consola` y un `SECRET_KEY` aleatorio. **Nunca usa la base de desarrollo.**
3. Compila el frontend si falta o está viejo.
4. Aplica las migraciones.
5. Si no hay un Administrador operativo, **te pide por terminal** nombre, email y contraseña
   (12 o más caracteres, con mayúscula, número y símbolo). **La contraseña se escribe dos veces** (no se ve al
   teclearla): si no coinciden te avisa y vuelve a pedirla, hasta 3 intentos; al tercero no crea nada.
6. Detecta la IP y el nombre `<equipo>.local` e **imprime las URLs que deben usar los alumnos**.
7. Arranca el servidor en `0.0.0.0:8000` bajo `caffeinate -dims` y deja el log en
   `logs/local/uvicorn-<fecha>.log`.

Para dejarlo corriendo en segundo plano: `scripts/local/levantar.sh --fondo`.
Volver a ejecutarlo es seguro: no pisa `.env.local` ni el Administrador.

### Si me pedís que lo instale
Puedo correr los pasos y revisar el resultado, pero **la contraseña del Administrador la escribís vos** en la
terminal (no la ingreso yo). Conviene que la corrida sea en una terminal tuya, no en segundo plano.

---

## 4b. Cargar tus materias y preguntas (estado: probado sobre una base descartable con los 17 cuestionarios reales; sin probar sobre `cognion_local`)

Después de `levantar.sh` la base solo tiene el Administrador. Las materias y preguntas se cargan con un comando
(`US-8.7.1`) desde archivos que **no se versionan**: guardalos en una carpeta tuya, por ejemplo `~/CognionDatos/`
(la carpeta debe tener solo los archivos a cargar: el comando procesa **todos** los `*.json` y los
`* - Cuestionario.md` que encuentre y marca como error los que no tienen el formato).

```bash
set -a; . ./.env.local; set +a        # usa la base cognion_local
.venv/bin/python -m src.banco_preguntas.frameworks.cli.cargar_datos_iniciales ~/CognionDatos --materia "Gestión de Proyectos" --simular
.venv/bin/python -m src.banco_preguntas.frameworks.cli.cargar_datos_iniciales ~/CognionDatos --materia "Gestión de Proyectos"
```

Primero con `--simular` (valida todo y no escribe); después sin él. Es **idempotente**: volver a correrlo omite las
preguntas cuyo texto ya está activo en el banco. Un archivo con una pregunta inválida no carga nada de ese archivo
y el resto sigue; la salida es distinta de cero si alguno falló. Se puede hacer con la aplicación levantada o detenida.

**Formatos aceptados**
- **Markdown** (cuestionarios de opción múltiple, un archivo por tema, `<Tema> - Cuestionario.md`): `--materia` es
  obligatorio. La unidad temática sale de la línea `**Unidad temática:**`, el tema del nombre del archivo, la
  dificultad de `*(Nivel: Fácil|Medio|Difícil)*` (bajo, medio, alto) y la importancia se deriva de la dificultad
  (se puede ajustar después desde la pantalla).
- **JSON** (opción múltiple y verdadero/falso, una materia por archivo; la materia va adentro): ejemplo en
  `docs/plans/ejemplos/datos-iniciales.ejemplo.json`.

Si la materia ya existe (por ejemplo, creada desde la pantalla) se reutiliza. No carga estudiantes, comisiones ni
docentes: eso se hace desde la aplicación.

---

## 5. Parar y retomar (estado: probado)

```bash
scripts/local/detener.sh      # solo para el servidor lanzado con --fondo
```

En primer plano se detiene con `Ctrl+C`. Para retomar: volver a ejecutar `scripts/local/levantar.sh`.
Los datos están en la base, no en el proceso: reiniciar no pierde nada.

---

## 6. Respaldo y restauración (estado: probado con una base descartable)

```bash
scripts/local/respaldar.sh                      # antes y después de cada clase
scripts/local/restaurar.sh <archivo.dump>       # ENSAYO: restaura en una base temporal y compara conteos
scripts/local/restaurar.sh <archivo.dump> --sobre-local   # reemplaza cognion_local (pide escribir RESTAURAR)
```

- El archivo lleva el nombre de la base respaldada (`<base>-<fecha>.dump`, con la base por defecto `cognion_local-<fecha>.dump`):
  si usás dos bases en la misma Mac (por ejemplo una de prueba con `COGNION_LOCAL_BASE`), sus respaldos no se mezclan y la
  rotación de cada una no toca los de la otra. Los respaldos anteriores a `v0.9.0` se llaman siempre `cognion_local-…`.
- Los respaldos van a `~/CognionRespaldos/` (cambiable con `COGNION_RESPALDOS`), con `sha256`; se conservan los
  últimos 30 (`COGNION_RESPALDOS_N`).
- Reemplazar la base exige **detener el servidor** antes.
- Conviene hacer el ensayo de restauración al menos una vez: un respaldo que nunca se restauró no es un respaldo.
- Los respaldos contienen datos de estudiantes: la carpeta queda con permisos 700 y fuera de git.

---

## 7. Emails: modo consola (estado: probado con un `uvicorn` real el 2026-10-26, `US-ADJ-64`)

No hay servidor de correo. El contenido de cada email (invitaciones, recuperación de contraseña, notificaciones de
actividad) se escribe en el log del servidor:

```bash
grep -A8 "Email (modo consola)" logs/local/uvicorn-$(date +%F).log
```

- **Recuperar contraseña:** el email trae el link `/recuperar-password/<token>`; copialo y abrilo en el navegador.
- **Invitación por email:** el cuerpo trae el **token suelto** ("Token de invitación: …"), no un link. Para registrar al
  estudiante usá `<dirección de la aplicación>/registro?token=<token>`, o generá el link desde la pantalla de la Comisión
  (botón "Generar link de invitación", que ya lo muestra completo).
- **Aviso de apertura/cierre de actividad:** un email por estudiante de la Comisión.

**Antes de `US-ADJ-64` esto no funcionaba** con `levantar.sh`: la aplicación no configuraba el logging y `uvicorn` descartaba
los mensajes de la aplicación (hallazgo #2 de la UAT de `v0.9.0`).

**Los tokens de las URLs no quedan completos en el log de acceso:** el JWT del canal en vivo, el token de una invitación
(`/registro?token=…`) y el del link de recuperación se registran como `***`. El cuerpo de los emails de consola **sí** los
trae completos: es lo que permite recuperar una cuenta sin correo. Por eso el log sigue siendo sensible: no lo compartas.
`LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING`, `ERROR`; por defecto `INFO`) ajusta el detalle de los mensajes de la aplicación.

---

## 8. Red del aula (estado: probado desde un celular en la misma wifi el 2026-10-18; sin probar en la red del aula)

- **Misma red:** los celulares deben estar en la misma red que la Mac. La red wifi institucional puede **aislar a los
  clientes entre sí** (los dispositivos no se ven). Alternativas: hotspot del celular, o un router propio.
- **Detectar el aislamiento:** desde un celular conectado a esa red, abrir `http://<ip>:8000/api/health`. Si no
  responde pero la Mac sí responde a sí misma, es el aislamiento o el firewall.
- **Firewall de macOS:** la primera vez puede preguntar si Python acepta conexiones entrantes; hay que permitirlo
  (Ajustes del Sistema → Red → Firewall).
- **La IP cambia:** usar el nombre `http://<equipo>.local:8000/` que imprime el script, o reservar la IP en el router.
- **Links de invitación:** el link que genera la pantalla de la Comisión usa **la dirección con la que abriste la
  aplicación**. Si la abrís por `http://127.0.0.1:8000/`, el link dice `127.0.0.1` y **no funciona en el celular de un
  alumno**. Antes de generar links, entrá por la IP o por el nombre `<equipo>.local` que imprime el script.
- **VPN o antivirus en el celular:** una VPN de dispositivo o un filtro de seguridad (por ejemplo **Norton Mobile
  Security** en un iPhone) puede impedir que el celular abra el canal en tiempo real de la sesión en vivo: las opciones
  de cada pregunta tardan varios segundos en aparecer, y en el log se ven rechazos `403` a `WebSocket ws%3A//…`. Se
  comprobó el 2026-10-31: con la VPN de Norton desactivada la respuesta es inmediata (1 a 5 s entre opciones y
  respuesta, 0 rechazos). Si un alumno ve ese retraso, pedile que desactive la VPN o el filtro para esta red
  (en Norton, desde su propia app: desde Ajustes → VPN se reconecta sola).
- **Suspensión:** `caffeinate -dims` evita que se duerma mientras el servidor corre. Con la tapa cerrada o con batería
  baja la Mac puede dormirse igual: dejala enchufada y con la tapa abierta durante la clase.

---

## 9. Diagnóstico rápido (estado: probado)

| Qué | Cómo |
|---|---|
| ¿Responde? | `curl http://127.0.0.1:8000/api/health` |
| ¿Responde por la red? | `curl http://<ip>:8000/api/health` (y lo mismo desde otro dispositivo) |
| Ver el log | `tail -f logs/local/uvicorn-$(date +%F).log` |
| ¿Quién escucha el puerto? | `lsof -nP -iTCP:8000 -sTCP:LISTEN` |
| ¿Postgres vive? | `pg_isready` |
| Puerto ocupado al arrancar | `scripts/local/detener.sh` o cambiar el puerto con `COGNION_LOCAL_PUERTO` |
| Un celular ve las opciones de la sesión en vivo con segundos de retraso | Mirar el log: rechazos `403` a `WebSocket` de la IP de ese celular indican una VPN o un filtro de seguridad en el celular (sección 8) |
| ¿Salieron los emails (recuperar contraseña, invitaciones, avisos)? | `grep -A8 "Email (modo consola)" logs/local/uvicorn-$(date +%F).log` (sección 7) |

---

## 10. Datos y privacidad

Los datos de los alumnos (cuentas, respuestas, sesiones) quedan **en esta máquina** y en los respaldos de
`~/CognionRespaldos/`. Decidir con la facultad si la prueba usa cuentas reales o de prueba y qué avisar a los alumnos:
**es una decisión institucional, no técnica**.

---

## 11. Lo que todavía no está comprobado

Comprobado el 2026-10-18: la primera corrida de `levantar.sh` sobre `cognion_local` real (Administrador creado por
terminal, login, autoregistro de Docente) y el acceso desde un celular en la misma wifi (el log mostró otra IP
de origen distinta de la de la Mac).

Falta:
- Probar en la **red del aula** (puede aislar clientes; ver sección 8).
- El comportamiento con la tapa cerrada.
- Cuántos alumnos conectados a la vez soporta esta máquina.
- El aviso del firewall de macOS: en esta Mac no hizo falta ninguna acción, pero puede variar según su configuración.

Al comprobar cada uno, actualizar la marca de estado de su sección.
