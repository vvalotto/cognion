#!/usr/bin/env bash
# Decide si un cambio exige el CI completo. Lee de la entrada estándar la lista de archivos modificados (uno por línea)
# e imprime `completo=true` o `completo=false`.
#
# `completo=false` SOLO si la lista no está vacía y TODOS los archivos son documentación que ningún test ni el
# empaquetado leen. Ante cualquier duda (lista vacía, archivo desconocido) imprime `completo=true`.
#
# Documentación segura:  docs/** (salvo docs/INSTALACION.md, que valida tests/unit/inc10 y lleva el paquete),
#                        .cm/**, quality/reports/**, README.md y CLAUDE.md de la raíz.
# NO es segura:          CHANGELOG.md (lo leen tests/unit/inc10), ni ningún otro .md fuera de las rutas de arriba.
set -euo pipefail

total=0
while IFS= read -r archivo || [ -n "$archivo" ]; do
  [ -n "$archivo" ] || continue
  total=$((total + 1))
  case "$archivo" in
    *..*) echo "completo=true"; exit 0 ;;
    docs/INSTALACION.md) echo "completo=true"; exit 0 ;;
    docs/*|.cm/*|quality/reports/*|README.md|CLAUDE.md) ;;
    *) echo "completo=true"; exit 0 ;;
  esac
done

if [ "$total" -eq 0 ]; then
  echo "completo=true"
else
  echo "completo=false"
fi
