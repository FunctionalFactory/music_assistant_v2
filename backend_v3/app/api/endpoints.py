import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..models.response_models import TaskResponse, TaskStatusResponse, TaskStatus
from ..tasks.audio_tasks import analyze_audio_async
from ..celery_app import celery_app

router = APIRouter()

ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac'}


@router.post("/api/v3/analysis", response_model=TaskResponse)
async def analyze_audio(file: UploadFile = File(...)):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File format not supported. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size too large. Maximum size: 50MB")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        task = analyze_audio_async.delay(temp_file_path)

        return TaskResponse(
            task_id=task.id,
            message="Analysis task queued successfully"
        )

    except Exception as e:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio file: {str(e)}"
        )


@router.get("/api/v3/analysis/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    try:
        task_result = celery_app.AsyncResult(task_id)

        if task_result.state == 'PENDING':
            status = TaskStatus.PENDING
            result = None
            error = None
        elif task_result.state == 'PROCESSING':
            status = TaskStatus.PROCESSING
            result = None
            error = None
        elif task_result.state == 'SUCCESS':
            status = TaskStatus.SUCCESS
            result = task_result.result
            error = None
        elif task_result.state == 'FAILURE':
            status = TaskStatus.FAILED
            result = None
            error = str(task_result.info)
        else:
            status = TaskStatus.PENDING
            result = None
            error = None

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