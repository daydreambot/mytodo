from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from database import get_db
from models import Task, TodoList as TodoListModel
from schemas import (
    Task as TaskSchema,
    TaskCreate,
    TaskListResponse,
    TodoList as TodoListSchema,
    TodoListCreate,
    TodoListListResponse,
)

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])
lists_router = APIRouter(prefix="/lists", tags=["lists"])


@tasks_router.post("/", response_model=TaskSchema, status_code=201)
def create_task(task: TaskCreate, db: Annotated[Session, Depends(get_db)]):
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@tasks_router.get("/", response_model=TaskListResponse)
def list_tasks(
    db: Annotated[Session, Depends(get_db)],
    completed: Annotated[bool | None, Query(description="Filter by completion status")] = None,
    priority: Annotated[int | None, Query(ge=0, le=5, description="Filter by priority level")] = None,
    todo_list_id: Annotated[int | None, Query(gt=0, description="Filter by todo list ID")] = None,
    sort_by: Annotated[Literal["created_at", "updated_at", "title", "priority", "due_date"], Query(description="Field to sort by")] = "created_at",
    sort_order: Annotated[Literal["asc", "desc"], Query(description="Sort direction")] = "desc",
    page: Annotated[int, Query(ge=1, description="Page number to fetch")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of rows to return")] = 20,
):
    query = db.query(Task)

    if completed is not None:
        query = query.filter(Task.completed == completed)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if todo_list_id is not None:
        query = query.filter(Task.todo_list_id == todo_list_id)

    sort_column = getattr(Task, sort_by)
    order_by_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    ordered_query = query.order_by(order_by_expression)
    total = ordered_query.count()
    total_pages = (total + limit - 1) // limit if total else 0
    offset = (page - 1) * limit
    items = ordered_query.offset(offset).limit(limit).all()

    return TaskListResponse(
        items=[TaskSchema.model_validate(item, from_attributes=True) for item in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@tasks_router.get("/{task_id}", response_model=TaskSchema)
def read_task(task_id: int, db: Annotated[Session, Depends(get_db)]):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@tasks_router.put("/{task_id}", response_model=TaskSchema)
def update_task(task_id: int, task: TaskCreate, db: Annotated[Session, Depends(get_db)]):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task.model_dump().items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


@tasks_router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Annotated[Session, Depends(get_db)]):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return Response(status_code=204)


@lists_router.post("/", response_model=TodoListSchema, status_code=201)
def create_list(list_in: TodoListCreate, db: Annotated[Session, Depends(get_db)]):
    db_list = TodoListModel(**list_in.model_dump())
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    return db_list


@lists_router.get("/", response_model=TodoListListResponse)
def list_lists(
    db: Annotated[Session, Depends(get_db)],
    title: Annotated[str | None, Query(description="Filter lists by title text")] = None,
    sort_by: Annotated[Literal["created_at", "updated_at", "title"], Query(description="Field to sort by")] = "created_at",
    sort_order: Annotated[Literal["asc", "desc"], Query(description="Sort direction")] = "desc",
    page: Annotated[int, Query(ge=1, description="Page number to fetch")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of rows to return")] = 20,
):
    query = db.query(TodoListModel)

    if title is not None:
        query = query.filter(TodoListModel.title.ilike(f"%{title}%"))

    sort_column = getattr(TodoListModel, sort_by)
    order_by_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    ordered_query = query.order_by(order_by_expression)
    total = ordered_query.count()
    total_pages = (total + limit - 1) // limit if total else 0
    offset = (page - 1) * limit
    items = ordered_query.offset(offset).limit(limit).all()

    return TodoListListResponse(
        items=[TodoListSchema.model_validate(item, from_attributes=True) for item in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@lists_router.post("/{list_id}/tasks", response_model=TaskSchema, status_code=201)
def create_task_for_list(
    list_id: int,
    task: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
):
    db_list = db.query(TodoListModel).filter(TodoListModel.id == list_id).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Todo list not found")

    task_data = task.model_dump()
    task_data["todo_list_id"] = list_id

    db_task = Task(**task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@lists_router.get("/{list_id}/tasks", response_model=TaskListResponse)
def list_tasks_for_list(
    list_id: int,
    db: Annotated[Session, Depends(get_db)],
    completed: Annotated[bool | None, Query(description="Filter tasks by completion status")] = None,
    priority: Annotated[int | None, Query(ge=0, le=5, description="Filter tasks by priority level")] = None,
    sort_by: Annotated[Literal["created_at", "updated_at", "title", "priority", "due_date"], Query(description="Field to sort by")] = "created_at",
    sort_order: Annotated[Literal["asc", "desc"], Query(description="Sort direction")] = "desc",
    page: Annotated[int, Query(ge=1, description="Page number to fetch")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of rows to return")] = 20,
):
    db_list = db.query(TodoListModel).filter(TodoListModel.id == list_id).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Todo list not found")

    query = db.query(Task).filter(Task.todo_list_id == list_id)

    if completed is not None:
        query = query.filter(Task.completed == completed)
    if priority is not None:
        query = query.filter(Task.priority == priority)

    sort_column = getattr(Task, sort_by)
    order_by_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    ordered_query = query.order_by(order_by_expression)
    total = ordered_query.count()
    total_pages = (total + limit - 1) // limit if total else 0
    offset = (page - 1) * limit
    items = ordered_query.offset(offset).limit(limit).all()

    return TaskListResponse(
        items=[TaskSchema.model_validate(item, from_attributes=True) for item in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@lists_router.get("/{list_id}", response_model=TodoListSchema)
def read_list(list_id: int, db: Annotated[Session, Depends(get_db)]):
    db_list = db.query(TodoListModel).filter(TodoListModel.id == list_id).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Todo list not found")
    return db_list


@lists_router.put("/{list_id}", response_model=TodoListSchema)
def update_list(list_id: int, list_in: TodoListCreate, db: Annotated[Session, Depends(get_db)]):
    db_list = db.query(TodoListModel).filter(TodoListModel.id == list_id).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Todo list not found")
    for key, value in list_in.model_dump().items():
        setattr(db_list, key, value)
    db.commit()
    db.refresh(db_list)
    return db_list


@lists_router.delete("/{list_id}", status_code=204)
def delete_list(list_id: int, db: Annotated[Session, Depends(get_db)]):
    db_list = db.query(TodoListModel).filter(TodoListModel.id == list_id).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Todo list not found")
    db.delete(db_list)
    db.commit()
    return Response(status_code=204)