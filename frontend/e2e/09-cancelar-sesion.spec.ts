import { cerrar, docente, estudiante } from "./soporte/actores"
import { TEMAS, datos } from "./soporte/datos"
import { crearSesion, esperarSala, unirse } from "./soporte/flujos"
import { expect, test } from "./soporte/prueba"

/**
 * Circuito 9 — cancelar una sesión que no se inició (US-ADJ-58, INV-AEV-10): el Docente la cancela
 * desde la sala con confirmación, el Estudiante en la sala ve la cancelación y la sesión deja de
 * figurar como activa para los dos.
 */
test("cancelar una sesión desde la sala de espera", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  const est1 = await estudiante(browser, 1)

  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 2, tiempo: 60 })
  await unirse(est1)
  await esperarSala(est1, 1)

  await doc.page.getByRole("button", { name: "Cancelar sesión" }).click()
  await expect(doc.page.getByRole("heading", { name: "¿Cancelar esta sesión?" })).toBeVisible()
  // "Volver a la sala" no toca la sesión.
  await doc.page.getByRole("button", { name: "Volver a la sala" }).click()
  await expect(doc.page.getByRole("heading", { name: "Sala de espera" })).toBeVisible()

  await doc.page.getByRole("button", { name: "Cancelar sesión" }).click()
  await doc.page.getByRole("button", { name: "Cancelar sesión" }).click()
  await expect(doc.page).toHaveURL(new RegExp(`/actividad-evaluativa/comisiones/${datos().comisionId}$`))
  await expect(doc.page.getByRole("button", { name: "Continuar" })).toHaveCount(0)

  await expect(est1.page.getByRole("heading", { name: "El Docente canceló la sesión" })).toBeVisible()
  await testInfo.attach("celular-sesion-cancelada", { body: await est1.page.screenshot(), contentType: "image/png" })
  await est1.page.getByRole("link", { name: "Volver a mis actividades" }).click()
  await est1.page.goto(`/mis-actividades/materias/${datos().materiaId}/actividades`)
  await expect(est1.page.getByText("Por ahora no hay sesiones en vivo.")).toBeVisible()

  await cerrar(doc, est1)
})
