import { useEffect, useRef, useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router"

import { PasswordInput } from "@/components/PasswordInput"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { ApiError } from "@/lib/api-client"
import {
  autoregistrarEstudiante,
  listarComisionesAutoregistro,
  listarMateriasAutoregistro,
  type ComisionAutoregistroResponse,
  type MateriaAutoregistroResponse,
} from "@/lib/identidad-autoregistro-api"

/**
 * Pantalla de autoregistro de Estudiante (`#autoregistro-estudiante`,
 * `wireframes-identidad-autoservicio.md` §5.3) — consume
 * `POST /identidad/autoregistro/estudiante` (`US-ADJ-42`). Selector Materia→Comisión en
 * cascada, antes de los datos personales (mismo orden que la spec).
 */
export function AutoregistroEstudiante() {
  const navigate = useNavigate()

  const [materias, setMaterias] = useState<MateriaAutoregistroResponse[] | null>(null)
  const [materiaId, setMateriaId] = useState("")
  const [comisiones, setComisiones] = useState<ComisionAutoregistroResponse[] | null>(null)
  const [comisionId, setComisionId] = useState("")

  const [nombre, setNombre] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmarPassword, setConfirmarPassword] = useState("")
  const [error, setError] = useState<string | null>(null)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    // Crea un controller nuevo en cada montaje real — mismo motivo que AutoregistroDocente.tsx.
    const controller = new AbortController()
    controladorSubmitRef.current = controller
    return () => controller.abort()
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    listarMateriasAutoregistro(controller.signal)
      .then((resultado) => setMaterias(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [])

  useEffect(() => {
    setComisionId("")
    if (!materiaId) {
      setComisiones(null)
      return
    }
    const controller = new AbortController()
    setComisiones(null)
    listarComisionesAutoregistro(materiaId, controller.signal)
      .then((resultado) => setComisiones(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (password !== confirmarPassword) {
      setError("Las contraseñas no coinciden.")
      return
    }

    try {
      await autoregistrarEstudiante(
        nombre,
        email,
        password,
        comisionId,
        controladorSubmitRef.current?.signal,
      )
      void navigate("/autoregistro/exito")
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && (err.status === 409 || err.status === 422)) {
        setError(err.message)
        return
      }
      throw err
    }
  }

  return (
    <div>
      <p className="mb-2 inline-block rounded-full bg-muted px-2.5 py-1 text-xs font-medium">
        🎓 Perfil: Estudiante
      </p>
      <h1 className="text-lg font-semibold">Creá tu cuenta de Estudiante</h1>
      <p className="mb-4 text-sm text-muted-foreground">
        Elegí tu materia y comisión para quedar inscripto
      </p>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-estudiante-materia">Materia</Label>
          <Select
            id="autoregistro-estudiante-materia"
            required
            value={materiaId}
            onChange={(event) => setMateriaId(event.target.value)}
          >
            <option value="" disabled>
              {materias === null ? "Cargando…" : "Elegí una materia"}
            </option>
            {materias?.map((materia) => (
              <option key={materia.id} value={materia.id}>
                {materia.nombre}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-estudiante-comision">Comisión</Label>
          <Select
            id="autoregistro-estudiante-comision"
            required
            disabled={!materiaId || comisiones === null}
            value={comisionId}
            onChange={(event) => setComisionId(event.target.value)}
          >
            <option value="" disabled>
              {!materiaId ? "Elegí primero una materia" : comisiones === null ? "Cargando…" : "Elegí una comisión"}
            </option>
            {comisiones?.map((comision) => (
              <option key={comision.id} value={comision.id}>
                {comision.horario}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-estudiante-nombre">Nombre completo</Label>
          <Input
            id="autoregistro-estudiante-nombre"
            type="text"
            required
            value={nombre}
            onChange={(event) => setNombre(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-estudiante-email">Email</Label>
          <Input
            id="autoregistro-estudiante-email"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-estudiante-password">Contraseña</Label>
          <PasswordInput
            id="autoregistro-estudiante-password"
            required
            minLength={12}
            mostrarFortaleza
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-estudiante-confirmar-password">Confirmar contraseña</Label>
          <PasswordInput
            id="autoregistro-estudiante-confirmar-password"
            required
            minLength={12}
            value={confirmarPassword}
            onChange={(event) => setConfirmarPassword(event.target.value)}
          />
        </div>
        <Button type="submit" disabled={!comisionId}>
          Crear cuenta
        </Button>
      </form>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        <Link
          to="/autoregistro"
          className="font-medium text-foreground underline-offset-2 hover:underline"
        >
          ‹ Elegir otro perfil
        </Link>
      </p>
    </div>
  )
}
