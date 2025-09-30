import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from ..models.response_models import TaskResponse, TaskStatusResponse, TaskStatus
from ..tasks.audio_tasks import analyze_audio_async
from ..celery_app import celery_app

router = APIRouter()

ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/api/v4/analysis", response_model=TaskResponse)
async def create_analysis_task(
    file: UploadFile = File(...),
    delta: float = Form(default=1.14),
    wait: float = Form(default=0.03),
    bpm: float = Form(default=None),
    grid_resolution: str = Form(default="1/16")
):
    """
    Upload audio file and create analysis task with rhythm quantization.

    Args:
        file: Audio file to analyze
        delta: Onset detection sensitivity (higher = less sensitive, default: 1.14)
        wait: Minimum time between onsets in seconds (default: 0.03)
        bpm: Manual tempo in BPM (auto-estimated if not provided)
        grid_resolution: Quantization grid resolution (default: "1/16")

    Returns:
        Task ID for async processing
    """
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Validate parameters
    if delta <= 0:
        raise HTTPException(status_code=400, detail="delta must be positive")
    if wait < 0:
        raise HTTPException(status_code=400, detail="wait must be non-negative")
    if bpm is not None and bpm <= 0:
        raise HTTPException(status_code=400, detail="bpm must be positive")

    # Validate grid_resolution
    valid_resolutions = {"1/4", "1/8", "1/16", "1/8t", "1/32"}
    if grid_resolution not in valid_resolutions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid grid_resolution. Allowed: {', '.join(valid_resolutions)}"
        )

    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Queue task for async processing with all parameters
        task = analyze_audio_async.delay(
            temp_file_path,
            delta=delta,
            wait=wait,
            bpm=bpm,
            grid_resolution=grid_resolution
        )

        return TaskResponse(
            task_id=task.id,
            message="Analysis task queued successfully"
        )

    except Exception as e:
        # Clean up on error
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@router.get("/api/v4/analysis/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status and result of analysis task.

    Poll this endpoint to check task progress.
    """
    try:
        task_result = celery_app.AsyncResult(task_id)

        # Map Celery states to our TaskStatus enum
        state_mapping = {
            'PENDING': TaskStatus.PENDING,
            'PROCESSING': TaskStatus.PROCESSING,
            'SUCCESS': TaskStatus.SUCCESS,
            'FAILURE': TaskStatus.FAILED
        }

        status = state_mapping.get(task_result.state, TaskStatus.PENDING)
        result = task_result.result if status == TaskStatus.SUCCESS else None
        error = str(task_result.info) if status == TaskStatus.FAILED else None

        return TaskStatusResponse(
            task_id=task_id,
            status=status,
            result=result,
            error=error
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving task status: {str(e)}"
        )