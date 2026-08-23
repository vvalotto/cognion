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

function paginado<T>(preguntas: T[]): { preguntas: T[]; total: number } {
  return { preguntas, total: preguntas.length }
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
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))

    renderBanco()

    expect(
      await screen.findByRole("heading", { name: "Ingeniería de Software" }),
    ).toBeInTheDocument()
    expect(
      await screen.findByText(/¿Qué principio de Clean Architecture/),
    ).toBeInTheDocument()
    expect(screen.getByText(/Un Aggregate Root/)).toBeInTheDocument()
    expect(screen.getByText("2 preguntas activas en el banco")).toBeInTheDocument()
  })

  it("[US-ADJ-01] Tipo, Dificultad e Importancia se muestran con tags de color y el botón Eliminar es sólido", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    expect(screen.getByText("Opción múltiple")).toHaveClass("bg-blue-50")
    expect(screen.getByText("Verdadero/Falso")).toHaveClass("bg-violet-50")
    const tagAlto = screen
      .getAllByText("Alto")
      .find((el) => el.getAttribute("data-slot") === "badge")
    expect(tagAlto).toHaveClass("bg-red-50")
    expect(screen.getAllByText("Eliminar")[0]).toHaveClass("bg-destructive")
  })

  it("filtrar por dificultad dispara una nueva consulta con ese filtro", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado([preguntasResponse[0]])))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.selectOptions(screen.getByLabelText("Dificultad"), "alto")

    await screen.findByText("1 pregunta activa en el banco")
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("dificultad=alto")
  })

  it("una combinación de filtros sin resultados deja la tabla vacía sin mensaje de error", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado([])))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.selectOptions(screen.getByLabelText("Dificultad"), "bajo")

    await screen.findByText("0 preguntas activas en el banco")
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument()
  })

  it("el botón 'Editar' de una fila navega a la edición de esa pregunta", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.click(screen.getAllByText("Editar")[0])

    expect(await screen.findByText("Editar pregunta")).toBeInTheDocument()
  })

  it("el botón 'Eliminar' de una fila navega a la confirmación de eliminación de esa pregunta", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.click(screen.getAllByText("Eliminar")[0])

    expect(await screen.findByText("Eliminar pregunta")).toBeInTheDocument()
  })

  it("filtrar por unidad temática dispara una nueva consulta con ese filtro", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado([preguntasResponse[1]])))

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    fireEvent.change(screen.getByLabelText("Unidad temática"), { target: { value: "Unidad 2" } })

    await screen.findByText("1 pregunta activa en el banco")
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("unidad=Unidad")
  })

  it("'Limpiar filtros' vuelve a mostrar todas las preguntas activas", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado([preguntasResponse[0]])))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)
    await user.selectOptions(screen.getByLabelText("Dificultad"), "alto")
    await screen.findByText("1 pregunta activa en el banco")

    await user.click(screen.getByText("Limpiar filtros"))

    await screen.findByText("2 preguntas activas en el banco")
    expect(screen.getByLabelText("Dificultad")).toHaveValue("")
  })

  it("el botón '+ Nueva pregunta' navega al alta de pregunta", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    await user.click(screen.getByText("+ Nueva pregunta"))

    expect(await screen.findByText("Nueva pregunta")).toBeInTheDocument()
  })

  function paginaDe20(offset: number) {
    return Array.from({ length: 20 }, (_, i) => ({
      id: `pag-${offset + i}`,
      banco_id: "b1",
      texto: `Pregunta ${offset + i}`,
      opciones: [
        { texto: "a", es_correcta: true },
        { texto: "b", es_correcta: false },
      ],
      unidad_tematica: "Unidad 1",
      tema: "Tema",
      dificultad: "medio",
      importancia: "medio",
      activa: true,
    }))
  }

  it("[US-ADJ-03] banco con más de una página muestra los controles de paginación", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado([])))
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: paginaDe20(1), total: 71 }))

    renderBanco()

    expect(await screen.findByText("Pregunta 1")).toBeInTheDocument()
    expect(screen.getByText("71 preguntas activas en el banco")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "4" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Siguiente" })).toBeEnabled()
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled()
  })

  it("[US-ADJ-03] cambiar de página pide la página siguiente al backend", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado([])))
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: paginaDe20(1), total: 71 }))
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: paginaDe20(21), total: 71 }))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText("Pregunta 1")

    await user.click(screen.getByRole("button", { name: "Siguiente" }))

    expect(await screen.findByText("Pregunta 21")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("pagina=2")
    expect(ultimaLlamada).toContain("tamanio_pagina=20")
  })

  it("[US-ADJ-03] cambiar un filtro reinicia la paginación a la página 1", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado([])))
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: paginaDe20(1), total: 71 }))
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: paginaDe20(21), total: 71 }))
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: paginaDe20(1), total: 30 }))
    const user = userEvent.setup()

    renderBanco()
    await screen.findByText("Pregunta 1")
    await user.click(screen.getByRole("button", { name: "Siguiente" }))
    await screen.findByText("Pregunta 21")

    await user.selectOptions(screen.getByLabelText("Dificultad"), "alto")

    await screen.findByText("30 preguntas activas en el banco")
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("pagina=1")
  })

  it("[US-ADJ-03] banco con una sola página no muestra controles de paginación", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))

    renderBanco()
    await screen.findByText(/¿Qué principio de Clean Architecture/)

    expect(screen.queryByRole("navigation", { name: "Paginación" })).not.toBeInTheDocument()
  })
})
