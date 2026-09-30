import { readFileSync } from "node:fs"
import { join } from "node:path"

export const API = "http://localhost:8000"
export const PASSWORD = "Password123!UatE2e"
export const ESTADO = join(import.meta.dirname, "..", ".estado", "datos.json")

/** Temas del banco sembrado: cada circuito crea su sesión filtrando por uno (controla el tipo). */
export const TEMAS = {
  opcionMultiple: "Opcion multiple",
  verdaderoFalso: "Verdadero Falso",
  tresOpciones: "Tres opciones",
} as const

export interface Usuario {
  id: string
  email: string
  nombre: string
  token: string
}

export interface DatosSembrados {
  prefijo: string
  materiaId: string
  materiaNombre: string
  comisionId: string
  docente: Usuario
  estudiantes: Usuario[]
}

export function datos(): DatosSembrados {
  return JSON.parse(readFileSync(ESTADO, "utf8")) as DatosSembrados
}
