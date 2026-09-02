import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Card } from "@/components/ui/card"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"

/** Pantalla de listado de materias (§2.1 `wireframes-banco-preguntas.md`) — consume `GET /materias`. */
export function Materias() {
  const navigate = useNavigate()
  const [materias, setMaterias] = useState<MateriaListItemResponse[] | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((resultado) => setMaterias(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [])

  return (
    <div>
      <Breadcrumb items={[{ label: "Banco de preguntas" }, { label: "Materias" }]} />
      <h1 className="text-lg font-semibold">Materias</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Elegí una materia para ver y cargar su banco de preguntas.
      </p>

      {materias === null ? (
        <p className="mt-4 text-sm text-muted-foreground">Cargando…</p>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {materias.map((materia) => (
            <Card
              key={materia.id}
              role="button"
              tabIndex={0}
              className="cursor-pointer p-5 transition-colors hover:border-primary"
              onClick={() => navigate(`/materias/${materia.id}/banco`)}
              onKeyDown={(e) => {
                if (e.key === "Enter") navigate(`/materias/${materia.id}/banco`)
              }}
            >
              <p className="mb-2 text-xl">📘</p>
              <p className="font-semibold">{materia.nombre}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {materia.cantidadPreguntasActivas} pregunta
                {materia.cantidadPreguntasActivas === 1 ? "" : "s"} activa
                {materia.cantidadPreguntasActivas === 1 ? "" : "s"}
              </p>
            </Card>
          ))}

          <Card
            role="button"
            tabIndex={0}
            className="flex cursor-pointer flex-col items-center justify-center border-dashed p-5 text-center font-semibold text-primary shadow-none transition-colors hover:border-primary"
            onClick={() => navigate("/materias/nueva")}
            onKeyDown={(e) => {
              if (e.key === "Enter") navigate("/materias/nueva")
            }}
          >
            <p className="mb-1 text-xl">+</p>
            <p>Nueva materia</p>
          </Card>
        </div>
      )}
    </div>
  )
}
