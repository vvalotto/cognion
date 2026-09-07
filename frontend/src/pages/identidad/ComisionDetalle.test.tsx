import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ComisionDetalle } from "@/pages/identidad/ComisionDetalle"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderComisionDetalle(comisionId = "c1") {
  return render(
    <MemoryRouter initialEntries={[`/comisiones/${comisionId}`]}>
      <Routes>
        <Route path="/comisiones/:comisionId" element={<ComisionDetalle />} />
        <Route path="/comisiones" element={<p>Comisiones listado</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

const comisionSinDocente = {
  id: "c1",
  materia_id: "m1",
  horario: "Lunes 18-20hs",
  administrador_id: "a1",
  docentes_asignados: [],
}

const comisionConDocente = {
  ...comisionSinDocente,
  docentes_asignados: ["d1"],
}

const docentes = {
  cuentas: [{ id: "d1", nombre: "Juan Pérez", email: "juan@x.com", perfil: "docente", bloqueada: false }],
  total: 1,
}

describe("ComisionDetalle", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra la alerta de 'sin docente asignado' cuando la comisión no tiene ninguno", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comisionSinDocente))
      .mockResolvedValueOnce(jsonResponse(200, docentes))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderComisionDetalle()

    expect(
      await screen.findByText(/no puede generar link de invitación/),
    ).toBeInTheDocument()
    expect(screen.getByText("Sin docente asignado")).toBeInTheDocument()
  })

  it("no muestra la alerta cuando ya hay un docente asignado", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comisionConDocente))
      .mockResolvedValueOnce(jsonResponse(200, docentes))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderComisionDetalle()

    expect(await screen.findByText("Juan Pérez")).toBeInTheDocument()
    expect(screen.queryByText(/no puede generar link de invitación/)).not.toBeInTheDocument()
  })

  it("asigna un docente y actualiza la vista sin recargar", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comisionSinDocente))
      .mockResolvedValueOnce(jsonResponse(200, docentes))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, comisionConDocente))

    renderComisionDetalle()
    await screen.findByText("Sin docente asignado")

    const user = userEvent.setup()
    await user.selectOptions(screen.getByLabelText("Asignar Docente"), "d1")
    await user.click(screen.getByRole("button", { name: "Asignar" }))

    expect(await screen.findByText("Juan Pérez")).toBeInTheDocument()
    expect(screen.queryByText("Sin docente asignado")).not.toBeInTheDocument()
    const [url, init] = vi.mocked(fetch).mock.calls[3]
    expect(String(url)).toContain("/comisiones/c1/docentes")
    expect(JSON.parse(init?.body as string)).toEqual({ docente_id: "d1" })
  })

  it("muestra el estado vacío de estudiantes", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comisionSinDocente))
      .mockResolvedValueOnce(jsonResponse(200, docentes))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderComisionDetalle()

    expect(
      await screen.findByText("Esta comisión todavía no tiene estudiantes inscriptos."),
    ).toBeInTheDocument()
  })

  it("lista los estudiantes inscriptos", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comisionSinDocente))
      .mockResolvedValueOnce(jsonResponse(200, docentes))
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "e1", nombre: "Ana Gómez" }]))

    renderComisionDetalle()

    expect(await screen.findByText("Ana Gómez")).toBeInTheDocument()
  })

  it("el botón 'Volver a Comisiones' navega al listado", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comisionSinDocente))
      .mockResolvedValueOnce(jsonResponse(200, docentes))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderComisionDetalle()
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Lunes 18-20hs" })).toBeInTheDocument(),
    )

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "‹ Volver a Comisiones" }))

    expect(await screen.findByText("Comisiones listado")).toBeInTheDocument()
  })
})
