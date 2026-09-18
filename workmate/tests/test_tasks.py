#知道一个功能应该检查什么

from fastapi.testclient import TestClient
import store
from main import app

def test_task_list_starts_empty(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    monkeypatch.setattr(store, "DB_PATH", test_db_path)

    with TestClient(app) as client:
        response = client.get("/tasks")

        assert response.status_code == 200
        assert response.json() == []

def test_task_crud_flow(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    monkeypatch.setattr(store, "DB_PATH", test_db_path)

    with TestClient(app) as client:
        # 1. 创建任务
        create_response = client.post(
            "/tasks",
            json={
                "title": "学习接口测试",
                "description": "练习创建后查询",
                "status": "todo",
            },
        )

        assert create_response.status_code == 201

        created_task = create_response.json()
        assert created_task["title"] == "学习接口测试"
        assert created_task["status"] == "todo"

        # 2. 使用创建接口返回的 ID 查询
        task_id = created_task["id"]
        get_response = client.get(f"/tasks/{task_id}")

        assert get_response.status_code == 200

        # 3. 检查查询结果是否与创建结果一致
        fetched_task = get_response.json()
        assert fetched_task == created_task
                # 4. 只修改状态
        patch_response = client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
        )

        assert patch_response.status_code == 200

        updated_task = patch_response.json()

        # 提交的字段应该改变
        assert updated_task["status"] == "done"

        # 没提交的字段应该保留
        assert updated_task["title"] == created_task["title"]
        assert updated_task["description"] == created_task["description"]

        # ID 和创建时间不应该改变
        assert updated_task["id"] == task_id
        assert updated_task["created_at"] == created_task["created_at"]

        # 5. 再查询一次，确认更新已保存
        get_after_patch = client.get(f"/tasks/{task_id}")

        assert get_after_patch.status_code == 200
        assert get_after_patch.json() == updated_task
                # 空更新应被拒绝
        empty_patch = client.patch(
            f"/tasks/{task_id}",
            json={},
        )

        assert empty_patch.status_code == 400

        # 状态不能显式设置为 null
        invalid_patch = client.patch(
            f"/tasks/{task_id}",
            json={
                "description": "这段描述不应该保存",
                "status": None,
            },
        )

        assert invalid_patch.status_code == 422

        # 请求被拒绝后，原数据应该保持不变
        check_response = client.get(f"/tasks/{task_id}")

        assert check_response.status_code == 200
        assert check_response.json() == updated_task

                # 6. 删除刚才创建的任务
        delete_response = client.delete(f"/tasks/{task_id}")

        assert delete_response.status_code == 204
        assert delete_response.content == b""

        # 7. 删除后应查询不到
        get_after_delete = client.get(f"/tasks/{task_id}")

        assert get_after_delete.status_code == 404

        # 8. 重复删除应返回 404
        delete_again = client.delete(f"/tasks/{task_id}")

        assert delete_again.status_code == 404