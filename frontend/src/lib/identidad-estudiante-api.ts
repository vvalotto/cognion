import { apiFetch } from "@/lib/api-client"

export interface MateriaEstudianteResponse {
  id: string
  nombre: string
}

interface MateriaEstudianteApiResponse {
  id: string
  nombre: string
}

/** Cliente API de autoservicio del Estudiante en BC Identidad (`US-3.4.5`). */
export async function listarMisMaterias(): Promise<MateriaEstudianteResponse[]> {
  const response = await apiFetch<MateriaEstudianteApiResponse[]>("/identidad/estudiante/materias")
  return response.map((materia) => ({ id: materia.id, nombre: materia.nombre }))
}
