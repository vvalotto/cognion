import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EliminarPregunta } from "@/pages/EliminarPregunta"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function paginado<T>(preguntas: T[]): { preguntas: T[]; total: number } {
  return { preguntas, total: preguntas.length }
}

const materiaResponse = [
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 2 },
]

const preguntaOpcionMultiple = {
  id: "p1",
  banco_id: "b1",
  texto: "¿Qué principio de Clean Architecture prohíbe importar una capa externa?",
  opciones: [
    { texto: "DIP", es_correcta: true },
    { texto: "SRP", es_correcta: false },
  ],
  unidad_tematica: "Unidad 3",
  tema: "Arquitectura",
  dificultad: "alto",
  importancia: "alto",
  activa: true,
}

const preguntasResponse = [preguntaOpcionMultiple]

function renderEliminacion(preguntaId: string) {
  return render(
    <MemoryRouter initialEntries={[`/materias/m1/banco/preguntas/${preguntaId}/eliminar`]}>
      <Routes>
        <Route
          path="/materias/:materiaId/banco/preguntas/:preguntaId/eliminar"
          element={<EliminarPregunta />}
        />
        <Route path="/materias/:materiaId/banco" element={<p>Banco</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EliminarPregunta", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el texto de la pregunta y la aclaración de baja lógica", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))

    renderEliminacion("p1")

    expect(await screen.findByText(preguntaOpcionMultiple.texto)).toBeInTheDocument()
    expect(screen.getByText(/baja lógica/)).toBeInTheDocument()
    expect(screen.getByText(/sesiones pasadas/)).toBeInTheDocument()
  })

  it("confirmar eliminación ejecuta la baja lógica y vuelve al banco", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    const user = userEvent.setup()

    renderEliminacion("p1")
    await screen.findByText(preguntaOpcionMultiple.texto)

    await user.click(screen.getByText("Sí, eliminar"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(ultimaLlamada?.[0]).toContain("/preguntas/p1")
    expect((ultimaLlamada![1] as RequestInit).method).toBe("DELETE")
  })

  it("cancelar vuelve al banco sin llamar al backend", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
    const user = userEvent.setup()

    renderEliminacion("p1")
    await screen.findByText(preguntaOpcionMultiple.texto)

    await user.click(screen.getByText("Cancelar"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it("pregunta inexistente muestra un mensaje en vez de la confirmación", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))

    renderEliminacion("no-existe")

    expect(
      await screen.findByText("No se encontró la pregunta a eliminar."),
    ).toBeInTheDocument()
  })
})
