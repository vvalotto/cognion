import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { CambiarPassword } from "@/pages/identidad/CambiarPassword"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(body === null ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderCambiarPassword() {
  return render(
    <MemoryRouter initialEntries={["/materias", "/mi-cuenta/cambiar-password"]} initialIndex={1}>
      <Routes>
        <Route path="/materias" element={<p>Materias</p>} />
        <Route path="/mi-cuenta/cambiar-password" element={<CambiarPassword />} />
      </Routes>
    </MemoryRouter>,
  )
}

async function completarFormulario(
  user: ReturnType<typeof userEvent.setup>,
  { actual = "actual123", nueva = "nuevaClave123", confirmacion = "nuevaClave123" } = {},
) {
  await user.type(screen.getByLabelText("Contraseña actual"), actual)
  await user.type(screen.getByLabelText("Contraseña nueva"), nueva)
  await user.type(screen.getByLabelText("Confirmar contraseña nueva"), confirmacion)
  await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }))
}

describe("CambiarPassword", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("cambia la contraseña exitosamente y muestra la confirmación", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(204, null))
    const user = userEvent.setup()

    renderCambiarPassword()
    await completarFormulario(user)

    expect(await screen.findByText("Contraseña actualizada")).toBeInTheDocument()
    expect(screen.getByText(/no hizo falta volver a iniciar sesión/i)).toBeInTheDocument()
  })

  it('"Continuar" vuelve a la pantalla desde la que se navegó', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(204, null))
    const user = userEvent.setup()

    renderCambiarPassword()
    await completarFormulario(user)
    await screen.findByText("Contraseña actualizada")
    await user.click(screen.getByRole("button", { name: "Continuar" }))

    expect(await screen.findByText("Materias")).toBeInTheDocument()
  })

  it("rechaza una contraseña nueva de menos de 8 caracteres sin llamar al backend", async () => {
    const user = userEvent.setup()

    renderCambiarPassword()
    await completarFormulario(user, { nueva: "corta", confirmacion: "corta" })

    expect(await screen.findByRole("alert")).toHaveTextContent(/al menos 8 caracteres/i)
    expect(fetch).not.toHaveBeenCalled()
  })

  it("rechaza contraseña nueva y confirmación que no coinciden sin llamar al backend", async () => {
    const user = userEvent.setup()

    renderCambiarPassword()
    await completarFormulario(user, { nueva: "passwordUno1", confirmacion: "passwordDos1" })

    expect(await screen.findByRole("alert")).toHaveTextContent(/no coinciden/i)
    expect(fetch).not.toHaveBeenCalled()
  })

  it("muestra los intentos restantes cuando la contraseña actual es incorrecta y limpia los campos", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(401, {
        detail: { mensaje: "La contraseña actual es incorrecta.", intentos_restantes: 2 },
      }),
    )
    const user = userEvent.setup()

    renderCambiarPassword()
    await completarFormulario(user, { actual: "mala" })

    expect(await screen.findByRole("alert")).toHaveTextContent(/intentos restantes.*2/i)
    expect(screen.getByLabelText("Contraseña actual")).toHaveValue("")
    expect(screen.getByLabelText("Contraseña nueva")).toHaveValue("")
    expect(screen.getByLabelText("Confirmar contraseña nueva")).toHaveValue("")
  })

  it("muestra que la cuenta quedó bloqueada tras el tercer fallo consecutivo", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(401, {
        detail: { mensaje: "La contraseña actual es incorrecta.", bloqueada: true },
      }),
    )
    const user = userEvent.setup()

    renderCambiarPassword()
    await completarFormulario(user, { actual: "mala" })

    expect(await screen.findByRole("alert")).toHaveTextContent(/bloqueada/i)
    expect(screen.getByRole("alert")).toHaveTextContent(/administrador/i)
    expect(screen.getByRole("button", { name: "Cambiar contraseña" })).toBeDisabled()
  })
})
