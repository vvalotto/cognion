#!/usr/bin/env bash
# Corre en local lo mismo que el CI (IQ-06), con un solo comando y sin depender del hook de push.
#
#   scripts/calidad.sh               rápido: ruff, mypy, import-linter, DesignReviewer y el frontend (oxlint, tsc, Vitest)
#   scripts/calidad.sh --backend     solo lo de Python
#   scripts/calidad.sh --frontend    solo lo de frontend/
#   scripts/calidad.sh --completo    además pytest con cobertura (exige DATABASE_URL apuntando a una base *_test)
#   scripts/calidad.sh --seguridad   además pip-audit y npm audit (informativos, como en el CI)
#
# Corre todos los pasos aunque alguno falle y al final resume cuáles fallaron. Sale con 1 si falló alguno.
# DesignReviewer (acoplamiento, CBO) es el que más tarde avisa: aquí corre antes de pushear, no durante el push.
# Mantener sincronizado con `.github/workflows/ci.yml`: `tests/unit/inc12/test_calidad_script.py` lo comprueba.
set -uo pipefail
cd "$(dirname "$0")/.."

hacer_backend=1; hacer_frontend=1; hacer_tests=0; hacer_seguridad=0
for arg in "$@"; do
  case "$arg" in
    --backend)   hacer_frontend=0 ;;
    --frontend)  hacer_backend=0 ;;
    --completo)  hacer_tests=1 ;;
    --seguridad) hacer_seguridad=1 ;;
    -h|--ayuda|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opción desconocida: $arg (probá --ayuda)" >&2; exit 2 ;;
  esac
done

fallaron=()
paso() { # paso "nombre" comando...  [carpeta opcional en $CARPETA]
  local nombre="$1"; shift
  echo; echo "▶ $nombre"
  if ( cd "${CARPETA:-.}" && "$@" ); then echo "✔ $nombre"; else echo "✘ $nombre"; fallaron+=("$nombre"); fi
}

ruta_hooks="$(git config --get core.hooksPath || true)"
if [ "${ruta_hooks##*/}" != ".githooks" ]; then  # sirve la ruta relativa o la absoluta
  echo "AVISO: el hook de push no está activo en este clon (corre DesignReviewer al pushear)."
  echo "       Activalo una vez con: git config core.hooksPath .githooks"
fi

if [ "$hacer_backend" = 1 ]; then
  paso "ruff" uv run ruff check src/
  paso "mypy" uv run mypy src/
  paso "import-linter (capas y aislamiento entre BC)" uv run lint-imports
  paso "DesignReviewer" uv run designreviewer src/ --config pyproject.toml
fi

if [ "$hacer_frontend" = 1 ]; then
  CARPETA=frontend paso "oxlint" npm run lint
  CARPETA=frontend paso "tsc -b" npx tsc -b
  CARPETA=frontend paso "Vitest (con umbrales de cobertura)" npm run test:coverage
fi

if [ "$hacer_tests" = 1 ]; then
  case "${DATABASE_URL:-}" in
    *_test)
      paso "pytest" uv run pytest --cov=src --cov-report=term-missing
      paso "cobertura de las capas internas" uv run coverage report --omit='src/*/frameworks/*' --fail-under=95
      paso "cobertura de frameworks/" uv run coverage report --include='src/*/frameworks/*' --fail-under=82 ;;
    *) echo; echo "✘ pytest: DATABASE_URL tiene que apuntar a una base cuyo nombre termine en _test (los tests la vacían)."; fallaron+=("pytest (sin base *_test)") ;;
  esac
fi

if [ "$hacer_seguridad" = 1 ]; then
  echo; echo "▶ Seguridad de dependencias (informativo: no cuenta como falla)"
  uv export --frozen --no-dev --no-hashes --no-emit-project -o /tmp/requirements-audit.txt \
    && uvx pip-audit -r /tmp/requirements-audit.txt --no-deps --disable-pip || echo "  (hay avisos de pip-audit)"
  ( cd frontend && npm audit --omit=dev --audit-level=high ) || echo "  (hay avisos de npm audit)"
fi

echo
if [ "${#fallaron[@]}" -eq 0 ]; then echo "Todo en orden."; exit 0; fi
echo "Fallaron: ${fallaron[*]}"; exit 1
