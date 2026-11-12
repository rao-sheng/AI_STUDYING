from unittest.mock import Mock

from redis.exceptions import ConnectionError

import business_tools
import store


def test_sku_cache_hit_invalidation_and_degradation(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "products.db")
    values = {}
    redis = Mock()
    redis.get.side_effect = values.get
    redis.set.side_effect = lambda key, value, ex: values.update({key: value})
    redis.delete.side_effect = lambda key: values.pop(key, None)
    monkeypatch.setattr(business_tools, "cache", lambda: redis)

    sku = "SKU-1001"
    assert business_tools.get_product_metrics(sku)["stock"] == 8
    assert redis.set.call_args.kwargs["ex"] == 60
    assert business_tools.get_product_metrics(sku)["stock"] == 8
    assert redis.set.call_count == 1
    assert business_tools.update_product_stock(sku, 16)
    redis.delete.assert_called_once_with(business_tools.cache_key(sku))
    assert business_tools.get_product_metrics(sku)["stock"] == 16
    redis.get.side_effect = ConnectionError("unavailable")
    redis.set.side_effect = ConnectionError("unavailable")
    assert business_tools.get_product_metrics(sku)["stock"] == 16
