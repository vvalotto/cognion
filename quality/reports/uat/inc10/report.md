# Reporte UAT — Incremento 10, Iteración 1 (`US-10.1.1`, 2026-11-11)

**Versión probada:** `v0.10.0` (`main` en `64b4262`, `develop` sin cambios en `src/`, `frontend/` ni `migrations/`).
**Resultado:** ✅ **Sin hallazgos 🔴.** 1 observación 🟡. La prueba en un celular real **se desestimó** por decisión de Víctor (2026-11-11) y queda como no verificada.

## Resultados

| Verificación | Resultado | Evidencia |
|---|---|---|
| Instalación local con `scripts/local/levantar.sh` (base, migraciones, frontend, primer administrador) | ✅ sin pasos manuales | consola; log en `logs/uat10/` (no versionado) |
| Capa 1: suite completa de `BL-015` (2378 tests, cobertura 97.03 %) | ✅ | `.cm/baselines/BL-015-incremento-9-correcciones-y-robustez.md` |
| Capa 2 HTTP, 27 verificaciones: salud, readiness, link grupal, errores del registro, revocación, aviso del último intento, log sin token | ✅ 27/27 | `capa2-http.json` |
| 30 logins simultáneos: `/health` sigue respondiendo (efecto de `US-ADJ-63`) | ✅ 30 logins en 2,9 s; `/health` mediana 15 ms, máx 77 ms durante la ráfaga (2 ms en reposo) | `carga-logins.txt` |
| Navegador: aviso "te queda 1 intento" en el login (1.er fallo sin aviso, 2.º con aviso y link para recuperar) | ✅ | recorrido manual |
| Navegador: el docente genera el link grupal; ve vigencia, contador y estudiantes inscriptos | ✅ | recorrido manual |
| Navegador: registro de un estudiante con el link (contraseña débil deshabilita el botón y explica; válida lo habilita) | ✅ cuenta creada y vinculada a la comisión | recorrido manual |
| Navegador: el contador pasa a "1 estudiante se registró" y el estudiante aparece en la lista | ✅ | recorrido manual |
| Navegador: "Desactivar link" y pantalla "Este link fue desactivado" para quien lo abre | ✅ | recorrido manual |
| Navegador a 375 px (emulado): registro y tarjeta del docente | ✅ sin desbordes | recorrido manual |

## Hallazgos

| # | Sev. | Descripción | Track |
|---|---|---|---|
| H-1 | 🟡 | El link que el docente copia se arma con `window.location.origin` (`ComisionDetalleDocente.tsx:162`). Si el docente abre la app por `localhost`, el link dice `localhost` y **no funciona en los celulares de los alumnos**. Hay que abrir la app por la IP o el nombre `.local` que ven los alumnos. | Documentarlo en la guía de instalación (`US-10.2.2`). Un arreglo en código (usar una URL pública configurable) sería `src/` + `frontend/`: track formal. |

## No verificado
- **Celular real:** el registro y la tarjeta se probaron con un viewport emulado, no con un teléfono. **Desestimado por decisión de Víctor (2026-11-11).** Lo único que se comprobó desde un iPhone es que ingresó al sistema por la IP de la red local con el login del docente.
- **Canal en vivo con JWT vencido** (#605): requiere esperar el vencimiento del token (60 min); solo cubierto por los tests automáticos.
- **Regresión completa de los RF validados:** no se repitió a mano; la cubren los 2378 tests de la suite.
- **VM de GCP:** no se desplegó; la carga se midió en la Mac, no en la `e2-micro`.

## Conclusión
Con esta evidencia, el código de la `v0.10.0` no tiene hallazgos bloqueantes. `US-10.1.1` se cierra con el celular real como riesgo aceptado y declarado (también en `BL-016` y en la guía de instalación).
