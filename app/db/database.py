from sqlalchemy import create_engine
from app.config.settings import settings


def build_connection(server: str, instance: str, database: str, user: str, password: str):
    return (
        f"mssql+pyodbc://{user}:{password}@{server}\\{instance}/{database}"
        "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
    )


source_engine = create_engine(
    build_connection(
        settings.SOURCE_SERVER,
        settings.SOURCE_INSTANCE,
        settings.SOURCE_DATABASE,
        settings.SOURCE_USER,
        settings.SOURCE_PASSWORD,
    ),
    future=True,
)

agora_engine = create_engine(
    build_connection(
        settings.AGORA_SERVER,
        settings.AGORA_INSTANCE,
        settings.AGORA_DATABASE,
        settings.AGORA_USER,
        settings.AGORA_PASSWORD,
    ),
    future=True,
)
