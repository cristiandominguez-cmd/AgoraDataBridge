from db import source_connection, agora_connection


def _load_families(cursor):

    cursor.execute("""
        SELECT Id, Name
        FROM Family
        WHERE DeletionDate IS NULL
    """)

    familias = {}

    for row in cursor.fetchall():
        familias[row.Name.strip().upper()] = row.Id

    return familias




def _load_source_families(cursor):

    cursor.execute("""
        SELECT CodigoDeFamilia, Descripcion
        FROM FamiliasDeArticulos
    """)

    familias = {}

    for row in cursor.fetchall():
        familias[(row.CodigoDeFamilia or "").strip().upper()] = (row.Descripcion or "").strip().upper()

    return familias

def _load_vats(cursor):

    cursor.execute("""
        SELECT Id, VatRate
        FROM Vat
    """)

    ivas = {}

    for row in cursor.fetchall():

        porcentaje = int(round(float(row.VatRate) * 100))

        ivas[str(porcentaje)] = row.Id

    return ivas


def _load_prices(cursor):

    cursor.execute("""
        SELECT
            CodigoDeArticulo,
            Precio
        FROM Tarifas
        WHERE Tarifa = 1
    """)

    precios = {}

    for row in cursor.fetchall():
        precios[(row.CodigoDeArticulo or "").strip()] = float(row.Precio or 0)

    return precios


def _load_default_price_list(cursor):

    cursor.execute("""
        SELECT TOP 1 Id
        FROM PriceList
        WHERE DeletionDate IS NULL
        ORDER BY Id
    """)

    row = cursor.fetchone()

    if row is None:
        raise Exception("No existe ninguna lista de precios.")

    return row.Id


IVA_MAP = {"E": "0", "S": "4", "R": "10", "N": "21"}

