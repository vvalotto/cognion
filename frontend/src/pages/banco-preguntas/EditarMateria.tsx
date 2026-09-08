import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiError } from "@/lib/api-client"
import { editarMateria, listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"

/**
 * Pantalla de corrección del nombre de una materia — accesible a Docente y Administrador
 * (a diferencia de `Banco.tsx`, que sigue siendo solo de Docente). No existía ninguna forma
 * de corregir un nombre cargado con error de tipeo hasta este hallazgo de la prueba manual.
 */
export function EditarMateria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [nombre, setNombre] = useState("")
  const [error, setError] = useState<string | null>(null)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((materias) => {
        const encontrada = materias.find((m) => m.id === materiaId) ?? null
        setMateria(encontrada)
        if (encontrada) setNombre(encontrada.nombre)
      })
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    // Crea un controller nuevo en cada montaje real — en StrictMode (dev), React monta,
    // desmonta y vuelve a montar el efecto para detectar cleanups faltantes; si el cleanup
    // abortara el mismo controller creado en el render (arriba), el segundo montaje quedaría
    // con la señal ya abortada y todo submit posterior se descartaría en silencio.
    const controller = new AbortController()
    controladorSubmitRef.current = controller
    return () => controller.abort()
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (!materiaId) return

    try {
      await editarMateria(materiaId, nombre, controladorSubmitRef.current?.signal)
      void navigate("/materias")
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 409) {
        setError("Ya existe otra materia con ese nombre.")
        return
      }
      throw err
    }
  }

  function handleCancelar() {
    void navigate("/materias")
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Banco de preguntas" },
          { label: "Materias", to: "/materias" },
          { label: materia?.nombre ?? "…" },
          { label: "Editar" },
        ]}
      />
      <h1 className="text-lg font-semibold">Editar materia</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Corregí el nombre si se cargó con un error — no toca el banco de preguntas.
      </p>

      <Card className="mt-4">
        <CardContent>
          {error && (
            <div
              role="alert"
              className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
            >
              <p className="font-medium">{error}</p>
            </div>
          )}

          <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="editar-materia-nombre">Nombre de la materia</Label>
              <Input
                id="editar-materia-nombre"
                type="text"
                required
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit">Guardar cambios</Button>
              <Button type="button" variant="outline" onClick={handleCancelar}>
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
