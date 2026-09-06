import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EvaluacionSuspendida } from "@/pages/actividad-evaluativa/EvaluacionSuspendida"

const ACTIVIDAD_ID = "act-1"
const EVALUACION_ID = "eval-1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function evaluacionBody(overrides?: Partial<Record<string, unknown>>) {
  return {
    id: EVALUACION_ID,
    actividad_id: ACTIVIDAD_ID,
    estudiante_id: "est-1",
    preguntas_asignadas: [],
    preguntas_respondidas: ["p1", "p2", "p3"],
    respuestas_confirmadas: [],
    estado: "Suspendida",
    iniciada_en: "2026-09-01T00:00:00+00:00",
    ...overrides,
  }
}

function renderEvaluacionSuspendida() {
  return render(
    <MemoryRouter initialEntries={[`/mis-actividades/actividades/${ACTIVIDAD_ID}/suspendida`]}>
      <Routes>
        <Route
          path="/mis-actividades/actividades/:actividadId/suspendida"
          element={<EvaluacionSuspendida />}
        />
        <Route
          path="/mis-actividades/actividades/:actividadId/rendir"
          element={<p>Rendir</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EvaluacionSuspendida", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra la cantidad de respuestas ya guardadas", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, evaluacionBody()))
    renderEvaluacionSuspendida()

    expect(await screen.findByText(/Guardamos tus 3 respuestas/)).toBeInTheDocument()
  })

  it("continuar reanuda la evaluación y navega de vuelta a rendir", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, evaluacionBody()))
    renderEvaluacionSuspendida()
    await screen.findByText(/Guardamos tus 3 respuestas/)

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, evaluacionBody({ estado: "EnCurso" })),
    )

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Continuar" }))

    expect(await screen.findByText("Rendir")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(ultimaLlamada?.[0]).toContain(`/evaluaciones/${EVALUACION_ID}/reanudar`)
  })

  it("menciona el mecanismo automático de pausa por inactividad", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, evaluacionBody()))
    renderEvaluacionSuspendida()

    expect(await screen.findByText("También pasa automáticamente")).toBeInTheDocument()
  })
})
