# /docs-audit — Auditoría de trazabilidad documental en docs/

Detecta documentos huérfanos: archivos reales en `docs/` que ningún documento de
gobernanza reconoce como fuente de verdad. Previene la deriva documental observada en
AtaraxiaDive, donde activos nuevos se acumulaban sin quedar indexados y se perdía
trazabilidad.

**Alcance:** solo `docs/`. No audita `src/<bc>/README.md` ni `tests/README.md` — esos
son verificación de contenido, no de indexación, y quedan fuera de este skill.

**Modo:** solo reporta. Nunca edita `FUENTES-DE-VERDAD-DOCUMENTAL.md` ni
`DOCUMENTATION-MAP.md` — son documentos de autoridad y la decisión editorial de cómo
indexar un gap (fila nueva, ampliar una fila existente a nivel de carpeta, etc.) queda
en manos de Víctor.

## Cuándo usarlo

- Al cerrar un Incremento o Baseline (antes de `chore(cm): registrar BL-NNN`)
- Cuando se generó una tanda de documentos nuevos (ADRs, HITOs, specs de US) y no se
  actualizó el índice en el mismo momento

## Procedimiento

1. **Inventario real:** `find docs -maxdepth 3 -type d` y listar archivos de cada
   subcarpeta top-level de `docs/`.
2. **Leer completas** (no grep) las dos fuentes de gobernanza:
   - `docs/inventario/FUENTES-DE-VERDAD-DOCUMENTAL.md` §3 (tabla tema → fuente →
     secundarios)
   - `docs/inventario/DOCUMENTATION-MAP.md` §4 (atajos de navegación)
3. **Cruzar archivo por archivo.** Para cada archivo real preguntar: ¿aparece nombrado
   explícitamente en alguna tabla, o está cubierto por una fila a nivel de carpeta
   completa (ej. `docs/iedd/` cubre todos sus archivos como marco metodológico)?
4. **Filtrar falsos positivos antes de reportar.** No todo archivo sin fila propia es
   un gap. Criterio de corte: si mañana hay una duda o conflicto sobre este tema, ¿hay
   ambigüedad real sobre cuál es la fuente de verdad? Si no la hay (archivo único y
   autoevidente en su carpeta, ej. `docs/traceability/matrix.md`), no es gap.
5. **Reportar únicamente los huérfanos reales:** listar cada archivo/carpeta sin
   cobertura, y para cada uno proponer como texto sugerido la fila que agregaría a
   `FUENTES-DE-VERDAD-DOCUMENTAL.md` §3 (tema | fuente | secundarios | regla de uso) y,
   si corresponde, la entrada equivalente en `DOCUMENTATION-MAP.md` §4. No aplicar la
   edición — solo mostrarla para que Víctor la confirme o ajuste.
6. Si no se detectan huérfanos, decirlo explícitamente en una línea — no generar un
   reporte vacío con secciones sin contenido.

## Instrucciones para Claude

Seguir el procedimiento anterior en orden. El resultado esperado es una lista corta
(idealmente vacía) de huérfanos con su fila propuesta — no un volcado de todo el árbol
de `docs/`, no una reescritura de las tablas existentes.
