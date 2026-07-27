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



IVA_MAP = {"E":"0","S":"4","R":"10","N":"21"}

def migrate():

    src = source_connection()
    dst = agora_connection()

    src_cursor = src.cursor()
    dst_cursor = dst.cursor()

    familias = _load_families(dst_cursor)
    familias_origen = _load_source_families(src_cursor)
    ivas = _load_vats(dst_cursor)

    src_cursor.execute("""
        SELECT
            CodigoDeArticulo,
            Descripcion,
            Familia,
            TipoIva,
            PrecioCosteReal,
            UnidadDeMedida,
            TratarStock,
            CodigoBarras_ean13
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
                codigo_barras
            ) = producto

            codigo = (codigo or "").strip()
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

            dst_cursor.execute("""
                SELECT Id
                FROM Product
                WHERE PriceLookUpCode = ?
                  AND DeletionDate IS NULL
            """, codigo)

            row = dst_cursor.fetchone()

            if row:
                new_product_id = row.Id

                dst_cursor.execute("""
                    SELECT Id
                    FROM SaleFormat
                    WHERE ProductId = ?
                """, new_product_id)

                sf = dst_cursor.fetchone()

                if sf:
                    print(f"Ya completo: {codigo}")
                    continue
            else:
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
                    '',
                    NULL,
                    NULL,
                    NULL,
                    0,
                    '',
                    '',
                    '',
                    NULL,
                    NULL,
                    0,
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
                vat_id
            )

                new_product_id = dst_cursor.execute(
                    "SELECT CAST(SCOPE_IDENTITY() AS INT)"
                ).fetchone()[0]

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
                    ?, ?, 1, 0, 1, 1, 1,
                    ?, ?, ?,
                    '0xFFFFFFFF',
                    '00000000-0000-0000-0000-000000000000',
                    0
                )
            """, nombre, new_product_id, nombre, nombre, nombre)

            sale_format_id = dst_cursor.execute(
                "SELECT CAST(SCOPE_IDENTITY() AS INT)"
            ).fetchone()[0]

            dst_cursor.execute("""
                INSERT INTO SaleFormatPrice
                (
                    PriceListId, Main, Addin, MenuItem,
                    ReferenceCostPrice, UpdatedAt,
                    SpecificVatId, SaleFormatId
                )
                VALUES
                (
                    1, 0, NULL, 0,
                    ?, GETDATE(),
                    NULL, ?
                )
            """, precio_coste or 0, sale_format_id)

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

