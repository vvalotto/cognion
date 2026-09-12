import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it } from "vitest"

import { PasswordInput } from "@/components/PasswordInput"

describe("PasswordInput", () => {
  afterEach(() => {
    cleanup()
  })

  it("arranca oculto (type=password) con el botón 'Mostrar contraseña'", () => {
    render(<PasswordInput id="p" defaultValue="secreta" />)

    const input = screen.getByDisplayValue("secreta")
    expect(input).toHaveAttribute("type", "password")
    expect(screen.getByRole("button", { name: "Mostrar contraseña" })).toBeInTheDocument()
  })

  it("alterna a texto visible sin perder el valor", async () => {
    const user = userEvent.setup()
    render(<PasswordInput id="p" defaultValue="secreta" />)

    await user.click(screen.getByRole("button", { name: "Mostrar contraseña" }))

    const input = screen.getByDisplayValue("secreta")
    expect(input).toHaveAttribute("type", "text")
    expect(screen.getByRole("button", { name: "Ocultar contraseña" })).toBeInTheDocument()
  })

  it("vuelve a ocultar al hacer clic de nuevo", async () => {
    const user = userEvent.setup()
    render(<PasswordInput id="p" defaultValue="secreta" />)

    const toggle = () => screen.getByRole("button", { name: /contraseña/ })
    await user.click(toggle())
    await user.click(toggle())

    expect(screen.getByDisplayValue("secreta")).toHaveAttribute("type", "password")
  })

  it("propaga props adicionales al input (id, required, onChange)", async () => {
    const user = userEvent.setup()
    let valor = ""
    render(
      <PasswordInput
        id="login-password"
        required
        value={valor}
        onChange={(e) => {
          valor = e.target.value
        }}
      />,
    )

    const input = document.getElementById("login-password") as HTMLInputElement
    expect(input).toBeRequired()

    await user.type(input, "a")
    expect(valor).toBe("a")
  })
})
