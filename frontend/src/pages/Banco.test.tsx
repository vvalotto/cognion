import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { Banco } from "@/pages/Banco"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const materiaResponse = [
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 2 },
]

const preguntasResponse = [
  {
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
  },
  {
    id: "p2",
    banco_id: "b1",
    texto: "Un Aggregate Root solo referencia a otro por identidad.",
    respuesta_correcta: true,
    unidad_tematica: "Unidad 2",
    tema: "DDD",
    dificultad: "medio",
    importancia: "alto",
    activa: true,
  },
]

function renderBanco() {
  return render(
    <MemoryRouter initialEntries={["/materias/m1/banco"]}>
      <Routes>
        <Route path="/materias/:materiaId/banco" element={<Banco />} />
        <Route path="/materias/:materiaId/banco/preguntas/nueva" element={<p>Nueva pregunta</p>} />
        <Route
          path="/materias/:materiaId/banco/preguntas/:preguntaId/editar"
          element={<p>Editar pregunta</p>}
        />
        <Route
          path="/materias/:materiaId/banco/preguntas/:preguntaId/eliminar"
          element={<p>Eliminar pregunta</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("Banco", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra todas las preguntas activas de la materia sin filtros", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, preguntasResponse))

    renderBanco()

    expect(await screen.findByText("Ingeniería de Software")).toBeInTheDocument()
    expect(
      await screen.findByText(/¿Qué principio de Clean Architecture/),
    ).toBeInTheDocument()
    expect(screen.getByText(/Un Aggregate Root/)).toBeInTheDocument()
    expect(screen.getByText("2 preguntas activas")).toBeInTheDocument()
  })

  it("filtrar por dificultad dispara una nueva consulta con ese filtro", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, preguntasResponse))
      .mockResolvedValueOnce(jsonResponse(200, [preguntasResponse[0]]))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.selectOptions(screen.getByLabelText("Dificultad"), "alto")

    await screen.findByText("1 pregunta activa")
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("dificultad=alto")
  })

  it("una combinación de filtros sin resultados deja la tabla vacía sin mensaje de error", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, preguntasResponse))
      .mockResolvedValueOnce(jsonResponse(200, []))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.selectOptions(screen.getByLabelText("Dificultad"), "bajo")

    await screen.findByText("0 preguntas activas")
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument()
  })

  it("el botón 'Editar' de una fila navega a la edición de esa pregunta", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, preguntasResponse))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.click(screen.getAllByText("Editar")[0])

    expect(await screen.findByText("Editar pregunta")).toBeInTheDocument()
  })

  it("el botón 'Eliminar' de una fila navega a la confirmación de eliminación de esa pregunta", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, preguntasResponse))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.click(screen.getAllByText("Eliminar")[0])

    expect(await screen.findByText("Eliminar pregunta")).toBeInTheDocument()
  })

  it("filtrar por unidad temática dispara una nueva consulta con ese filtro", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, preguntasResponse))
      .mockResolvedValueOnce(jsonResponse(200, [preguntasResponse[1]]))

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    fireEvent.change(screen.getByLabelText("Unidad temática"), { target: { value: "Unidad 2" } })

    await screen.findByText("1 pregunta activa")
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("unidad=Unidad")
  })

  it("'Limpiar filtros' vuelve a mostrar todas las preguntas activas", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, preguntasResponse))
      .mockResolvedValueOnce(jsonResponse(200, [preguntasResponse[0]]))
      .mockResolvedValueOnce(jsonResponse(200, preguntasResponse))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)
    await user.selectOptions(screen.getByLabelText("Dificultad"), "alto")
    await screen.findByText("1 pregunta activa")

    await user.click(screen.getByText("Limpiar filtros"))

    await screen.findByText("2 preguntas activas")
    expect(screen.getByLabelText("Dificultad")).toHaveValue("")
  })

  it("el botón '+ Nueva pregunta' navega al alta de pregunta", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, preguntasResponse))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.click(screen.getByText("+ Nueva pregunta"))

    expect(await screen.findByText("Nueva pregunta")).toBeInTheDocument()
  })
})
