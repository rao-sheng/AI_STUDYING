import json 
from pathlib import Path
DATA_PATH=(
    Path(__file__).resolve().parent
    / "data"
    / "mock_products.json"
)

def load_products() ->list[dict]:
    with DATA_PATH.open("r",encoding="utf-8") as file:
        products=json.load(file)

    if not isinstance(products,list):
        raise ValueError("商品数据必须是JSON列表")
    return products


def get_low_stock_items(threshold:int) ->list[dict]:
    products=load_products()
    low_stock=[
        product
        for product in products
        if product["stock"] <=threshold
    ]

    return sorted(
        low_stock,
        key=lambda product:product["stock"]
    )

def get_product_metrics(sku_id:str) ->dict|None:
    products=load_products()
    for product in products:
        if product["sku_id"]==sku_id:
            return {
    "sku_id": product["sku_id"],
    "name": product["name"],
    "stock": product["stock"],
    "views": product["views"],
    "orders": product["orders"],
    "paid_orders": product["paid_orders"],
    "revenue": product["revenue"],
    "order_conversion_rate": product["orders"] / product["views"] if product["views"] > 0 else None,
    "payment_conversion_rate": product["paid_orders"] / product["views"] if product["views"] > 0 else None,
}
    return None