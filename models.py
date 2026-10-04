from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class TodoList(Base):
    __tablename__ = "todo_lists"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc).astimezone(), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc).astimezone(), onupdate=datetime.now(timezone.utc).astimezone(), nullable=False)

    tasks = relationship("Task", back_populates="todo_list", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TodoList(id={self.id}, title={self.title})>"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, default="", nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc).astimezone(), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc).astimezone(), onupdate=datetime.now(timezone.utc).astimezone() , nullable=False)
    todo_list_id = Column(Integer, ForeignKey("todo_lists.id"), nullable=False)

    todo_list = relationship("TodoList", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, completed={self.completed})>"

DATABASE_URL = "sqlite:///./todo.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)