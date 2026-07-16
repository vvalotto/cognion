"""
Comandos de tracking para control manual del usuario.

Estos comandos permiten al usuario controlar pausas y consultar el estado
del tracking durante la implementación de una Historia de Usuario.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _find_active_tracking() -> Path | None:
    """Busca un archivo de tracking activo (sin completed_at).

    Returns:
        Path al archivo de tracking activo, o None si no hay ninguno
    """
    tracking_dir = Path(".claude/tracking")
    if not tracking_dir.exists():
        return None

    # Buscar archivos JSON en el directorio
    for json_file in tracking_dir.glob("US-*-tracking.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
                # Si no tiene completed_at, está activo
                if data.get("timeline", {}).get("completed_at") is None:
                    return json_file
        except (json.JSONDecodeError, FileNotFoundError):
            continue

    return None


def _load_tracker_from_file(file_path: Path):
    """Carga un TimeTracker desde un archivo JSON.

    Args:
        file_path: Path al archivo JSON

    Returns:
        Instancia de TimeTracker cargada
    """
    # Importar aquí para evitar dependencias circulares
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tracking.time_tracker import TimeTracker

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Crear tracker a partir de metadata
    metadata = data["metadata"]
    tracker = TimeTracker(
        us_id=metadata["us_id"],
        us_title=metadata["us_title"],
        us_points=metadata["us_points"],
        producto=metadata["producto"],
    )

    # Cargar el estado completo desde el archivo JSON
    # (esto es simplificado, en producción se reconstruiría todo el estado)
    tracker.storage_path = file_path

    return tracker


def track_pause(reason: str = "") -> dict[str, Any]:
    """Pausa el tracking actual.

    Args:
        reason: Motivo de la pausa (opcional)

    Returns:
        Dict con resultado de la operación
    """
    tracking_file = _find_active_tracking()

    if not tracking_file:
        return {
            "success": False,
            "message": "No hay tracking activo. Inicia una implementación con /implement-us primero.",
        }

    try:
        tracker = _load_tracker_from_file(tracking_file)
        tracker.pause(reason=reason)

        # Calcular duración actual
        status = tracker.get_status()
        elapsed_mins = status["elapsed_seconds"] // 60
        elapsed_secs = status["elapsed_seconds"] % 60

        return {
            "success": True,
            "message": f"⏸️  Tracking pausado\n   Duración actual: {elapsed_mins}min {elapsed_secs}s",
            "status": status,
        }
    except ValueError as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def track_resume() -> dict[str, Any]:
    """Reanuda el tracking pausado.

    Returns:
        Dict con resultado de la operación
    """
    tracking_file = _find_active_tracking()

    if not tracking_file:
        return {
            "success": False,
            "message": "No hay tracking activo. Inicia una implementación con /implement-us primero.",
        }

    try:
        tracker = _load_tracker_from_file(tracking_file)

        # Obtener duración de la pausa antes de resumir
        if tracker.current_pause:
            now = datetime.now(UTC)
            pause_seconds = int((now - tracker.current_pause.started_at).total_seconds())
            pause_mins = pause_seconds // 60

            tracker.resume()

            return {
                "success": True,
                "message": f"▶️  Tracking reanudado\n   Pausa: {pause_mins}min",
                "pause_duration_minutes": pause_mins,
            }
        else:
            return {"success": False, "message": "No hay pausa activa para resumir"}
    except ValueError as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def track_status() -> dict[str, Any]:
    """Muestra el estado actual del tracking.

    Returns:
        Dict con información del estado
    """
    tracking_file = _find_active_tracking()

    if not tracking_file:
        return {
            "success": False,
            "message": "No hay tracking activo. Inicia una implementación con /implement-us primero.",
        }

    try:
        tracker = _load_tracker_from_file(tracking_file)
        status = tracker.get_status()

        # Formatear el output
        elapsed_h = status["elapsed_seconds"] // 3600
        elapsed_m = (status["elapsed_seconds"] % 3600) // 60

        effective_h = status["effective_seconds"] // 3600
        effective_m = (status["effective_seconds"] % 3600) // 60

        paused_m = status["paused_seconds"] // 60

        # Determinar estado
        estado_icon = "⏸️  EN PAUSA" if status["status"] == "paused" else "▶️  EN CURSO"

        # Construir mensaje formateado
        message = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️  TRACKING STATUS - {tracker.us_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Progreso: {status.get('current_phase', 'N/A')}
📋 Tarea actual: {status.get('current_task', 'N/A') if status.get('current_task') else 'Ninguna'}

⏰ Tiempos:
   • Inicio:       {status['started_at'][:19] if 'started_at' in status else 'N/A'}
   • Transcurrido: {elapsed_h}h {elapsed_m}min
   • Efectivo:     {effective_h}h {effective_m}min
   • Pausado:      {paused_m}min
   • Estado:       {estado_icon}

✅ Completadas: {status['completed_tasks']}/{status['total_tasks']} tareas"""

        return {"success": True, "message": message, "status": status}
    except Exception as e:
        return {"success": False, "message": f"Error al obtener estado: {str(e)}"}


