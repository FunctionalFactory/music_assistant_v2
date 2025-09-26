from pydantic import BaseModel
from typing import List


class PitchPoint(BaseModel):
    """Model for a single pitch point in the contour."""
    time: float
    frequency: float
    note: str


class OnsetPoint(BaseModel):
    """Model for a single onset point."""
    time: float
    note: str
    frequency: float


class WaveformData(BaseModel):
    """Model for waveform data with time axis."""
    data: List[float]
    times: List[float]


class SpectrogramData(BaseModel):
    """Model for spectrogram data with frequency axis."""
    data: List[List[float]]
    frequencies: List[float]


class AudioAnalysisResponse(BaseModel):
    """Response model for audio analysis results."""
    pitch_contour: List[PitchPoint]
    onsets: List[OnsetPoint]
    waveform: WaveformData
    spectrogram: SpectrogramData


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str