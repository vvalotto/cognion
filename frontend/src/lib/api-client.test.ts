import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const { navigateMock } = vi.hoisted(() => ({ navigateMock: vi.fn() }))
vi.mock("@/router", () => ({
  router: { navigate: navigateMock },
}))

import { apiFetch, ApiError } from "@/lib/api-client"
import { getSession, setSession } from "@/lib/session"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("apiFetch", () => {
  beforeEach(() => {
    localStorage.clear()
    navigateMock.mockClear()
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("adjunta el JWT en el header Authorization si hay sesión", async () => {
    setSession({ token: "token-valido", rol: "docente" })
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { ok: true }))

    await apiFetch("/comisiones/123/invitaciones", { method: "POST", body: {} })

    const [, init] = vi.mocked(fetch).mock.calls[0]
    const headers = new Headers(init?.headers)
    expect(headers.get("Authorization")).toBe("Bearer token-valido")
  })

  it("no adjunta Authorization si no hay sesión", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { ok: true }))

    await apiFetch("/identidad/login", { method: "POST", body: {} })

    const [, init] = vi.mocked(fetch).mock.calls[0]
    const headers = new Headers(init?.headers)
    expect(headers.has("Authorization")).toBe(false)
  })

  it("un 401 limpia la sesión y navega a /login", async () => {
    setSession({ token: "token-vencido", rol: "docente" })
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(401, { detail: "Token expirado." })
    )

    await expect(apiFetch("/usuarios", { method: "POST", body: {} })).rejects.toThrow(
      ApiError
    )

    expect(getSession()).toBeNull()
    expect(navigateMock).toHaveBeenCalledWith("/login")
  })

  it("un 403 propaga el mensaje generico del backend sin limpiar la sesion", async () => {
    setSession({ token: "token-valido", rol: "docente" })
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(403, { detail: "El rol del usuario no tiene acceso a este recurso." })
    )

    const error = await apiFetch("/usuarios", { method: "POST", body: {} }).catch(
      (e: unknown) => e
    )

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(403)
    expect((error as ApiError).message).toBe(
      "El rol del usuario no tiene acceso a este recurso."
    )
    expect(getSession()).not.toBeNull()
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it("devuelve undefined ante una respuesta 204 sin body", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(null, { status: 204 }))

    const result = await apiFetch("/comisiones/123/docentes", {
      method: "POST",
      body: {},
    })

    expect(result).toBeUndefined()
  })

  it("devuelve el body parseado ante una respuesta exitosa", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, { access_token: "abc", rol: "administrador" })
    )

    const result = await apiFetch<{ access_token: string; rol: string }>(
      "/identidad/login",
      { method: "POST", body: {} }
    )

    expect(result).toEqual({ access_token: "abc", rol: "administrador" })
  })

  it("usa un mensaje generico si la respuesta de error no trae body JSON", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(null, { status: 500 }))

    const error = await apiFetch("/usuarios", { method: "POST", body: {} }).catch(
      (e: unknown) => e
    )

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).message).toBe("Error inesperado.")
  })
})
