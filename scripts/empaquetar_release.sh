#!/usr/bin/env bash
# Arma el paquete de instalación de una versión (US-10.2.1): dist/cognion-X.Y.Z-instalacion.tar.gz.
#
#   scripts/empaquetar_release.sh 1.0.0
#
# Lleva VERSION, CHANGELOG.md y, si existen, la guía de instalación y deploy/servidor/ (los crea US-10.2.2).
# La instalación local sin Docker usa el código fuente de la propia GitHub Release. Falla si la versión pedida no
# es la de VERSION o si falta un archivo obligatorio. Variables opcionales: RAIZ (carpeta del proyecto) y SALIDA.
set -euo pipefail

abortar() { echo "ERROR: $1" >&2; exit 1; }
VERSION_PEDIDA="${1:-}"
[ -n "$VERSION_PEDIDA" ] || abortar "Indicá la versión. Ej.: $0 1.0.0"
RAIZ="${RAIZ:-$(cd "$(dirname "$0")/.." && pwd)}"
SALIDA="${SALIDA:-$RAIZ/dist}"

OBLIGATORIOS=(VERSION CHANGELOG.md)
OPCIONALES=(docs/INSTALACION.md deploy/servidor)

[ -f "$RAIZ/VERSION" ] || abortar "Falta $RAIZ/VERSION."
[ "$(tr -d '[:space:]' < "$RAIZ/VERSION")" = "$VERSION_PEDIDA" ] \
  || abortar "La versión pedida ($VERSION_PEDIDA) no coincide con VERSION ($(tr -d '[:space:]' < "$RAIZ/VERSION"))."
for f in "${OBLIGATORIOS[@]}"; do
  [ -e "$RAIZ/$f" ] || abortar "Falta el archivo obligatorio: $f"
done

NOMBRE="cognion-$VERSION_PEDIDA"
TEMPORAL="$(mktemp -d)"
trap 'rm -rf "$TEMPORAL"' EXIT
mkdir -p "$TEMPORAL/$NOMBRE" "$SALIDA"
for f in "${OBLIGATORIOS[@]}" "${OPCIONALES[@]}"; do
  [ -e "$RAIZ/$f" ] || continue
  mkdir -p "$TEMPORAL/$NOMBRE/$(dirname "$f")"
  cp -R "$RAIZ/$f" "$TEMPORAL/$NOMBRE/$f"
done
ARCHIVO="$SALIDA/$NOMBRE-instalacion.tar.gz"
tar -czf "$ARCHIVO" -C "$TEMPORAL" "$NOMBRE"
echo "$ARCHIVO"
