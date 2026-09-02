import { useEffect, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  obtenerActividad,
  modificarTitulo,
  type ActividadResumenResponse,
} from "@/lib/actividad-evaluativa-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import { ApiError } from "@/lib/api-client"

/** Formulario de edición de título de una actividad ya creada (`US-ADJ-10`). */
export function EditarTituloActividad() {
  const { actividadId } = useParams<{ actividadId: string }>()
  const navigate = useNavigate()

  const [actividad, setActividad] = useState<ActividadResumenResponse | null>(null)
  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [titulo, setTitulo] = useState("")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!actividadId) return
    let cancelado = false
    obtenerActividad(actividadId).then((resultado) => {
      if (!cancelado) {
        setActividad(resultado)
        setTitulo(resultado.titulo)
      }
    })
    return () => {
      cancelado = true
    }
  }, [actividadId])

  useEffect(() => {
    if (!actividad) return
    let cancelado = false
    listarMaterias().then((materias) => {
      if (!cancelado) setMateria(materias.find((m) => m.id === actividad.materiaId) ?? null)
    })
    return () => {
      cancelado = true
    }
  }, [actividad])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    if (!actividadId) return

    try {
      await modificarTitulo(actividadId, titulo.trim())
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setError(err.message)
        return
      }
      throw err
    }
    void navigate(`/actividad-evaluativa/actividades/${actividadId}`)
  }

  if (actividad === null || materia === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          {
            label: materia.nombre,
            to: `/actividad-evaluativa/materias/${actividad.materiaId}/actividades`,
          },
          {
            label: "Actividades",
            to: `/actividad-evaluativa/materias/${actividad.materiaId}/actividades`,
          },
          { label: "Editar título" },
        ]}
      />
      <h1 className="text-lg font-semibold">Editar título</h1>

      {error && (
        <div
          role="alert"
          className="mb-4 mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <Card className="mt-4">
        <CardContent>
          <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="et-titulo">Título</Label>
              <Input
                id="et-titulo"
                type="text"
                value={titulo}
                onChange={(event) => setTitulo(event.target.value)}
                placeholder="Ej: Parcial 1 — Unidades 1 a 3"
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit">Guardar título</Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(`/actividad-evaluativa/actividades/${actividadId}`)}
              >
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
