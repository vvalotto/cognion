import { beforeEach, describe, expect, it } from "vitest"

import { clearSession, getSession, setSession } from "@/lib/session"

describe("session", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it("getSession devuelve null si no hay sesión guardada", () => {
    expect(getSession()).toBeNull()
  })

  it("setSession guarda la sesión y getSession la recupera", () => {
    setSession({ token: "abc123", rol: "docente" })

    expect(getSession()).toEqual({ token: "abc123", rol: "docente" })
  })

  it("clearSession elimina la sesión guardada", () => {
    setSession({ token: "abc123", rol: "administrador" })

    clearSession()

    expect(getSession()).toBeNull()
  })

  it("getSession devuelve null ante contenido corrupto en localStorage", () => {
    localStorage.setItem("cognion.session", "{esto no es json")

    expect(getSession()).toBeNull()
  })
})
