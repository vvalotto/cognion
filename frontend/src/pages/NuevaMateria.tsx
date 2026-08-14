import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { crearMateria } from "@/lib/banco-preguntas-api"
import { ApiError } from "@/lib/api-client"

/** Pantalla de alta de materia (§2.2 `wireframes-banco-preguntas.md`) — consume `POST /materias`. */
export function NuevaMateria() {
  const navigate = useNavigate()

  const [nombre, setNombre] = useState("")
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    try {
      await crearMateria(nombre)
      void navigate("/materias")
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("Ya existe una materia con ese nombre.")
        return
      }
      throw err
    }
  }

  return (
    <div>
      <p className="text-sm text-muted-foreground">Materias › Nueva materia</p>
      <h1 className="text-lg font-semibold">Crear materia</h1>

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
          <Label htmlFor="nueva-materia-nombre">Nombre de la materia</Label>
          <Input
            id="nueva-materia-nombre"
            type="text"
            required
            value={nombre}
            onChange={(event) => setNombre(event.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button type="submit">Crear materia</Button>
          <Button type="button" variant="outline" onClick={() => navigate("/materias")}>
            Cancelar
          </Button>
        </div>
      </form>
    </div>
  )
}
