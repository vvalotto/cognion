import { Outlet } from "react-router"

/**
 * Layout de la proyección del modo en vivo — sin `AppLayout` (`TopStrip`/`AppNav`/`Footer`/
 * `UserMenu`), fondo oscuro con los tokens `--stage-*`
 * (`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1.1). Pensado para un
 * dispositivo distinto al resto del sistema, sin navegación ni menú.
 */
export function StageLayout() {
  return (
    <div
      className="min-h-screen"
      style={{ background: "var(--stage-bg)", color: "var(--stage-fg)" }}
    >
      <Outlet />
    </div>
  )
}
