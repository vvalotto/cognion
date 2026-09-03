import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Card } from "@/components/ui/card"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"

/** Pantalla "Mis materias" del BC Actividad Evaluativa (`#doc-materias`, `US-3.4.2`).
 *
 * Reutiliza `listarMaterias()` (`banco-preguntas-api.ts`, `US-2.1.9`) sin cambios — mismo dato
 * que `Materias.tsx` de Banco de Preguntas, con destino de navegación distinto. Sin comisión
 * ni conteo de actividades por tarjeta (simplificación documentada en
 * `docs/plans/inc3/US-3.4.2-context.md` §Gap 3 — esos datos no los expone `GET /materias`).
 */
export function MateriasActividades() {
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
      <Breadcrumb items={[{ label: "Actividad evaluativa" }, { label: "Mis materias" }]} />
      <h1 className="text-lg font-semibold">Mis materias</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Elegí una materia para ver y gestionar sus actividades de período abierto.
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
              onClick={() => navigate(`/actividad-evaluativa/materias/${materia.id}/actividades`)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  navigate(`/actividad-evaluativa/materias/${materia.id}/actividades`)
                }
              }}
            >
              <p className="mb-2 text-xl">📘</p>
              <p className="font-semibold">{materia.nombre}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
