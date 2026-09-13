import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { RecuperarPasswordSolicitar } from "@/pages/identidad/RecuperarPasswordSolicitar"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderPantalla() {
  return render(
    <MemoryRouter initialEntries={["/recuperar-password"]}>
      <Routes>
        <Route path="/recuperar-password" element={<RecuperarPasswordSolicitar />} />
        <Route path="/recuperar-password/solicitado" element={<p>Revisá tu email</p>} />
        <Route path="/login" element={<p>Iniciar sesión</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("RecuperarPasswordSolicitar", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("envía el email y navega a la pantalla de confirmación", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(202, {}))
    const user = userEvent.setup()

    renderPantalla()
    await user.type(screen.getByLabelText("Email"), "ana@fiuner.edu.ar")
    await user.click(screen.getByRole("button", { name: "Enviar link de recuperación" }))

    expect(await screen.findByText("Revisá tu email")).toBeInTheDocument()
    const [, options] = vi.mocked(fetch).mock.calls[0]
    expect(JSON.parse(String(options?.body))).toEqual({ email: "ana@fiuner.edu.ar" })
  })

  it("el link 'Volver a iniciar sesión' navega a /login", async () => {
    const user = userEvent.setup()
    renderPantalla()

    await user.click(screen.getByRole("link", { name: /volver a iniciar sesión/i }))

    expect(await screen.findByText("Iniciar sesión")).toBeInTheDocument()
  })
})
