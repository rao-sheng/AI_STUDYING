from fastapi.testclient import TestClient

import main 

def test_agent_chat_returns_Async_Agent_answer(monkeypatch):
    captured={}

    async def fake_run_agent(
            question:str,
            knowledge_chunks:list[dict],
            max_rounds:int,
    )->str:
        captured["question"] = question
        captured["knowledge_chunks"] = knowledge_chunks
        captured["max_rounds"] = max_rounds
        return "模拟 Agent 回答"
    #monkeypatch测试时替换，结束后自动恢复
    monkeypatch.setattr(main,"run_agent",fake_run_agent)
    with TestClient(main.app) as client:
        response = client.post(
            "/agent/chat",
            json={"question": "哪些商品需要补货？"},
        )

    assert response.status_code == 200
    assert response.json() == {"answer": "模拟 Agent 回答"}
    assert captured["question"] == "哪些商品需要补货？"
    assert captured["max_rounds"] == 3
    assert isinstance(captured["knowledge_chunks"], list)