from dataclasses import dataclass


@dataclass
class Product:

    code: str
    name: str

    family_name: str
    family_id: int | None

    vat_rate: str
    vat_id: int | None

    cost_price: float

    is_sold_by_weight: bool
    stock_control_mode: int

    barcode: str
