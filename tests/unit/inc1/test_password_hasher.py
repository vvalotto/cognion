from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher


class TestBcryptPasswordHasher:
    def test_hash_no_es_igual_a_password_plano(self):
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("claveSegura1")

        assert hashed != "claveSegura1"

    def test_verificar_password_correcto(self):
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("claveSegura1")

        assert hasher.verificar("claveSegura1", hashed) is True

    def test_verificar_password_incorrecto(self):
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("claveSegura1")

        assert hasher.verificar("otraClave", hashed) is False
