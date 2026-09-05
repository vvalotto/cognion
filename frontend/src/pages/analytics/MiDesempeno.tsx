import { useEffect, useState } from "react"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Card } from "@/components/ui/card"
import {
  obtenerMiDesempeno,
  type DesempenoEstudianteResponse,
} from "@/lib/analytics-api"
import { listarActividadesVisibles } from "@/lib/actividad-evaluativa-api"
import { listarMisMaterias, type MateriaEstudianteResponse } from "@/lib/identidad-estudiante-api"

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

interface FilaDesempeno {
  evaluacionId: string
  titulo: string
  finalizadaEn: string
  cantidadCorrectas: number
  cantidadIncorrectas: number
}

function armarFilas(
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

/** Pantalla "Mi desempeño" del Estudiante (`#est-desempeno`, `US-4.1.3`). */
export function MiDesempeno() {
  const [materias, setMaterias] = useState<MateriaEstudianteResponse[] | null>(null)
  const [materiaId, setMateriaId] = useState<string | null>(null)
  const [desempeno, setDesempeno] = useState<DesempenoEstudianteResponse | null>(null)
  const [filas, setFilas] = useState<FilaDesempeno[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listarMisMaterias(controller.signal)
      .then((resultado) => {
        setMaterias(resultado)
        if (resultado.length > 0) {
          setMateriaId(resultado[0].id)
        }
      })
      .catch(() => {})
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    setError(null)
    setDesempeno(null)
    setFilas(null)
    Promise.all([
      obtenerMiDesempeno(materiaId, controller.signal),
      listarActividadesVisibles(materiaId, controller.signal),
    ])
      .then(([resultadoDesempeno, actividades]) => {
        const titulosPorActividad = new Map(actividades.map((a) => [a.id, a.titulo]))
        setDesempeno(resultadoDesempeno)
        setFilas(armarFilas(resultadoDesempeno, titulosPorActividad))
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError("No se pudo cargar tu desempeño. Intentá de nuevo más tarde.")
      })
    return () => controller.abort()
  }, [materiaId])

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb items={[{ label: "Analytics" }, { label: "Mi desempeño" }]} />
      <h1 className="text-lg font-semibold">Mi desempeño</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Historial de tus evaluaciones de período abierto en la materia elegida.
      </p>

      {materias !== null && materias.length > 1 && (
        <div className="mt-4">
          <label htmlFor="materia" className="text-sm font-medium">
            Materia
          </label>
          <select
            id="materia"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={materiaId ?? ""}
            onChange={(e) => setMateriaId(e.target.value)}
          >
            {materias.map((materia) => (
              <option key={materia.id} value={materia.id}>
                {materia.nombre}
              </option>
            ))}
          </select>
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      {!error && desempeno !== null && filas !== null && (
        <>
          {filas.length === 0 ? (
            <p className="mt-4 text-sm text-muted-foreground">
              Todavía no finalizaste ninguna evaluación de esta materia.
            </p>
          ) : (
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
                  <p className="text-2xl font-semibold">
                    {desempeno.resumen.porcentajeAcierto}%
                  </p>
                  <p className="text-xs text-muted-foreground">Acierto</p>
                </Card>
                <Card className="p-4">
                  <p className="text-2xl font-semibold">
                    {desempeno.resumen.cantidadEvaluaciones}
                  </p>
                  <p className="text-xs text-muted-foreground">Evaluaciones finalizadas</p>
                </Card>
              </div>

              <p className="mt-4 mb-2 text-sm text-muted-foreground">Detalle por evaluación</p>

              <div className="flex flex-col gap-3">
                {filas.map((fila) => (
                  <Card
                    key={fila.evaluacionId}
                    className="flex items-center justify-between gap-3 p-4"
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
            </>
          )}
        </>
      )}
    </div>
  )
}
