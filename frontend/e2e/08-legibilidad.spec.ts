import { cerrar, docente, estudiante } from "./soporte/actores"
import { TEMAS } from "./soporte/datos"
import {
  cerrarPregunta,
  crearSesion,
  esperarSala,
  esperarTarjetas,
  finalizar,
  iniciar,
  mostrarOpciones,
  responder,
  unirse,
  verRanking,
} from "./soporte/flujos"
import { medir, sinScroll, type Medicion } from "./soporte/legibilidad"
import { expect, test } from "./soporte/prueba"

/**
 * Circuito 8 — legibilidad en proyección (§1.1 del wireframe) medida en el navegador a 1920×1080, y
 * tamaño táctil de las tarjetas en el celular (≥ 44 px). Las cajas de opción se miden y se informan
 * (contraste de colores de marca aprobados en el prototipo), sin bloquear.
 */
test("legibilidad de la proyección y tamaño táctil del celular", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  const est = await estudiante(browser, 1)
  const informe: Record<string, Medicion | boolean | number> = {}

  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 1, tiempo: 60 })
  await unirse(est)
  await esperarSala(est, 1)
  await iniciar(doc)

  // Pregunta sola.
  const eyebrow = doc.page.getByText(/^Pregunta 1 de 1$/)
  informe.enunciadoPreguntaSola = await medir(doc.page.getByRole("heading", { level: 1 }))
  informe.eyebrow = await medir(eyebrow)
  informe.sinScrollPreguntaSola = await sinScroll(doc.page)
  await expect(eyebrow).toHaveCSS("text-transform", "uppercase")

  // Pregunta con opciones.
  await mostrarOpciones(doc)
  informe.enunciadoConOpciones = await medir(doc.page.getByRole("heading", { level: 1 }))
  informe.temporizador = await medir(doc.page.getByRole("timer"))
  informe.conteo = await medir(doc.page.getByText(/ya respondieron/))
  const cajas = doc.page.getByRole("listitem")
  for (let i = 0; i < 4; i++) informe[`caja-${"abcd"[i]}`] = await medir(cajas.nth(i))
  informe.sinScrollConOpciones = await sinScroll(doc.page)

  // Celular: tarjetas ≥ 44 px de alto y de ancho.
  await esperarTarjetas(est)
  const cajaTarjeta = await est.page.getByRole("button", { name: "B", exact: true }).boundingBox()
  informe.tarjetaAltoPx = cajaTarjeta?.height ?? 0
  informe.tarjetaAnchoPx = cajaTarjeta?.width ?? 0
  informe.celularSinScrollHorizontal = await est.page.evaluate(
    () => document.documentElement.scrollWidth <= window.innerWidth,
  )
  await responder(est, "B")

  // Histograma, ranking y podio.
  await cerrarPregunta(doc)
  informe.sinScrollHistograma = await sinScroll(doc.page)
  await verRanking(doc)
  informe.sinScrollRanking = await sinScroll(doc.page)
  await finalizar(doc)
  informe.cierre = await medir(doc.page.getByText("¡Gracias por participar!"))
  informe.sinScrollPodio = await sinScroll(doc.page)

  await testInfo.attach("legibilidad.json", {
    body: JSON.stringify(informe, null, 2),
    contentType: "application/json",
  })

  const m = (clave: string) => informe[clave] as Medicion
  // Criterios de §1.1.
  expect.soft(m("enunciadoPreguntaSola").tamanoPx, "enunciado ≥ 40 px").toBeGreaterThanOrEqual(40)
  expect.soft(m("eyebrow").tamanoPx, "eyebrow ≥ 18 px").toBeGreaterThanOrEqual(18)
  expect.soft(m("temporizador").tamanoPx, "temporizador ≥ 26 px").toBeGreaterThanOrEqual(26)
  for (const c of "abcd") expect.soft(m(`caja-${c}`).tamanoPx, `opción ${c} ≥ 26 px`).toBeGreaterThanOrEqual(26)
  for (const clave of ["enunciadoPreguntaSola", "enunciadoConOpciones", "temporizador", "conteo", "cierre"]) {
    expect.soft(m(clave).contraste, `${clave}: contraste ≥ 7:1`).toBeGreaterThanOrEqual(7)
  }
  for (const clave of Object.keys(informe).filter((k) => k.startsWith("sinScroll"))) {
    expect.soft(informe[clave], `${clave}: sin scroll a 1920×1080`).toBe(true)
  }
  expect.soft(informe.tarjetaAltoPx as number, "tarjeta ≥ 44 px de alto").toBeGreaterThanOrEqual(44)
  expect.soft(informe.tarjetaAnchoPx as number, "tarjeta ≥ 44 px de ancho").toBeGreaterThanOrEqual(44)
  expect.soft(informe.celularSinScrollHorizontal, "celular sin scroll horizontal").toBe(true)
  // Cajas de opción: se informan, no bloquean (colores aprobados en el prototipo).
  testInfo.annotations.push({
    type: "contraste-cajas",
    description: "abcd".split("").map((c) => `${c}=${m(`caja-${c}`).contraste}:1`).join(", "),
  })

  await cerrar(doc, est)
})
