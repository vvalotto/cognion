import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EditarComision } from "@/pages/identidad/EditarComision"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const comisionApi = {
  id: "c1",
  materia_id: "m1",
  horario: "Lunes 18-20hs",
  administrador_id: "a1",
  docentes_asignados: [],
}

function renderEditarComision() {
  return render(
    <MemoryRouter initialEntries={["/comisiones/c1/editar"]}>
      <Routes>
        <Route path="/comisiones/:comisionId/editar" element={<EditarComision />} />
        <Route path="/comisiones/:comisionId" element={<p>Detalle de comisión</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EditarComision", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("precarga el horario actual de la comisión", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, comisionApi))

    renderEditarComision()

    expect(await screen.findByLabelText("Horario")).toHaveValue("Lunes 18-20hs")
  })

  it("guarda el horario corregido y vuelve al detalle de la comisión", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comisionApi))
      .mockResolvedValueOnce(jsonResponse(200, { ...comisionApi, horario: "Martes 19-21hs" }))
    const user = userEvent.setup()

    renderEditarComision()
    await screen.findByLabelText("Horario")

    await user.clear(screen.getByLabelText("Horario"))
    await user.type(screen.getByLabelText("Horario"), "Martes 19-21hs")
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }))

    expect(await screen.findByText("Detalle de comisión")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(String(ultimaLlamada?.[0])).toMatch(/\/comisiones\/c1$/)
    expect(ultimaLlamada?.[1]?.method).toBe("PATCH")
  })

  it("cancelar vuelve al detalle de la comisión sin ejecutar ningún cambio", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, comisionApi))
    const user = userEvent.setup()

    renderEditarComision()
    await screen.findByLabelText("Horario")

    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Detalle de comisión")).toBeInTheDocument()
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1)
  })
})
