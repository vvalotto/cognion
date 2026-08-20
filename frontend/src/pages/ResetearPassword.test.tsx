import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ResetearPassword } from "@/pages/ResetearPassword"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const cuentaApi = {
  id: "u1",
  nombre: "Ana Docente",
  email: "ana@fiuner.edu.ar",
  perfil: "docente",
  bloqueada: true,
  creado_en: "2026-08-01T10:00:00Z",
  comision_id: null,
}

function renderResetearPassword() {
  return render(
    <MemoryRouter initialEntries={["/cuentas/u1/resetear-password"]}>
      <Routes>
        <Route path="/cuentas/:usuarioId/resetear-password" element={<ResetearPassword />} />
        <Route path="/cuentas/:usuarioId" element={<p>Detalle de cuenta</p>} />
        <Route path="/cuentas/:usuarioId/reseteada" element={<p>Contraseña reseteada</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("ResetearPassword", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("resetea la contraseña exitosamente y navega a la pantalla de confirmación", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, cuentaApi))
      .mockResolvedValueOnce(jsonResponse(200, { ...cuentaApi, bloqueada: false }))
    const user = userEvent.setup()

    renderResetearPassword()
    await screen.findByLabelText("Nueva contraseña temporal")

    await user.type(screen.getByLabelText("Nueva contraseña temporal"), "nuevaPassword123")
    await user.type(screen.getByLabelText("Confirmar contraseña"), "nuevaPassword123")
    await user.click(screen.getByRole("button", { name: "Resetear contraseña" }))

    expect(await screen.findByText("Contraseña reseteada")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(String(ultimaLlamada?.[0])).toMatch(/\/usuarios\/u1\/resetear-password$/)
  })

  it("rechaza una contraseña de menos de 8 caracteres sin llamar al backend", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaApi))
    const user = userEvent.setup()

    renderResetearPassword()
    await screen.findByLabelText("Nueva contraseña temporal")

    await user.type(screen.getByLabelText("Nueva contraseña temporal"), "corta")
    await user.type(screen.getByLabelText("Confirmar contraseña"), "corta")
    await user.click(screen.getByRole("button", { name: "Resetear contraseña" }))

    expect(await screen.findByRole("alert")).toHaveTextContent(/al menos 8 caracteres/i)
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1)
  })

  it("rechaza contraseña y confirmación que no coinciden sin llamar al backend", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaApi))
    const user = userEvent.setup()

    renderResetearPassword()
    await screen.findByLabelText("Nueva contraseña temporal")

    await user.type(screen.getByLabelText("Nueva contraseña temporal"), "passwordUno")
    await user.type(screen.getByLabelText("Confirmar contraseña"), "passwordDos")
    await user.click(screen.getByRole("button", { name: "Resetear contraseña" }))

    expect(await screen.findByRole("alert")).toHaveTextContent(/no coinciden/i)
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1)
  })

  it("cancelar vuelve al detalle de la cuenta sin ejecutar ningún cambio", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaApi))
    const user = userEvent.setup()

    renderResetearPassword()
    await screen.findByLabelText("Nueva contraseña temporal")

    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Detalle de cuenta")).toBeInTheDocument()
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1)
  })
})
