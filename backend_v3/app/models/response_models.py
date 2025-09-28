from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class AnalysisParameters(BaseModel):
    delta: Optional[float] = Field(default=1.14, ge=1.0, le=2.0, description="Onset detection threshold")
    wait: Optional[float] = Field(default=0.03, ge=0.01, le=2.0, description="Minimum time between onsets in seconds")


class TaskResponse(BaseModel):
    task_id: str
    message: str


class WaveformData(BaseModel):
    data: List[float] = Field(description="Amplitude values for waveform visualization")
    times: List[float] = Field(description="Time values corresponding to amplitude data")


class AnalysisMetadata(BaseModel):
    delta: float = Field(description="Onset detection threshold used")
    wait: float = Field(description="Minimum time between onsets used")
    sample_rate: int = Field(description="Audio sample rate used for analysis")


class VisualizationData(BaseModel):
    waveform: WaveformData = Field(description="Waveform data for visualization")
    pitch_contour: List[List[Optional[float]]] = Field(description="[time, frequency] pairs, null for no pitch")
    onsets: List[float] = Field(description="Onset times in seconds")
    metadata: AnalysisMetadata = Field(description="Analysis parameters and settings")


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[VisualizationData] = None
    error: Optional[str] = None