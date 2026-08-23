import { cleanup, render, screen } from "@testing-library/react"
import { RouterProvider } from "react-router"
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest"

import { clearSession, setSession } from "@/lib/session"
import { router } from "@/router"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("router (integración)", () => {
  // El fetch mockeado se deja stubeado durante todo el archivo (no se restaura entre tests):
  // varias pantallas (Banco, EditarPregunta, NuevaPregunta*) disparan más de un fetch en
  // paralelo tras montar, y alguno puede resolverse después de que el test que lo montó ya
  // terminó. Si `unstubAllGlobals()` corriera en cada `afterEach`, ese fetch tardío pegaría
  // contra la red real en vez del mock — restaurar el fetch real recién en `afterAll` evita
  // esa carrera sin importar el timing exacto de cada efecto.
  beforeAll(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterAll(() => {
    vi.unstubAllGlobals()
  })

  beforeEach(() => {
    clearSession()
    vi.mocked(fetch).mockReset().mockResolvedValue(jsonResponse(200, []))
  })

  afterEach(() => {
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

    expect(await screen.findByRole("heading", { name: "Crear tu cuenta" })).toBeInTheDocument()
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
        jsonResponse(200, {
          preguntas: [
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
          ],
          total: 1,
        }),
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
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: [], total: 0 }))
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
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: [], total: 0 }))
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
        jsonResponse(200, {
          preguntas: [
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
          ],
          total: 1,
        }),
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
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: [], total: 0 }))
      .mockResolvedValueOnce(jsonResponse(200, { preguntas: [], total: 0 }))
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias/m1/banco")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Ingeniería de Software" })).toBeInTheDocument()
    expect(await screen.findByText("0 preguntas activas")).toBeInTheDocument()
    // Banco.tsx dispara dos fetch en paralelo (sugerencias + tabla) tras cargar la materia —
    // hay que esperar a que ambos se resuelvan antes de que el afterEach restaure el fetch
    // real, o el que todavía esté pendiente termina pegándole a la red real.
    await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(3))
  })

  it("la ruta /cuentas muestra acceso denegado con sesión de rol distinto de administrador", async () => {
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/cuentas")
    render(<RouterProvider router={router} />)

    expect(await screen.findByText("Acceso denegado")).toBeInTheDocument()
  })

  it("la ruta /cuentas renderiza el listado de cuentas con sesión de administrador", async () => {
    vi.mocked(fetch).mockReset()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, {
        cuentas: [
          { id: "u1", nombre: "Ana", email: "ana@fiuner.edu.ar", perfil: "docente", bloqueada: false },
        ],
        total: 1,
      }),
    )
    setSession({ token: "t", rol: "administrador" })
    await router.navigate("/cuentas")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Cuentas" })).toBeInTheDocument()
    expect(await screen.findByText("Ana")).toBeInTheDocument()
  })

  it("la ruta /cuentas/:usuarioId renderiza el detalle de cuenta con sesión de administrador", async () => {
    vi.mocked(fetch).mockReset()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, {
        id: "u1",
        nombre: "Ana",
        email: "ana@fiuner.edu.ar",
        perfil: "docente",
        bloqueada: false,
        creado_en: "2026-08-01T10:00:00Z",
        comision_id: null,
      }),
    )
    setSession({ token: "t", rol: "administrador" })
    await router.navigate("/cuentas/u1")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Ana" })).toBeInTheDocument()
  })

  it("la ruta /cuentas/:usuarioId/resetear-password renderiza el formulario de reseteo con sesión de administrador", async () => {
    vi.mocked(fetch).mockReset()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, {
        id: "u1",
        nombre: "Ana",
        email: "ana@fiuner.edu.ar",
        perfil: "docente",
        bloqueada: true,
        creado_en: "2026-08-01T10:00:00Z",
        comision_id: null,
      }),
    )
    setSession({ token: "t", rol: "administrador" })
    await router.navigate("/cuentas/u1/resetear-password")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Resetear contraseña" })).toBeInTheDocument()
  })

  it("la ruta /cuentas/:usuarioId/reseteada renderiza la confirmación con sesión de administrador", async () => {
    setSession({ token: "t", rol: "administrador" })
    await router.navigate("/cuentas/u1/reseteada")
    render(<RouterProvider router={router} />)

    expect(await screen.findByRole("heading", { name: "Contraseña reseteada" })).toBeInTheDocument()
  })
})
