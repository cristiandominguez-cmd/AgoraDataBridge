from db import source_connection

conn = source_connection()
cur = conn.cursor()

cur.execute("""
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Articulos'
ORDER BY ORDINAL_POSITION
""")

for row in cur.fetchall():
    print(f"{row.COLUMN_NAME}|{row.DATA_TYPE}")

conn.close()
