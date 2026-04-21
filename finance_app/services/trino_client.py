import os
from sqlalchemy import create_engine

def get_engine():
    user = os.getenv("TRINO_USER", "trino")
    host = os.getenv("TRINO_HOST", "trino")
    port = os.getenv("TRINO_PORT", "8080")
    catalog = os.getenv("TRINO_CATALOG", "iceberg")
    schema = os.getenv("TRINO_SCHEMA", "gold")

    url = f"trino://{user}@{host}:{port}/{catalog}/{schema}"
    return create_engine(url)