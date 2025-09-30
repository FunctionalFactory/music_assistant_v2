from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class TaskResponse(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    message: str = Field(..., description="Status message")


class TaskStatusResponse(BaseModel):
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Current task status")
    result: Optional[Any] = Field(None, description="Analysis result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")