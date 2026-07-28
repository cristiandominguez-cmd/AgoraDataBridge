from pathlib import Path

from database import get_connection


def run_audit(sql_file: str, title: str):
    conn = get_connection()
    cursor = conn.cursor()

    sql_path = Path(__file__).parent.parent / "sql" / sql_file

    with open(sql_path, encoding="utf-8") as f:
        sql = f.read()

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    cursor.execute(sql)

    while True:
        row = cursor.fetchone()

        if row:
            name = row[0]
            value = row[1]

            if value == 0:
                print(f"[ OK ] {name}")
            else:
                print(f"[INFO] {name}: {value}")

        if not cursor.nextset():
            break

    conn.close()
