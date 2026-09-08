import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"

/**
 * Pantalla de listado de materias (§2.1 `wireframes-banco-preguntas.md`) — consume
 * `GET /materias`. Tabla con acciones explícitas por fila ("Ver banco" / "Editar"), mismo
 * patrón que `Cuentas.tsx` — reemplaza la grilla de cards anterior, que mezclaba "entrar al
 * banco" y "editar el nombre" como dos destinos distintos sobre el mismo elemento clickeable.
 */
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Materias</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Elegí una materia para ver y cargar su banco de preguntas.
          </p>
        </div>
        <Button onClick={() => navigate("/materias/nueva")}>+ Nueva materia</Button>
      </div>

      <Card className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border bg-muted text-[11px] font-bold tracking-wide text-muted-foreground uppercase">
              <th className="py-2 pr-4 pl-4">Nombre</th>
              <th className="py-2 pr-4">Preguntas activas</th>
              <th className="py-2 pr-4"></th>
            </tr>
          </thead>
          <tbody>
            {materias === null ? (
              <tr>
                <td colSpan={3} className="py-4 pl-4 text-muted-foreground">
                  Cargando…
                </td>
              </tr>
            ) : materias.length === 0 ? (
              <tr>
                <td colSpan={3} className="py-4 pl-4 text-muted-foreground">
                  Todavía no hay materias creadas.
                </td>
              </tr>
            ) : (
              materias.map((materia) => (
                <tr
                  key={materia.id}
                  className="cursor-pointer border-b border-border last:border-0 hover:bg-accent"
                  onClick={() => navigate(`/materias/${materia.id}/banco`)}
                >
                  <td className="py-3 pr-4 pl-4">{materia.nombre}</td>
                  <td className="py-3 pr-4">{materia.cantidadPreguntasActivas}</td>
                  <td className="flex gap-2 py-3 pr-4">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/materias/${materia.id}/banco`)
                      }}
                    >
                      Ver banco
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/materias/${materia.id}/editar`)
                      }}
                    >
                      Editar
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
