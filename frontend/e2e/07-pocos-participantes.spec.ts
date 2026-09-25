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

/** Circuito 7 — pocos participantes (H9): sin nadie ("Nadie participó") y con uno solo. */
test("sin participantes: la sesión se puede conducir y dice 'Nadie participó'", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 1, tiempo: 60 })
  await expect(doc.page.getByRole("alert")).toContainText("podés iniciar igual")
  await iniciar(doc)
  await mostrarOpciones(doc)
  await expect(doc.page.getByText("0 / 0 ya respondieron")).toBeVisible()
  await cerrarPregunta(doc)
  await verRanking(doc)
  await expect(doc.page.getByText("Nadie participó")).toBeVisible()
  await finalizar(doc)
  await expect(doc.page.getByText("Nadie participó")).toBeVisible()
  await testInfo.attach("podio-vacio", { body: await doc.page.screenshot(), contentType: "image/png" })
  await cerrar(doc)
})

test("un solo participante: ranking y podio con un puesto", async ({ browser }) => {
  const doc = await docente(browser)
  const est = await estudiante(browser, 1)
  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 1, tiempo: 60 })
  await unirse(est)
  await esperarSala(est, 1)
  await iniciar(doc)
  await mostrarOpciones(doc)
  await esperarTarjetas(est)
  await responder(est, "B")
  await cerrarPregunta(doc)
  await verRanking(doc)
  await expect(doc.page.getByRole("listitem")).toHaveCount(1)
  await finalizar(doc)
  await expect(doc.page.getByRole("list", { name: "Podio" }).getByRole("listitem")).toHaveCount(1)
  await expect(est.page.getByText(/Quedaste 1° con \d+ puntos/)).toBeVisible()
  await cerrar(doc, est)
})
