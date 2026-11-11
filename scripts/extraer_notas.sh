#!/usr/bin/env bash
# Imprime la sección de CHANGELOG.md de una versión, para las notas de la GitHub Release (US-10.2.1).
#
#   scripts/extraer_notas.sh 1.0.0
#
# Falla si la versión no tiene sección o si está vacía. RAIZ (opcional) indica la carpeta con CHANGELOG.md.
set -euo pipefail

abortar() { echo "ERROR: $1" >&2; exit 1; }
VERSION="${1:-}"
[ -n "$VERSION" ] || abortar "Indicá la versión. Ej.: $0 1.0.0"
RAIZ="${RAIZ:-$(cd "$(dirname "$0")/.." && pwd)}"
ARCHIVO="$RAIZ/CHANGELOG.md"
[ -f "$ARCHIVO" ] || abortar "No existe $ARCHIVO."

NOTAS="$(awk -v v="$VERSION" '
  index($0, "## [" v "]") == 1 { dentro = 1; next }
  dentro && /^## \[/ { exit }
  dentro { print }
' "$ARCHIVO")"

[ -n "$(printf '%s' "$NOTAS" | tr -d '[:space:]')" ] || abortar "CHANGELOG.md no tiene una sección con contenido para la versión $VERSION."
printf '%s\n' "$NOTAS"
