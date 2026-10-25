# Guion de UAT — versión local `v0.9.0`

**Incremento:** 8, Iteración 7 · **Baseline prevista:** `BL-013` · **Procedimiento:** `docs/plans/PROCEDIMIENTO-UAT.md` §11
**Ejecuta:** Víctor, en su Mac (y un iPhone o iPad para la sesión en vivo) · **Escribe el registro:** la sesión de Claude Code, narrado en vivo
**Código bajo prueba:** `develop` en `d43007b` (lo mismo que se etiquetará como `v0.9.0` si la UAT sale bien)

---

## 1. Para qué sirve y cuándo se aprueba

Es la primera vez que el sistema se instala **como lo va a usar un docente**: un solo comando, el frontend ya compilado, un
solo puerto, sin servidor de desarrollo. Por eso esta UAT no repite el recorrido funcional completo de
`quality/reports/uat/inc7/plan-de-pruebas.md` (30 pasos, ya ejecutados): prueba **la instalación, la siembra de datos y la
operación local**, y hace un recorrido funcional corto con los cuatro roles para confirmar que nada se rompió al
empaquetar.

**Se etiqueta `v0.9.0` si no queda ningún hallazgo 🔴 (bloqueante).** Los 🟡 y ⚪ se registran y se priorizan después
(`PROCEDIMIENTO-UAT.md` §8). Un 🔴 se corrige antes de etiquetar: la etiqueta tiene que ser la versión que viste funcionar.

**Fuera de alcance:** carga con muchos alumnos a la vez, red del aula, nube (GCP/Fly.io), RF-07 y RF-18, y US-ADJ-63.

---

## 2. Entorno aislado (no toca `cognion_local` ni la base de desarrollo)

`levantar.sh` acepta variables para usar otra base y otro archivo de configuración. La UAT usa **`cognion_uat`**: queda
como una instalación limpia y tu `cognion_local` (con lo que ya tengas) no se modifica.

```bash
export COGNION_LOCAL_BASE=cognion_uat COGNION_LOCAL_ENV=.env.uat COGNION_LOCAL_LOGS=logs/uat
```

- Hay que **exportar las tres variables en cada terminal** que se use durante la UAT (`levantar.sh`, `detener.sh`,
  `respaldar.sh`, `restaurar.sh` y el comando de carga leen `.env.uat`).
- `.env.uat` queda fuera de git (agregado a `.gitignore`).
- El puerto es el 8000: si hay otro servidor ahí, `levantar.sh` avisa y se detiene (`scripts/local/detener.sh` primero).
- No hace falta correr `pytest` y no hay que hacerlo con `DATABASE_URL` apuntando a `cognion_uat`.

**Antes de empezar**
1. `git checkout develop && git pull --ff-only` y confirmar `git log --oneline -1` = `d43007b` o posterior.
2. Armar la carpeta de datos con **solo** los cuestionarios (nada más):
   ```bash
   mkdir -p ~/CognionDatos && cp tests/uat/datos-reales/*" - Cuestionario.md" ~/CognionDatos/ && ls ~/CognionDatos | wc -l   # 17
   ```
3. Tener a mano un iPhone o iPad en la misma wifi.

---

## 3. Recorrido

Marcar cada paso con ✅ / ❌ en `registro-ejecuciones.md`. Ante un ❌, detenerse y registrarlo en `registro-hallazgos.md`
antes de seguir.

### Bloque A — Instalación limpia (`US-8.5.3`, `US-8.1.x`)

| # | Paso | Resultado esperado |
|---|---|---|
| A1 | Con las variables exportadas: `scripts/local/levantar.sh --fondo` | Prerrequisitos verificados, base `cognion_uat` creada, `.env.uat` creado (permisos 600), frontend compilado, migraciones aplicadas |
| A2 | Ingresar nombre, email y contraseña del Administrador cuando los pide | Se crea el Administrador; la contraseña rechazada si no cumple (12+ caracteres, mayúscula, número, símbolo) |
| A3 | Leer lo que imprime el script | Imprime las URLs `http://<ip>:8000/` y `http://<equipo>.local:8000/` y el aviso de que los emails no se envían |
| A4 | `curl -s http://127.0.0.1:8000/api/health` | Responde ok |
| A5 | Abrir `http://127.0.0.1:8000/` en el navegador, **sin sesión** | Redirige a `/login` (sin pantalla en blanco) |
| A6 | Login como Administrador | Llega a su portada con el menú persistente |
| A7 | Repetir `scripts/local/levantar.sh --fondo` con el servidor ya corriendo | Avisa que el puerto está en uso; no pisa nada |

### Bloque B — Siembra de materias y preguntas (`US-8.7.1`)

| # | Paso | Resultado esperado |
|---|---|---|
| B1 | `.venv/bin/python -m src.banco_preguntas.frameworks.cli.cargar_datos_iniciales ~/CognionDatos` (sin `--materia`) | Error claro: pide `--materia`; salida distinta de cero; no escribe nada |
| B2 | Mismo comando con `--materia "Gestión de Proyectos" --simular` (cargando antes `set -a; . ./.env.uat; set +a`) | 17 archivos bien, 0 con error, `[simulación]`; la base no cambia |
| B3 | Mismo comando sin `--simular` | 17 archivos, 340 cargadas, 0 omitidas; materia marcada `(nueva)` en el primer archivo |
| B4 | Repetir B3 | 0 cargadas y 20 omitidas por archivo; salida 0 |
| B5 | En la aplicación (Administrador → Materias) | Aparece "Gestión de Proyectos" |
| B6 | Como Docente asignado (después de C3), abrir el banco de la materia | 340 preguntas, paginadas de a 20; filtros por unidad (10), tema (17), dificultad e importancia funcionan; la dificultad e importancia coinciden con el `Nivel` de los archivos |
| B7 | Abrir una pregunta de un cuestionario y compararla con el `.md` de origen | Enunciado, opciones y respuesta correcta idénticos |
| B8 | Poner una carpeta con un archivo roto (copiar un `.md` y borrarle la línea `Unidad temática`) y cargarla | Ese archivo da error con la pregunta o línea; los demás no se afectan; salida distinta de cero |

