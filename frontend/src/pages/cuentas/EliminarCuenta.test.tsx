import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EliminarCuenta } from "@/pages/cuentas/EliminarCuenta"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const cuentaResponse = {
  id: "u1",
  nombre: "Alejandra Morales",
  email: "alejandra.morales@fiuner.edu.ar",
  perfil: "docente",
  bloqueada: false,
  creado_en: "2026-01-01T00:00:00Z",
  comision_id: null,
  deshabilitada: false,
}

function renderEliminarCuenta() {
  return render(
    <MemoryRouter initialEntries={["/cuentas/u1/eliminar"]}>
      <Routes>
        <Route path="/cuentas/:usuarioId/eliminar" element={<EliminarCuenta />} />
        <Route path="/cuentas" element={<p>Cuentas listado</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EliminarCuenta", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el nombre y email de la cuenta a eliminar", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaResponse))

    renderEliminarCuenta()

    expect(await screen.findByText("Alejandra Morales")).toBeInTheDocument()
    expect(screen.getByText("alejandra.morales@fiuner.edu.ar")).toBeInTheDocument()
  })

  it("confirmar elimina y vuelve al listado de cuentas", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, cuentaResponse))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    const user = userEvent.setup()

    renderEliminarCuenta()
    await screen.findByText("Alejandra Morales")

    await user.click(screen.getByRole("button", { name: "Sí, eliminar" }))

    expect(await screen.findByText("Cuentas listado")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(String(ultimaLlamada?.[0])).toMatch(/\/usuarios\/u1$/)
    expect(ultimaLlamada?.[1]?.method).toBe("DELETE")
  })

  it("cancelar vuelve al listado sin eliminar nada", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaResponse))
    const user = userEvent.setup()

    renderEliminarCuenta()
    await screen.findByText("Alejandra Morales")

    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Cuentas listado")).toBeInTheDocument()
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1)
  })
})
