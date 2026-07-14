#!/bin/bash
# Hook SessionEnd — captura el estado del repo al cerrar la sesión.
# Actualiza session-current.md, session-metadata.json y activa el flag
# para que check-session-start.sh avise en la próxima sesión.

MEMORY_DIR="$HOME/.claude/projects/-Users-victor-PycharmProjects-cognion/memory"
CURRENT_MD="$MEMORY_DIR/session-current.md"
METADATA_JSON="$MEMORY_DIR/session-metadata.json"
HISTORY_MD="$MEMORY_DIR/session-history.md"
FLAG="$MEMORY_DIR/session-needs-summary.flag"

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
BRANCH=$(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || echo "desconocido")
GIT_STATUS=$(git -C "$PROJECT_DIR" status --short 2>/dev/null || echo "(limpio)")
RECENT_COMMITS=$(git -C "$PROJECT_DIR" log --oneline -5 2>/dev/null || echo "(sin commits)")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE_HUMAN=$(date +"%Y-%m-%d %H:%M")

# Actualizar session-current.md
cat > "$CURRENT_MD" << EOF
# Estado al cierre de sesión — Cognion

**Fecha:** $DATE_HUMAN
**Branch:** $BRANCH

## Git status
\`\`\`
$GIT_STATUS
\`\`\`

## Últimos commits
\`\`\`
$RECENT_COMMITS
\`\`\`
EOF

# Agregar entrada al historial
echo "" >> "$HISTORY_MD"
echo "## $DATE_HUMAN — branch: $BRANCH" >> "$HISTORY_MD"
echo '```' >> "$HISTORY_MD"
echo "$RECENT_COMMITS" >> "$HISTORY_MD"
echo '```' >> "$HISTORY_MD"

# Actualizar session-metadata.json
cat > "$METADATA_JSON" << EOF
{
  "last_session_end": "$TIMESTAMP",
  "branch": "$BRANCH",
  "needs_summary": true
}
EOF

# Activar flag para la próxima sesión
touch "$FLAG"
