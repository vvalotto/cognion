"""Configuración de la aplicación cargada desde variables de entorno."""

from typing import Literal
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_SECRET_KEY_EJEMPLO = "cambiar-por-un-secreto-seguro"
_SECRET_KEY_LARGO_MINIMO = 32
_HOSTS_LOCALES = frozenset({"localhost", "127.0.0.1", "::1"})
_ENTORNOS_ESTRICTOS = frozenset({"staging", "produccion"})


def _es_local(url_o_host: str) -> bool:
    """Indica si una URL (o un host suelto) apunta a la máquina local."""
    host = urlparse(url_o_host if "://" in url_o_host else f"//{url_o_host}").hostname
    return host in _HOSTS_LOCALES


class Settings(BaseSettings):
    """Parámetros de configuración leídos de `.env` o del entorno del proceso."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    entorno: Literal["desarrollo", "staging", "produccion"] = "desarrollo"
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-responder@cognion.local"
    verificador_vencimientos_cadencia_segundos: int = 120
    verificador_vencimientos_umbral_inactividad_minutos: int = 15
    administrador_bloqueo_temporal_minutos: int = 15
    frontend_url: str = "http://localhost:5173"
    cors_allowed_origins: str = "http://localhost:5173"

    @field_validator("cors_allowed_origins")
    @classmethod
    def _rechazar_origen_comodin(cls, valor: str) -> str:
        """Rechaza `*`: es incompatible con `allow_credentials=True` en CORS."""
        if "*" in [origen.strip() for origen in valor.split(",")]:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS no admite '*' porque la API usa credenciales; "
                "listar los orígenes explícitos separados por coma"
            )
        return valor

    @model_validator(mode="after")
    def _validar_entorno_estricto(self) -> "Settings":
        """En staging/producción rechaza valores de desarrollo y lista todas las violaciones.

        Nunca incluye el valor del secreto en el mensaje (`US-8.1.3`).
        """
        if self.entorno not in _ENTORNOS_ESTRICTOS:
            return self
        errores: list[str] = []
        if (
            len(self.secret_key) < _SECRET_KEY_LARGO_MINIMO
            or self.secret_key == _SECRET_KEY_EJEMPLO
        ):
            errores.append(
                f"SECRET_KEY debe tener al menos {_SECRET_KEY_LARGO_MINIMO} caracteres "
                "y no ser el valor de ejemplo"
            )
        if _es_local(self.database_url):
            errores.append("DATABASE_URL no puede apuntar a localhost")
        if _es_local(self.smtp_host):
            errores.append("SMTP_HOST no puede ser localhost")
        if self.smtp_from.endswith("@cognion.local"):
            errores.append("SMTP_FROM no puede usar el dominio de ejemplo @cognion.local")
        if _es_local(self.frontend_url):
            errores.append("FRONTEND_URL no puede apuntar a localhost")
        if any(_es_local(origen) for origen in self.cors_origins_list):
            errores.append("CORS_ALLOWED_ORIGINS no puede incluir orígenes localhost")
        if errores:
            raise ValueError(
                f"Configuración inválida para ENTORNO={self.entorno}: " + "; ".join(errores)
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Orígenes CORS permitidos, separados por coma, sin espacios ni vacíos."""
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


settings = Settings()