def track_report(us_id: str | None = None) -> dict[str, Any]:
    """Genera reporte inmediato de una US.

    Args:
        us_id: ID de la US (ej: "US-001"). Si es None, usa la activa.

    Returns:
        Dict con resultado de la operación
    """
    # Determinar qué archivo leer
    if us_id:
        tracking_file = Path(f".claude/tracking/{us_id}-tracking.json")
        if not tracking_file.exists():
            return {"success": False, "message": f"No existe tracking para {us_id}"}
    else:
        tracking_file = _find_active_tracking()
        if not tracking_file:
            return {
                "success": False,
                "message": "No hay tracking activo. Especifica un US-ID o inicia /implement-us",
            }

    try:
        with open(tracking_file, encoding="utf-8") as f:
            data = json.load(f)

        # Generar reporte simple
        metadata = data["metadata"]
        timeline = data["timeline"]
        summary = data.get("summary", {})
        phases = data.get("phases", [])

        # Calcular duración total
        if timeline.get("completed_at"):
            total_seconds = timeline["total_elapsed_seconds"]
            status_text = "✅ COMPLETADO"
        else:
            # Calcular duración hasta ahora
            started = datetime.fromisoformat(timeline["started_at"].replace("Z", "+00:00"))
            now = datetime.now(UTC)
            total_seconds = int((now - started).total_seconds())
            status_text = "🔄 EN PROGRESO"

        total_h = total_seconds // 3600
        total_m = (total_seconds % 3600) // 60

        # Formatear reporte
        report = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 REPORTE DE TRACKING - {metadata['us_id']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Historia: {metadata['us_title']}
🎯 Puntos: {metadata['us_points']}
📦 Producto: {metadata['producto']}
⏱️  Estado: {status_text}

━━━ Tiempos ━━━

• Total:     {total_h}h {total_m}min
• Efectivo:  {format_duration(timeline.get('effective_seconds', 0))}
• Pausado:   {format_duration(timeline.get('paused_seconds', 0))}

━━━ Progreso ━━━

• Fases completadas: {len([p for p in phases if p.get('status') == 'completed'])}/{len(phases)}
• Tareas completadas: {summary.get('completed_tasks', 0)}/{summary.get('total_tasks', 0)}

━━━ Estimaciones ━━━

• Estimado: {summary.get('estimated_total_minutes', 0):.0f} min
• Real:     {summary.get('actual_total_minutes', 0):.0f} min
• Varianza: {summary.get('variance_percent', 0):+.1f}%

━━━ Archivos ━━━

• Tracking: {tracking_file}
• Reporte:  docs/reports/{metadata['us_id']}-tracking-report.md (generado al finalizar)
"""

        return {"success": True, "message": report, "data": data}

    except Exception as e:
        return {"success": False, "message": f"Error al generar reporte: {str(e)}"}


def track_history(
    last: int | None = None, producto: str | None = None, desde: str | None = None
) -> dict[str, Any]:
    """Muestra historial de USs trackeadas.

    Args:
        last: Número de USs más recientes a mostrar
        producto: Filtrar por producto (ej: "ux_termostato")
        desde: Fecha desde (formato YYYY-MM-DD)

    Returns:
        Dict con resultado de la operación
    """
    tracking_dir = Path(".claude/tracking")
    if not tracking_dir.exists():
        return {"success": False, "message": "No hay trackings registrados aún"}

    # Recolectar todos los trackings
    trackings = []
    for json_file in tracking_dir.glob("US-*-tracking.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            metadata = data["metadata"]
            timeline = data["timeline"]
            summary = data.get("summary", {})

            # Aplicar filtros
            if producto and metadata["producto"] != producto:
                continue

            if desde:
                started = datetime.fromisoformat(timeline["started_at"].replace("Z", "+00:00"))
                desde_dt = datetime.fromisoformat(f"{desde}T00:00:00+00:00")
                if started < desde_dt:
                    continue

            # Calcular duración
            if timeline.get("completed_at"):
                completed = datetime.fromisoformat(timeline["completed_at"].replace("Z", "+00:00"))
                duration_seconds = timeline["total_elapsed_seconds"]
                status = "✅"
            else:
                completed = None
                started = datetime.fromisoformat(timeline["started_at"].replace("Z", "+00:00"))
                duration_seconds = int((datetime.now(UTC) - started).total_seconds())
                status = "🔄"

            trackings.append(
                {
                    "us_id": metadata["us_id"],
                    "us_title": metadata["us_title"],
                    "us_points": metadata["us_points"],
                    "producto": metadata["producto"],
                    "started_at": timeline["started_at"],
                    "completed_at": completed,
                    "duration_seconds": duration_seconds,
                    "variance_percent": summary.get("variance_percent", 0),
                    "status": status,
                }
            )

        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            continue

    if not trackings:
        return {
            "success": False,
            "message": "No se encontraron trackings con los filtros especificados",
        }

    # Ordenar por fecha de inicio (más reciente primero)
    trackings.sort(key=lambda x: x["started_at"], reverse=True)

    # Aplicar límite
    if last:
        trackings = trackings[:last]

    # Formatear salida
    header = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    header += "📊 HISTORIAL DE TRACKING\n"
    header += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    lines = []
    total_duration = 0
    total_points = 0
    variances = []

    for t in trackings:
        duration = format_duration(t["duration_seconds"])
        variance = f"{t['variance_percent']:+.0f}%"
        date = t["started_at"][:10]  # YYYY-MM-DD

        line = f"{t['status']} {t['us_id']} | {t['us_title'][:30]:<30} | {t['us_points']}pts | {duration:>10} | {variance:>6} | {date}"
        lines.append(line)

        total_duration += t["duration_seconds"]
        total_points += t["us_points"]
        if t["variance_percent"] != 0:
            variances.append(t["variance_percent"])

    # Calcular promedios
    avg_variance = sum(variances) / len(variances) if variances else 0
    avg_hours_per_point = (total_duration / 3600) / total_points if total_points > 0 else 0

    footer = "\n\n📈 Promedios:\n"
    footer += f"   • Tiempo por punto: {avg_hours_per_point:.1f}h\n"
    footer += f"   • Varianza promedio: {avg_variance:+.0f}%\n"
    footer += f"   • Total USs: {len(trackings)}\n"
    footer += f"   • Total puntos: {total_points}"

    message = header + "\n".join(lines) + footer

    return {"success": True, "message": message, "trackings": trackings}


# Funciones de ayuda para formateo
def format_duration(seconds: int) -> str:
    """Formatea segundos a 'Xh Ymin'.

    Args:
        seconds: Duración en segundos

    Returns:
        String formateado
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}min"
    return f"{minutes}min"
