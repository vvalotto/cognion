import { createBrowserRouter } from "react-router"

import { RequireRole } from "@/components/RequireRole"
import { AppLayout } from "@/layouts/AppLayout"
import { AuthLayout } from "@/layouts/AuthLayout"
import { StageLayout } from "@/layouts/StageLayout"
import { AltaDocente } from "@/pages/identidad/AltaDocente"
import { ComisionDetalle } from "@/pages/identidad/ComisionDetalle"
import { EditarComision } from "@/pages/identidad/EditarComision"
import { EliminarComision } from "@/pages/identidad/EliminarComision"
import { AltaDocenteExito } from "@/pages/identidad/AltaDocenteExito"
import { Inicio } from "@/pages/Inicio"
import { Actividades } from "@/pages/actividad-evaluativa/Actividades"
import { ActividadDetalle } from "@/pages/actividad-evaluativa/ActividadDetalle"
import { CompletitudActividad } from "@/pages/analytics/CompletitudActividad"
import { Banco } from "@/pages/banco-preguntas/Banco"
import { CambiarPassword } from "@/pages/identidad/CambiarPassword"
import { CerrarActividad } from "@/pages/actividad-evaluativa/CerrarActividad"
import { ComisionDetalleDocente } from "@/pages/actividad-evaluativa/ComisionDetalleDocente"
import { ComisionesDeMateria } from "@/pages/actividad-evaluativa/ComisionesDeMateria"
import { CuentaDetalle } from "@/pages/cuentas/CuentaDetalle"
import { EditarCuenta } from "@/pages/cuentas/EditarCuenta"
import { EliminarCuenta } from "@/pages/cuentas/EliminarCuenta"
import { CuentaReseteada } from "@/pages/cuentas/CuentaReseteada"
import { Cuentas } from "@/pages/cuentas/Cuentas"
import { Analytics } from "@/pages/analytics/Analytics"
import { DesempenoPorAlumno } from "@/pages/analytics/DesempenoPorAlumno"
import { DesempenoPorComision } from "@/pages/analytics/DesempenoPorComision"
import { DesempenoPorComisionDetalleEstudiante } from "@/pages/analytics/DesempenoPorComisionDetalleEstudiante"
import { DesempenoPorTema } from "@/pages/analytics/DesempenoPorTema"
import { EvolucionTemporal } from "@/pages/analytics/EvolucionTemporal"
import { RankingPreguntasFalladas } from "@/pages/analytics/RankingPreguntasFalladas"
import { EditarPregunta } from "@/pages/banco-preguntas/EditarPregunta"
import { EditarTituloActividad } from "@/pages/actividad-evaluativa/EditarTituloActividad"
import { EliminarPregunta } from "@/pages/banco-preguntas/EliminarPregunta"
import { EvaluacionSuspendida } from "@/pages/actividad-evaluativa/EvaluacionSuspendida"
import { ExtenderPlazo } from "@/pages/actividad-evaluativa/ExtenderPlazo"
import { FueraDePeriodo } from "@/pages/actividad-evaluativa/FueraDePeriodo"
import { Login } from "@/pages/identidad/Login"
import { Materias } from "@/pages/banco-preguntas/Materias"
import { MateriasActividades } from "@/pages/actividad-evaluativa/MateriasActividades"
import { MiDesempeno } from "@/pages/analytics/MiDesempeno"
import { MisActividades } from "@/pages/actividad-evaluativa/MisActividades"
import { MisMaterias } from "@/pages/actividad-evaluativa/MisMaterias"
import { NuevaActividad } from "@/pages/actividad-evaluativa/NuevaActividad"
import { NuevaComision } from "@/pages/identidad/NuevaComision"
import { EditarMateria } from "@/pages/banco-preguntas/EditarMateria"
import { EliminarMateria } from "@/pages/banco-preguntas/EliminarMateria"
import { VerMateria } from "@/pages/banco-preguntas/VerMateria"
import { NuevaMateria } from "@/pages/banco-preguntas/NuevaMateria"
import { NuevaPreguntaOpcionMultiple } from "@/pages/banco-preguntas/NuevaPreguntaOpcionMultiple"
import { NuevaPreguntaTipo } from "@/pages/banco-preguntas/NuevaPreguntaTipo"
import { NuevaPreguntaVerdaderoFalso } from "@/pages/banco-preguntas/NuevaPreguntaVerdaderoFalso"
import { RecuperarPasswordExito } from "@/pages/identidad/RecuperarPasswordExito"
import { RecuperarPasswordNueva } from "@/pages/identidad/RecuperarPasswordNueva"
import { RecuperarPasswordSolicitado } from "@/pages/identidad/RecuperarPasswordSolicitado"
import { RecuperarPasswordSolicitar } from "@/pages/identidad/RecuperarPasswordSolicitar"
import { RecuperarPasswordTokenInvalido } from "@/pages/identidad/RecuperarPasswordTokenInvalido"
import { AutoregistroDocente } from "@/pages/identidad/AutoregistroDocente"
import { AutoregistroEstudiante } from "@/pages/identidad/AutoregistroEstudiante"
import { AutoregistroExito } from "@/pages/identidad/AutoregistroExito"
import { AutoregistroPerfil } from "@/pages/identidad/AutoregistroPerfil"
import { Registro } from "@/pages/identidad/Registro"
import { RegistroError } from "@/pages/identidad/RegistroError"
import { RegistroExito } from "@/pages/identidad/RegistroExito"
import { RendirEvaluacion } from "@/pages/actividad-evaluativa/RendirEvaluacion"
import { ResetearPassword } from "@/pages/cuentas/ResetearPassword"
import { RevisionEvaluacion } from "@/pages/actividad-evaluativa/RevisionEvaluacion"
import { RevisionEvaluacionDocente } from "@/pages/analytics/RevisionEvaluacionDocente"
import { ProyeccionSesionEnVivo } from "@/pages/actividad-evaluativa/ProyeccionSesionEnVivo"
import { NuevaSesionEnVivo } from "@/pages/actividad-evaluativa/NuevaSesionEnVivo"
import { SalaEsperaDocente } from "@/pages/actividad-evaluativa/SalaEsperaDocente"
import { SesionEnVivoEstudiante } from "@/pages/actividad-evaluativa/SesionEnVivoEstudiante"

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
      { path: "/autoregistro", element: <AutoregistroPerfil /> },
      { path: "/autoregistro/docente", element: <AutoregistroDocente /> },
      { path: "/autoregistro/estudiante", element: <AutoregistroEstudiante /> },
      { path: "/autoregistro/exito", element: <AutoregistroExito /> },
      { path: "/registro", element: <Registro /> },
      { path: "/registro/error", element: <RegistroError /> },
      { path: "/registro/exito", element: <RegistroExito /> },
      { path: "/recuperar-password", element: <RecuperarPasswordSolicitar /> },
      { path: "/recuperar-password/solicitado", element: <RecuperarPasswordSolicitado /> },
      { path: "/recuperar-password/invalido", element: <RecuperarPasswordTokenInvalido /> },
      { path: "/recuperar-password/exito", element: <RecuperarPasswordExito /> },
      { path: "/recuperar-password/:token", element: <RecuperarPasswordNueva /> },
    ],
  },
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <Inicio /> },
      { path: "/mi-cuenta/cambiar-password", element: <CambiarPassword /> },
      {
        path: "/comisiones/nueva",
        element: (
          <RequireRole rol="administrador">
            <NuevaComision />
          </RequireRole>
        ),
      },
      {
        path: "/comisiones/:comisionId",
        element: (
          <RequireRole rol="administrador">
            <ComisionDetalle />
          </RequireRole>
        ),
      },
      {
        path: "/comisiones/:comisionId/editar",
        element: (
          <RequireRole rol="administrador">
            <EditarComision />
          </RequireRole>
        ),
      },
      {
        path: "/comisiones/:comisionId/eliminar",
        element: (
          <RequireRole rol="administrador">
            <EliminarComision />
          </RequireRole>
        ),
      },
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
          <RequireRole rol={["docente", "administrador"]}>
            <Materias />
          </RequireRole>
        ),
      },
      {
        path: "/materias/nueva",
        element: (
          <RequireRole rol="administrador">
            <NuevaMateria />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/editar",
        element: (
          <RequireRole rol="administrador">
            <EditarMateria />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/ver",
        element: (
          <RequireRole rol={["docente", "administrador"]}>
            <VerMateria />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/eliminar",
        element: (
          <RequireRole rol="administrador">
            <EliminarMateria />
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
            <CuentaDetalle />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas/:usuarioId/editar",
        element: (
          <RequireRole rol="administrador">
            <EditarCuenta />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas/:usuarioId/resetear-password",
        element: (
          <RequireRole rol="administrador">
            <ResetearPassword />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas/:usuarioId/reseteada",
        element: (
          <RequireRole rol="administrador">
            <CuentaReseteada />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas/:usuarioId/eliminar",
        element: (
          <RequireRole rol="administrador">
            <EliminarCuenta />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/materias",
        element: (
          <RequireRole rol="docente">
            <MateriasActividades />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/materias/:materiaId/actividades",
        element: (
          <RequireRole rol="docente">
            <Actividades />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/materias/:materiaId/actividades/nueva",
        element: (
          <RequireRole rol="docente">
            <NuevaActividad />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/materias/:materiaId/comisiones",
        element: (
          <RequireRole rol="docente">
            <ComisionesDeMateria />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/comisiones/:comisionId",
        element: (
          <RequireRole rol="docente">
            <ComisionDetalleDocente />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/actividades/:actividadId",
        element: (
          <RequireRole rol="docente">
            <ActividadDetalle />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/actividades/:actividadId/editar-titulo",
        element: (
          <RequireRole rol="docente">
            <EditarTituloActividad />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/actividades/:actividadId/extender-plazo",
        element: (
          <RequireRole rol="docente">
            <ExtenderPlazo />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/actividades/:actividadId/cerrar",
        element: (
          <RequireRole rol="docente">
            <CerrarActividad />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/actividades/:actividadId/completitud",
        element: (
          <RequireRole rol="docente">
            <CompletitudActividad />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/materias",
        element: (
          <RequireRole rol="estudiante">
            <MisMaterias />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/materias/:materiaId/actividades",
        element: (
          <RequireRole rol="estudiante">
            <MisActividades />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/:actividadId/fuera-de-periodo",
        element: (
          <RequireRole rol="estudiante">
            <FueraDePeriodo />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/actividades/:actividadId/rendir",
        element: (
          <RequireRole rol="estudiante">
            <RendirEvaluacion />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/actividades/:actividadId/suspendida",
        element: (
          <RequireRole rol="estudiante">
            <EvaluacionSuspendida />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/evaluaciones/:evaluacionId/revision",
        element: (
          <RequireRole rol="estudiante">
            <RevisionEvaluacion />
          </RequireRole>
        ),
      },
      {
        path: "/analytics/mi-desempeno",
        element: (
          <RequireRole rol="estudiante">
            <MiDesempeno />
          </RequireRole>
        ),
      },
      {
        path: "/analytics",
        element: (
          <RequireRole rol="docente">
            <Analytics />
          </RequireRole>
        ),
      },
      {
        path: "/analytics/desempeno-por-comision",
        element: (
          <RequireRole rol="docente">
            <DesempenoPorComision />
          </RequireRole>
        ),
      },
      {
        path: "/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId",
        element: (
          <RequireRole rol="docente">
            <DesempenoPorComisionDetalleEstudiante />
          </RequireRole>
        ),
      },
      {
        path: "/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId/evaluaciones/:evaluacionId/revision",
        element: (
          <RequireRole rol="docente">
            <RevisionEvaluacionDocente />
          </RequireRole>
        ),
      },
      {
        path: "/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId/evolucion",
        element: (
          <RequireRole rol="docente">
            <EvolucionTemporal />
          </RequireRole>
        ),
      },
      {
        path: "/analytics/desempeno-por-alumno",
        element: (
          <RequireRole rol="docente">
            <DesempenoPorAlumno />
          </RequireRole>
        ),
      },
      {
        path: "/analytics/desempeno-por-tema",
        element: (
          <RequireRole rol="docente">
            <DesempenoPorTema />
          </RequireRole>
        ),
      },
      {
        path: "/analytics/ranking-preguntas-falladas",
        element: (
          <RequireRole rol="docente">
            <RankingPreguntasFalladas />
          </RequireRole>
        ),
      },
      {
        path: "/sesiones-en-vivo/comisiones/:comisionId/nueva",
        element: (
          <RequireRole rol="docente">
            <NuevaSesionEnVivo />
          </RequireRole>
        ),
      },
      {
        path: "/sesiones-en-vivo/:sesionId/sala",
        element: (
          <RequireRole rol="docente">
            <SalaEsperaDocente />
          </RequireRole>
        ),
      },
      {
        path: "/mis-sesiones-en-vivo/:sesionId",
        element: (
          <RequireRole rol="estudiante">
            <SesionEnVivoEstudiante />
          </RequireRole>
        ),
      },
    ],
  },
  {
    element: <StageLayout />,
    children: [
      {
        path: "/sesiones-en-vivo/:sesionId/proyeccion",
        element: (
          <RequireRole rol="docente">
            <ProyeccionSesionEnVivo />
          </RequireRole>
        ),
      },
    ],
  },
])
