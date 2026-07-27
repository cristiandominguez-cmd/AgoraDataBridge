import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def _build_connection(prefix: str) -> str:
    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={os.getenv(prefix + '_SERVER')}\\{os.getenv(prefix + '_INSTANCE')};"
        f"DATABASE={os.getenv(prefix + '_DATABASE')};"
        f"UID={os.getenv(prefix + '_USER')};"
        f"PWD={os.getenv(prefix + '_PASSWORD')};"
        "TrustServerCertificate=yes;"
    )

def source_connection():
    return pyodbc.connect(_build_connection("SOURCE"))

def agora_connection():
    return pyodbc.connect(_build_connection("AGORA"))
