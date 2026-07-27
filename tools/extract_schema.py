import json
import pyodbc

SERVER = r"localhost\AGORA"
USER = "sa"
PASSWORD = "igt123"

DATABASES = [
    "MARTINEZ",
    "igtpos"
]

QUERY = """
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CHARACTER_MAXIMUM_LENGTH,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
ORDER BY TABLE_NAME, ORDINAL_POSITION
"""

for db in DATABASES:

    print(f"Leyendo {db}...")

    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE={db};"
        f"UID={USER};"
        f"PWD={PASSWORD};"
        "TrustServerCertificate=yes;"
    )

    cur = conn.cursor()

    schema = {}

    for row in cur.execute(QUERY):

        table = row.TABLE_NAME

        schema.setdefault(table, []).append({
            "name": row.COLUMN_NAME,
            "type": row.DATA_TYPE,
            "nullable": row.IS_NULLABLE,
            "length": row.CHARACTER_MAXIMUM_LENGTH,
            "position": row.ORDINAL_POSITION
        })

    filename = f"{db.lower()}_schema.json"

    with open(filename, "w", encoding="utf8") as f:
        json.dump(schema, f, indent=4, ensure_ascii=False)

    print(f"✔ {filename} generado")

    conn.close()

print("FINALIZADO")
