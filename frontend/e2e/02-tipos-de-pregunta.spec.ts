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
import { expect, test } from "./soporte/prueba"

/** Circuito 2 — tipos de pregunta: Verdadero/Falso (H1) y tres opciones (H2), en proyección y celular. */
test("Verdadero/Falso: dos cajas y dos tarjetas, histograma de dos barras", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  const est1 = await estudiante(browser, 1)
  const est2 = await estudiante(browser, 2)

  await crearSesion(doc, { tema: TEMAS.verdaderoFalso, cantidad: 1, tiempo: 60 })
  await unirse(est1)
  await esperarSala(est1, 1)
  await unirse(est2)
  await esperarSala(est2, 2)
  await iniciar(doc)
  await mostrarOpciones(doc)

  const cajas = doc.page.getByRole("listitem")
  await expect(cajas).toHaveText(["Verdadero", "Falso"])
  await expect(cajas.nth(0)).toHaveAttribute("data-color", "b")
  await expect(cajas.nth(1)).toHaveAttribute("data-color", "c")

  await esperarTarjetas(est1)
  await expect(est1.page.getByRole("button", { name: /^(Verdadero|Falso)$/ })).toHaveCount(2)
  await testInfo.attach("celular-vf", { body: await est1.page.screenshot(), contentType: "image/png" })

  expect((await responder(est1, "Verdadero")).correcta).toBe(true)
  expect((await responder(est2, "Falso")).correcta).toBe(false)

  await cerrarPregunta(doc)
  const barras = doc.page.getByTestId("barra-histograma")
  await expect(barras).toHaveText(["1", "1"])
  await expect(doc.page.getByRole("listitem").filter({ hasText: "Verdadero ✓" })).toHaveAttribute("data-correcta", "true")
  await testInfo.attach("histograma-vf", { body: await doc.page.screenshot(), contentType: "image/png" })

  await verRanking(doc)
  await finalizar(doc)
  await cerrar(doc, est1, est2)
})

test("tres opciones: la tercera ocupa el ancho completo en proyección y celular", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  const est1 = await estudiante(browser, 1)

  await crearSesion(doc, { tema: TEMAS.tresOpciones, cantidad: 1, tiempo: 60 })
  await unirse(est1)
  await esperarSala(est1, 1)
  await iniciar(doc)
  await mostrarOpciones(doc)

  const cajas = doc.page.getByRole("listitem")
  await expect(cajas).toHaveText(["A", "B", "C"])
  await expect(cajas.nth(2)).toHaveClass(/col-span-2/)

  await esperarTarjetas(est1)
  const tarjetas = est1.page.getByRole("button", { name: /^[ABC]$/ })
  await expect(tarjetas).toHaveCount(3)
  await expect(tarjetas.nth(2)).toHaveClass(/col-span-2/)
  await testInfo.attach("celular-3-opciones", { body: await est1.page.screenshot(), contentType: "image/png" })

  expect((await responder(est1, "B")).correcta).toBe(true)
  await cerrarPregunta(doc)
  await expect(doc.page.getByTestId("barra-histograma")).toHaveText(["0", "1", "0"])
  await verRanking(doc)
  await finalizar(doc)
  await cerrar(doc, est1)
})
