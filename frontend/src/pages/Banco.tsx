import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import {
  filtrarBanco,
  listarMaterias,
  type Dificultad,
  type FiltrosBanco,
  type Importancia,
  type MateriaListItemResponse,
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

/** Pantalla de listado y filtro del banco de preguntas (§2.3 `wireframes-banco-preguntas.md`). */
export function Banco() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [preguntas, setPreguntas] = useState<PreguntaResponse[] | null>(null)
  const [unidad, setUnidad] = useState("")
  const [tema, setTema] = useState("")
  const [dificultad, setDificultad] = useState<Dificultad | "">("")
  const [importancia, setImportancia] = useState<Importancia | "">("")

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
    const filtros: FiltrosBanco = {
      unidad: unidad || undefined,
      tema: tema || undefined,
      dificultad: dificultad || undefined,
      importancia: importancia || undefined,
    }
    filtrarBanco(materia.bancoId, filtros).then((resultado) => {
      if (!cancelado) setPreguntas(resultado)
    })
    return () => {
      cancelado = true
    }
  }, [materia, unidad, tema, dificultad, importancia])

  function limpiarFiltros() {
    setUnidad("")
    setTema("")
    setDificultad("")
    setImportancia("")
  }

  if (materia === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">{materia.nombre}</h1>
          <p className="text-sm text-muted-foreground">
            {preguntas?.length ?? 0} pregunta{preguntas?.length === 1 ? "" : "s"} activa
            {preguntas?.length === 1 ? "" : "s"}
          </p>
        </div>
        <button
          type="button"
          className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          onClick={() => navigate(`/materias/${materiaId}/banco/preguntas/nueva`)}
        >
          + Nueva pregunta
        </button>
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="filtro-unidad" className="text-sm text-muted-foreground">
            Unidad temática
          </label>
          <input
            id="filtro-unidad"
            type="text"
            value={unidad}
            onChange={(e) => setUnidad(e.target.value)}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label htmlFor="filtro-tema" className="text-sm text-muted-foreground">
            Tema
          </label>
          <input
            id="filtro-tema"
            type="text"
            value={tema}
            onChange={(e) => setTema(e.target.value)}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label htmlFor="filtro-dificultad" className="text-sm text-muted-foreground">
            Dificultad
          </label>
          <select
            id="filtro-dificultad"
            value={dificultad}
            onChange={(e) => setDificultad(e.target.value as Dificultad | "")}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          >
            <option value="">Todas</option>
            {NIVELES.map((nivel) => (
              <option key={nivel} value={nivel}>
                {ETIQUETA_NIVEL[nivel]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="filtro-importancia" className="text-sm text-muted-foreground">
            Importancia
          </label>
          <select
            id="filtro-importancia"
            value={importancia}
            onChange={(e) => setImportancia(e.target.value as Importancia | "")}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          >
            <option value="">Todas</option>
            {NIVELES.map((nivel) => (
              <option key={nivel} value={nivel}>
                {ETIQUETA_NIVEL[nivel]}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className="rounded-md border border-border px-3 py-1 text-sm hover:bg-accent"
          onClick={limpiarFiltros}
        >
          Limpiar filtros
        </button>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              <th className="py-2 pr-4">Pregunta</th>
              <th className="py-2 pr-4">Tipo</th>
              <th className="py-2 pr-4">Unidad / Tema</th>
              <th className="py-2 pr-4">Dificultad</th>
              <th className="py-2 pr-4">Importancia</th>
              <th className="py-2 pr-4"></th>
            </tr>
          </thead>
          <tbody>
            {preguntas === null ? (
              <tr>
                <td colSpan={6} className="py-4 text-muted-foreground">
                  Cargando…
                </td>
              </tr>
            ) : (
              preguntas.map((pregunta) => (
                <tr key={pregunta.id} className="border-b border-border">
                  <td className="max-w-xs truncate py-2 pr-4">{pregunta.texto}</td>
                  <td className="py-2 pr-4">
                    {esOpcionMultiple(pregunta) ? "Opción múltiple" : "Verdadero/Falso"}
                  </td>
                  <td className="py-2 pr-4">
                    {pregunta.unidadTematica} · {pregunta.tema}
                  </td>
                  <td className="py-2 pr-4">{ETIQUETA_NIVEL[pregunta.dificultad]}</td>
                  <td className="py-2 pr-4">{ETIQUETA_NIVEL[pregunta.importancia]}</td>
                  <td className="py-2 pr-4">
                    <button
                      type="button"
                      className="mr-2 rounded-md border border-border px-2 py-1 text-xs hover:bg-accent"
                      onClick={() =>
                        navigate(
                          `/materias/${materiaId}/banco/preguntas/${pregunta.id}/editar`,
                        )
                      }
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      className="rounded-md border border-destructive px-2 py-1 text-xs text-destructive hover:bg-destructive/10"
                      onClick={() =>
                        navigate(
                          `/materias/${materiaId}/banco/preguntas/${pregunta.id}/eliminar`,
                        )
                      }
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
