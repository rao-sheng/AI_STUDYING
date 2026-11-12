import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from threading import RLock

from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import select

import store

DATA_PATH = Path(__file__).resolve().parent / "data" / "mock_products.json"
logger = logging.getLogger(__name__)
product_lock = RLock()


def load_products() -> list[dict]:
    with DATA_PATH.open(encoding="utf-8") as file:
        products = json.load(file)
    if not isinstance(products, list):
        raise ValueError("商品数据必须是JSON列表")
    return products


@lru_cache
def prepare_products(db_path: Path) -> None:
    store.init_db()
    store.seed_products(load_products())


@lru_cache
def cache_client(url: str) -> Redis:
    return Redis.from_url(url, decode_responses=True, socket_timeout=0.3,
                          socket_connect_timeout=0.3)


def cache():
    url = os.getenv("REDIS_URL")
    return cache_client(url) if url else None


def cache_key(sku_id: str) -> str:
    return f"workmate:product:v1:{sku_id}"


def product_data(product: store.Product) -> dict:
    return {column.key: getattr(product, column.key) for column in store.Product.__table__.columns}


def get_low_stock_items(threshold: int) -> list[dict]:
    prepare_products(store.DB_PATH)
    product = store.Product
    statement = select(product).where(product.stock <= threshold).order_by(product.stock, product.sku_id)
    with store.session_factory(store.DB_PATH)() as session:
        return [product_data(row) for row in session.scalars(statement)]


def get_product_metrics(sku_id: str) -> dict | None:
    prepare_products(store.DB_PATH)
    client = cache()
    key = cache_key(sku_id)
    with product_lock:
        if client is not None:
            try:
                hit = client.get(key)
                if hit is not None:
                    return json.loads(hit)
            except (RedisError, ValueError):
                logger.warning("商品缓存读取失败，回源 SQLite")
        with store.session_factory(store.DB_PATH)() as session:
            product = session.get(store.Product, sku_id)
            if product is None:
                return None
            result = product_data(product)
        views = result["views"]
        result["order_conversion_rate"] = result["orders"] / views if views else None
        result["payment_conversion_rate"] = result["paid_orders"] / views if views else None
        if client is not None:
            try:
                client.set(key, json.dumps(result, ensure_ascii=False), ex=60)
            except RedisError:
                logger.warning("商品缓存写入失败")
        return result


def update_product_stock(sku_id: str, stock: int) -> bool:
    if type(stock) is not int or stock < 0:
        raise ValueError("库存必须是非负整数")
    prepare_products(store.DB_PATH)
    with product_lock:
        with store.session_factory(store.DB_PATH).begin() as session:
            product = session.get(store.Product, sku_id)
            if product is None:
                return False
            product.stock = stock
        client = cache()
        if client is not None:
            try:
                client.delete(cache_key(sku_id))
            except RedisError:
                logger.warning("商品缓存失效失败，缓存将在 TTL 到期后刷新")
        return True


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
    parser = argparse.ArgumentParser(description="更新商品库存并使 SKU 缓存失效")
    parser.add_argument("sku_id")
    parser.add_argument("stock", type=int)
    args = parser.parse_args()
    if not update_product_stock(args.sku_id, args.stock):
        parser.exit(1, "未找到指定 SKU\n")
    print(f"{args.sku_id} 库存已更新为 {args.stock}")
