# Plan de corrección — UAT de cierre del Incremento 7-ADJ

Documento de **priorización, no de ejecución** (`PROCEDIMIENTO-UAT.md` §11): propone cómo resolver cada hallazgo; no implementa nada. Gate de cierre: aprobación de Víctor. Hallazgos en `registro-hallazgos.md`.

**Resultado de la UAT (Bloques 0 a 6):** `US-ADJ-59`, `60`, `61` y `62`, y los arreglos #7 y #9, verificados en navegador real. Sin hallazgos 🔴. El hallazgo #1 de la UAT v1 quedó **no reproducible**. El #6 (iPhone) queda fuera de esta UAT.

| # | Sev. | Qué | Track | Propuesta | Esfuerzo |
|---|---|---|---|---|---|
| H-1 | 🟡 | Cierre manual muestra una fecha de cierre futura ("Cerró el 12/10" hoy 05/10) | **Informal** (solo `frontend/`) | En `FueraDePeriodo.tsx` y en el listado, si `fechaCierre` es posterior a ahora (cierre manual), omitir la fecha: "Esta actividad ya cerró. Ya no se puede rendir." / en la columna Período mostrar "Cerrada" sin "Cierra …". Evita tocar `src/` | XS |
| H-1b | — | Alternativa formal (si se quiere mostrar *cuándo* se cerró): exponer la fecha real del cierre manual (`cerrada_en`, ya está en el evento `ActividadEvaluativaCerrada`) en `ActividadVisibleResponse` | Formal (`src/`) → `US-ADJ` | Solo si Víctor quiere esa fecha; no recomendada ahora | S |
| H-2 | ⚪ | Última etiqueta del eje X cortada contra el borde del gráfico | **Informal** (solo `frontend/`) | En `EvolucionTemporal.tsx`: `text-anchor` `end` para la última etiqueta y `start` para la primera (o recortar según el margen disponible en los extremos) | XS |
| O-1 | ⚪ | El 3.er intento fallido (el que bloquea) sigue diciendo "Email o contraseña incorrectos"; el bloqueo se informa en el 4.º | Formal (`src/`) si se cambia | Decisión de producto: dejarlo (cumple la spec) o avisar en el 3.er intento. Recomendación: dejarlo — cambiarlo revela el umbral de bloqueo y rompe `US-ADJ-60`/`US-2.2.1` ya validadas | — |
| O-2 | ⚪ | `**` al inicio de una pregunta de la siembra | Dato | Corregir el texto de esa pregunta en el banco (edición desde la UI) | XS |

**Secuencia propuesta:** H-1 y H-2 en un solo PR informal de `frontend/` (mismo criterio que #7/#9); O-2 a mano; O-1 sin acción salvo decisión contraria.

**Cierre del 7-ADJ:** con H-1/H-2 resueltos (o aceptados) y este plan aprobado → `BL-012` (matriz de trazabilidad, `CHANGELOG`, merge `develop → main` y tag; hoy `develop` va por delante de `v0.8.0`).

**Fuera de esta UAT, siguen abiertos:** hallazgo #6 (demora en el iPhone, necesita el dispositivo y/o staging con WSS real) y los 3 PRs de Dependabot (#468/#469/#470).
