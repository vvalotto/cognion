import { execFileSync } from "node:child_process"
import { join } from "node:path"

import { datos } from "./datos"

/** Borra lo sembrado con el script de limpieza existente (`tests/uat/inc6/limpiar_uat.sh`). */
export default async function limpiar() {
  if (process.env.E2E_CONSERVAR_DATOS) return
  const raiz = join(import.meta.dirname, "..", "..", "..")
  execFileSync(join(raiz, "tests/uat/inc6/limpiar_uat.sh"), [datos().prefijo], { cwd: raiz, stdio: "inherit" })
}
