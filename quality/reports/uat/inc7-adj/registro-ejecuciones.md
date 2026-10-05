# Registro de ejecuciones — UAT de cierre del Incremento 7-ADJ

Bitácora de lo ejecutado, en orden. Plan: `plan-de-pruebas.md`. Hallazgos: `registro-hallazgos.md`.
Ejecutor: Víctor (decisión y supervisión) · Conductor y escritor: sesión de Claude Code.
Navegador usado: **navegador integrado de Claude Desktop (Chromium)**, no el navegador propio de Víctor.

## 2026-10-05 — Bloque 0: preparación del entorno

| Paso | Qué se hizo | Resultado |
|---|---|---|
| 0.0 | Estado inicial de la base `cognion`: 0 usuarios, 1 materia ("Materia - UAT7"), 3 preguntas, 42 eventos huérfanos (restos de la UAT v1), migración en `a6c2d4f8b1e3` | Se hizo `pg_dump` antes de tocar nada (respaldo en el scratchpad de la sesión) |
| 0.1 | `alembic upgrade head` | `c4d1f9a27b60` (`usuario.bloqueada_hasta`) aplicada — **sin ella `US-ADJ-60` no funcionaba en esta base** |
| 0.2 | `DELETE FROM events` (42 eventos huérfanos de la UAT v1, sin usuarios asociados; ya rompieron consultas de Analytics antes) y `tests/uat/datos-reales/sembrar.py` | 20 usuarios (1 Administrador, 2 Docentes, 17 Estudiantes), 3 materias, 1 comisión, 110 preguntas, 85 eventos. Login del Administrador `200` |
| 0.3 | Backend (`:8000`) y frontend dev (`:5173`) levantados con `preview_start` | `/docs` `200` |

Cuentas de la siembra: `admin@fiuner.edu.ar`, `victor.valotto@fiuner.edu.ar` (Docente Ing. de Software), `alejandra.morales@fiuner.edu.ar` (Docente Gestión de Proyectos); contraseñas en `tests/uat/datos-reales/usuarios.md` (fuera de git). Estudiantes: contraseña única de la siembra.

## 2026-10-05 — Bloque 1: spike del hallazgo #1 (autoregistro `201` sin persistir)

Método: cada intento se hizo desde el navegador (formulario real), y se contrastó el log del backend (`POST` y status) con `psql` (fila en `usuario`). Cuentas de prueba `spike.*@fiuner.edu.ar`.

| Caso | Entorno | Intentos | `POST` con 201 | Filas nuevas | Resultado |
|---|---|---|---|---|---|
| 1.2 Autoregistro de Docente | **Dev** (`npm run dev`, StrictMode activo) | 5 | 5 | 5 | ✅ Cada 201 persistió; 0 duplicados |
| 1.1 Autoregistro de Docente | **Build de producción** (`vite build` + `vite preview`, mismo puerto 5173 por el CORS) | 5 | 5 | 5 | ✅ Idem |
| 1.3a Autoregistro de Estudiante (Materia → Comisión) | Dev | 1 | 1 | 1 (con comisión) | ✅ |
| 1.3b Recuperación de contraseña completa (solicitar → token de `psql` → definir contraseña → login) | Build | 1 | `202` + `200` | token usado | ✅ Login `200` con la contraseña nueva; sin `422` |
| 1.3c Ídem | Dev | 1 | `202` + `200` | token usado | ✅ Idem |

Observaciones:
- El intento 2 de la primera tanda en dev no llegó a enviarse (sin `POST`, sin fila): fue un artefacto de **mi** automatización (un lote interrumpido por un error de coordenadas). Repetido en limpio, persistió.
- Lectura del código: `AutoregistroDocente.tsx` y `RecuperarPasswordNueva.tsx` crean el `AbortController` dentro del `useEffect` (corrección de `US-ADJ-20`); no hay doble envío posible desde ahí. Los mensajes de política de contraseña del backend empiezan con "La contraseña debe", así que el frontend los distingue del token inválido.
- Limpieza: las 11 cuentas `spike.*` y sus tokens se borraron de la base (volvió a 20 usuarios).

**Resultado del spike:** no reproduce en 13 envíos (modo dev y build). Ver hallazgo #1.

## 2026-10-05 — Bloque 2: `US-ADJ-59` (cuenta deshabilitada no inicia sesión)

