import asyncio
from mcp_tool_client import call_mcp_tool

def test_call_mcp_tool_returns_low_stock_items():
    result=asyncio.run(
        call_mcp_tool(
            "get_low_stock_items",
            {"threshold":10}
        )
    )
    assert result["ok"] is True 
    assert [product["sku_id"] for product in result["data"]]==[
        "SKU-1003",
        "SKU-1001"
    ]

def test_call_mcp_tool_returns_business_error():
    result = asyncio.run(
        call_mcp_tool(
            "get_product_metrics",
            {"sku_id": "SKU-9999"},
        )
    )

    assert result["ok"] is False
    assert "未找到商品 SKU-9999" in result["error"]