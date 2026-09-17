import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const { navigateMock } = vi.hoisted(() => ({ navigateMock: vi.fn() }))
vi.mock("@/router", () => ({
  router: { navigate: navigateMock },
}))

import { AutoregistroDocente } from "@/pages/identidad/AutoregistroDocente"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderPantalla() {
  return render(
    <MemoryRouter initialEntries={["/autoregistro/docente"]}>
      <Routes>
        <Route path="/autoregistro/docente" element={<AutoregistroDocente />} />
        <Route path="/autoregistro" element={<p>Autoregistro perfil</p>} />
        <Route path="/autoregistro/exito" element={<p>Autoregistro exito</p>} />
      </Routes>
    </MemoryRouter>
  )
}

async function completarFormulario(
  email: string,
  password = "Password#123x",
  confirmar = password,
) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText("Nombre completo"), "Nico")
  await user.type(screen.getByLabelText("Email"), email)
  await user.type(screen.getByLabelText("Contraseña"), password)
  await user.type(screen.getByLabelText("Confirmar contraseña"), confirmar)
  await user.click(screen.getByRole("button", { name: "Crear cuenta" }))
}

describe("AutoregistroDocente", () => {
  beforeEach(() => {
    navigateMock.mockClear()
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("autoregistro exitoso crea la cuenta y muestra la pantalla de éxito", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, {
        id: "u1",
        nombre: "Nico",
        email: "nico@fiuner.edu.ar",
        tipo_perfil: "docente",
      }),
    )

    renderPantalla()
    await completarFormulario("nico@fiuner.edu.ar")

    expect(await screen.findByText("Autoregistro exito")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/identidad/autoregistro/docente"),
      expect.objectContaining({ method: "POST" }),
    )
  })

  it("email ya registrado (409) muestra el error en el propio formulario, sin navegar", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(409, { detail: "El email ya está registrado." }),
    )

    renderPantalla()
    await completarFormulario("ya-existe@fiuner.edu.ar")

    expect(await screen.findByRole("alert")).toHaveTextContent("El email ya está registrado.")
    expect(screen.getByLabelText("Email")).toHaveValue("ya-existe@fiuner.edu.ar")
  })

  it("contraseña insegura (422) muestra el error del backend en el propio formulario", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(422, { detail: "La contraseña debe tener al menos 12 caracteres." }),
    )

    renderPantalla()
    await completarFormulario("nico@fiuner.edu.ar", "cortita1234", "cortita1234")

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "La contraseña debe tener al menos 12 caracteres.",
    )
  })

  it("contraseñas que no coinciden muestran error de cliente sin llamar al backend", async () => {
    renderPantalla()
    await completarFormulario("nico@fiuner.edu.ar", "Password#123x", "otra-password")

    expect(await screen.findByRole("alert")).toHaveTextContent("Las contraseñas no coinciden.")
    expect(fetch).not.toHaveBeenCalled()
  })

  it("el link '‹ Elegir otro perfil' navega a /autoregistro", async () => {
    const user = userEvent.setup()
    renderPantalla()

    await user.click(screen.getByRole("link", { name: "‹ Elegir otro perfil" }))

    expect(await screen.findByText("Autoregistro perfil")).toBeInTheDocument()
  })
})