Cuenta usada: Sara Jovanovich (Estudiante con evaluaciones → la baja es lógica). Todo por la UI salvo donde se indica.

| Caso | Pasos | Resultado |
|---|---|---|
| 2.1 | Administrador → Cuentas → Eliminar a Sara: la pantalla avisa que con datos asociados se **deshabilita** y que sin datos se borra de forma permanente (fix #3 de la UAT v1 verificado de paso). Sara queda "Inactiva". Login de Sara con la contraseña **correcta** | ✅ Alerta "Cuenta deshabilitada — Tu cuenta fue dada de baja y no puede iniciar sesión. Contactá a un Administrador."; la URL no cambia y no queda ninguna clave de sesión en `localStorage` |
| 2.2 | Login con contraseña **incorrecta** | ✅ Mismo mensaje (no revela si la contraseña era válida). `psql`: `deshabilitada = t`, `bloqueada = f`, `intentos_fallidos_login = 0` (no consume intentos) |
| 2.3 | Administrador pulsa "Activar" (Sara vuelve a "Activa"); Sara entra con su contraseña | ✅ Entra y ve su portal de Estudiante |

## 2026-10-05 — Bloque 3: `US-ADJ-60` (siempre ≥ 1 Administrador operativo)

| Caso | Pasos | Resultado |
|---|---|---|
| 3.1 / 3.5 | Con **un solo** Administrador operativo, Cuentas → Eliminar sobre su propia cuenta | ✅ La pantalla es la variante **"Deshabilitar cuenta"** ("Un Administrador nunca se borra… se puede reactivar"). Al confirmar: "No se puede deshabilitar esta cuenta — Es el único Administrador operativo…". `psql`: sigue `deshabilitada = f` |
| 3.2 | 3 logins fallidos del Administrador | ✅ El bloqueo es **temporal**: `psql` `bloqueada = t`, `bloqueada_hasta` ≈ +15 min. El 4.º intento muestra "Cuenta bloqueada temporalmente — Podés volver a intentar en unos 15 minutos" y el **formulario queda habilitado** (email, contraseña y botón no están `disabled`). Ver observación O-1 sobre el 3.er intento |
| 3.3 | Re-bloqueo por API (3 fallos); el 4.º intento con la contraseña **correcta** responde `403` con `reintentar_en_segundos: 899`. Se simula el vencimiento con `UPDATE … bloqueada_hasta = now() - 1 min` y se loguea | ✅ Login `200`; `psql`: `bloqueada = f`, `bloqueada_hasta` NULL, contador 0 (vencimiento perezoso) |
| 3.4 | 2.º Administrador creado con `scripts/seed_admin.py` (ADR-016; la UI solo da de alta Docentes). Entrando como el 2.º, se deshabilita al 1.º | ✅ Permitido (queda uno operativo): el 1.º figura "Inactiva". Se lo reactivó con "Activar" |

## 2026-10-05 — Bloque 4: `US-ADJ-62` (recuperar la contraseña desbloquea)

| Caso | Pasos | Resultado |
|---|---|---|
| 4.1 | Sara (Estudiante) falla 3 veces y un 4.º intento | ✅ Alerta "Cuenta bloqueada — Superaste el máximo de intentos permitidos. **Podés recuperar tu contraseña por email o pedirle a un Administrador que la restablezca.**" con **"recuperar tu contraseña por email"** como link (`/recuperar-password`) |
| 4.2 | Click en el link → solicitar → token tomado de `psql` (no hay SMTP) → definir contraseña nueva válida | ✅ "Contraseña actualizada" |
| 4.3 | Login con la contraseña nueva, **sin intervención de un Administrador** | ✅ Entra al portal de Estudiante. `psql`: `bloqueada = f`, `bloqueada_hasta` NULL, `intentos_fallidos_login = 0`, `intentos_fallidos_password = 0` |
| 4.4 | El único Administrador, bloqueado temporalmente (caso 3.2), recupera su contraseña por el mismo flujo | ✅ Queda libre en el acto, sin esperar los 15 minutos: `bloqueada = f`, `bloqueada_hasta` NULL, contadores 0; login `200` |
| 4.5 | Camila (cuenta **deshabilitada** por API como preparación) completa la recuperación por la UI | ✅ La contraseña se cambia ("Contraseña actualizada") pero el login sigue mostrando "Cuenta deshabilitada": recuperar no reactiva |

**Restauración al terminar (2026-10-05):** Camila reactivada; Sara y Camila con su contraseña de la siembra (hash copiado de otro Estudiante, porque `prueba-uat` no pasa la política de 12 caracteres que impone el endpoint); Administrador de prueba y sus tokens borrados. `psql`: 20 usuarios, 0 deshabilitados, 0 bloqueados, 1 Administrador.

Nota del método: en el navegador integrado, las capturas de pantalla a veces muestran el estado anterior de la página (desfase de render). Para los resultados se tomó como referencia el DOM (`get_page_text`, `javascript_tool`) y la base.

## 2026-10-05 — Bloque 5: `US-ADJ-61` (la actividad cerrada se ve como cerrada)

Preparación (API, como Docente Víctor): 3 actividades nuevas en Ingeniería de Software — "UAT Cerrada a mano" (vigente), "UAT Vencida por fecha" (apertura -8 d, cierre -1 d) y "UAT Finalizada y luego cerrada" (Sara la inicia y finaliza, luego el Docente la cierra). El cierre de la primera se hizo **por la UI** (Docente → detalle → "Cerrar actividad ahora" → confirmación; el detalle pasa a "Cerrada"). Observador: Lucía, que no rindió nada, y Sara.

| Caso | Resultado |
|---|---|
| 5.1 Listado del Estudiante (Lucía) | ✅ Cerrada a mano y vencida por fecha → badge **"Cerrada"**; Parcial 1 y 2 siguen "Pendiente de responder". Estilo del badge verificado en el navegador: gris neutro (`rgb(244,247,249)`) con borde 1 px, distinto del verde de "Pendiente" |
| 5.2 Abrir la actividad cerrada | ✅ "Esta actividad ya cerró … Ya no se puede rendir"; sin "volvé a entrar". ⚠️ **Hallazgo H-1** (fecha mostrada) |
| 5.3 "Mis materias" | ✅ "2 pendientes" (solo Parcial 1 y 2): las 3 cerradas no cuentan |
| 5.4 Vencida por fecha sin rendir | ✅ Mismo badge "Cerrada" (ver 5.1) |
| 5.5 Sara (finalizó "UAT Finalizada y luego cerrada", que luego se cerró) | ✅ Ve "Finalizada — ver revisión" en esa y en Parcial 1 y 2; las dos que no rindió, "Cerrada" |
| 5.6 Sin contexto | ✅ Recargando la ruta con el `history.state` vaciado, y entrando directo a `/rendir` de la actividad cerrada (camino del `422`): "Esta actividad no está disponible en este momento" |

## 2026-10-05 — Bloque 6: hallazgos #7 y #9 y fixes #3 y #8

Preparación: comisión "Comision UAT - Jueves de 8 a 10" en Gestión de Proyectos con Alejandra Morales asignada (por API), para tener una materia sin presentaciones visible para un Docente.

| Caso | Resultado |
|---|---|
| 6.1 "Preguntas más falladas", Gestión de Proyectos (Alejandra) | ✅ "Esta materia todavía no tiene preguntas presentadas en actividades de período abierto. Las sesiones en vivo no se incluyen en este informe." |
| 6.2 Ranking con datos (Ing. de Software, Víctor) | ✅ "1 presentación · 1 fallo", "2 presentaciones · 2 fallos", "2 presentaciones · 0 fallos" |
| 6.3 "Evolución temporal" (Sara: 3 actividades; Máximo: 1 punto propio) | ✅ parcial: el promedio de la comisión se dibuja como **anillo hueco** y es visible aunque coincida con el punto del estudiante (y con un solo dato propio); el título completo está en el tooltip. ❌ **Hallazgo H-2**: la última etiqueta del eje queda cortada contra el borde derecho del gráfico ("UAT Finalizada y lue") |
| 6.4 Fixes #3 y #8 | ✅ #3 ya verificado en 2.1 (la pantalla avisa del borrado permanente). #8: la revisión de Sara arranca en **"1."** |

Datos de prueba que **quedan** en la base de desarrollo para que se puedan ver: las 3 actividades "UAT …" (y la evaluación finalizada de Sara en una de ellas) y la comisión "Comision UAT - Jueves de 8 a 10" con Alejandra asignada. Se eliminan re-sembrando.

Pendiente de toda la UAT: Bloque 7 (iPhone, hallazgo #6) — fuera de esta UAT por decisión de Víctor.
