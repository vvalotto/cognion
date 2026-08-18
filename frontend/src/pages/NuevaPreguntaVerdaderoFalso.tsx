import { useEffect, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  cargarPreguntaVerdaderoFalso,
  derivarSugerencias,
  filtrarBanco,
  listarMaterias,
  type Dificultad,
  type Importancia,
  type MateriaListItemResponse,
} from "@/lib/banco-preguntas-api"

const NIVELES: Array<Dificultad | Importancia> = ["alto", "medio", "bajo"]
const ETIQUETA_NIVEL: Record<Dificultad | Importancia, string> = {
  alto: "Alto",
  medio: "Medio",
  bajo: "Bajo",
}

/** Formulario de carga de pregunta de Verdadero/Falso (§2.6 `wireframes-banco-preguntas.md`). */
export function NuevaPreguntaVerdaderoFalso() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [texto, setTexto] = useState("")
  const [respuestaCorrecta, setRespuestaCorrecta] = useState<boolean | null>(null)
  const [unidadTematica, setUnidadTematica] = useState("")
  const [tema, setTema] = useState("")
  const [dificultad, setDificultad] = useState<Dificultad>("medio")
  const [importancia, setImportancia] = useState<Importancia>("medio")
  const [error, setError] = useState<string | null>(null)
  const [sugerenciasUnidad, setSugerenciasUnidad] = useState<string[]>([])
  const [sugerenciasTema, setSugerenciasTema] = useState<string[]>([])

  useEffect(() => {
    let cancelado = false
    listarMaterias().then((materias) => {
      if (!cancelado) setMateria(materias.find((m) => m.id === materiaId) ?? null)
    })
    return () => {
      cancelado = true
    }
  }, [materiaId])

  useEffect(() => {
    if (!materia) return
    let cancelado = false
    filtrarBanco(materia.bancoId).then((preguntas) => {
      if (cancelado) return
      const { unidades, temas } = derivarSugerencias(preguntas)
      setSugerenciasUnidad(unidades)
      setSugerenciasTema(temas)
    })
    return () => {
      cancelado = true
    }
  }, [materia])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (respuestaCorrecta === null) {
      setError("Elegí si la respuesta correcta es Verdadero o Falso.")
      return
    }

    if (!materia) return
    await cargarPreguntaVerdaderoFalso({
      bancoId: materia.bancoId,
      texto,
      respuestaCorrecta,
      unidadTematica,
      tema,
      dificultad,
      importancia,
    })
    void navigate(`/materias/${materiaId}/banco`)
  }

  if (materia === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <p className="text-sm text-muted-foreground">Banco › Nueva pregunta › Verdadero/Falso</p>
      <h1 className="text-lg font-semibold">Cargar pregunta de Verdadero/Falso</h1>

      {error && (
        <div
          role="alert"
          className="mb-4 mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <form className="mt-4 flex flex-col gap-3" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="vf-texto">Texto de la pregunta</Label>
          <textarea
            id="vf-texto"
            required
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            className="rounded-md border border-border px-2 py-1 text-sm"
          />
        </div>

        <div className="flex flex-col gap-2">
          <Label>Respuesta correcta</Label>
          <div className="flex gap-2">
            <button
              type="button"
              aria-pressed={respuestaCorrecta === true}
              onClick={() => setRespuestaCorrecta(true)}
              className={`rounded-md border px-3 py-1 text-sm ${
                respuestaCorrecta === true
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border"
              }`}
            >
              Verdadero
            </button>
            <button
              type="button"
              aria-pressed={respuestaCorrecta === false}
              onClick={() => setRespuestaCorrecta(false)}
              className={`rounded-md border px-3 py-1 text-sm ${
                respuestaCorrecta === false
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border"
              }`}
            >
              Falso
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="vf-unidad">Unidad temática</Label>
          <Input
            id="vf-unidad"
            type="text"
            required
            list="vf-unidad-sugerencias"
            value={unidadTematica}
            onChange={(e) => setUnidadTematica(e.target.value)}
          />
          <datalist id="vf-unidad-sugerencias">
            {sugerenciasUnidad.map((valor) => (
              <option key={valor} value={valor} />
            ))}
          </datalist>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="vf-tema">Tema</Label>
          <Input
            id="vf-tema"
            type="text"
            required
            list="vf-tema-sugerencias"
            value={tema}
            onChange={(e) => setTema(e.target.value)}
          />
          <datalist id="vf-tema-sugerencias">
            {sugerenciasTema.map((valor) => (
              <option key={valor} value={valor} />
            ))}
          </datalist>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="vf-dificultad">Dificultad</Label>
          <select
            id="vf-dificultad"
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
          <Label htmlFor="vf-importancia">Importancia</Label>
          <select
            id="vf-importancia"
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
    </div>
  )
}
