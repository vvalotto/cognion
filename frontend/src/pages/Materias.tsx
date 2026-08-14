import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"

/** Pantalla de listado de materias (§2.1 `wireframes-banco-preguntas.md`) — consume `GET /materias`. */
export function Materias() {
  const navigate = useNavigate()
  const [materias, setMaterias] = useState<MateriaListItemResponse[] | null>(null)

  useEffect(() => {
    let cancelado = false
    listarMaterias().then((resultado) => {
      if (!cancelado) setMaterias(resultado)
    })
    return () => {
      cancelado = true
    }
  }, [])

  return (
    <div>
      <h1 className="text-lg font-semibold">Materias</h1>

      {materias === null ? (
        <p className="mt-4 text-sm text-muted-foreground">Cargando…</p>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {materias.map((materia) => (
            <button
              key={materia.id}
              type="button"
              className="rounded-lg border border-border p-4 text-left transition-colors hover:bg-accent"
              onClick={() => navigate(`/materias/${materia.id}/banco`)}
            >
              <p className="font-medium">{materia.nombre}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {materia.cantidadPreguntasActivas} pregunta
                {materia.cantidadPreguntasActivas === 1 ? "" : "s"} activa
                {materia.cantidadPreguntasActivas === 1 ? "" : "s"}
              </p>
            </button>
          ))}

          <button
            type="button"
            className="rounded-lg border border-dashed border-border p-4 text-left text-muted-foreground transition-colors hover:bg-accent"
            onClick={() => navigate("/materias/nueva")}
          >
            <p className="font-medium">+ Nueva materia</p>
          </button>
        </div>
      )}
    </div>
  )
}
