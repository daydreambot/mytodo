from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# TodoList Schemas
class TodoListCreate(BaseModel):
    title: str = Field(min_length=5, max_length=100, description="The name must be 5-100 characters long")
    description: str = Field(default="", max_length=1000, description="A list of tasks assigned to the user")

class TodoList(TodoListCreate):
    id: int = Field(gt=0, description="The value must be greater than 0")
    created_at: datetime = Field(description="The date and time when the list was created")
    updated_at: datetime = Field(description="The date and time when the list was last updated")

class TodoListListResponse(BaseModel):
    items: list[TodoList]
    total: int
    page: int
    limit: int
    total_pages: int

# Task Schemas
class TaskCreate(BaseModel):
    title: str = Field(min_length=5, max_length=100, description="The title must be 5-100 characters long")
    description: str = Field(default="", max_length=1000, description="The task description")
    completed: bool = Field(default=False, description="Indicates whether the task is completed or not")
    due_date: Optional[datetime] = Field(default=None, description="The date and time when the task is due")
    priority: int = Field(default=0, ge=0, le=5, description="The priority level of the task (0-5)")
    todo_list_id: Optional[int] = Field(default=None, gt=0, description="The ID of the todo list to which the task belongs")

    @field_validator("due_date")
    def validate_due_date(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None and value < datetime.now():
            raise ValueError("due_date must be in the present or future")
        return value

class Task(TaskCreate):
    id: int = Field(gt=0, description="The value must be greater than 0")
    created_at: datetime = Field(description="The date and time when the task was created")
    updated_at: datetime = Field(description="The date and time when the task was last updated")

class TaskListResponse(BaseModel):
    items: list[Task]
    total: int
    page: int
    limit: int
    total_pages: int