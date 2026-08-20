import { createBrowserRouter } from "react-router"

import { RequireRole } from "@/components/RequireRole"
import { AppLayout } from "@/layouts/AppLayout"
import { AuthLayout } from "@/layouts/AuthLayout"
import { AltaDocente } from "@/pages/AltaDocente"
import { AltaDocenteExito } from "@/pages/AltaDocenteExito"
import { CuentaDetallePlaceholder, InicioPlaceholder } from "@/pages/_placeholders"
import { Banco } from "@/pages/Banco"
import { Cuentas } from "@/pages/Cuentas"
import { EditarPregunta } from "@/pages/EditarPregunta"
import { EliminarPregunta } from "@/pages/EliminarPregunta"
import { Login } from "@/pages/Login"
import { Materias } from "@/pages/Materias"
import { NuevaMateria } from "@/pages/NuevaMateria"
import { NuevaPreguntaOpcionMultiple } from "@/pages/NuevaPreguntaOpcionMultiple"
import { NuevaPreguntaTipo } from "@/pages/NuevaPreguntaTipo"
import { NuevaPreguntaVerdaderoFalso } from "@/pages/NuevaPreguntaVerdaderoFalso"
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
      {
        path: "/materias",
        element: (
          <RequireRole rol="docente">
            <Materias />
          </RequireRole>
        ),
      },
      {
        path: "/materias/nueva",
        element: (
          <RequireRole rol="docente">
            <NuevaMateria />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco",
        element: (
          <RequireRole rol="docente">
            <Banco />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/nueva",
        element: (
          <RequireRole rol="docente">
            <NuevaPreguntaTipo />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/nueva/opcion-multiple",
        element: (
          <RequireRole rol="docente">
            <NuevaPreguntaOpcionMultiple />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/nueva/verdadero-falso",
        element: (
          <RequireRole rol="docente">
            <NuevaPreguntaVerdaderoFalso />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/:preguntaId/editar",
        element: (
          <RequireRole rol="docente">
            <EditarPregunta />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/:preguntaId/eliminar",
        element: (
          <RequireRole rol="docente">
            <EliminarPregunta />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas",
        element: (
          <RequireRole rol="administrador">
            <Cuentas />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas/:usuarioId",
        element: (
          <RequireRole rol="administrador">
            <CuentaDetallePlaceholder />
          </RequireRole>
        ),
      },
    ],
  },
])
