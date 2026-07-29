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
})