def migrate():

    src = source_connection()
    dst = agora_connection()

    src_cursor = src.cursor()
    dst_cursor = dst.cursor()

    familias = _load_families(dst_cursor)
    familias_origen = _load_source_families(src_cursor)
    ivas = _load_vats(dst_cursor)
    price_list_id = _load_default_price_list(dst_cursor)
    precios = _load_prices(src_cursor)

    src_cursor.execute("""
        SELECT
            CodigoDeArticulo,
            Descripcion,
            Familia,
            TipoIva,
            PrecioCosteReal,
            UnidadDeMedida,
            TratarStock,
            CodigoBarras_ean13,
            ArticulosExtendidoNombre1,
            ArticulosExtendidoNombre2,
            ArticulosExtendidoNombre3,
            ArticulosExtendidoObservaciones3,
            OcultarEnTPV
        FROM Articulos
        ORDER BY CodigoDeArticulo
    """)

    productos = src_cursor.fetchall()

    limite = input("Cantidad de productos (0 = todos): ").strip()
    if limite.isdigit():
        limite = int(limite)
        if limite > 0:
            productos = productos[:limite]

    if not productos:

        print()
        print("No existen productos para migrar.")

        src.close()
        dst.close()

        return

    print()
    print("=" * 50)
    print("MIGRACIÃ“N DE PRODUCTOS")
    print("=" * 50)
    print(f"Productos encontrados : {len(productos)}")
    print()

    continuar = input("Â¿Continuar? (S/N): ").strip().upper()

    if continuar != "S":

        src.close()
        dst.close()

        print("MigraciÃ³n cancelada.")
        return

    insertados = 0
    omitidos = 0
    errores = 0

    try:

        for producto in productos:

            (
                codigo,
                nombre,
                familia,
                tipo_iva,
                precio_coste,
                unidad,
                tratar_stock,
                codigo_barras,
                texto1,
                texto2,
                texto3,
                conservacion,
                ocultar_en_tpv
            ) = producto

            codigo = (codigo or "").strip()
            precio_venta = float(precios.get(codigo, 0) or 0)
            nombre = (nombre or "").strip()

            familia = (familia or "").strip().upper()

            tipo_iva = str(tipo_iva or "").strip().upper()
            tipo_iva = IVA_MAP.get(tipo_iva)

            if tipo_iva is None:
                print(f"IVA no soportado: {codigo} ({nombre})")
                continue

            nombre_familia = familias_origen.get(familia)
            family_id = familias.get(nombre_familia) if nombre_familia else None

            if family_id is None:

                print(f"Familia no encontrada: {familia}")
                continue

            vat_id = ivas.get(tipo_iva)

            if vat_id is None:

                print(f"IVA no encontrado: {tipo_iva}")
                continue

            is_sold_by_weight = (
                str(unidad or "").strip().upper() == "KG"
            )

            stock_control = 1 if tratar_stock else 0

            lineas = []

            TEXTOS_EXCLUIDOS = (
                "FECHA DESHUESADO",
            )

            for texto in (texto1, texto2, texto3):

                if not texto:
                    continue

                texto = texto.strip()

                if not texto:
                    continue

                if any(x in texto.upper() for x in TEXTOS_EXCLUIDOS):
                    continue

                lineas.append(texto)

            if conservacion and conservacion.strip():
                lineas.append(conservacion.strip())

            label_lines = None if not lineas else "\r\n".join(lineas)

            print(codigo, repr(label_lines))

            dst_cursor.execute("""
                SELECT
                    Id,
                    Name,
                    PriceLookUpCode
                FROM Product
                WHERE DeletionDate IS NULL
                  AND (
                        PriceLookUpCode = ?
                     OR Name = ?
                  )
            """, codigo, nombre)

            row = dst_cursor.fetchone()

            if row:
                print(
                    f"[EXISTE] Código origen={codigo} "
                    f"Nombre={nombre} "
                    f"ID={row.Id} "
                    f"Código destino={row.PriceLookUpCode}"
                )
                omitidos += 1
                continue

            print(f"[NUEVO] {codigo} - {nombre}")
            print("ANTES DEL INSERT PRODUCT")
            dst_cursor.execute("""
                INSERT INTO Product
                (
                    Type,
                    Name,
                    PriceLookUpCode,
                    IsSoldByWeight,
                    AskForPreparationNotes,
                    OnQuantityChanged,
                    StockControlMode,
                    UseAsDirectSale,
                    HasRestrictedAvailability,
                    AvgCostPrice,
                    Origin,
                    PrintMode,
                    CostPriceMode,
                    PurchaseUnitId,
                    ProductionUnitId,
                    PreparationTypeId,
                    PreparationOrderId,
                    FamilyId,
                    VatId,
                    PurchaseVatId,
                    RecipeNotes,
                    HasLotControl,
                    HasLotControlOnSale,
                    AllowCustomNoteInDigitalMenu,
                    AdjustIngredientsOnSale,
                    LabelLines,
                    StockUnitId,
                    StockProductId,
                    MenuTag,
                    IsSoldBySizeAndColor,
                    BarcodeSummary,
                    CategorySummary,
                    ShelfInfoReferenceUnits,
                    ShelfInfoReferenceQuantity,
                    ShelfInfoActualQuantity,
                    RecipeUnitId,
                    IsEnabledForInternalOrders,
                    CanBePurchased,
                    GenerateAutomaticLot,
                    AutomaticLotExpirationInDays,
                    ResetAvailabilityQuantity,
                    AutomaticLotNeverExpire
                )
                VALUES
                (
                    'P',
                    ?,
                    ?,
                    ?,
                    0,
                    0,
                    ?,
                    0,
                    0,
                    ?,
                    0,
                    1,
                    0,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    ?,
                    ?,
                    NULL,
                    '',
                    0,
                    0,
                    0,
                    0,
                    ?,
                    1,
                    NULL,
                    NULL,
                    '',
                    '',
                    '',
                    '',
                    NULL,
                    NULL,
                    NULL,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
            """,
                nombre,
                codigo,
                is_sold_by_weight,
                stock_control,
                precio_coste or 0,
                family_id,
                vat_id,
                label_lines
            )
            print("DESPUES DEL INSERT PRODUCT")
            dst_cursor.execute("""
                SELECT Id
                FROM Product
                WHERE PriceLookUpCode = ?
                  AND DeletionDate IS NULL
                ORDER BY Id DESC
            """, codigo)

            new_product_id = dst_cursor.fetchone()[0]

            dst_cursor.execute("""
                UPDATE Product
                SET
                    StockUnitId = 1,
                    RecipeUnitId = NULL,
                    MenuTag = NULL
                WHERE Id = ?
            """, new_product_id)

            dst_cursor.execute("""
                SELECT StockUnitId, RecipeUnitId, MenuTag
                FROM Product
                WHERE Id = ?
            """, new_product_id)

            print("PRODUCTO:", new_product_id, dst_cursor.fetchone())

            dst_cursor.execute("""
                SELECT TOP 1 Id
                FROM SaleFormat
                WHERE ProductId = ?
                  AND IsBase = 1
                  AND DeletionDate IS NULL
                ORDER BY Id
            """, new_product_id)

            sf = dst_cursor.fetchone()

            saleable_as_main = 0 if ocultar_en_tpv else 1

            if sf:
                sale_format_id = sf.Id
            else:
                dst_cursor.execute("""
                    INSERT INTO SaleFormat
                    (
                        Name, ProductId, SaleableAsMain, SaleableAsAddin,
                        Ratio, IsBase, AskForAddins,
                        DocumentText, PreparationText, StyleText,
                        StyleBackColor, StyleImageId, Priority
                    )
                    VALUES
                    (
                        ?, ?, ?, 0, 1, 1, 1,
                        ?, ?, ?,
                        '0xFFFFFFFF',
                        '00000000-0000-0000-0000-000000000000',
                        0
                    )
                   """,
                nombre,
                new_product_id,
                saleable_as_main,
                nombre,
                nombre,
                nombre
            )

                dst_cursor.execute("""
                    SELECT Id
                    FROM SaleFormat
                    WHERE ProductId = ?
                      AND IsBase = 1
                      AND DeletionDate IS NULL
                    ORDER BY Id DESC
                """, new_product_id)

                sf_new = dst_cursor.fetchone()

                if sf_new is None:
                    raise Exception(
                        f"No se creó SaleFormat para producto {nombre} ID {new_product_id}"
                    )

                sale_format_id = sf_new[0]

            print("SALE FORMAT ID:", sale_format_id)

            dst_cursor.execute("""
                SELECT 1
                FROM SaleFormatPrice
                WHERE PriceListId = ?
                  AND SaleFormatId = ?
            """, price_list_id, sale_format_id)

            if not dst_cursor.fetchone():

                if sale_format_id is None:
                    raise Exception(
                        f"SaleFormatId NULL para producto {nombre} ID {new_product_id}"
                    )

                print(
                    "PRODUCTO:",
                    nombre,
                    "ID:",
                    new_product_id,
                    "SALEFORMAT:",
                    sale_format_id
                )

                dst_cursor.execute("""
                    INSERT INTO SaleFormatPrice
                    (
                        PriceListId,
                        Main,
                        Addin,
                        MenuItem,
                        ReferenceCostPrice,
                        UpdatedAt,
                        SpecificVatId,
                        SaleFormatId
                    )
                    VALUES
                    (
                        ?, ?, NULL, 0,
                        ?, GETDATE(),
                        NULL, ?
                    )
                """,
                    price_list_id,
                    precio_venta,
                    precio_coste or 0,
                    sale_format_id
                )

            insertados += 1

        dst.commit()

        print()
        print(f"Productos insertados: {insertados}")

    except Exception as ex:

        dst.rollback()

        print()
        print("ERROR DURANTE LA MIGRACIÃ“N")
        print(ex)

    finally:

        src.close()
        dst.close()

