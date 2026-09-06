import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { RevisionEvaluacion } from "@/pages/actividad-evaluativa/RevisionEvaluacion"

const EVALUACION_ID = "eval-1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function revisionBody(overrides?: Partial<Record<string, unknown>>) {
  return {
    evaluacion_id: EVALUACION_ID,
    cantidad_preguntas: 2,
    cantidad_correctas: 1,
    cantidad_incorrectas: 1,
    detalle: [
      {
        pregunta_id: "p1",
        orden: 1,
        texto: "¿Cuál NO es un principio SOLID?",
        respondida: true,
        contenido_propio: { opcion_indice: 0 },
        es_correcta: true,
        contenido_correcto: null,
        opciones: ["Responsabilidad única", "Herencia múltiple obligatoria"],
      },
      {
        pregunta_id: "p2",
        orden: 2,
        texto: "El patrón Repository pertenece a la infraestructura.",
        respondida: true,
        contenido_propio: { valor: true },
        es_correcta: false,
        contenido_correcto: { valor: false },
        opciones: null,
      },
    ],
    ...overrides,
  }
}

function renderRevision() {
  return render(
    <MemoryRouter initialEntries={[`/mis-actividades/evaluaciones/${EVALUACION_ID}/revision`]}>
      <Routes>
        <Route
          path="/mis-actividades/evaluaciones/:evaluacionId/revision"
          element={<RevisionEvaluacion />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("RevisionEvaluacion", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el resumen de correctas, incorrectas y total", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, revisionBody()))
    renderRevision()

    expect(await screen.findByText("Revisión completa")).toBeInTheDocument()
    expect(screen.getByText("Correctas").previousSibling?.textContent).toBe("1")
    expect(screen.getByText("Incorrectas").previousSibling?.textContent).toBe("1")
    expect(screen.getByText("Total").previousSibling?.textContent).toBe("2")

    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(ultimaLlamada?.[0]).toContain(`/evaluaciones/${EVALUACION_ID}/revision`)
  })

  it("una pregunta correcta de opción múltiple muestra el texto de la opción elegida, sin respuesta correcta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, revisionBody({ detalle: [revisionBody().detalle[0]] })),
    )
    renderRevision()

    await screen.findByText("¿Cuál NO es un principio SOLID?", { exact: false })
    expect(screen.getByText("Tu respuesta: Responsabilidad única")).toBeInTheDocument()
    expect(screen.queryByText(/Respuesta correcta:/)).not.toBeInTheDocument()
  })

  it("una pregunta incorrecta de Verdadero/Falso muestra también la respuesta correcta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, revisionBody()))
    renderRevision()

    await screen.findByText(/El patrón Repository/, { exact: false })
    expect(screen.getByText("Tu respuesta: Verdadero")).toBeInTheDocument()
    expect(screen.getByText("Respuesta correcta: Falso")).toBeInTheDocument()
  })

  it("una pregunta sin responder muestra 'Sin responder'", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(
        200,
        revisionBody({
          detalle: [
            {
              pregunta_id: "p1",
              orden: 1,
              texto: "Sin contestar",
              respondida: false,
              contenido_propio: null,
              es_correcta: false,
              contenido_correcto: { valor: true },
              opciones: null,
            },
          ],
        }),
      ),
    )
    renderRevision()

    await screen.findByText("Sin contestar", { exact: false })
    expect(screen.getByText("Tu respuesta: Sin responder")).toBeInTheDocument()
    expect(screen.getByText("Respuesta correcta: Verdadero")).toBeInTheDocument()
  })
})
