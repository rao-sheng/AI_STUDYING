from fastapi.testclient import TestClient

from main import app

def test_root_returns_api_info():
    with TestClient(app) as client:
        test_response=client.get(
            "/"
        )

    assert test_response.status_code==200
    
    assert test_response.json()=={
  "name": "WorkMate API",
  "version": "0.1.0",
  "docs": "/docs"
}