### Bloque C — Alta de actores desde la aplicación (RF-01, RF-03, RF-25)

Usar cuentas de prueba propias (emails inventados), no cuentas de alumnos reales.

| # | Paso | Resultado esperado |
|---|---|---|
| C1 | Administrador: crear una Comisión de "Gestión de Proyectos" | Queda en el listado de la materia |
| C2 | Administrador: dar de alta un Docente (Cuentas) | La cuenta queda activa |
| C3 | Administrador: asignar ese Docente a la Comisión | Aparece asignado; la alerta de "sin Docente" desaparece |
| C4 | Docente: generar el link de invitación de la Comisión y copiarlo | Link con token; el email no sale, **el link queda en el log** (`logs/uat/uvicorn-<fecha>.log`) |
| C5 | Estudiante 1: abrir el link (vista previa sin login) y registrarse | Ve materia y comisión antes de registrarse; queda inscripto |
| C6 | Estudiante 2: autoregistro eligiendo Materia → Comisión | Cuenta creada e inscripta |
| C7 | Recuperación de contraseña de un Estudiante | El link llega **al log**, no por email; permite definir contraseña nueva |

### Bloque D — Recorrido funcional corto (los 4 roles sobre lo recién instalado)

| # | Paso | Resultado esperado |
|---|---|---|
| D1 | Docente: crear una actividad de período abierto con unidad/tema y asignarla a la Comisión | Visible en el listado; el aviso de apertura queda **en el log** (RF-14) |
| D2 | Estudiante: rendir la actividad — responder, pausar, reanudar desde otra pestaña, finalizar, ver la revisión | Sin pérdida de respuestas; la revisión numera desde 1 |
| D3 | Docente: ver Reportes (desempeño por alumno, por tema, ranking de falladas) | Muestran la actividad rendida |
| D4 | Docente: crear una sesión en vivo desde el detalle de la Comisión | Sala de espera |
| D5 | Estudiante en el **iPhone/iPad** (`http://<ip>:8000/`): unirse, responder con las tarjetas | Feedback inmediato; el celular reconecta si se apaga y enciende la pantalla |
| D6 | Docente: proyectar → mostrar opciones → cerrar → avanzar → finalizar | Histograma, ranking Top 3 y podio |
| D7 | RBAC: con la sesión del Estudiante, escribir en la barra la URL de Cuentas o de Materias | Bloqueado, no muestra datos |
| D8 | Estudiante: "Mi desempeño" | Incluye lo rendido en período abierto y en vivo |

### Bloque E — Operación local (`US-8.5.3`, `US-8.5.4`)

| # | Paso | Resultado esperado |
|---|---|---|
| E1 | `scripts/local/respaldar.sh` | Archivo en `~/CognionRespaldos/` con su `sha256`; avisa si algo falla |
| E2 | `scripts/local/detener.sh` | El servidor se detiene; el puerto queda libre |
| E3 | `scripts/local/levantar.sh --fondo` otra vez | **No** pide Administrador ni pisa `.env.uat`; arranca; los datos siguen (340 preguntas, cuentas, actividad) |
| E4 | Login con las mismas cuentas | Funciona |
| E5 | `scripts/local/restaurar.sh <archivo del E1>` (ensayo) | Restaura en una base temporal, compara conteos y la borra; avisa si difieren |
| E6 | (Opcional) borrar una pregunta, detener, `restaurar.sh <archivo> --sobre-local` (escribir `RESTAURAR`), levantar | La pregunta borrada vuelve. **Solo sobre `cognion_uat`.** |
| E7 | Mirar `logs/uat/uvicorn-<fecha>.log` | Legible; sin contraseñas ni tokens de sesión |

### Bloque F — Observaciones sin criterio de aprobación

Anotar lo que se vea, sin bloquear: tiempo desde `levantar.sh` hasta tener la pantalla de login; si la Mac se duerme con la
tapa cerrada durante una sesión en vivo (`caffeinate`); aviso del firewall de macOS; si el acceso por `<equipo>.local`
funciona además de la IP; consumo de memoria del equipo con el servidor y el navegador abiertos.

---

## 4. Cierre

1. Registrar todos los hallazgos en `registro-hallazgos.md` con severidad (🔴/🟡/⚪).
2. Si no hay 🔴: Víctor confirma, se cierra `BL-013`, merge `develop → main` y etiqueta `v0.9.0` (la imagen se publica en
   GHCR y se borra la versión de prueba del paquete).
3. Si hay 🔴: se clasifica el track (informal o `US-ADJ`), se corrige, y se repiten **solo** los pasos afectados.
4. Limpieza: `scripts/local/detener.sh` y, si ya no hace falta, `DROP DATABASE cognion_uat` (lo hace Víctor).
