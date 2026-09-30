import { cerrar, docente, estudiante } from "./soporte/actores"
import { TEMAS, datos } from "./soporte/datos"
import {
  cerrarPregunta,
  crearSesion,
  esperarEsperaOpciones,
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

/**
 * Circuito 4 — unión tardía: un Estudiante entra con la pregunta presentada (espera de opciones) y otro
 * con las opciones ya a la vista (tarjetas directo). Ambos responden y el conteo del Docente los suma.
 */
test("unión tardía con la sesión en curso", async ({ browser }) => {
  const doc = await docente(browser)
  const est1 = await estudiante(browser, 1)
  const est2 = await estudiante(browser, 2)
  const est3 = await estudiante(browser, 3)

  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 1, tiempo: 90 })
  await unirse(est1)
  await esperarSala(est1, 1)
  await iniciar(doc)

  // En curso, pregunta sola: la tarjeta de la sesión dice "En curso".
  await est2.page.goto(`/mis-actividades/materias/${datos().materiaId}/actividades`)
  await expect(est2.page.getByRole("button", { name: new RegExp(datos().materiaNombre) })).toContainText("En curso")
  await unirse(est2)
  await esperarEsperaOpciones(est2, 1, 1)

  await mostrarOpciones(doc)
  await esperarTarjetas(est2)

  // Con las opciones ya mostradas: entra directo a las tarjetas.
  await unirse(est3)
  await esperarTarjetas(est3)

  for (const est of [est1, est2, est3]) {
    await esperarTarjetas(est)
    await responder(est, "B")
  }
  await expect(doc.page.getByText("3 / 3 ya respondieron")).toBeVisible()
  await cerrarPregunta(doc)
  await verRanking(doc)
  await expect(doc.page.getByRole("listitem")).toHaveCount(3)
  await finalizar(doc)
  await cerrar(doc, est1, est2, est3)
})
