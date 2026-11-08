import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { LoginError } from "@/pages/identidad/LoginError"

function renderError(intentosRestantes?: number | null) {
  return render(
    <MemoryRouter>
      <LoginError intentosRestantes={intentosRestantes} />
    </MemoryRouter>,
  )
}

describe("LoginError", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el mensaje genérico de credenciales inválidas", () => {
    renderError()

    const alert = screen.getByRole("alert")
    expect(alert).toHaveTextContent("Email o contraseña incorrectos")
    expect(alert).toHaveTextContent("Verificá tus datos e intentá de nuevo.")
    expect(screen.queryByRole("link")).not.toBeInTheDocument()
  })

  it("con 1 intento restante avisa del bloqueo y ofrece recuperar la contraseña (US-ADJ-69)", () => {
    renderError(1)

    const alert = screen.getByRole("alert")
    expect(alert).toHaveTextContent("Email o contraseña incorrectos")
    expect(alert).toHaveTextContent("Te queda 1 intento antes del bloqueo de la cuenta.")
    expect(alert).not.toHaveTextContent("Verificá tus datos")
    expect(screen.getByRole("link", { name: "recuperala por email" })).toHaveAttribute(
      "href",
      "/recuperar-password",
    )
  })

  it("un valor que no sea 1 no muestra el aviso", () => {
    renderError(2)

    expect(screen.getByRole("alert")).not.toHaveTextContent("Te queda")
  })
})
