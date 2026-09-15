import { useEffect, useState } from "react"

import { Breadcrumb } from "@/components/Breadcrumb"
import {
  obtenerRankingPreguntasFalladas,
  type RankingPreguntaFalladaResponse,
} from "@/lib/analytics-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import {
  listarComisionesPorMateria,
  type ComisionResumenResponse,
} from "@/lib/identidad-comisiones-api"

type Severidad = "alta" | "media" | "baja"

const COLOR_TEXTO: Record<Severidad, string> = {
  alta: "text-red-600",
  media: "text-amber-600",
  baja: "text-emerald-700",
}

function severidad(tasaError: number): Severidad {
  if (tasaError >= 0.5) return "alta"
  if (tasaError >= 0.2) return "media"
  return "baja"
}

/** Pantalla "Preguntas más falladas" del Docente (`#doc-ranking-preguntas`, `US-ADJ-50`, RF-22). */
export function RankingPreguntasFalladas() {
  const [materias, setMaterias] = useState<MateriaListItemResponse[]>([])
  const [materiaId, setMateriaId] = useState<string>("")

  const [comisiones, setComisiones] = useState<ComisionResumenResponse[]>([])
  const [comisionId, setComisionId] = useState<string>("")

  const [ranking, setRanking] = useState<RankingPreguntaFalladaResponse[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then(setMaterias)
      .catch(() => {})
    return () => controller.abort()
  }, [])

  function elegirMateria(value: string) {
    setMateriaId(value)
    setComisionId("")
    setRanking(null)
    setError(null)
  }

  useEffect(() => {
    if (!materiaId) {
      setComisiones([])
      return undefined
    }
    const controller = new AbortController()
    listarComisionesPorMateria(materiaId, controller.signal)
      .then(setComisiones)
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    setError(null)
    setRanking(null)
    obtenerRankingPreguntasFalladas(materiaId, comisionId || undefined, controller.signal)
      .then(setRanking)
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError("No se pudo cargar el ranking de preguntas falladas. Intentá de nuevo más tarde.")
      })
    return () => controller.abort()
  }, [materiaId, comisionId])

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb items={[{ label: "Analytics" }, { label: "Preguntas más falladas" }]} />
      <h1 className="text-lg font-semibold">Preguntas más falladas</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Ranking de preguntas por tasa de error, de toda la materia o de una comisión puntual.
      </p>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="materia" className="text-sm font-medium">
            Materia
          </label>
          <select
            id="materia"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={materiaId}
            onChange={(e) => elegirMateria(e.target.value)}
          >
            <option value="">Elegí una materia</option>
            {materias.map((materia) => (
              <option key={materia.id} value={materia.id}>
                {materia.nombre}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="comision" className="text-sm font-medium">
            Comisión
          </label>
          <select
            id="comision"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={comisionId}
            onChange={(e) => setComisionId(e.target.value)}
            disabled={!materiaId}
          >
            <option value="">Toda la materia</option>
            {comisiones.map((comision) => (
              <option key={comision.id} value={comision.id}>
                {comision.horario}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!materiaId && !error && (
        <p className="mt-4 text-sm text-muted-foreground">
          Elegí una materia para ver el ranking de preguntas más falladas.
        </p>
      )}

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      {!error && ranking !== null && ranking.length === 0 && (
        <p className="mt-4 text-sm text-muted-foreground">
          Esta materia todavía no tiene ninguna pregunta presentada.
        </p>
      )}

      {!error && ranking !== null && ranking.length > 0 && (
        <div className="mt-4 flex flex-col gap-2">
          {ranking.map((fila, indice) => {
            const nivel = severidad(fila.tasaError)
            const porcentaje = Math.round(fila.tasaError * 100)
            return (
              <div key={fila.preguntaId} className="ranking-row rounded-lg border p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex min-w-0 gap-3">
                    <span className="shrink-0 text-sm font-semibold text-muted-foreground">
                      {indice + 1}.
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{fila.enunciado}</p>
                      <p className="text-xs text-muted-foreground">
                        {fila.unidadTematica} · {fila.tema}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`shrink-0 text-sm font-bold ${COLOR_TEXTO[nivel]}`}
                  >
                    {porcentaje}%
                  </span>
                </div>
                <p className="mt-1 pl-6 text-xs text-muted-foreground">
                  {fila.cantidadPresentaciones} presentaciones · {fila.cantidadFallos} fallos
                </p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
