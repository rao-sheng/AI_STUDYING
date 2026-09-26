import rag_practice

def test_retrieve_chunks_filters_irrelevant_chunks(monkeypatch):
    def fake_embedding(text:str) ->list[float]:
        return [1.0,0.0]
    monkeypatch.setattr(rag_practice,
                        "get_embedding",
                        fake_embedding)

    chunks=[
        {
            "id": "return-policy",
            "source": "merchant_rules.md",
            "text": "商品支持七天无理由退货。",
            "vector": [0.99, 0.01],
        },
        {
            "id": "inventory-policy",
            "source": "merchant_rules.md",
            "text": "库存不足时不支持预售。",
            "vector": [0.0, 1.0],
        },
    ]

    result = rag_practice.retrieve_chunks(
        question="如何申请退货？",
        chunks=chunks,
        top_k=2,
        threshold=0.40,
    )

    assert [chunk["id"] for chunk in result] == ["return-policy"]