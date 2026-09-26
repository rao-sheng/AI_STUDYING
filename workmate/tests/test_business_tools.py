from business_tools import get_low_stock_items,get_product_metrics

def test_get_low_stock_items_returns_sorted_matches():
    results=get_low_stock_items(10)
    assert [product["sku_id"] for product in results]==[
        "SKU-1003",
        "SKU-1001",
    ]

def test_get_product_metrics_returns_none_for_unknown_sku():
    result = get_product_metrics("SKU-9999")

    assert result is None