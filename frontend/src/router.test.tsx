import { cleanup, render, screen } from "@testing-library/react"
import { RouterProvider } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { router } from "@/router"

describe("router (integración)", () => {
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
})
