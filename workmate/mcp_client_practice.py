from pathlib import Path
import json

from mcp import Client,StdioServerParameters,MCPError
from mcp.client.stdio import stdio_client

PROJECT_DIR = Path(__file__).resolve().parent
PYTHON_PATH = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
SERVER_PATH = PROJECT_DIR / "mcp_server.py"

async def call_mcp_tool(tool_name:str,arguments:dict) -> dict:
    """调用本地MCP工具，并返回统一结果。"""
    if not isinstance(tool_name,str):
        return {
            "ok":False,
            "error":"MCP工具名必须是字符串。"
        }
    tool_name=tool_name.strip()
    if not tool_name:
        return{
            "ok":False,
            "error":"MCP工具名不能为空。"
        }
    if not isinstance(arguments,dict):
        return{
            "ok":False,
            "error":"MCP工具参数必须是对象。"
        }
    params=StdioServerParameters(
        command=str(PYTHON_PATH),
        args=[str(SERVER_PATH)]
    )
    try:
        async with Client(stdio_client(params)) as client:
            result=await client.call_tool(tool_name,arguments)
    except MCPError as e:
        return {
            "ok":False,
            "error":e
        }
    if result.is_error:
        error_texts=[
            content.text for content in result.content if content.type=="text"
        ]
        return {
            "ok":False,
            "error":error_texts
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
        "deta":data
    }