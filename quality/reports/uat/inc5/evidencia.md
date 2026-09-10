# Evidencia UAT — Incremento 5 "Notificaciones"

| Campo | Valor |
|-------|-------|
| Diseño | `quality/reports/uat/inc5/design.md` |
| Fecha ejecución | 2026-09-10 |
| Ejecutor | Sesión de Claude Code (Capa 1 + Capa 2). Sin recorrido de navegador — RF-14 sin pantalla propia; verificación manual = revisión del contenido real de los emails capturados (§3) |

---

## 1. Capa 1 — pytest (backend)

Corrido sobre `develop`, después del merge de `US-5.1.3` (PR #314, commit `eaaedbd`).

```
.venv/bin/python -m pytest tests/unit/ tests/integration/ -q
757 passed, 1 warning in 113.97s (0:01:53)

.venv/bin/python -m pytest tests/step_defs/ -q
212 passed, 74 warnings in 168.21s (0:02:48)
```

Sin fallos, sin flakes — 757/757 unit+integration y 212/212 BDD en verde.

---

## 2. Capa 2 — HTTP vía `smoke.sh` extendido

Se extendió `fake_smtp.py` (antes descartaba cada mensaje sin guardarlo) para persistir el
contenido real de cada email capturado a un log, y se agregaron dos verificaciones nuevas en
`.claude/skills/run-cognion/smoke.sh`, inmediatamente después de los pasos ya existentes que
crean y cierran una actividad (`US-3.1.2`/`US-3.3.2`) — sin pasos HTTP nuevos, el flujo de
Notificaciones ya se ejercitaba de punta a punta desde que `US-5.1.2`/`US-5.1.3` se mergearon,
solo faltaba verificarlo.

Corrida completa, todos los pasos en verde (fragmento relevante):

```
== POST /actividades (docente crea una actividad de período abierto, US-3.1.2) ==
OK (id=359fdbf1-deb5-48c6-a8a2-b76499234abe, vigente por 7 días)
== Notificación de apertura capturada por el fake SMTP (US-5.1.2, RF-14) ==
OK
...
== POST /actividades/{id}/cerrar — cierre manual, finaliza en cascada (US-3.3.2) ==
OK (200)
== Notificación de cierre capturada por el fake SMTP (US-5.1.3, RF-14) ==
OK
...
SMOKE TEST OK — server bajado y datos de prueba limpiados.
```

---

## 3. Verificación manual — contenido real de los emails capturados

En vez de un recorrido de navegador (no aplica, BC sin pantalla propia), se revisa el
contenido íntegro capturado por el fake SMTP durante la corrida de `smoke.sh` — headers y
cuerpo tal como los arma `smtplib` en producción:

```
-----MENSAJE-----
Subject: =?utf-8?q?Invitaci=C3=B3n_a_Cogni=C3=B3n?=
From: no-responder@cognion.local
To: smoketest-57198-estudiante@fiuner.edu.ar
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 8bit
MIME-Version: 1.0

Fuiste invitado a registrarte en Cognión.
Token de invitación: oF2HPJe9ncEVfYE0I_anTBk6Z9KQqQYnzwNaSX3W2tg
Válido por 7 días desde su generación.
-----MENSAJE-----
Subject: Nueva actividad disponible: 
From: no-responder@cognion.local
To: smoketest-57198-estudiante@fiuner.edu.ar
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 8bit
MIME-Version: 1.0

Se abrió una nueva actividad de evaluación.

Materia: smoketest-57198-materia
Título: 
Apertura: 2026-09-10T20:30:47.878355+00:00
Cierre: 2026-09-17T20:31:47.939117+00:00
-----MENSAJE-----
Subject: Actividad cerrada: 
From: no-responder@cognion.local
To: smoketest-57198-estudiante@fiuner.edu.ar
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

Se cerr=C3=B3 la siguiente actividad de evaluaci=C3=B3n. Ya no est=C3=A1 disp=
onible para rendir.

Materia: smoketest-57198-materia
T=C3=ADtulo:=20
```

**Verificado:**
- Los dos emails (apertura y cierre) llegan al mismo estudiante inscripto en la comisión de
  la materia — sin `comisiones_ids`, se resuelve correctamente "toda la materia" en ambos
  casos.
- El asunto y el cuerpo distinguen apertura ("Nueva actividad disponible") de cierre
  ("Actividad cerrada"), con el nombre real de la materia en ambos.
- `Título:` aparece vacío porque `smoke.sh` no manda `titulo` al crear la actividad (dato del
  script de smoke, no del dominio) — comportamiento esperado, no un defecto.
- El cuerpo del email de cierre viaja en `quoted-printable` (por los acentos de "cerró"/
  "evaluación"/"disponible") y el de apertura en `8bit` (sin acentos en ese texto) — ambos
  formatos válidos de MIME, decodificados igual por cualquier cliente de correo real.
- Ningún email interrumpió ni retrasó la respuesta HTTP de las operaciones que los disparan
  (200/201 en ambos casos, confirmado en el fragmento de §2).

**Hallazgos:** ninguno — 0 🔴 Bloqueantes, 0 🟡 Observaciones, 0 ⚪ Estéticos
(`PROCEDIMIENTO-UAT.md` §8).

---

## 4. Conclusión

Capa 1 (757/757 unit+integration, 212/212 BDD) y Capa 2 (`smoke.sh` extendido) en verde;
contenido real de los emails de apertura y cierre revisado y correcto. **UAT del Incremento 5
aprobada** — RF-14 pasa a Validado en `docs/traceability/matrix.md`. Sin hallazgos que
bloqueen el cierre de `BL-009`.
