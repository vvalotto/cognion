#!/bin/bash
# Hook SessionStart — verifica si hay una sesión anterior sin resumir.
# Si el flag existe, avisa al usuario antes de continuar.

MEMORY_DIR="$HOME/.claude/projects/-Users-victor-PycharmProjects-cognion/memory"
FLAG="$MEMORY_DIR/session-needs-summary.flag"

if [ -f "$FLAG" ]; then
    echo ""
    echo "⚠️  Hay una sesión anterior sin resumir."
    echo "   Ejecutá /resume para restaurar el contexto antes de continuar."
    echo "   (El flag se limpia automáticamente al ejecutar /resume o /checkpoint)"
    echo ""
fi
