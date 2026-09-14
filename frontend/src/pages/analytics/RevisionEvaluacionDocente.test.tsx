import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { RevisionEvaluacionDocente } from "@/pages/analytics/RevisionEvaluacionDocente"

const MATERIA_ID = "m1"
const COMISION_ID = "c1"
const ESTUDIANTE_ID = "u1"
const EVALUACION_ID = "eval-1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function revisionBody() {
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
  }
}

function renderPantalla() {
  return render(
    <MemoryRouter
      initialEntries={[
        `/analytics/desempeno-por-comision/materias/${MATERIA_ID}/comisiones/${COMISION_ID}/estudiantes/${ESTUDIANTE_ID}/evaluaciones/${EVALUACION_ID}/revision`,
      ]}
    >
      <Routes>
        <Route
          path="/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId/evaluaciones/:evaluacionId/revision"
          element={<RevisionEvaluacionDocente />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("RevisionEvaluacionDocente", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra la revisión completa con la etiqueta de respuesta del estudiante", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, revisionBody()))
    renderPantalla()

    expect(await screen.findByText("Revisión completa")).toBeInTheDocument()
    expect(
      screen.getByText("Respuesta del estudiante: Responsabilidad única"),
    ).toBeInTheDocument()
    expect(screen.getByText("Respuesta del estudiante: Verdadero")).toBeInTheDocument()
    expect(screen.getByText("Respuesta correcta: Falso")).toBeInTheDocument()

    const [url] = vi.mocked(fetch).mock.calls[0]
    expect(String(url)).toContain(`/evaluaciones/${EVALUACION_ID}/revision`)
  })

  it("evaluación inexistente: muestra el mensaje de error", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "No existe" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    )
    renderPantalla()

    expect(
      await screen.findByText(
        "No se pudo cargar la revisión de esta evaluación. Intentá de nuevo más tarde.",
      ),
    ).toBeInTheDocument()
  })
})
