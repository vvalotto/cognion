import { useEffect, useState } from "react"

import { Card } from "@/components/ui/card"
import { Pagination } from "@/components/ui/pagination"
import type { DesempenoEstudianteResponse } from "@/lib/analytics-api"

const TAMANIO_PAGINA = 20

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
  onFilaClick?: (evaluacionId: string) => void
}

/**
 * Resumen acumulado + detalle por evaluación — componente visual único compartido por
 * "Mi desempeño" (`US-4.1.3`), "Desempeño por alumno" (`US-4.2.5`) y el drill-down 1° de
 * "Desempeño por comisión" (`US-ADJ-48`), solo cambia el origen de los datos
 * (wireframes-analytics.md §4, hot spot 2). `onFilaClick` es opcional — sin él, cada
 * `.eval-item` se muestra sin drill-down 2° (comportamiento sin cambios de `US-4.1.3`/`4.2.5`).
 */
export function DesempenoResumenDetalle({
  desempeno,
  filas,
  mensajeVacio,
  onFilaClick,
}: DesempenoResumenDetalleProps) {
  const [pagina, setPagina] = useState(1)

  useEffect(() => {
    setPagina(1)
  }, [filas])

  if (filas.length === 0) {
    return <p className="mt-4 text-sm text-muted-foreground">{mensajeVacio}</p>
  }

  const totalPaginas = Math.ceil(filas.length / TAMANIO_PAGINA)
  const filasPagina = filas.slice((pagina - 1) * TAMANIO_PAGINA, pagina * TAMANIO_PAGINA)

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
        {filasPagina.map((fila) => (
          <Card
            key={fila.evaluacionId}
            className={`eval-item flex items-center justify-between gap-3 p-4 ${
              onFilaClick ? "cursor-pointer hover:bg-accent" : ""
            }`}
            role={onFilaClick ? "button" : undefined}
            tabIndex={onFilaClick ? 0 : undefined}
            onClick={onFilaClick ? () => onFilaClick(fila.evaluacionId) : undefined}
            onKeyDown={
              onFilaClick
                ? (e) => {
                    if (e.key === "Enter" || e.key === " ") onFilaClick(fila.evaluacionId)
                  }
                : undefined
            }
          >
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
      <Pagination pagina={pagina} totalPaginas={totalPaginas} onCambiarPagina={setPagina} />
    </>
  )
}
