import uuid

from src.identidad.entities.comision import Comision


class TestComisionCrear:
    def test_crea_con_docentes_asignados_vacio(self):
        admin_id = uuid.uuid4()
        comision = Comision.crear("Ingeniería de Software", "lu 10-12", admin_id)

        assert comision.materia == "Ingeniería de Software"
        assert comision.horario == "lu 10-12"
        assert comision.administrador_id == admin_id
        assert comision.docentes_asignados == []


class TestComisionAsignarDocente:
    def test_agrega_docente_no_presente(self):
        comision = Comision.crear("IS", "lu 10-12", uuid.uuid4())
        docente_id = uuid.uuid4()

        comision.asignar_docente(docente_id)

        assert comision.docentes_asignados == [docente_id]

    def test_no_duplica_docente_ya_asignado(self):
        comision = Comision.crear("IS", "lu 10-12", uuid.uuid4())
        docente_id = uuid.uuid4()

        comision.asignar_docente(docente_id)
        comision.asignar_docente(docente_id)

        assert comision.docentes_asignados == [docente_id]
