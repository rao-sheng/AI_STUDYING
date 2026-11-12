import os
from functools import lru_cache
from pathlib import Path

from sqlalchemy import CheckConstraint, Index, Text, URL, create_engine, delete, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateIndex


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (CheckConstraint("status IN ('todo', 'in_progress', 'done')"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="todo")
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (CheckConstraint("role IN ('user', 'assistant')"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)


class Product(Base):
    __tablename__ = "products"

    sku_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    stock: Mapped[int] = mapped_column(index=True)
    views: Mapped[int]
    orders: Mapped[int]
    paid_orders: Mapped[int]
    revenue: Mapped[float]


message_history_index = Index(
    "ix_messages_conversation_id_id", Message.conversation_id, Message.id
)

DB_PATH = Path(os.getenv("WORKMATE_DB_PATH", str(Path(__file__).resolve().parent / "practice.db")))


@lru_cache
def get_engine(db_path: Path) -> Engine:
    return create_engine(
        URL.create("sqlite+pysqlite", database=str(db_path)),
        poolclass=NullPool,
    )


@lru_cache
def session_factory(db_path: Path) -> sessionmaker:
    return sessionmaker(bind=get_engine(db_path))


def init_db() -> None:
    engine = get_engine(DB_PATH)
    with engine.begin() as connection:
        Base.metadata.create_all(connection)
        # create_all skips existing tables, including their newly declared indexes.
        connection.execute(CreateIndex(message_history_index, if_not_exists=True))


def task_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def list_pending_tasks() -> list[dict]:
    statement = select(Task.id, Task.title, Task.status).where(Task.status != "done")
    with session_factory(DB_PATH)() as session:
        return [
            dict(row)
            for row in session.execute(statement.order_by(Task.id)).mappings()
        ]


def get_task(task_id: int) -> dict | None:
    with session_factory(DB_PATH)() as session:
        task = session.get(Task, task_id)
        return task_dict(task) if task is not None else None


def create_task(title, description, task_status, now1, now2) -> dict:
    task = Task(
        title=title,
        description=description,
        status=task_status,
        created_at=now1,
        updated_at=now2,
    )
    with session_factory(DB_PATH).begin() as session:
        session.add(task)
        session.flush()
        return task_dict(task)


def list_tasks(task_status: str | None = None) -> list[dict]:
    statement = select(Task).order_by(Task.id)
    if task_status is not None:
        statement = statement.where(Task.status == task_status)
    with session_factory(DB_PATH)() as session:
        return [task_dict(task) for task in session.scalars(statement)]


def update_task(task_id: int, update_data: dict, updated_at: str) -> dict | None:
    values = {
        field: update_data[field]
        for field in ("title", "description", "status")
        if field in update_data
    }
    statement = (
        update(Task)
        .where(Task.id == task_id)
        .values(**values, updated_at=updated_at)
        .returning(Task)
    )
    with session_factory(DB_PATH).begin() as session:
        task = session.scalars(statement).one_or_none()
        return task_dict(task) if task is not None else None


def delete_task(task_id: int) -> bool:
    statement = delete(Task).where(Task.id == task_id)
    with session_factory(DB_PATH).begin() as session:
        return session.execute(statement).rowcount > 0


def get_messages(conversation_id: str) -> list[dict]:
    statement = (
        select(Message.role, Message.content)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id)
    )
    with session_factory(DB_PATH)() as session:
        return [dict(row) for row in session.execute(statement).mappings()]


def save_message(conversation_id: str, role: str, content: str, created_at: str) -> None:
    with session_factory(DB_PATH).begin() as session:
        session.add(
            Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                created_at=created_at,
            )
        )


def save_turn(conversation_id: str, question: str, answer: str, created_at: str) -> None:
    with session_factory(DB_PATH).begin() as session:
        session.add_all(
            [
                Message(
                    conversation_id=conversation_id,
                    role="user",
                    content=question,
                    created_at=created_at,
                ),
                Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=answer,
                    created_at=created_at,
                ),
            ]
        )


def seed_products(products: list[dict]) -> None:
    with session_factory(DB_PATH).begin() as session:
        if products:
            session.execute(insert(Product).on_conflict_do_nothing(index_elements=["sku_id"]), products)