import { cleanup, render, screen } from "@testing-library/react"
import { RouterProvider } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { clearSession, setSession } from "@/lib/session"
import { router } from "@/router"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("router (integración)", () => {
  beforeEach(() => {
    clearSession()
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, [])))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("la ruta /login renderiza dentro del layout de auth", async () => {
    await router.navigate("/login")
    render(<RouterProvider router={router} />)

    expect(await screen.findByText("Iniciar sesión")).toBeInTheDocument()
  })

  it("la ruta /registro renderiza dentro del layout de auth", async () => {
    await router.navigate("/registro")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Crear cuenta" })).toBeInTheDocument()
  })

  it("la ruta /docentes/nuevo redirige a login sin sesión", async () => {
    await router.navigate("/docentes/nuevo")
    render(<RouterProvider router={router} />)

    expect(await screen.findByText("Iniciar sesión")).toBeInTheDocument()
  })

  it("la ruta /docentes/nuevo renderiza dentro del layout de app con sesión de administrador", async () => {
    setSession({ token: "t", rol: "administrador" })
    await router.navigate("/docentes/nuevo")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Crear cuenta de Docente" })).toBeInTheDocument()
  })

  it("la ruta /materias redirige a login sin sesión", async () => {
    await router.navigate("/materias")
    render(<RouterProvider router={router} />)

    expect(await screen.findByText("Iniciar sesión")).toBeInTheDocument()
  })

  it("la ruta /materias muestra acceso denegado con sesión de rol distinto de docente", async () => {
    setSession({ token: "t", rol: "administrador" })
    await router.navigate("/materias")
    render(<RouterProvider router={router} />)

    expect(await screen.findByText("Acceso denegado")).toBeInTheDocument()
  })

  it("la ruta /materias renderiza el listado de materias con sesión de docente", async () => {
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Materias" })).toBeInTheDocument()
  })

  it("la ruta /materias/nueva renderiza el formulario de alta con sesión de docente", async () => {
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias/nueva")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Crear materia" })).toBeInTheDocument()
  })

  it("la ruta .../preguntas/:id/editar renderiza el formulario de edición con sesión de docente", async () => {
    vi.mocked(fetch).mockReset()
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 1 },
        ]),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, [
          {
            id: "p1",
            banco_id: "b1",
            texto: "¿Qué principio prohíbe importar una capa externa?",
            respuesta_correcta: true,
            unidad_tematica: "Unidad 3",
            tema: "Arquitectura",
            dificultad: "alto",
            importancia: "alto",
            activa: true,
          },
        ]),
      )
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias/m1/banco/preguntas/p1/editar")
    render(<RouterProvider router={router} />)

    expect(
      await screen.findByRole("heading", { name: "Editar pregunta de Verdadero/Falso" }),
    ).toBeInTheDocument()
  })

  it("la ruta /materias/:id/banco/preguntas/nueva renderiza la selección de tipo con sesión de docente", async () => {
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias/m1/banco/preguntas/nueva")
    render(<RouterProvider router={router} />)

    expect(
      await screen.findByRole("heading", { name: "¿Qué tipo de pregunta querés cargar?" }),
    ).toBeInTheDocument()
  })

  it("la ruta .../nueva/opcion-multiple renderiza el formulario de Opción múltiple con sesión de docente", async () => {
    vi.mocked(fetch).mockReset()
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 0 },
        ]),
      )
      .mockResolvedValueOnce(jsonResponse(200, []))
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias/m1/banco/preguntas/nueva/opcion-multiple")
    render(<RouterProvider router={router} />)

    expect(
      await screen.findByRole("heading", { name: "Cargar pregunta de Opción múltiple" }),
    ).toBeInTheDocument()
  })

  it("la ruta .../nueva/verdadero-falso renderiza el formulario de Verdadero/Falso con sesión de docente", async () => {
    vi.mocked(fetch).mockReset()
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 0 },
        ]),
      )
      .mockResolvedValueOnce(jsonResponse(200, []))
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias/m1/banco/preguntas/nueva/verdadero-falso")
    render(<RouterProvider router={router} />)

    expect(
      await screen.findByRole("heading", { name: "Cargar pregunta de Verdadero/Falso" }),
    ).toBeInTheDocument()
  })

  it("la ruta .../preguntas/:id/eliminar renderiza la confirmación con sesión de docente", async () => {
    vi.mocked(fetch).mockReset()
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 1 },
        ]),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, [
          {
            id: "p1",
            banco_id: "b1",
            texto: "¿Qué principio prohíbe importar una capa externa?",
            respuesta_correcta: true,
            unidad_tematica: "Unidad 3",
            tema: "Arquitectura",
            dificultad: "alto",
            importancia: "alto",
            activa: true,
          },
        ]),
      )
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias/m1/banco/preguntas/p1/eliminar")
    render(<RouterProvider router={router} />)

    expect(
      await screen.findByRole("heading", { name: "Eliminar pregunta" }),
    ).toBeInTheDocument()
  })

  it("la ruta /materias/:id/banco renderiza el banco de preguntas con sesión de docente", async () => {
    vi.mocked(fetch).mockReset()
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 0 },
        ]),
      )
      .mockResolvedValueOnce(jsonResponse(200, []))
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias/m1/banco")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Ingeniería de Software" })).toBeInTheDocument()
  })
})
