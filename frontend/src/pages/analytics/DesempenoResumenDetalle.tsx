import { Card } from "@/components/ui/card"
import type { DesempenoEstudianteResponse } from "@/lib/analytics-api"

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export interface FilaDesempeno {
  evaluacionId: string
  titulo: string
  finalizadaEn: string
  cantidadCorrectas: number
  cantidadIncorrectas: number
}

/** Arma las filas de detalle a partir del desempeño y los títulos de actividad resueltos aparte. */
export function armarFilas(
  desempeno: DesempenoEstudianteResponse,
  titulosPorActividad: Map<string, string>,
): FilaDesempeno[] {
  return [...desempeno.evaluaciones]
    .sort((a, b) => (a.finalizadaEn < b.finalizadaEn ? 1 : -1))
    .map((evaluacion) => ({
      evaluacionId: evaluacion.evaluacionId,
      titulo: titulosPorActividad.get(evaluacion.actividadId) ?? "Evaluación",
      finalizadaEn: evaluacion.finalizadaEn,
      cantidadCorrectas: evaluacion.cantidadCorrectas,
      cantidadIncorrectas: evaluacion.cantidadIncorrectas,
    }))
}

interface DesempenoResumenDetalleProps {
  desempeno: DesempenoEstudianteResponse
  filas: FilaDesempeno[]
  mensajeVacio: string
}

/**
 * Resumen acumulado + detalle por evaluación — componente visual único compartido por
 * "Mi desempeño" (`US-4.1.3`) y "Desempeño por alumno" (`US-4.2.5`), solo cambia el origen
 * de los datos (wireframes-analytics.md §4, hot spot 2).
 */
export function DesempenoResumenDetalle({
  desempeno,
  filas,
  mensajeVacio,
}: DesempenoResumenDetalleProps) {
  if (filas.length === 0) {
    return <p className="mt-4 text-sm text-muted-foreground">{mensajeVacio}</p>
  }

  return (
    <>
      <div className="mt-4 grid grid-cols-4 gap-3 text-center">
        <Card className="p-4">
          <p className="text-2xl font-semibold text-emerald-700">
            {desempeno.resumen.totalCorrectas}
          </p>
          <p className="text-xs text-muted-foreground">Correctas (acum.)</p>
        </Card>
        <Card className="p-4">
          <p className="text-2xl font-semibold text-destructive">
            {desempeno.resumen.totalIncorrectas}
          </p>
          <p className="text-xs text-muted-foreground">Incorrectas (acum.)</p>
        </Card>
        <Card className="p-4">
          <p className="text-2xl font-semibold">{desempeno.resumen.porcentajeAcierto}%</p>
          <p className="text-xs text-muted-foreground">Acierto</p>
        </Card>
        <Card className="p-4">
          <p className="text-2xl font-semibold">{desempeno.resumen.cantidadEvaluaciones}</p>
          <p className="text-xs text-muted-foreground">Evaluaciones finalizadas</p>
        </Card>
      </div>

      <p className="mt-4 mb-2 text-sm text-muted-foreground">Detalle por evaluación</p>

      <div className="flex flex-col gap-3">
        {filas.map((fila) => (
          <Card key={fila.evaluacionId} className="flex items-center justify-between gap-3 p-4">
            <div>
              <p className="text-sm font-semibold">{fila.titulo}</p>
              <p className="text-xs text-muted-foreground">
                Finalizada el {formatearFecha(fila.finalizadaEn)}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-emerald-700">
                {fila.cantidadCorrectas} ✓
              </span>
              <span className="text-sm font-semibold text-destructive">
                {fila.cantidadIncorrectas} ✗
              </span>
            </div>
          </Card>
        ))}
      </div>
    </>
  )
}
