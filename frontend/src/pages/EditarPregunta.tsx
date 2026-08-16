import { useEffect, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  editarPregunta,
  filtrarBanco,
  listarMaterias,
  type Dificultad,
  type Importancia,
  type MateriaListItemResponse,
  type Opcion,
  type PreguntaResponse,
} from "@/lib/banco-preguntas-api"

const NIVELES: Array<Dificultad | Importancia> = ["alto", "medio", "bajo"]
const ETIQUETA_NIVEL: Record<Dificultad | Importancia, string> = {
  alto: "Alto",
  medio: "Medio",
  bajo: "Bajo",
}

function esOpcionMultiple(pregunta: PreguntaResponse): boolean {
  return "opciones" in pregunta
}

function opcionVacia(): Opcion {
  return { texto: "", esCorrecta: false }
}

/** Pantalla de edición de una pregunta existente (§2.7 `wireframes-banco-preguntas.md`). */
export function EditarPregunta() {
  const { materiaId, preguntaId } = useParams<{ materiaId: string; preguntaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [pregunta, setPregunta] = useState<PreguntaResponse | null | undefined>(undefined)
  const [texto, setTexto] = useState("")
  const [opciones, setOpciones] = useState<Opcion[]>([opcionVacia(), opcionVacia()])
  const [respuestaCorrecta, setRespuestaCorrecta] = useState<boolean | null>(null)
  const [unidadTematica, setUnidadTematica] = useState("")
  const [tema, setTema] = useState("")
  const [dificultad, setDificultad] = useState<Dificultad>("medio")
  const [importancia, setImportancia] = useState<Importancia>("medio")
  const [error, setError] = useState<string | null>(null)

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
      const encontrada = preguntas.find((p) => p.id === preguntaId) ?? null
      setPregunta(encontrada)
      if (encontrada) {
        setTexto(encontrada.texto)
        setUnidadTematica(encontrada.unidadTematica)
        setTema(encontrada.tema)
        setDificultad(encontrada.dificultad)
        setImportancia(encontrada.importancia)
        if (esOpcionMultiple(encontrada) && "opciones" in encontrada) {
          setOpciones(encontrada.opciones)
        } else if ("respuestaCorrecta" in encontrada) {
          setRespuestaCorrecta(encontrada.respuestaCorrecta)
        }
      }
    })
    return () => {
      cancelado = true
    }
  }, [materia, preguntaId])

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

    if (!pregunta || !preguntaId) return
    const esOM = esOpcionMultiple(pregunta)

    if (esOM) {
      if (opciones.length < 2) {
        setError("Se necesitan al menos 2 opciones.")
        return
      }
      if (!opciones.some((o) => o.esCorrecta)) {
        setError("Marcá exactamente una opción como correcta.")
        return
      }
    } else if (respuestaCorrecta === null) {
      setError("Elegí si la respuesta correcta es Verdadero o Falso.")
      return
    }

    await editarPregunta(preguntaId, {
      texto,
      unidadTematica,
      tema,
      dificultad,
      importancia,
      opciones: esOM ? opciones : undefined,
      respuestaCorrecta: esOM ? undefined : (respuestaCorrecta ?? undefined),
    })
    void navigate(`/materias/${materiaId}/banco`)
  }

  if (materia === null || pregunta === undefined) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  if (pregunta === null) {
    return <p className="text-sm text-muted-foreground">No se encontró la pregunta a editar.</p>
  }

  const esOM = esOpcionMultiple(pregunta)

  return (
    <div>
      <p className="text-sm text-muted-foreground">Banco › Editar pregunta</p>
      <h1 className="text-lg font-semibold">
        Editar pregunta de {esOM ? "Opción múltiple" : "Verdadero/Falso"}
      </h1>

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
          <Label htmlFor="editar-texto">Texto de la pregunta</Label>
          <textarea
            id="editar-texto"
            required
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            className="rounded-md border border-border px-2 py-1 text-sm"
          />
        </div>

        {esOM ? (
          <div className="flex flex-col gap-2">
            <Label>Opciones</Label>
            {opciones.map((opcion, indice) => (
              <div key={indice} className="flex items-center gap-2">
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
          </div>
        ) : (
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
        )}

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="editar-unidad">Unidad temática</Label>
          <Input
            id="editar-unidad"
            type="text"
            required
            value={unidadTematica}
            onChange={(e) => setUnidadTematica(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="editar-tema">Tema</Label>
          <Input
            id="editar-tema"
            type="text"
            required
            value={tema}
            onChange={(e) => setTema(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="editar-dificultad">Dificultad</Label>
          <select
            id="editar-dificultad"
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
          <Label htmlFor="editar-importancia">Importancia</Label>
          <select
            id="editar-importancia"
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
          <Button type="submit">Guardar cambios</Button>
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
