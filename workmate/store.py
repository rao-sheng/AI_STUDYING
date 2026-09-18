import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "practice.db"

def init_db():
    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'todo'
                    CHECK (status IN ('todo', 'in_progress', 'done')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def list_pending_tasks() ->list[dict]:
    conn=get_connection()
    try:
        cursor=conn.execute(
            """
            SELECT id,title,status
            FROM tasks
            WHERE status !=?
            ORDER BY id
""",
            ("done",),
        )
        rows=cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
        

def get_task(task_id: int) -> dict | None:
    conn = get_connection()

    try:
        cursor = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        conn.close()

def create_task(title, description, task_status, now1, now2):
    conn=get_connection()
    try:
        cursor=conn.execute(
            """
    INSERT INTO tasks (
        title, description, status, created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    (title, description, task_status, now1, now2),
        )
        new_id=cursor.lastrowid
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise   
    finally:
        conn.close()
    return get_task(new_id)#type:ignore

def list_tasks(task_status:str|None=None) ->list[dict]:
    conn=get_connection()
    try:
        if task_status is None:
            cursor = conn.execute(
                "SELECT * FROM tasks ORDER BY id"
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY id",
                (task_status,),
            )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def update_task(
    task_id: int,
    update_data: dict,
    updated_at: str,
) -> dict | None:
    conn = get_connection()
    try:
        fields = []
        values = []

        for field_name in ("title", "description", "status"):
            if field_name in update_data:
                fields.append(f"{field_name} = ?")
                values.append(update_data[field_name])

        fields.append("updated_at = ?")
        values.append(updated_at)
        values.append(task_id)
        #会转成很多带有？的等式，示例：status=?
        cursor = conn.execute(
            f"""
            UPDATE tasks
            SET {", ".join(fields)} 
            WHERE id = ?
            """,
            #tuple转成元组
            tuple(values),
        )

        if cursor.rowcount == 0:
            return None

        conn.commit()

        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        return dict(row)
    finally:
        conn.close()

def delete_task(task_id:int) ->bool:
    conn=get_connection()
    try:
        cursor=conn.execute(
            "DELETE FROM tasks WHERE id=?",
            (task_id,),
        )
        conn.commit()
        return cursor.rowcount>0
    finally:
        conn.close()

def get_messages(conversation_id:str) ->list[dict]:
    conn=get_connection()
    try:
        cursor=conn.execute(
            "SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id",
            (conversation_id,),
        )
        rows=cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def save_message(
        conversation_id:str,
        role:str,
        content:str,
        created_at:str
) ->None:
    conn=get_connection()
    try:
        conn.execute(
            """
INSERT INTO messages(conversation_id,role,content,created_at)
 VALUES(?,?,?,?)
""",
       (conversation_id,role,content,created_at)
        )
        conn.commit()
    except sqlite3.Error:
            conn.rollback()
            raise 
    finally:
        conn.close()

def save_turn(
        conversation_id:str,
        question:str,
        answer:str,
        created_at:str,
) ->None:
    conn=get_connection()
    try:
        sql="""
        INSERT INTO messages(
        conversation_id,role,content,created_at)
        VALUES(?,?,?,?)
"""
        conn.execute(
        sql,(conversation_id,"user",question,created_at)
    )
        conn.execute(
        sql,(conversation_id,"assistant",answer,created_at)
    )
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()
