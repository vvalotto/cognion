import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const { navigateMock } = vi.hoisted(() => ({ navigateMock: vi.fn() }))
vi.mock("@/router", () => ({
  router: { navigate: navigateMock },
}))

import { AutoregistroEstudiante } from "@/pages/identidad/AutoregistroEstudiante"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const MATERIAS = [
  { id: "mat-1", nombre: "Ingeniería de Software" },
  { id: "mat-2", nombre: "Gestión de Proyectos" },
]

const COMISIONES = [
  { id: "com-1", horario: "Lunes 18-21hs" },
  { id: "com-2", horario: "Miércoles 18-21hs" },
]

function renderPantalla() {
  return render(
    <MemoryRouter initialEntries={["/autoregistro/estudiante"]}>
      <Routes>
        <Route path="/autoregistro/estudiante" element={<AutoregistroEstudiante />} />
        <Route path="/autoregistro" element={<p>Autoregistro perfil</p>} />
        <Route path="/autoregistro/exito" element={<p>Autoregistro exito</p>} />
      </Routes>
    </MemoryRouter>
  )
}

async function elegirMateriaYComision() {
  const user = userEvent.setup()
  await screen.findByRole("option", { name: "Ingeniería de Software" })
  await user.selectOptions(screen.getByLabelText("Materia"), "mat-1")
  await screen.findByRole("option", { name: "Lunes 18-21hs" })
  await user.selectOptions(screen.getByLabelText("Comisión"), "com-1")
  return user
}

describe("AutoregistroEstudiante", () => {
  beforeEach(() => {
    navigateMock.mockClear()
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input)
        if (url.includes("/identidad/autoregistro/materias/")) {
          return Promise.resolve(jsonResponse(200, COMISIONES))
        }
        if (url.endsWith("/identidad/autoregistro/materias")) {
          return Promise.resolve(jsonResponse(200, MATERIAS))
        }
        return Promise.resolve(jsonResponse(404, { detail: "no configurado" }))
      }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("puebla el selector de Materia al montar", async () => {
    renderPantalla()

    expect(await screen.findByRole("option", { name: "Ingeniería de Software" })).toBeInTheDocument()
    expect(screen.getByRole("option", { name: "Gestión de Proyectos" })).toBeInTheDocument()
  })

  it("el selector de Comisión está deshabilitado hasta elegir una Materia", async () => {
    renderPantalla()
    await screen.findByRole("option", { name: "Ingeniería de Software" })

    expect(screen.getByLabelText("Comisión")).toBeDisabled()
  })

  it("elegir una Materia puebla el selector de Comisión con las comisiones de esa materia", async () => {
    renderPantalla()

    await elegirMateriaYComision()

    expect(screen.getByLabelText("Comisión")).not.toBeDisabled()
    expect(screen.getByRole("option", { name: "Miércoles 18-21hs" })).toBeInTheDocument()
  })

  it("autoregistro exitoso crea la cuenta y muestra la pantalla de éxito", async () => {
    renderPantalla()
    const user = await elegirMateriaYComision()

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, {
        id: "u1",
        nombre: "Vale",
        email: "vale@fiuner.edu.ar",
        tipo_perfil: "estudiante",
      }),
    )

    await user.type(screen.getByLabelText("Nombre completo"), "Vale")
    await user.type(screen.getByLabelText("Email"), "vale@fiuner.edu.ar")
    await user.type(screen.getByLabelText("Contraseña"), "Password#123x")
    await user.type(screen.getByLabelText("Confirmar contraseña"), "Password#123x")
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }))

    expect(await screen.findByText("Autoregistro exito")).toBeInTheDocument()
  })

  it("email ya registrado (409) muestra el error en el propio formulario, sin navegar", async () => {
    renderPantalla()
    const user = await elegirMateriaYComision()

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(409, { detail: "El email ya está registrado." }),
    )

    await user.type(screen.getByLabelText("Nombre completo"), "Vale")
    await user.type(screen.getByLabelText("Email"), "ya-existe@fiuner.edu.ar")
    await user.type(screen.getByLabelText("Contraseña"), "Password#123x")
    await user.type(screen.getByLabelText("Confirmar contraseña"), "Password#123x")
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }))

    expect(await screen.findByRole("alert")).toHaveTextContent("El email ya está registrado.")
  })

  it("contraseñas que no coinciden muestran error de cliente sin llamar al backend de autoregistro", async () => {
    renderPantalla()
    const user = await elegirMateriaYComision()
    const llamadasPrevias = vi.mocked(fetch).mock.calls.length

    await user.type(screen.getByLabelText("Nombre completo"), "Vale")
    await user.type(screen.getByLabelText("Email"), "vale@fiuner.edu.ar")
    await user.type(screen.getByLabelText("Contraseña"), "Password#123x")
    await user.type(screen.getByLabelText("Confirmar contraseña"), "otra-password")
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }))

    expect(await screen.findByRole("alert")).toHaveTextContent("Las contraseñas no coinciden.")
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.length).toBe(llamadasPrevias))
  })

  it("el link '‹ Elegir otro perfil' navega a /autoregistro", async () => {
    const user = userEvent.setup()
    renderPantalla()

    await user.click(screen.getByRole("link", { name: "‹ Elegir otro perfil" }))

    expect(await screen.findByText("Autoregistro perfil")).toBeInTheDocument()
  })
})
