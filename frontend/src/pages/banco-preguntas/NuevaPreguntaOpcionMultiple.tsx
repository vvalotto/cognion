import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  cargarPreguntaOpcionMultiple,
  derivarSugerencias,
  filtrarBanco,
  listarMaterias,
  type Dificultad,
  type Importancia,
  type MateriaListItemResponse,
  type Opcion,
} from "@/lib/banco-preguntas-api"

const NIVELES: Array<Dificultad | Importancia> = ["alto", "medio", "bajo"]
const ETIQUETA_NIVEL: Record<Dificultad | Importancia, string> = {
  alto: "Alto",
  medio: "Medio",
  bajo: "Bajo",
}

function opcionVacia(): Opcion {
  return { texto: "", esCorrecta: false }
}

/** Formulario de carga de pregunta de Opción Múltiple (§2.5 `wireframes-banco-preguntas.md`). */
export function NuevaPreguntaOpcionMultiple() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [texto, setTexto] = useState("")
  const [opciones, setOpciones] = useState<Opcion[]>([opcionVacia(), opcionVacia()])
  const [unidadTematica, setUnidadTematica] = useState("")
  const [tema, setTema] = useState("")
  const [dificultad, setDificultad] = useState<Dificultad>("medio")
  const [importancia, setImportancia] = useState<Importancia>("medio")
  const [error, setError] = useState<string | null>(null)
  const [sugerenciasUnidad, setSugerenciasUnidad] = useState<string[]>([])
  const [sugerenciasTema, setSugerenciasTema] = useState<string[]>([])

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
    if (!materia) return undefined
    const controller = new AbortController()
    filtrarBanco(materia.bancoId, {}, undefined, controller.signal)
      .then((resultado) => {
        const { unidades, temas } = derivarSugerencias(resultado.preguntas)
        setSugerenciasUnidad(unidades)
        setSugerenciasTema(temas)
      })
      .catch(() => {})
    return () => controller.abort()
  }, [materia])

  useEffect(() => {
    const controller = controladorSubmitRef.current
    return () => controller?.abort()
  }, [])

  function actualizarOpcionTexto(indice: number, texto: string) {
    setOpciones((prev) => prev.map((o, i) => (i === indice ? { ...o, texto } : o)))
  }

  function marcarCorrecta(indice: number) {
    setOpciones((prev) => prev.map((o, i) => ({ ...o, esCorrecta: i === indice })))
  }

  function agregarOpcion() {
    setOpciones((prev) => [...prev, opcionVacia()])
  }

  function quitarOpcion(indice: number) {
    setOpciones((prev) => prev.filter((_, i) => i !== indice))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (opciones.length < 2) {
      setError("Se necesitan al menos 2 opciones.")
      return
    }
    if (!opciones.some((o) => o.esCorrecta)) {
      setError("Marcá exactamente una opción como correcta.")
      return
    }

    if (!materia) return
    try {
      await cargarPreguntaOpcionMultiple(
        {
          bancoId: materia.bancoId,
          texto,
          opciones,
          unidadTematica,
          tema,
          dificultad,
          importancia,
        },
        controladorSubmitRef.current?.signal,
      )
      void navigate(`/materias/${materiaId}/banco`)
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      throw err
    }
  }

  if (materia === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Banco de preguntas" },
          { label: materia?.nombre ?? "…", to: `/materias/${materiaId}/banco` },
          { label: "Nueva pregunta", to: `/materias/${materiaId}/banco/preguntas/nueva` },
          { label: "Opción múltiple" },
        ]}
      />
      <h1 className="text-lg font-semibold">Nueva pregunta — Opción múltiple</h1>

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
          <Label htmlFor="om-texto">Texto de la pregunta</Label>
          <textarea
            id="om-texto"
            required
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Escribí el enunciado..."
            className="rounded-md border border-border px-2 py-1 text-sm"
          />
        </div>

        <div className="flex flex-col gap-2">
          <Label>Opciones — marcá cuál es la correcta</Label>
          {opciones.map((opcion, indice) => (
            <div
              key={indice}
              className={
                "flex items-center gap-2 rounded-lg border px-2 py-1.5 " +
                (opcion.esCorrecta ? "border-accent bg-accent/10" : "border-border")
              }
            >
              <input
                type="radio"
                name="opcion-correcta"
                aria-label={`Marcar opción ${indice + 1} como correcta`}
                checked={opcion.esCorrecta}
                onChange={() => marcarCorrecta(indice)}
              />
              <Input
                type="text"
                required
                value={opcion.texto}
                onChange={(e) => actualizarOpcionTexto(indice, e.target.value)}
                placeholder={`Opción ${indice + 1}`}
              />
              <button
                type="button"
                disabled={opciones.length <= 2}
                aria-label={`Quitar opción ${indice + 1}`}
                onClick={() => quitarOpcion(indice)}
                className="rounded-md border border-border px-2 py-1 text-xs disabled:opacity-40"
              >
                ✕
              </button>
            </div>
          ))}
          <Button type="button" variant="outline" onClick={agregarOpcion}>
            + Agregar opción
          </Button>
          <p className="text-xs text-muted-foreground">
            Mínimo 2 opciones. Exactamente una debe estar marcada como correcta.
          </p>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="om-unidad">Unidad temática</Label>
          <Input
            id="om-unidad"
            type="text"
            required
            list="om-unidad-sugerencias"
            value={unidadTematica}
            onChange={(e) => setUnidadTematica(e.target.value)}
          />
          <datalist id="om-unidad-sugerencias">
            {sugerenciasUnidad.map((valor) => (
              <option key={valor} value={valor} />
            ))}
          </datalist>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="om-tema">Tema</Label>
          <Input
            id="om-tema"
            type="text"
            required
            list="om-tema-sugerencias"
            value={tema}
            onChange={(e) => setTema(e.target.value)}
          />
          <datalist id="om-tema-sugerencias">
            {sugerenciasTema.map((valor) => (
              <option key={valor} value={valor} />
            ))}
          </datalist>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="om-dificultad">Dificultad</Label>
          <select
            id="om-dificultad"
            value={dificultad}
            onChange={(e) => setDificultad(e.target.value as Dificultad)}
            className="rounded-md border border-border px-2 py-1 text-sm"
          >
            {NIVELES.map((nivel) => (
              <option key={nivel} value={nivel}>
                {ETIQUETA_NIVEL[nivel]}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="om-importancia">Importancia</Label>
          <select
            id="om-importancia"
            value={importancia}
            onChange={(e) => setImportancia(e.target.value as Importancia)}
            className="rounded-md border border-border px-2 py-1 text-sm"
          >
            {NIVELES.map((nivel) => (
              <option key={nivel} value={nivel}>
                {ETIQUETA_NIVEL[nivel]}
              </option>
            ))}
          </select>
        </div>

        <div className="flex gap-2">
          <Button type="submit">Guardar pregunta</Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate(`/materias/${materiaId}/banco`)}
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
