import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EditarTituloActividad } from "@/pages/actividad-evaluativa/EditarTituloActividad"

const MATERIA_ID = "materia-1"
const ACTIVIDAD_ID = "act-1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function actividadResumen(titulo: string) {
  return {
    id: ACTIVIDAD_ID,
    materia_id: MATERIA_ID,
    titulo,
    fecha_apertura: "2026-09-20T09:00:00+00:00",
    fecha_cierre: "2026-09-27T23:59:00+00:00",
    cantidad_preguntas: 10,
    cantidad_intentos_permitidos: 1,
    estado: "en_curso",
    cantidad_evaluaciones_activas: 0,
    cantidad_evaluaciones_finalizadas: 0,
  }
}

function mockCargaInicial(tituloActual = "Parcial 1") {
  vi.mocked(fetch)
    .mockResolvedValueOnce(jsonResponse(200, actividadResumen(tituloActual)))
    .mockResolvedValueOnce(
      jsonResponse(200, [
        { id: MATERIA_ID, nombre: "Ingeniería de Software", banco_id: "banco-1", cantidad_preguntas_activas: 20 },
      ]),
    )
}

function renderEditarTitulo() {
  return render(
    <MemoryRouter
      initialEntries={[`/actividad-evaluativa/actividades/${ACTIVIDAD_ID}/editar-titulo`]}
    >
      <Routes>
        <Route
          path="/actividad-evaluativa/actividades/:actividadId/editar-titulo"
          element={<EditarTituloActividad />}
        />
        <Route
          path="/actividad-evaluativa/actividades/:actividadId"
          element={<p>Detalle de actividad</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EditarTituloActividad", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("precarga el título actual y lo edita con éxito", async () => {
    mockCargaInicial("Parcial 1")
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, {
        id: ACTIVIDAD_ID,
        materia_id: MATERIA_ID,
        fecha_apertura: "2026-09-20T09:00:00+00:00",
        fecha_cierre: "2026-09-27T23:59:00+00:00",
        cantidad_preguntas: 10,
        cantidad_intentos_permitidos: 1,
        cerrada_manualmente: false,
        titulo: "Parcial 1 (final)",
      }),
    )

    renderEditarTitulo()
    const input = await screen.findByLabelText("Título")
    expect(input).toHaveValue("Parcial 1")

    const user = userEvent.setup()
    await user.clear(input)
    await user.type(input, "Parcial 1 (final)")
    await user.click(screen.getByRole("button", { name: "Guardar título" }))

    expect(await screen.findByText("Detalle de actividad")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/actividades/${ACTIVIDAD_ID}/titulo`),
      expect.objectContaining({ method: "PATCH" }),
    )
  })

  it("cancelar vuelve al detalle sin llamar al backend", async () => {
    mockCargaInicial()

    renderEditarTitulo()
    await screen.findByLabelText("Título")
    const llamadasPrevias = vi.mocked(fetch).mock.calls.length

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Detalle de actividad")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(llamadasPrevias)
  })
})
