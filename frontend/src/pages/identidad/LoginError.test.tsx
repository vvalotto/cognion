import { cleanup, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { LoginError } from "@/pages/identidad/LoginError"

describe("LoginError", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el mensaje genérico de credenciales inválidas", () => {
    render(<LoginError />)

    const alert = screen.getByRole("alert")
    expect(alert).toHaveTextContent("Email o contraseña incorrectos")
    expect(alert).toHaveTextContent("Verificá tus datos e intentá de nuevo.")
  })
})
