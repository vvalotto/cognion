import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { RecuperarPasswordNueva } from "@/pages/identidad/RecuperarPasswordNueva"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderPantalla(token = "tok-123") {
  return render(
    <MemoryRouter initialEntries={[`/recuperar-password/${token}`]}>
      <Routes>
        <Route path="/recuperar-password/:token" element={<RecuperarPasswordNueva />} />
        <Route path="/recuperar-password/exito" element={<p>Contraseña actualizada</p>} />
        <Route path="/recuperar-password/invalido" element={<p>Link no válido</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

async function completarFormulario(
  user: ReturnType<typeof userEvent.setup>,
  { nueva = "nuevaClave123", confirmacion = "nuevaClave123" } = {},
) {
  await user.type(screen.getByLabelText("Contraseña nueva"), nueva)
  await user.type(screen.getByLabelText("Confirmar contraseña nueva"), confirmacion)
  await user.click(screen.getByRole("button", { name: "Guardar nueva contraseña" }))
}

describe("RecuperarPasswordNueva", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("token vigente y contraseña válida navega a la pantalla de éxito", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, {}))
    const user = userEvent.setup()

    renderPantalla("tok-123")
    await completarFormulario(user)

    expect(await screen.findByText("Contraseña actualizada")).toBeInTheDocument()
    const [url, options] = vi.mocked(fetch).mock.calls[0]
    expect(String(url)).toMatch(/\/identidad\/recuperar-password\/confirmar$/)
    expect(JSON.parse(String(options?.body))).toEqual({
      token: "tok-123",
      password_nueva: "nuevaClave123",
    })
  })

  it("rechaza una contraseña de menos de 12 caracteres sin llamar al backend", async () => {
    const user = userEvent.setup()

    renderPantalla()
    await completarFormulario(user, { nueva: "corta", confirmacion: "corta" })

    expect(await screen.findByRole("alert")).toHaveTextContent(/al menos 12 caracteres/i)
    expect(fetch).not.toHaveBeenCalled()
  })

  it("rechaza contraseña y confirmación que no coinciden sin llamar al backend", async () => {
    const user = userEvent.setup()

    renderPantalla()
    await completarFormulario(user, { nueva: "passwordUno1", confirmacion: "passwordDos1" })

    expect(await screen.findByRole("alert")).toHaveTextContent(/no coinciden/i)
    expect(fetch).not.toHaveBeenCalled()
  })

  it("una contraseña que no cumple la política del backend muestra error inline, sin navegar", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(422, { detail: "La contraseña debe incluir al menos una mayúscula, un número y un símbolo." }),
    )
    const user = userEvent.setup()

    renderPantalla()
    await completarFormulario(user)

    expect(await screen.findByRole("alert")).toHaveTextContent(/mayúscula, un número y un símbolo/i)
    expect(screen.getByRole("button", { name: "Guardar nueva contraseña" })).toBeInTheDocument()
  })

  it("un token vencido/inválido/ya usado navega a la pantalla de link no válido", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(422, { detail: "El token de recuperación 'tok-123' ya venció." }),
    )
    const user = userEvent.setup()

    renderPantalla("tok-123")
    await completarFormulario(user)

    expect(await screen.findByText("Link no válido")).toBeInTheDocument()
  })
})
