import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { fetchConMaterias, llamadasSinMaterias } from "@/test/fetch-con-materias"

import { EliminarComision } from "@/pages/identidad/EliminarComision"

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

function renderEliminarComision() {
  return render(
    <MemoryRouter initialEntries={["/comisiones/c1/eliminar"]}>
      <Routes>
        <Route path="/comisiones/:comisionId/eliminar" element={<EliminarComision />} />
        <Route path="/comisiones/:comisionId" element={<p>Detalle de comisión</p>} />
        <Route path="/materias/:materiaId/ver" element={<p>Detalle de materia</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EliminarComision", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el horario de la comisión a eliminar", async () => {
    fetchConMaterias([
      jsonResponse(200, comisionApi),
    ])

    renderEliminarComision()

    expect((await screen.findAllByText("Lunes 18-20hs")).length).toBeGreaterThan(0)
  })

  it("confirmar elimina y vuelve al detalle de la materia", async () => {
    fetchConMaterias([
      jsonResponse(200, comisionApi),
      new Response(null, { status: 204 }),
    ])
    const user = userEvent.setup()

    renderEliminarComision()
    await screen.findAllByText("Lunes 18-20hs")

    await user.click(screen.getByRole("button", { name: "Sí, eliminar" }))

    expect(await screen.findByText("Detalle de materia")).toBeInTheDocument()
    const ultimaLlamada = llamadasSinMaterias().at(-1)
    expect(String(ultimaLlamada?.[0])).toMatch(/\/comisiones\/c1$/)
    expect(ultimaLlamada?.[1]?.method).toBe("DELETE")
  })

  it("cancelar vuelve al detalle sin eliminar nada", async () => {
    fetchConMaterias([
      jsonResponse(200, comisionApi),
    ])
    const user = userEvent.setup()

    renderEliminarComision()
    await screen.findAllByText("Lunes 18-20hs")

    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Detalle de comisión")).toBeInTheDocument()
    expect(llamadasSinMaterias()).toHaveLength(1)
  })
})
