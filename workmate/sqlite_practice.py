import sqlite3
from pathlib import Path

DB_PATH=Path(__file__).resolve().parent/"practice.db"

conn=sqlite3.connect(DB_PATH)
#改变查询数据返回的格式
conn.row_factory=sqlite3.Row

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'todo'
            CHECK (status IN ('todo', 'in_progress', 'done')),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
"""
)

from datetime import datetime, timezone

title = "学习 A"
description = "完成第一次插入"
task_status = "todo"
now = datetime.now(timezone.utc).isoformat()
cursor = conn.execute(
    """
    INSERT INTO tasks (
        title, description, status, created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    (title, description, task_status, now, now),
)

conn.commit()

a_id= cursor.lastrowid
print("新任务 ID：", a_id)

title = "学习 B"
description = "完成第二次插入"
task_status = "in_progress"
now = datetime.now(timezone.utc).isoformat()
cursor = conn.execute(
    """
    INSERT INTO tasks (
        title, description, status, created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    (title, description, task_status, now, now),
)

conn.commit()

b_id = cursor.lastrowid
print("新任务 ID：", b_id)

title = "学习 C"
description = "完成第三次插入"
task_status = "done"
now = datetime.now(timezone.utc).isoformat()
cursor = conn.execute(
    """
    INSERT INTO tasks (
        title, description, status, created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    (title, description, task_status, now, now),
)

conn.commit()

c_id = cursor.lastrowid
print("新任务 ID：", c_id)

#查询所有任务
cursor = conn.execute(
    "SELECT * FROM tasks ORDER BY id"
)

rows = cursor.fetchall()

if not rows:
    print("暂无任务")
else:
    for row in rows:
        print(row["id"],row["title"],row["status"])
print(len(rows))

#按done筛选
tasker="done"
cursor = conn.execute(
    "SELECT * FROM tasks WHERE status = ?",
    (tasker,)
)

row = cursor.fetchone()

if row is None:
    print("任务不存在")
else:
    print(row["title"])
    print(dict(row))

target_status="in_progress"
min_id=0
cursor=conn.execute(
    "SELECT * FROM TASKS WHERE status=? and id>? ORDER BY id",
    (target_status,min_id),
)
rows=cursor.fetchall()
if not rows:
    print("无匹配任务")
else:
    for row in rows:
        print(row["id"],row["title"],row["status"])
print("匹配总数",len(rows))
