import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EditarCuenta } from "@/pages/cuentas/EditarCuenta"

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
  bloqueada: false,
  creado_en: "2026-08-01T10:00:00Z",
  comision_id: null,
}

function renderEditarCuenta() {
  return render(
    <MemoryRouter initialEntries={["/cuentas/u1/editar"]}>
      <Routes>
        <Route path="/cuentas/:usuarioId/editar" element={<EditarCuenta />} />
        <Route path="/cuentas/:usuarioId" element={<p>Detalle de cuenta</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EditarCuenta", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("precarga el formulario con los datos actuales de la cuenta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaApi))

    renderEditarCuenta()

    expect(await screen.findByLabelText("Nombre completo")).toHaveValue("Ana Docente")
    expect(screen.getByLabelText("Email")).toHaveValue("ana@fiuner.edu.ar")
  })

  it("guarda los cambios y navega al detalle de la cuenta", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, cuentaApi))
      .mockResolvedValueOnce(jsonResponse(200, { ...cuentaApi, nombre: "Ana M. Docente" }))
    const user = userEvent.setup()

    renderEditarCuenta()
    await screen.findByLabelText("Nombre completo")

    await user.clear(screen.getByLabelText("Nombre completo"))
    await user.type(screen.getByLabelText("Nombre completo"), "Ana M. Docente")
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }))

    expect(await screen.findByText("Detalle de cuenta")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(String(ultimaLlamada?.[0])).toMatch(/\/usuarios\/u1$/)
    expect(ultimaLlamada?.[1]?.method).toBe("PATCH")
  })

  it("muestra un error si el email ya pertenece a otra cuenta (409)", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, cuentaApi))
      .mockResolvedValueOnce(
        jsonResponse(409, { detail: "El email 'otra@fiuner.edu.ar' ya está registrado." }),
      )
    const user = userEvent.setup()

    renderEditarCuenta()
    await screen.findByLabelText("Email")

    await user.clear(screen.getByLabelText("Email"))
    await user.type(screen.getByLabelText("Email"), "otra@fiuner.edu.ar")
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }))

    expect(await screen.findByRole("alert")).toHaveTextContent(/ya existe otra cuenta/i)
  })

  it("cancelar vuelve al detalle de la cuenta sin ejecutar ningún cambio", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaApi))
    const user = userEvent.setup()

    renderEditarCuenta()
    await screen.findByLabelText("Nombre completo")

    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Detalle de cuenta")).toBeInTheDocument()
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1)
  })
})
