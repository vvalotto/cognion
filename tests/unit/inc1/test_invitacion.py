import uuid
from datetime import timedelta

from src.identidad.entities.invitacion import Invitacion


class TestInvitacionCrear:
    def test_crea_con_token_unico_y_sin_usar(self):
        comision_id = uuid.uuid4()
        docente_id = uuid.uuid4()

        invitacion = Invitacion.crear(comision_id, docente_id)

        assert invitacion.comision_id == comision_id
        assert invitacion.docente_id == docente_id
        assert invitacion.token
        assert invitacion.usada_en is None

    def test_expira_en_7_dias_desde_generacion(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())

        assert invitacion.expira_en - invitacion.generada_en == timedelta(days=7)

    def test_tokens_de_invitaciones_distintas_son_unicos(self):
        comision_id = uuid.uuid4()
        docente_id = uuid.uuid4()

        primera = Invitacion.crear(comision_id, docente_id)
        segunda = Invitacion.crear(comision_id, docente_id)

        assert primera.token != segunda.token
        assert primera.id != segunda.id
