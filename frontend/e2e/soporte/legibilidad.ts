import type { Locator, Page } from "@playwright/test"

export interface Medicion {
  tamanoPx: number
  contraste: number
}

/** Tamaño de fuente y contraste (WCAG) del texto contra el primer fondo opaco de sus ancestros. */
export async function medir(locator: Locator): Promise<Medicion> {
  return locator.evaluate((el) => {
    const rgb = (valor: string) => (valor.match(/[\d.]+/g) ?? []).map(Number)
    const luminancia = ([r, g, b]: number[]) => {
      const canal = (c: number) => {
        const v = c / 255
        return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
      }
      return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)
    }
    const estilo = getComputedStyle(el)
    let fondo: number[] = [255, 255, 255]
    for (let nodo: Element | null = el; nodo; nodo = nodo.parentElement) {
      const valores = rgb(getComputedStyle(nodo).backgroundColor)
      if (valores.length >= 3 && (valores.length === 3 || valores[3] > 0.5)) {
        fondo = valores.slice(0, 3)
        break
      }
    }
    const [a, b] = [luminancia(rgb(estilo.color).slice(0, 3)), luminancia(fondo)].sort((x, y) => y - x)
    return { tamanoPx: parseFloat(estilo.fontSize), contraste: Math.round(((a + 0.05) / (b + 0.05)) * 100) / 100 }
  })
}

/** ¿La página entra en el viewport sin scroll? */
export async function sinScroll(page: Page): Promise<boolean> {
  return page.evaluate(
    () =>
      document.documentElement.scrollHeight <= window.innerHeight &&
      document.documentElement.scrollWidth <= window.innerWidth,
  )
}
