import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const { navigateMock } = vi.hoisted(() => ({ navigateMock: vi.fn() }))
vi.mock("@/router", () => ({
  router: { navigate: navigateMock },
}))

import { Registro } from "@/pages/identidad/Registro"
import { getSession } from "@/lib/session"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function previewVigente(): Response {
  return jsonResponse(200, { materia: "Ingeniería de Software", horario: "lu 10-12" })
}

function renderRegistro(token = "token-vigente") {
  return render(
    <MemoryRouter initialEntries={[`/registro?token=${token}`]}>
      <Routes>
        <Route path="/registro" element={<Registro />} />
        <Route path="/registro/error" element={<p>Registro error</p>} />
        <Route path="/registro/exito" element={<p>Registro exito</p>} />
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>
  )
}

async function completarFormulario(
  email: string,
  password = "password123x",
  confirmar = password
) {
  const user = userEvent.setup()
  await user.type(await screen.findByLabelText("Nombre completo"), "Nico")
  await user.type(screen.getByLabelText("Email"), email)
  await user.type(screen.getByLabelText("Contraseña"), password)
  await user.type(screen.getByLabelText("Confirmar contraseña"), confirmar)
  await user.click(screen.getByRole("button", { name: "Crear cuenta" }))
}

describe("Registro", () => {
  beforeEach(() => {
    navigateMock.mockClear()
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el chip de materia y comisión de la invitación vigente (US-ADJ-08)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(previewVigente())

    renderRegistro()

    const chip = await screen.findByText(/Te vas a unir a/)
    expect(chip).toHaveTextContent("Ingeniería de Software — lu 10-12")
  })

  it("registro exitoso con invitación vigente crea el usuario y muestra la pantalla de éxito", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(previewVigente())
      .mockResolvedValueOnce(
        jsonResponse(201, {
          id: "u1",
          nombre: "Nico",
          email: "nico@fiuner.edu.ar",
          comision_id: "c1",
          materia: "Ingeniería de Software",
        })
      )

    renderRegistro()
    await completarFormulario("nico@fiuner.edu.ar")

    expect(await screen.findByText("Registro exito")).toBeInTheDocument()
    expect(getSession()).toBeNull()
  })

  it.each([
    ["token vencido", "token-vencido"],
    ["token ya usado", "token-ya-usado"],
    ["token inexistente", "token-inexistente"],
  ])(
    "%s (404/422 en la vista previa) navega directo a la pantalla de error, sin mostrar el formulario",
    async (_caso, token) => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(422, { detail: "La invitación ya no es válida." })
      )

      renderRegistro(token)

      expect(await screen.findByText("Registro error")).toBeInTheDocument()
      expect(screen.queryByLabelText("Nombre completo")).not.toBeInTheDocument()
    }
  )

  it.each([
    ["token vencido", "token-vencido"],
    ["token ya usado", "token-ya-usado"],
    ["token inexistente", "token-inexistente"],
  ])("%s (422 en el submit) muestra la misma pantalla de error de registro", async (_caso, token) => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(previewVigente())
      .mockResolvedValueOnce(jsonResponse(422, { detail: "La invitación ya no es válida." }))

    renderRegistro(token)
    await completarFormulario("nico@fiuner.edu.ar")

    expect(await screen.findByText("Registro error")).toBeInTheDocument()
  })

  it("email ya registrado (409) muestra el error en el propio formulario, sin navegar", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(previewVigente())
      .mockResolvedValueOnce(jsonResponse(409, { detail: "El email ya está registrado." }))

    renderRegistro()
    await completarFormulario("ya-existe@fiuner.edu.ar")

    expect(await screen.findByRole("alert")).toHaveTextContent("Ese email ya está registrado.")
    expect(screen.getByLabelText("Email")).toHaveValue("ya-existe@fiuner.edu.ar")
  })

  it("contraseñas que no coinciden muestran error de cliente sin llamar al backend", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(previewVigente())

    renderRegistro()
    await completarFormulario("nico@fiuner.edu.ar", "password123x", "otra-password")

    expect(await screen.findByRole("alert")).toHaveTextContent("Las contraseñas no coinciden.")
    expect(fetch).toHaveBeenCalledTimes(1)
  })
})
