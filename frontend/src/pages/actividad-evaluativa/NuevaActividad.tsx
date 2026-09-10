import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { crearActividad } from "@/lib/actividad-evaluativa-api"
import {
  derivarSugerencias,
  filtrarBanco,
  listarMaterias,
  type MateriaListItemResponse,
  type PreguntaResponse,
} from "@/lib/banco-preguntas-api"
import { ApiError } from "@/lib/api-client"
import {
  listarComisionesPorMateria,
  type ComisionResumenResponse,
} from "@/lib/identidad-comisiones-api"

/** Formulario de creación de actividad de período abierto (`#doc-nueva-actividad`, US-3.4.3). */
export function NuevaActividad() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [comisiones, setComisiones] = useState<ComisionResumenResponse[]>([])
  const [comisionesSeleccionadas, setComisionesSeleccionadas] = useState<Set<string>>(new Set())
  const [preguntas, setPreguntas] = useState<PreguntaResponse[]>([])
  const [unidadTematica, setUnidadTematica] = useState("")
  const [tema, setTema] = useState("")
  const [titulo, setTitulo] = useState("")
  const [fechaApertura, setFechaApertura] = useState("")
  const [fechaCierre, setFechaCierre] = useState("")
  const [cantidadPreguntas, setCantidadPreguntas] = useState(1)
  const [cantidadIntentos, setCantidadIntentos] = useState(1)
  const [error, setError] = useState<string | null>(null)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    listarComisionesPorMateria(materiaId, controller.signal)
      .then(setComisiones)
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materia) return undefined
    const controller = new AbortController()
    filtrarBanco(materia.bancoId, {}, undefined, controller.signal)
      .then((resultado) => setPreguntas(resultado.preguntas))
      .catch(() => {})
    return () => controller.abort()
  }, [materia])

  const { unidades, temas } = derivarSugerencias(preguntas)
  const cantidadDisponible = preguntas.filter(
    (p) =>
      (!unidadTematica || p.unidadTematica === unidadTematica) && (!tema || p.tema === tema),
  ).length
  const hayRestriccion = Boolean(unidadTematica || tema)

  function alternarComision(comisionId: string) {
    setComisionesSeleccionadas((actual) => {
      const siguiente = new Set(actual)
      if (siguiente.has(comisionId)) siguiente.delete(comisionId)
      else siguiente.add(comisionId)
      return siguiente
    })
  }

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

    if (!fechaApertura || !fechaCierre || fechaApertura >= fechaCierre) {
      setError("La fecha de cierre debe ser posterior a la de apertura.")
      return
    }
    if (cantidadIntentos < 1) {
      setError("Los intentos permitidos deben ser al menos 1.")
      return
    }

    if (!materiaId) return
    try {
      await crearActividad(
        {
          materiaId,
          titulo: titulo.trim(),
          fechaApertura,
          fechaCierre,
          cantidadPreguntas,
          cantidadIntentosPermitidos: cantidadIntentos,
          comisionesIds: [...comisionesSeleccionadas],
          unidadTematica: unidadTematica || null,
          tema: tema || null,
        },
        controladorSubmitRef.current?.signal,
      )
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 422) {
        setError(err.message)
        return
      }
      throw err
    }
    void navigate(`/actividad-evaluativa/materias/${materiaId}/actividades`)
  }

  if (materia === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          {
            label: materia.nombre,
            to: `/actividad-evaluativa/materias/${materiaId}/actividades`,
          },
          { label: "Actividades", to: `/actividad-evaluativa/materias/${materiaId}/actividades` },
          { label: "Nueva actividad" },
        ]}
      />
      <h1 className="text-lg font-semibold">Nueva actividad de período abierto</h1>
      <p className="mt-1 text-sm text-muted-foreground">Materia: {materia.nombre}</p>

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
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="na-titulo">Título (opcional)</Label>
              <Input
                id="na-titulo"
                type="text"
                value={titulo}
                onChange={(event) => setTitulo(event.target.value)}
                placeholder="Ej: Parcial 1 — Unidades 1 a 3"
              />
            </div>
            <div className="flex gap-4">
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="na-apertura">Apertura (fecha y hora)</Label>
                <Input
                  id="na-apertura"
                  type="datetime-local"
                  required
                  value={fechaApertura}
                  onChange={(event) => setFechaApertura(event.target.value)}
                />
              </div>
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="na-cierre">Cierre (fecha y hora)</Label>
                <Input
                  id="na-cierre"
                  type="datetime-local"
                  required
                  value={fechaCierre}
                  onChange={(event) => setFechaCierre(event.target.value)}
                />
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Comisiones</Label>
              {comisiones.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  Esta materia todavía no tiene comisiones — la actividad queda visible para
                  todos sus estudiantes.
                </p>
              ) : (
                <>
                  <div className="flex flex-col gap-2 rounded-lg border border-border bg-muted/30 p-3">
                    {comisiones.map((comision) => (
                      <label
                        key={comision.id}
                        className="flex items-center gap-2.5 text-sm"
                        htmlFor={`na-comision-${comision.id}`}
                      >
                        <input
                          id={`na-comision-${comision.id}`}
                          type="checkbox"
                          className="size-4 rounded border-input accent-primary"
                          checked={comisionesSeleccionadas.has(comision.id)}
                          onChange={() => alternarComision(comision.id)}
                        />
                        {comision.horario}
                      </label>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {comisionesSeleccionadas.size === 0
                      ? "Ninguna marcada: la actividad queda visible para todas las comisiones de la materia."
                      : "Solo los estudiantes de las comisiones marcadas van a ver esta actividad."}
                  </p>
                </>
              )}
            </div>
            <div className="flex gap-4">
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="na-unidad">Unidad temática</Label>
                <Select
                  id="na-unidad"
                  value={unidadTematica}
                  onChange={(event) => setUnidadTematica(event.target.value)}
                >
                  <option value="">Todas</option>
                  {unidades.map((valor) => (
                    <option key={valor} value={valor}>
                      {valor}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="na-tema">Tema</Label>
                <Select
                  id="na-tema"
                  value={tema}
                  onChange={(event) => setTema(event.target.value)}
                >
                  <option value="">Todos</option>
                  {temas.map((valor) => (
                    <option key={valor} value={valor}>
                      {valor}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            <p className="-mt-3 text-xs text-muted-foreground">
              {hayRestriccion
                ? "Las preguntas de esta actividad salen solo de la combinación elegida de unidad temática y tema."
                : "Sin restricción: las preguntas pueden salir de cualquier unidad temática y tema del banco."}
            </p>
            <div className="flex gap-4">
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="na-cantidad-preguntas">Cantidad de preguntas</Label>
                <Input
                  id="na-cantidad-preguntas"
                  type="number"
                  min={1}
                  required
                  value={cantidadPreguntas}
                  onChange={(event) => setCantidadPreguntas(Number(event.target.value))}
                />
                <p className="text-xs text-muted-foreground">
                  No puede superar la cantidad de preguntas activas de{" "}
                  {hayRestriccion ? "esa selección" : "la materia"} ({cantidadDisponible}{" "}
                  disponibles)
                </p>
              </div>
              <div className="flex flex-1 flex-col gap-1.5">
                <Label htmlFor="na-cantidad-intentos">Intentos permitidos por pregunta</Label>
                <Input
                  id="na-cantidad-intentos"
                  type="number"
                  min={1}
                  required
                  value={cantidadIntentos}
                  onChange={(event) => setCantidadIntentos(Number(event.target.value))}
                />
                <p className="text-xs text-muted-foreground">
                  Por defecto 1 — cuántas veces puede responder la misma pregunta
                </p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Cada estudiante recibe un set aleatorio distinto, tomado del banco de preguntas de
              la materia.
            </p>
            <div className="flex gap-2 border-t border-border pt-5">
              <Button type="submit">Crear actividad</Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(`/actividad-evaluativa/materias/${materiaId}/actividades`)}
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
