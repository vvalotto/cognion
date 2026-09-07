import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate, useSearchParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import { crearComision } from "@/lib/identidad-comisiones-api"

/**
 * Pantalla de alta de Comisión (§3.2 `wireframes-portal-entrada.md`) — consume
 * `POST /comisiones` (`US-ADJ-24`). Materia preseleccionada si se llega con `?materiaId=`.
 */
export function NuevaComision() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const materiaPreseleccionada = searchParams.get("materiaId") ?? ""

  const [materias, setMaterias] = useState<MateriaListItemResponse[] | null>(null)
  const [materiaId, setMateriaId] = useState(materiaPreseleccionada)
  const [horario, setHorario] = useState("")

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    // Mismo patrón que NuevaMateria.tsx (US-ADJ-20): un controller nuevo por montaje real,
    // para que el doble montaje de StrictMode en dev no aborte el submit siguiente.
    const controller = new AbortController()
    controladorSubmitRef.current = controller

    listarMaterias(controller.signal)
      .then((resultado) => {
        setMaterias(resultado)
        if (!materiaPreseleccionada && resultado.length > 0) {
          setMateriaId((actual) => actual || resultado[0].id)
        }
      })
      .catch(() => {})

    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function volverAlListado() {
    void navigate(materiaId ? `/comisiones?materiaId=${materiaId}` : "/comisiones")
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    try {
      const comision = await crearComision(
        materiaId,
        horario,
        controladorSubmitRef.current?.signal,
      )
      void navigate(`/comisiones/${comision.id}`)
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      throw err
    }
  }

  return (
    <div>
      <Breadcrumb items={[{ label: "Comisiones", to: "/comisiones" }, { label: "Nueva Comisión" }]} />
      <h1 className="text-lg font-semibold">Crear comisión</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Sin docente asignado todavía — esa acción se hace después, desde el detalle de la
        comisión.
      </p>

      <Card className="mt-4">
        <CardContent>
          <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="nueva-comision-materia">Materia</Label>
              <select
                id="nueva-comision-materia"
                required
                value={materiaId}
                onChange={(e) => setMateriaId(e.target.value)}
                className="rounded-md border border-border px-2 py-1.5 text-sm"
              >
                {materias === null ? (
                  <option value="">Cargando…</option>
                ) : (
                  materias.map((materia) => (
                    <option key={materia.id} value={materia.id}>
                      {materia.nombre}
                    </option>
                  ))
                )}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="nueva-comision-horario">Horario</Label>
              <Input
                id="nueva-comision-horario"
                type="text"
                required
                placeholder="Ej. Lunes y Miércoles 18–20hs"
                value={horario}
                onChange={(event) => setHorario(event.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={!materiaId}>
                Crear Comisión
              </Button>
              <Button type="button" variant="outline" onClick={volverAlListado}>
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
