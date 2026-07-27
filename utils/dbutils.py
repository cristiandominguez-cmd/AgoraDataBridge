def fetch_dictionary(cursor, query, key_column, value_column):
    """
    Ejecuta una consulta y devuelve un diccionario.
    """

    cursor.execute(query)

    result = {}

    for row in cursor.fetchall():
        result[getattr(row, key_column)] = getattr(row, value_column)

    return result


def record_exists(cursor, table, field, value):
    """
    Comprueba si existe un registro.
    """

    cursor.execute(
        f"""
        SELECT 1
        FROM {table}
        WHERE {field} = ?
          AND DeletionDate IS NULL
        """,
        value
    )

    return cursor.fetchone() is not None
