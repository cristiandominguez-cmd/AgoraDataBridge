"""
Migración de clientes desde Martínez hacia Ágora.
"""

from db import source_connection, agora_connection


def migrate():

    src = source_connection()
    dst = agora_connection()

    src_cursor = src.cursor()
    dst_cursor = dst.cursor()

    src_cursor.execute("""
        SELECT
            CodigoDeCliente,
            Nombre,
            RazonSocial,
            CIF,
            Domicilio,
            CodigoPostal,
            Poblacion,
            Provincia,
            Telefono1,
            Email1,
            Descuento1,
            Observaciones,
            RecargoEnElIva,
            MostrarNotaDocumento
        FROM Clientes
        WHERE FechaBaja IS NULL
        ORDER BY CodigoDeCliente
    """)

    clientes = src_cursor.fetchall()

    limite = input("Cantidad de clientes (0 = todos): ").strip()

    if limite.isdigit():
        limite = int(limite)

        if limite > 0:
            clientes = clientes[:limite]

    if not clientes:

        print()
        print("No existen clientes para migrar.")

        src.close()
        dst.close()

        return

    print()
    print("=" * 50)
    print("MIGRACIÓN DE CLIENTES")
    print("=" * 50)
    print(f"Clientes encontrados : {len(clientes)}")
    print()

    continuar = input("¿Continuar? (S/N): ").strip().upper()

    if continuar != "S":

        src.close()
        dst.close()

        print("Migración cancelada.")
        return

    insertados = 0
    omitidos = 0
    errores = 0

    dst_cursor.execute("""
        SELECT ISNULL(MAX(Id), 0) + 1
        FROM Customer
    """)
    nuevo_id = dst_cursor.fetchone()[0]

    try:
        for cliente in clientes:

            (
                codigo,
                nombre,
                razon_social,
                cif,
                domicilio,
                codigo_postal,
                poblacion,
                provincia,
                telefono,
                email,
                descuento,
                observaciones,
                recargo_iva,
                mostrar_nota
            ) = cliente
            
            codigo = str(codigo or "").strip()
            nombre = str(nombre or "").strip()
            razon_social = str(razon_social or "").strip()
            cif = str(cif or "").strip()

            telefono = str(telefono or "").strip()
            email = str(email or "").strip()
            domicilio = str(domicilio or "").strip()
            codigo_postal = str(codigo_postal or "").strip()
            poblacion = str(poblacion or "").strip()
            provincia = str(provincia or "").strip()
            observaciones = str(observaciones or "").strip()

            if not nombre and not razon_social:

                print(f"[OMITIDO] {codigo} - Sin nombre ni razón social")

                omitidos += 1

                continue

            if not poblacion:
                poblacion = "Zaragoza"

            if not provincia:
                provincia = "Zaragoza"

            if not nombre:
                nombre = razon_social

            if not razon_social:
                razon_social = nombre

            dst_cursor.execute("""
                SELECT Id
                FROM Customer
                WHERE AccountCode = ?
                  AND DeletionDate IS NULL
            """, codigo)

            existe = dst_cursor.fetchone()

            if existe:

                print(f"[OMITIDO] {codigo} - {nombre} (Código ya existe)")

                omitidos += 1

                continue

            if cif:

                dst_cursor.execute("""
                    SELECT Id
                    FROM Customer
                    WHERE Cif = ?
                      AND DeletionDate IS NULL
                """, cif)

                existe = dst_cursor.fetchone()

                if existe:

                    print(f"[OMITIDO] {codigo} - {nombre} (CIF ya existe)")

                    omitidos += 1

                    continue

            print(f"[INSERTADO] {codigo} - {nombre}")

            descuento = descuento or 0
            
            recargo_iva = 1 if recargo_iva in (1, True, "1", "S", "s") else 0
            mostrar_nota = 1 if mostrar_nota in (1, True, "1", "S", "s") else 0

            dst_cursor.execute("""
                INSERT INTO Customer
                (   
                    Id,
                    DeletionDate,
                    FiscalName,
                    Cif,
                    BusinessName,
                    Telephone,
                    Email,
                    AccountCode,
                    ContactPerson,
                    DiscountRate,
                    CardNumber,
                    RequireIdentificationCard,
                    SendMailing,
                    ApplySurcharge,
                    ShowNotes,
                    CountryCode,
                    DocumentIdType,
                    Notes,
                    PriceListId,
                    ParentCustomerId,
                    Street,
                    City,
                    Region,
                    ZipCode,
                    ValidForAllPosGroups,
                    TypeId
                )
                VALUES
                ( 
                    ?,
                    NULL,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    '',
                    ?,
                    '',
                    0,
                    0,
                    ?,
                    ?,
                    'ES',
                    1,
                    ?,
                    NULL,
                    NULL,
                    ?,
                    ?,
                    ?,
                    ?,
                    1,
                    NULL
                )
            """,
                nuevo_id,
                razon_social,
                cif,
                nombre,
                telefono,
                email,
                codigo,
                descuento,
                recargo_iva,
                mostrar_nota,
                observaciones,
                domicilio,
                poblacion,
                provincia,
                codigo_postal
            )

            insertados += 1
            nuevo_id += 1


        dst.commit()

        print()
        print("=" * 50)
        print("MIGRACIÓN FINALIZADA")
        print("=" * 50)
        print(f"Insertados : {insertados}")
        print(f"Omitidos   : {omitidos}")
        print(f"Errores    : {errores}")

    except Exception as ex:

        errores += 1

        dst.rollback()

        print()
        print("ERROR DURANTE LA MIGRACIÓN")
        print(type(ex).__name__)
        print(ex)

    finally:

        src.close()
        dst.close()
 