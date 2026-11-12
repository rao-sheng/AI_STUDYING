import asyncio
import logging
import os
import sys
from pathlib import Path

from mcp import Client,StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_DIR = Path(__file__).resolve().parent
PYTHON_PATH = sys.executable
SERVER_PATH = PROJECT_DIR / "mcp_server.py"

logger = logging.getLogger(__name__)
ALLOWED_MCP_TOOLS = frozenset({"get_low_stock_items", "get_product_metrics"})


def server_parameters() -> StdioServerParameters:
    env = {key: os.environ[key] for key in ("REDIS_URL", "WORKMATE_DB_PATH") if key in os.environ}
    return StdioServerParameters(command=PYTHON_PATH, args=[str(SERVER_PATH)], env=env)


async def discover_mcp_tools() -> list[dict]:
    try:
        async with asyncio.timeout(10), Client(stdio_client(server_parameters())) as client:
            page = await client.list_tools()
            tools = list(page.tools)
            seen_cursors = set()
            while page.next_cursor:
                if page.next_cursor in seen_cursors:
                    raise ValueError("MCP 服务返回重复游标")
                seen_cursors.add(page.next_cursor)
                page = await client.list_tools(cursor=page.next_cursor)
                tools.extend(page.tools)
            return [
                {"type": "function", "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                }}
                for tool in tools if tool.name in ALLOWED_MCP_TOOLS
            ]
    except Exception:
        logger.exception("MCP 工具发现失败")
        return []


async def call_mcp_tool(tool_name:str,arguments:dict) -> dict:
    """调用本地MCP工具，并返回统一结果。"""
    if not isinstance(tool_name,str):
        return {
            "ok":False,
            "error":"MCP工具名必须是字符串。"
        }
    tool_name=tool_name.strip()
    if tool_name not in ALLOWED_MCP_TOOLS:
        return{
            "ok":False,
            "error":"不允许调用该 MCP 工具。"
        }
    if not isinstance(arguments,dict):
        return{
            "ok":False,
            "error":"MCP工具参数必须是对象。"
        }
    try:
        async with asyncio.timeout(15), Client(stdio_client(server_parameters())) as client:
            result=await client.call_tool(tool_name,arguments)
    except Exception:
        return {
            "ok":False,
            "error": "MCP 协议或通信错误"
        }
    if result.is_error:
        error_texts=[
            content.text for content in result.content if content.type=="text"
        ]
        return {
            "ok":False,
            "error": "\n".join(error_texts) or "MCP 工具调用失败。"
        }
    structured_content=result.structured_content
    if structured_content is None:
        return{
            "ok":False,
            "error":"MCP工具未返回结构化数据。"
        }
    if isinstance(structured_content,dict) and "result" in structured_content:
        data=structured_content["result"]
    else: data=structured_content
    return {
        "ok":True,
        "data":data
    }
