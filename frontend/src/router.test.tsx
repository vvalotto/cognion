import { cleanup, render, screen } from "@testing-library/react"
import { RouterProvider } from "react-router"
import { afterEach, beforeEach, describe, expect, it } from "vitest"

import { clearSession, setSession } from "@/lib/session"
import { router } from "@/router"

describe("router (integración)", () => {
  beforeEach(() => {
    clearSession()
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

  it("la ruta /materias renderiza el placeholder con sesión de docente", async () => {
    setSession({ token: "t", rol: "docente" })
    await router.navigate("/materias")
    render(<RouterProvider router={router} />)

    expect(
      await screen.findByText("Banco de Preguntas — pendiente de pantalla propia"),
    ).toBeInTheDocument()
  })

  it.each([
    "/materias/nueva",
    "/materias/m1/banco",
    "/materias/m1/banco/preguntas/nueva",
    "/materias/m1/banco/preguntas/nueva/opcion-multiple",
    "/materias/m1/banco/preguntas/nueva/verdadero-falso",
    "/materias/m1/banco/preguntas/p1/editar",
  ])("la ruta %s renderiza el placeholder con sesión de docente", async (path) => {
    setSession({ token: "t", rol: "docente" })
    await router.navigate(path)
    render(<RouterProvider router={router} />)

    expect(
      await screen.findByText("Banco de Preguntas — pendiente de pantalla propia"),
    ).toBeInTheDocument()
  })
})
