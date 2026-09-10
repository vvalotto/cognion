import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { editarComision, obtenerComision, type ComisionDetalleResponse } from "@/lib/identidad-comisiones-api"

/** Pantalla de corrección del horario de una comisión existente. */
export function EditarComision() {
  const { comisionId } = useParams<{ comisionId: string }>()
  const navigate = useNavigate()

  const [comision, setComision] = useState<ComisionDetalleResponse | null>(null)
  const [horario, setHorario] = useState("")

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    if (!comisionId) return undefined
    const controller = new AbortController()
    obtenerComision(comisionId, controller.signal)
      .then((resultado) => {
        setComision(resultado)
        setHorario(resultado.horario)
      })
      .catch(() => {})
    return () => controller.abort()
  }, [comisionId])

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
    if (!comisionId) return

    await editarComision(comisionId, horario, controladorSubmitRef.current?.signal)
    void navigate(`/comisiones/${comisionId}`)
  }

  function handleCancelar() {
    void navigate(`/comisiones/${comisionId}`)
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Comisiones", to: "/comisiones" },
          { label: comision?.horario ?? "…", to: comisionId ? `/comisiones/${comisionId}` : undefined },
          { label: "Editar" },
        ]}
      />
      <h1 className="text-lg font-semibold">Editar comisión</h1>
      <p className="mt-1 text-sm text-muted-foreground">Corregí el horario si se cargó con un error.</p>

      <Card className="mt-4">
        <CardContent>
          <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="editar-comision-horario">Horario</Label>
              <Input
                id="editar-comision-horario"
                type="text"
                required
                value={horario}
                onChange={(e) => setHorario(e.target.value)}
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
