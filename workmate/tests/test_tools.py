import tool_practice
import asyncio
import pytest
import tool_practice

def run_execute_tool(tool_call:dict) ->dict:
    return asyncio.run(
        tool_practice.execute_tool(
            tool_call,
            knowledge_chunks=[]
        )
    )

def test_execute_tool_rejects_unknown_function():

    tool_call = {
        "type": "function",
        "function": {
            "name": "delete_all_tasks",
            "arguments": "{}",
        },
    }

    result = run_execute_tool(tool_call)
    assert result=={"ok":False,"error":"不允许调用该工具，本次未执行工具"}
def test_get_low_stock():
    tool_call = {
            "type": "function",
            "function": {
                "name": "get_low_stock_items",
                "arguments": "{}",
            },
        }
    result = run_execute_tool(tool_call)
    assert result["ok"] is True
    assert [product["sku_id"] for product in result["data"]]==["SKU-1003", "SKU-1001"]


import pytest


def test_execute_tool_returns_product_metrics():
    tool_call = {
        "type": "function",
        "function": {
            "name": "get_product_metrics",
            "arguments": '{"sku_id": "SKU-1001"}',
        },
    }

    result = run_execute_tool(tool_call)
   
    assert result["ok"] is True
    assert result["data"]["sku_id"] == "SKU-1001"
    assert result["data"]["name"] == "蓝牙降噪耳机"
    assert result["data"]["order_conversion_rate"] == pytest.approx(0.07)
