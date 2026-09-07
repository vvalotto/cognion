import { beforeEach, describe, expect, it } from "vitest"

import { clearSession, getSession, obtenerUsuarioId, setSession } from "@/lib/session"

/** Arma un JWT con el payload dado — sin firma real, alcanza para testear el decode del cliente. */
function jwtFalso(payload: Record<string, unknown>): string {
  const base64url = (obj: unknown) =>
    btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
  return `${base64url({ alg: "HS256" })}.${base64url(payload)}.firma`
}

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

  describe("obtenerUsuarioId", () => {
    it("devuelve null si no hay sesión", () => {
      expect(obtenerUsuarioId()).toBeNull()
    })

    it("decodifica el claim sub del JWT de la sesión", () => {
      const token = jwtFalso({ sub: "11111111-1111-1111-1111-111111111111", rol: "administrador" })
      setSession({ token, rol: "administrador" })

      expect(obtenerUsuarioId()).toBe("11111111-1111-1111-1111-111111111111")
    })

    it("devuelve null si el token no tiene 3 partes", () => {
      setSession({ token: "no-es-un-jwt", rol: "administrador" })

      expect(obtenerUsuarioId()).toBeNull()
    })

    it("devuelve null si el payload no es JSON válido", () => {
      setSession({ token: "aaa.bbb.ccc", rol: "administrador" })

      expect(obtenerUsuarioId()).toBeNull()
    })

    it("devuelve null si el payload no tiene claim sub", () => {
      const token = jwtFalso({ rol: "administrador" })
      setSession({ token, rol: "administrador" })

      expect(obtenerUsuarioId()).toBeNull()
    })
  })
})
