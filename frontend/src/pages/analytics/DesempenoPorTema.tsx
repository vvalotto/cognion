import { useEffect, useState } from "react"

import { Breadcrumb } from "@/components/Breadcrumb"
import { obtenerTasaErrorPorTema, type TasaErrorTemaResponse } from "@/lib/analytics-api"
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

const COLOR_BARRA: Record<Severidad, string> = {
  alta: "bg-red-600",
  media: "bg-amber-600",
  baja: "bg-emerald-700",
}

function severidad(tasaError: number): Severidad {
  if (tasaError >= 0.5) return "alta"
  if (tasaError >= 0.2) return "media"
  return "baja"
}

/** Pantalla "Desempeño por tema" del Docente (`#doc-desempeno-tema`, `US-4.2.6`, RF-17). */
export function DesempenoPorTema() {
  const [materias, setMaterias] = useState<MateriaListItemResponse[]>([])
  const [materiaId, setMateriaId] = useState<string>("")

  const [comisiones, setComisiones] = useState<ComisionResumenResponse[]>([])
  const [comisionId, setComisionId] = useState<string>("")

  const [tasas, setTasas] = useState<TasaErrorTemaResponse[] | null>(null)
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
    setTasas(null)
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
    setTasas(null)
    obtenerTasaErrorPorTema(materiaId, comisionId || undefined, controller.signal)
      .then(setTasas)
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError("No se pudo cargar la tasa de error por tema. Intentá de nuevo más tarde.")
      })
    return () => controller.abort()
  }, [materiaId, comisionId])

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb items={[{ label: "Analytics" }, { label: "Desempeño por tema" }]} />
      <h1 className="text-lg font-semibold">Desempeño por tema</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Tasa de error agregada por unidad y tema, de toda la materia o de una comisión puntual.
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
          Elegí una materia para ver la tasa de error por tema.
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

      {!error && tasas !== null && tasas.length === 0 && (
        <p className="mt-4 text-sm text-muted-foreground">
          Esta materia todavía no tiene ninguna evaluación finalizada.
        </p>
      )}

      {!error && tasas !== null && tasas.length > 0 && (
        <div className="mt-4 flex flex-col gap-3">
          {tasas.map((tasaTema) => {
            const nivel = severidad(tasaTema.tasaError)
            const porcentaje = Math.round(tasaTema.tasaError * 100)
            return (
              <div
                key={`${tasaTema.unidadTematica}-${tasaTema.tema}`}
                className="rounded-lg border p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">
                      {tasaTema.unidadTematica}
                    </p>
                    <p className="text-sm font-semibold">{tasaTema.tema}</p>
                  </div>
                  <span className={`text-sm font-bold ${COLOR_TEXTO[nivel]}`}>{porcentaje}%</span>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-border">
                  <div
                    className={`h-full ${COLOR_BARRA[nivel]}`}
                    style={{ width: `${porcentaje}%` }}
                  />
                </div>
                <p className="mt-1.5 text-xs text-muted-foreground">
                  {tasaTema.cantidadRespuestas} respuestas · {tasaTema.cantidadIncorrectas}{" "}
                  incorrectas
                </p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
