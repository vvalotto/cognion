import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { MiDesempeno } from "@/pages/analytics/MiDesempeno"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function actividadVisible(id: string, titulo: string) {
  return {
    id,
    materia_id: "m1",
    titulo,
    fecha_apertura: "2026-08-01T00:00:00+00:00",
    fecha_cierre: "2026-09-01T00:00:00+00:00",
    estado: "finalizada",
    evaluacion_id: "e1",
  }
}

function desempeno(evaluaciones: unknown[], resumen: Record<string, number>) {
  return { evaluaciones, resumen }
}

function evaluacionDetalle(actividadId: string, finalizadaEn: string, correctas: number, incorrectas: number) {
  return {
    evaluacion_id: `ev-${actividadId}`,
    actividad_id: actividadId,
    finalizada_en: finalizadaEn,
    cantidad_correctas: correctas,
    cantidad_incorrectas: incorrectas,
  }
}

function renderMiDesempeno() {
  return render(
    <MemoryRouter>
      <MiDesempeno />
    </MemoryRouter>,
  )
}

describe("MiDesempeno", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("una sola materia: sin selector, muestra resumen y detalle", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          desempeno(
            [evaluacionDetalle("a1", "2026-08-30T10:00:00Z", 14, 3)],
            {
              total_correctas: 14,
              total_incorrectas: 3,
              porcentaje_acierto: 82,
              cantidad_evaluaciones: 1,
            },
          ),
        ),
      )
      .mockResolvedValueOnce(jsonResponse(200, [actividadVisible("a1", "Parcial 1")]))

    renderMiDesempeno()

    expect(await screen.findByText("Parcial 1")).toBeInTheDocument()
    expect(screen.getByText("14")).toBeInTheDocument()
    expect(screen.getByText("3")).toBeInTheDocument()
    expect(screen.getByText("82%")).toBeInTheDocument()
    expect(screen.queryByLabelText("Materia")).not.toBeInTheDocument()
  })

  it("ordena el detalle por fecha de finalización descendente y usa un título de reserva si no se resuelve la actividad", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          desempeno(
            [
              evaluacionDetalle("a1", "2026-08-30T10:00:00Z", 14, 3),
              evaluacionDetalle("a2", "2026-09-10T10:00:00Z", 5, 1),
            ],
            {
              total_correctas: 19,
              total_incorrectas: 4,
              porcentaje_acierto: 83,
              cantidad_evaluaciones: 2,
            },
          ),
        ),
      )
      // Solo se resuelve el título de "a2" — "a1" queda sin match y usa el título de reserva.
      .mockResolvedValueOnce(jsonResponse(200, [actividadVisible("a2", "Repaso Unidad 2")]))

    renderMiDesempeno()

    const titulos = (await screen.findAllByText(/Repaso Unidad 2|Evaluación/)).map(
      (el) => el.textContent,
    )
    expect(titulos).toEqual(["Repaso Unidad 2", "Evaluación"])
  })

  it("más de una materia: muestra el selector y actualiza al cambiar la selección", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "m1", nombre: "Ingeniería de Software" },
          { id: "m2", nombre: "Gestión de Proyectos" },
        ]),
      )
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          desempeno([evaluacionDetalle("a1", "2026-08-30T10:00:00Z", 14, 3)], {
            total_correctas: 14,
            total_incorrectas: 3,
            porcentaje_acierto: 82,
            cantidad_evaluaciones: 1,
          }),
        ),
      )
      .mockResolvedValueOnce(jsonResponse(200, [actividadVisible("a1", "Parcial 1")]))

    renderMiDesempeno()

    expect(await screen.findByText("Parcial 1")).toBeInTheDocument()
    const selector = screen.getByLabelText("Materia")
    expect(selector).toBeInTheDocument()

    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          desempeno([evaluacionDetalle("a2", "2026-09-01T10:00:00Z", 5, 1)], {
            total_correctas: 5,
            total_incorrectas: 1,
            porcentaje_acierto: 83,
            cantidad_evaluaciones: 1,
          }),
        ),
      )
      .mockResolvedValueOnce(jsonResponse(200, [actividadVisible("a2", "Repaso Unidad 2")]))

    const user = userEvent.setup()
    await user.selectOptions(selector, "m2")

    expect(await screen.findByText("Repaso Unidad 2")).toBeInTheDocument()
    expect(screen.queryByText("Parcial 1")).not.toBeInTheDocument()
  })

  it("materia sin evaluaciones finalizadas: muestra el estado vacío", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockResolvedValueOnce(jsonResponse(200, desempeno([], {
        total_correctas: 0,
        total_incorrectas: 0,
        porcentaje_acierto: 0,
        cantidad_evaluaciones: 0,
      })))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderMiDesempeno()

    expect(
      await screen.findByText("Todavía no finalizaste ninguna evaluación de esta materia."),
    ).toBeInTheDocument()
  })

  it("error de red/servidor: muestra un mensaje genérico sin romper la pantalla", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockRejectedValueOnce(new Error("network error"))

    renderMiDesempeno()

    await waitFor(() =>
      expect(
        screen.getByText("No se pudo cargar tu desempeño. Intentá de nuevo más tarde."),
      ).toBeInTheDocument(),
    )
  })

  it("un fetch abortado (cambio de materia en curso) no muestra el mensaje de error", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockRejectedValueOnce(new DOMException("aborted", "AbortError"))
      .mockRejectedValueOnce(new DOMException("aborted", "AbortError"))

    renderMiDesempeno()

    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalledTimes(3))
    expect(
      screen.queryByText("No se pudo cargar tu desempeño. Intentá de nuevo más tarde."),
    ).not.toBeInTheDocument()
  })
})
