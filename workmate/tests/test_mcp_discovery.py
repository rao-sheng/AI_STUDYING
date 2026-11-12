import asyncio

from mcp import Client

from mcp_tool_client import call_mcp_tool, discover_mcp_tools, server_parameters


def test_real_stdio_discovery_and_product_call(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKMATE_DB_PATH", str(tmp_path / "products.db"))
    monkeypatch.delenv("REDIS_URL", raising=False)
    async def negotiated_version():
        async with Client(server_parameters()) as client:
            return client.protocol_version

    assert asyncio.run(negotiated_version()) == "2026-07-28"
    tools = asyncio.run(discover_mcp_tools())
    functions = {tool["function"]["name"]: tool["function"] for tool in tools}
    assert set(functions) == {"get_low_stock_items", "get_product_metrics"}
    assert functions["get_product_metrics"]["parameters"]["required"] == ["sku_id"]
    result = asyncio.run(call_mcp_tool("get_product_metrics", {"sku_id": "SKU-1001"}))
    assert result["ok"] and result["data"]["stock"] == 8
    assert not asyncio.run(call_mcp_tool("unknown", {}))["ok"]


def test_agent_uses_discovered_product_schema_and_returns_tool_result(tmp_path, monkeypatch):
    import json

    import tool_practice

    monkeypatch.setenv("WORKMATE_DB_PATH", str(tmp_path / "products.db"))
    monkeypatch.delenv("REDIS_URL", raising=False)

    def model(messages, available_tools):
        assert any(tool["function"]["name"] == "get_product_metrics" for tool in available_tools)
        if messages[-1]["role"] == "tool":
            result = json.loads(messages[-1]["content"])
            return {"content": f"库存 {result['data']['stock']}"}
        return {"role": "assistant", "tool_calls": [{
            "id": "sku-query", "type": "function",
            "function": {"name": "get_product_metrics", "arguments": '{"sku_id":"SKU-1001"}'},
        }]}

    monkeypatch.setattr(tool_practice, "request_with_tools", model)
    answer = asyncio.run(tool_practice.run_agent("查 SKU-1001 的库存", []))
    assert answer == "库存 8"
