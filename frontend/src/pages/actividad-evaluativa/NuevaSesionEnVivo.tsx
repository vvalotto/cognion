import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { esEnteroPositivo, soloEnterosPositivos } from "@/lib/entero-positivo"
import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { ApiError } from "@/lib/api-client"
import {
  derivarSugerencias,
  filtrarBanco,
  listarMaterias,
  type MateriaListItemResponse,
  type PreguntaResponse,
} from "@/lib/banco-preguntas-api"
import { obtenerComision, type ComisionDetalleResponse } from "@/lib/identidad-comisiones-api"
import { crearSesion } from "@/lib/sesion-en-vivo-api"

/** Formulario de creación de una sesión en vivo desde una Comisión (`#doc-nueva-sesion`, US-6.3.5). */
export function NuevaSesionEnVivo() {
  const { comisionId } = useParams<{ comisionId: string }>()
  const navigate = useNavigate()

  const [comision, setComision] = useState<ComisionDetalleResponse | null>(null)
  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [preguntas, setPreguntas] = useState<PreguntaResponse[]>([])
  const [unidadTematica, setUnidadTematica] = useState("")
  const [tema, setTema] = useState("")
  const [cantidadPreguntas, setCantidadPreguntas] = useState(1)
  const [tiempoLimite, setTiempoLimite] = useState(20)
  const [error, setError] = useState<string | null>(null)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    if (!comisionId) return undefined
    const controller = new AbortController()
    obtenerComision(comisionId, controller.signal).then(setComision).catch(() => {})
    return () => controller.abort()
  }, [comisionId])

  useEffect(() => {
    if (!comision) return undefined
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === comision.materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [comision])

  useEffect(() => {
    if (!materia) return undefined
    const controller = new AbortController()
    filtrarBanco(materia.bancoId, {}, undefined, controller.signal)
      .then((resultado) => setPreguntas(resultado.preguntas))
      .catch(() => {})
    return () => controller.abort()
  }, [materia])

  const { unidades, temas } = derivarSugerencias(preguntas)

  useEffect(() => {
    // Crea un controller nuevo en cada montaje real — en StrictMode (dev), el doble montaje
    // abortaría el submit siguiente si reusara el creado en el render (US-ADJ-20).
    const controller = new AbortController()
    controladorSubmitRef.current = controller
    return () => controller.abort()
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (!esEnteroPositivo(cantidadPreguntas)) {
      setError("La cantidad de preguntas debe ser un número entero de al menos 1.")
      return
    }
    if (!esEnteroPositivo(tiempoLimite)) {
      setError("El tiempo límite por pregunta debe ser un número entero de segundos mayor a 0.")
      return
    }

    if (!comisionId) return
    let sesion
    try {
      sesion = await crearSesion(
        {
          comisionId,
          cantidadPreguntas,
          tiempoLimitePorPreguntaSegundos: tiempoLimite,
          unidadTematica: unidadTematica || null,
          tema: tema || null,
        },
        controladorSubmitRef.current?.signal,
      )
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && (err.status === 404 || err.status === 422)) {
        setError(err.message)
        return
      }
      throw err
    }
    void navigate(`/sesiones-en-vivo/${sesion.id}/sala`)
  }

  if (comision === null || materia === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          {
            label: materia.nombre,
            to: `/actividad-evaluativa/materias/${materia.id}/comisiones`,
          },
          {
            label: comision.horario,
            to: `/actividad-evaluativa/comisiones/${comisionId}`,
          },
          { label: "Nueva sesión en vivo" },
        ]}
      />
      <h1 className="text-lg font-semibold">Nueva sesión en vivo</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Comisión: {comision.horario} — Materia: {materia.nombre}
      </p>

      {error && (
        <div
          role="alert"
          className="mb-4 mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <Card className="mt-4">
        <CardContent className="p-6">
          <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
            <div className="flex gap-4">
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="ns-unidad">Unidad temática (opcional)</Label>
                <Select
                  id="ns-unidad"
                  value={unidadTematica}
                  onChange={(event) => setUnidadTematica(event.target.value)}
                >
                  <option value="">Cualquiera</option>
                  {unidades.map((valor) => (
                    <option key={valor} value={valor}>
                      {valor}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="ns-tema">Tema (opcional)</Label>
                <Select id="ns-tema" value={tema} onChange={(event) => setTema(event.target.value)}>
                  <option value="">Cualquiera</option>
                  {temas.map((valor) => (
                    <option key={valor} value={valor}>
                      {valor}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="ns-cantidad-preguntas">Cantidad de preguntas</Label>
                <Input
                  id="ns-cantidad-preguntas"
                  type="number"
                  inputMode="numeric"
                  required
                  value={cantidadPreguntas}
                  onKeyDown={soloEnterosPositivos}
                  onChange={(event) => setCantidadPreguntas(Number(event.target.value))}
                />
              </div>
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="ns-tiempo-limite">Tiempo límite por pregunta (segundos)</Label>
                <Input
                  id="ns-tiempo-limite"
                  type="number"
                  inputMode="numeric"
                  required
                  value={tiempoLimite}
                  onKeyDown={soloEnterosPositivos}
                  onChange={(event) => setTiempoLimite(Number(event.target.value))}
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              El puntaje de cada respuesta combina velocidad, dificultad e importancia de la
              pregunta.
            </p>
            <div className="flex gap-2 border-t border-border pt-5">
              <Button type="submit">Crear sesión</Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(`/actividad-evaluativa/comisiones/${comisionId}`)}
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
