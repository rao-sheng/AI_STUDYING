from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from business_tools import (
    get_low_stock_items as find_low_stock_items,
    get_product_metrics as find_product_metrics
)
from pydantic import BaseModel
class ProductMetrics(BaseModel):
    sku_id: str
    name: str
    stock: int
    views: int
    orders: int
    paid_orders: int
    revenue: float
    order_conversion_rate: float | None
    payment_conversion_rate: float | None


mcp=MCPServer("workmate-merchant-tools")

@mcp.tool()
def get_low_stock_items(threshold:int=10) ->list[dict]:
    """查询库存小于等于指定阈值的商品，供补货分析使用。"""
    if type(threshold) is not int or not 1<=threshold<=1000:
        raise ToolError("threshold 必须是 1 到 1000 的整数。")
    return find_low_stock_items(threshold)

@mcp.tool()
def get_product_metrics(sku_id:str) -> ProductMetrics:
    """查询指定商品的库存和经营指标"""
    sku_id=sku_id.strip()
    if not sku_id or len(sku_id)>100:
        raise ToolError("sku_id 不能为空，且不能超过 100 个字符。")
    metrics=find_product_metrics(sku_id)
    if metrics is None:
        raise ToolError(f"未找到商品 {sku_id}。")
    return  ProductMetrics(**metrics)

if __name__=="__main__":
    mcp.run(transport="stdio")