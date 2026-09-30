import { useEffect, useState } from "react"

import { listarMaterias } from "@/lib/banco-preguntas-api"

/**
 * Nombre de una Materia para los breadcrumbs de las pantallas de Comisión, que ahora cuelgan del
 * detalle de la Materia (revisión manual 2026-09-26). Incluye materias inactivas.
 */
export function useNombreMateria(materiaId: string | null | undefined): string | null {
  const [nombre, setNombre] = useState<string | null>(null)

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    listarMaterias(controller.signal, true)
      .then((materias) => setNombre(materias.find((m) => m.id === materiaId)?.nombre ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  return nombre
}

/** Ruta del detalle de la Materia (o el listado, si todavía no se conoce). */
export function rutaMateria(materiaId: string | null | undefined): string {
  return materiaId ? `/materias/${materiaId}/ver` : "/materias"
}
