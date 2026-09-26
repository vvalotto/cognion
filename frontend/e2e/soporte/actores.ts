import { expect, type Browser, type BrowserContext, type Page, type WebSocketRoute } from "@playwright/test"

import { datos, type Usuario } from "./datos"

/** Control del canal WebSocket de una página: cortarlo, restablecerlo y contar sockets abiertos. */
export class Canal {
  private cortado = false
  private zombi = false
  private actual: WebSocketRoute | null = null
  abiertos = 0
  aperturas = 0

  async instalar(page: Page) {
    await page.routeWebSocket(/\/sesiones-en-vivo\/.+\/canal/, (ws) => {
      if (this.cortado) {
        void ws.close({ code: 4000, reason: "corte simulado" })
        return
      }
      this.actual = ws
      this.aperturas++
      this.abiertos++
      ws.onClose(() => {
        this.abiertos--
      })
      const servidor = ws.connectToServer()
      // Se reenvía a mano para poder simular la conexión "zombi" de Safari en iOS.
      servidor.onMessage((mensaje) => {
        if (!this.zombi) ws.send(mensaje)
      })
      this.zombi = false
    })
  }

  /**
   * Conexión "zombi" (Safari iOS con la pantalla bloqueada, hallazgo #7): el socket sigue abierto pero
   * deja de entregar mensajes, sin cerrarse. Una conexión nueva vuelve a funcionar.
   */
  volverZombi() {
    this.zombi = true
  }

  /** Corta la conexión y rechaza las reconexiones hasta `restablecer()`. */
  async cortar() {
    this.cortado = true
    await this.actual?.close({ code: 4000, reason: "corte simulado" })
  }

  restablecer() {
    this.cortado = false
  }
}

export interface Actor {
  usuario: Usuario
  contexto: BrowserContext
  page: Page
  canal: Canal
}

async function crearActor(
  browser: Browser,
  usuario: Usuario,
  rol: "docente" | "estudiante",
  opciones: { sesionInyectada?: boolean } = {},
): Promise<Actor> {
  const contexto =
    rol === "docente"
      ? await browser.newContext({ viewport: { width: 1920, height: 1080 } })
      : await browser.newContext({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true })
  if (opciones.sesionInyectada !== false) {
    await contexto.addInitScript(
      ([token, r]) => {
        localStorage.setItem("cognion.session", JSON.stringify({ token, rol: r }))
      },
      [usuario.token, rol],
    )
  }
  const page = await contexto.newPage()
  const canal = new Canal()
  await canal.instalar(page)
  return { usuario, contexto, page, canal }
}

/** Docente en la proyección (1920×1080). */
export function docente(browser: Browser, opciones?: { sesionInyectada?: boolean }) {
  return crearActor(browser, datos().docente, "docente", opciones)
}

/** Estudiante `n` (1-based) en un celular emulado (375×812, táctil). */
export function estudiante(browser: Browser, n: number, opciones?: { sesionInyectada?: boolean }) {
  return crearActor(browser, datos().estudiantes[n - 1], "estudiante", opciones)
}

/** Login por la pantalla real (no inyecta la sesión). */
export async function loginPorPantalla(page: Page, email: string, password: string) {
  await page.goto("/login")
  await page.getByLabel("Email").fill(email)
  await page.getByRole("textbox", { name: "Contraseña" }).fill(password)
  await page.getByRole("button", { name: "Ingresar" }).click()
  await expect(page).not.toHaveURL(/\/login/)
}

export async function cerrar(...actores: Actor[]) {
  for (const actor of actores) await actor.contexto.close()
}
