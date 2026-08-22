import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  eliminarPregunta,
  filtrarBanco,
  listarMaterias,
  type MateriaListItemResponse,
  type PreguntaResponse,
} from "@/lib/banco-preguntas-api"

/** Pantalla de confirmación de eliminación de una pregunta (§2.8 `wireframes-banco-preguntas.md`). */
export function EliminarPregunta() {
  const { materiaId, preguntaId } = useParams<{ materiaId: string; preguntaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [pregunta, setPregunta] = useState<PreguntaResponse | null | undefined>(undefined)

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
      if (!cancelado) setPregunta(preguntas.find((p) => p.id === preguntaId) ?? null)
    })
    return () => {
      cancelado = true
    }
  }, [materia, preguntaId])

  async function handleEliminar() {
    if (!preguntaId) return
    await eliminarPregunta(preguntaId)
    void navigate(`/materias/${materiaId}/banco`)
  }

  function handleCancelar() {
    void navigate(`/materias/${materiaId}/banco`)
  }

  if (materia === null || pregunta === undefined) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  if (pregunta === null) {
    return <p className="text-sm text-muted-foreground">No se encontró la pregunta a eliminar.</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Banco de preguntas" },
          { label: "Banco", to: `/materias/${materiaId}/banco` },
          { label: "Eliminar pregunta" },
        ]}
      />
      <h1 className="text-lg font-semibold">Eliminar pregunta</h1>

      <Card className="mt-4 p-4">
        <p className="text-sm text-muted-foreground">Pregunta a eliminar:</p>
        <p className="mt-1 font-medium">{pregunta.texto}</p>
      </Card>

      <div
        role="alert"
        className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        <p>
          Esta es una baja lógica: la pregunta deja de estar disponible para el banco y nuevas
          sesiones, pero las sesiones pasadas que ya la usaron no se ven afectadas.
        </p>
      </div>

      <div className="mt-4 flex gap-2">
        <Button variant="destructive-solid" onClick={handleEliminar}>
          Sí, eliminar
        </Button>
        <Button variant="outline" onClick={handleCancelar}>
          Cancelar
        </Button>
      </div>
    </div>
  )
}
