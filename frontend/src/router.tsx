import { createBrowserRouter } from "react-router"

import { AppLayout } from "@/layouts/AppLayout"
import { AuthLayout } from "@/layouts/AuthLayout"
import { LoginPlaceholder, RegistroPlaceholder } from "@/pages/_placeholders"

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
      { path: "/login", element: <LoginPlaceholder /> },
      { path: "/registro", element: <RegistroPlaceholder /> },
    ],
  },
  {
    element: <AppLayout />,
    children: [],
  },
])
