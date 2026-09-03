import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { CerrarActividad } from "@/pages/actividad-evaluativa/CerrarActividad"

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

function renderCerrarActividad() {
  return render(
    <MemoryRouter initialEntries={[`/actividad-evaluativa/actividades/${ACTIVIDAD_ID}/cerrar`]}>
      <Routes>
        <Route
          path="/actividad-evaluativa/actividades/:actividadId/cerrar"
          element={<CerrarActividad />}
        />
        <Route
          path="/actividad-evaluativa/actividades/:actividadId"
          element={<p>Detalle actividad</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("CerrarActividad", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra la cantidad de evaluaciones activas en el aviso destructivo", async () => {
    mockObtenerActividad()

    renderCerrarActividad()

    expect(
      await screen.findByText(/Las 3 evaluaciones en curso o suspendidas se finalizan/),
    ).toBeInTheDocument()
  })

  it("confirmar cierra la actividad y vuelve al detalle", async () => {
    mockObtenerActividad()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, {
        id: ACTIVIDAD_ID,
        materia_id: "materia-1",
        fecha_apertura: "2026-09-20T09:00:00",
        fecha_cierre: "2026-09-27T23:59:00",
        cantidad_preguntas: 10,
        cantidad_intentos_permitidos: 1,
        cerrada_manualmente: true,
        titulo: "Parcial 1",
      }),
    )

    renderCerrarActividad()
    const user = userEvent.setup()
    await user.click(await screen.findByRole("button", { name: "Sí, cerrar actividad ahora" }))

    expect(await screen.findByText("Detalle actividad")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/actividades/${ACTIVIDAD_ID}/cerrar`),
      expect.objectContaining({ method: "POST" }),
    )
  })

  it("cancelar vuelve al detalle sin llamar al backend", async () => {
    mockObtenerActividad()

    renderCerrarActividad()
    const user = userEvent.setup()
    await screen.findByRole("button", { name: "Cancelar" })
    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Detalle actividad")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(1)
  })
})
