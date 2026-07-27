from db import source_connection, agora_connection


def _load_source_families(cursor):
    cursor.execute("""
        SELECT CodigoDeFamilia, Descripcion
        FROM FamiliasDeArticulos
        ORDER BY CodigoDeFamilia
    """)
    return cursor.fetchall()


def _load_existing_families(cursor):
    cursor.execute("""
        SELECT Name
        FROM Family
        WHERE DeletionDate IS NULL
    """)

    return {
        row.Name.strip().upper()
        for row in cursor.fetchall()
    }


def _get_families_to_insert(source_families, existing_families):

    families = []

    for _, name in source_families:

        if not name:
            continue

        name = name.strip()

        if name.upper() not in existing_families:
            families.append(name)

    return families


def _insert_family(cursor, name):

    cursor.execute("""
        INSERT INTO Family
        (
            Name,
            ShowInPos,
            ShowInMenuConfiguration,
            InvoicePrintOrder,
            MajorGroupId,
            StyleText,
            StyleBackColor,
            StyleImageId,
            ParentFamilyId,
            ValidForAllPosGroups
        )
        VALUES
        (
            ?,
            1,
            1,
            0,
            NULL,
            ?,
            0xFF5A616D,
            '00000000-0000-0000-0000-000000000000',
            NULL,
            1
        )
    """, name, name)


def migrate():

    src = source_connection()
    dst = agora_connection()

    try:

        src_cursor = src.cursor()
        dst_cursor = dst.cursor()

        source_families = _load_source_families(src_cursor)
        existing_families = _load_existing_families(dst_cursor)

        families_to_insert = _get_families_to_insert(
            source_families,
            existing_families
        )

        print()
        print("=" * 50)
        print("MIGRACION DE FAMILIAS")
        print("=" * 50)
        print(f"Familias origen : {len(source_families)}")
        print(f"A insertar      : {len(families_to_insert)}")
        print(f"Ya existentes   : {len(source_families) - len(families_to_insert)}")
        print()

        if not families_to_insert:
            print("No hay nada que migrar.")
            return

        continuar = input("¿Continuar? (S/N): ").strip().upper()

        if continuar != "S":
            print("Migracion cancelada.")
            return

        insertadas = 0

        for name in families_to_insert:

            _insert_family(dst_cursor, name)
            insertadas += 1

        dst.commit()

        print()
        print(f"Familias insertadas correctamente: {insertadas}")

    except Exception as ex:

        dst.rollback()

        print()
        print("ERROR DURANTE LA MIGRACION")
        print(ex)

    finally:

        src.close()
        dst.close()
