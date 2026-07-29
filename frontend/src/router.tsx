import { createBrowserRouter } from "react-router"

import { RequireRole } from "@/components/RequireRole"
import { AppLayout } from "@/layouts/AppLayout"
import { AuthLayout } from "@/layouts/AuthLayout"
import { AltaDocente } from "@/pages/AltaDocente"
import { AltaDocenteExito } from "@/pages/AltaDocenteExito"
import { InicioPlaceholder } from "@/pages/_placeholders"
import { Login } from "@/pages/Login"
import { Registro } from "@/pages/Registro"
import { RegistroError } from "@/pages/RegistroError"
import { RegistroExito } from "@/pages/RegistroExito"

/**
 * Router de la aplicación (React Router v7, modo data).
 *
 * Se exporta la instancia (en vez de solo el componente `<RouterProvider>`) para que
 * `api-client.ts` pueda navegar imperativamente a `/login` ante un 401, sin depender de un
 * hook de React (`useNavigate`) fuera del árbol de componentes.
 */
export const router = createBrowserRouter([
  {
    element: <AuthLayout />,
    children: [
      { path: "/login", element: <Login /> },
      { path: "/registro", element: <Registro /> },
      { path: "/registro/error", element: <RegistroError /> },
      { path: "/registro/exito", element: <RegistroExito /> },
    ],
  },
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <InicioPlaceholder /> },
      {
        path: "/docentes/nuevo",
        element: (
          <RequireRole rol="administrador">
            <AltaDocente />
          </RequireRole>
        ),
      },
      {
        path: "/docentes/nuevo/exito",
        element: (
          <RequireRole rol="administrador">
            <AltaDocenteExito />
          </RequireRole>
        ),
      },
    ],
  },
])
