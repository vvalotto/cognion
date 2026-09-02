import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ExtenderPlazo } from "@/pages/ExtenderPlazo"

const ACTIVIDAD_ID = "act-1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function actividadBody(overrides?: Partial<Record<string, unknown>>) {
  return {
    id: ACTIVIDAD_ID,
    materia_id: "materia-1",
    titulo: "Parcial 1",
    fecha_apertura: "2026-09-20T09:00:00",
    fecha_cierre: "2026-09-27T23:59:00",
    cantidad_preguntas: 10,
    cantidad_intentos_permitidos: 1,
    estado: "en_curso",
    cerrada_manualmente: false,
    cantidad_evaluaciones_activas: 3,
    cantidad_evaluaciones_finalizadas: 0,
    ...overrides,
  }
}

function mockObtenerActividad(overrides?: Partial<Record<string, unknown>>) {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, actividadBody(overrides)))
}

function renderExtenderPlazo() {
  return render(
    <MemoryRouter initialEntries={[`/actividad-evaluativa/actividades/${ACTIVIDAD_ID}/extender-plazo`]}>
      <Routes>
        <Route
          path="/actividad-evaluativa/actividades/:actividadId/extender-plazo"
          element={<ExtenderPlazo />}
        />
        <Route
          path="/actividad-evaluativa/actividades/:actividadId"
          element={<p>Detalle actividad</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("ExtenderPlazo", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("extensión exitosa actualiza el cierre y vuelve al detalle", async () => {
    mockObtenerActividad()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, {
        id: ACTIVIDAD_ID,
        materia_id: "materia-1",
        fecha_apertura: "2026-09-20T09:00:00",
        fecha_cierre: "2026-09-29T23:59:00",
        cantidad_preguntas: 10,
        cantidad_intentos_permitidos: 1,
        cerrada_manualmente: false,
        titulo: "Parcial 1",
      }),
    )

    renderExtenderPlazo()
    const user = userEvent.setup()
    const inputNuevoCierre = await screen.findByLabelText("Nuevo cierre")
    await user.type(inputNuevoCierre, "2026-09-29T23:59")
    await user.click(screen.getByRole("button", { name: "Guardar nuevo cierre" }))

    expect(await screen.findByText("Detalle actividad")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/actividades/${ACTIVIDAD_ID}/periodo`),
      expect.objectContaining({ method: "PATCH" }),
    )
  })

  it("rechazo del servidor por evaluaciones activas muestra el error inline sin navegar", async () => {
    mockObtenerActividad()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(422, {
        detail: "No se puede acortar el plazo de la actividad: hay evaluaciones activas.",
      }),
    )

    renderExtenderPlazo()
    const user = userEvent.setup()
    const inputNuevoCierre = await screen.findByLabelText("Nuevo cierre")
    await user.type(inputNuevoCierre, "2026-09-21T09:00")
    await user.click(screen.getByRole("button", { name: "Guardar nuevo cierre" }))

    expect(
      await screen.findByText(
        "No se puede acortar el plazo de la actividad: hay evaluaciones activas.",
      ),
    ).toBeInTheDocument()
    expect(screen.queryByText("Detalle actividad")).not.toBeInTheDocument()
  })

  it("cancelar vuelve al detalle sin llamar al backend", async () => {
    mockObtenerActividad()

    renderExtenderPlazo()
    const user = userEvent.setup()
    await screen.findByLabelText("Nuevo cierre")
    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Detalle actividad")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(1)
  })
})
