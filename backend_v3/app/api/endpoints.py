import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Response
from typing import Optional
from ..models.response_models import TaskResponse, TaskStatusResponse, TaskStatus, AnalysisParameters
from ..tasks.audio_tasks import analyze_audio_async
from ..celery_app import celery_app
from ..services.music_notation import MusicNotationService
from ..services.audio_analysis import AudioAnalysisService

router = APIRouter()

ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac'}


@router.post("/api/v3/analysis", response_model=TaskResponse)
async def analyze_audio(
    file: UploadFile = File(...),
    delta: Optional[float] = Form(default=1.14),
    wait: Optional[float] = Form(default=0.03)
):
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
        params = AnalysisParameters(delta=delta, wait=wait)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        task = analyze_audio_async.delay(temp_file_path, delta=params.delta, wait=params.wait)

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


@router.get("/api/v3/analysis/{task_id}/musicxml")
async def get_musicxml(task_id: str):
    """
    Generate MusicXML representation of the analyzed audio.
    Returns MusicXML as a string with appropriate content type.
    """
    try:
        # Get the task result first
        task_result = celery_app.AsyncResult(task_id)

        if task_result.state != 'SUCCESS':
            if task_result.state == 'PENDING':
                raise HTTPException(
                    status_code=202,
                    detail="Analysis not yet completed. Please wait for the analysis to finish."
                )
            elif task_result.state == 'PROCESSING':
                raise HTTPException(
                    status_code=202,
                    detail="Analysis in progress. Please wait for completion."
                )
            elif task_result.state == 'FAILURE':
                raise HTTPException(
                    status_code=400,
                    detail=f"Analysis failed: {str(task_result.info)}"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Analysis not completed successfully"
                )

        # Get the analysis result
        analysis_result = task_result.result
        if not analysis_result:
            raise HTTPException(
                status_code=404,
                detail="Analysis result not found"
            )

        # Extract data for MusicXML conversion
        pitch_contour = analysis_result.get("pitch_contour", [])
        onsets = analysis_result.get("onsets", [])
        metadata_info = analysis_result.get("metadata", {})

        # For V3 format, we need to convert the data structure
        if isinstance(onsets, list) and len(onsets) > 0:
            # Check if onsets are in V3 format (just time values)
            if isinstance(onsets[0], (int, float)):
                # Convert V3 format to expected format for MusicXML
                converted_onsets = []
                for i, onset_time in enumerate(onsets):
                    # Try to get corresponding pitch information
                    corresponding_pitch = None
                    if pitch_contour and i < len(pitch_contour):
                        pitch_data = pitch_contour[i]
                        if isinstance(pitch_data, list) and len(pitch_data) >= 2:
                            if pitch_data[1] is not None:  # frequency is not null
                                corresponding_pitch = {
                                    "time": float(onset_time),
                                    "frequency": float(pitch_data[1]),
                                    "note": _frequency_to_note(float(pitch_data[1]))
                                }

                    if corresponding_pitch:
                        converted_onsets.append(corresponding_pitch)
                    else:
                        # Fallback to default note if no pitch information
                        converted_onsets.append({
                            "time": float(onset_time),
                            "frequency": 440.0,
                            "note": "A4"
                        })
                onsets = converted_onsets

        # Create dummy tempo info if not available
        tempo_info = {
            "global_tempo": 120.0,
            "beat_times": [],
            "tempo_curve": [],
            "beat_count": 0
        }

        # Initialize MusicNotationService
        music_service = MusicNotationService()

        # Convert to MusicXML
        musicxml_string = music_service.convert_to_musicxml(
            pitch_contour=[],  # We'll use onsets as the primary source
            onsets=onsets,
            tempo_info=tempo_info,
            metadata_info=metadata_info
        )

        # Return MusicXML with appropriate content type
        return Response(
            content=musicxml_string,
            media_type="application/vnd.recordare.musicxml+xml",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{task_id}.musicxml"
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating MusicXML: {str(e)}"
        )


@router.get("/api/v3/analysis/{task_id}/pdf")
async def get_analysis_pdf(task_id: str):
    """
    Generate and return PDF sheet music for the analysis result.

    Args:
        task_id: The unique identifier for the analysis task

    Returns:
        PDF file containing the musical notation

    Raises:
        HTTPException: If task not found, not completed, or error in PDF generation
    """
    try:
        # Get task status using Celery
        task_result = celery_app.AsyncResult(task_id)

        if task_result.state == 'PENDING':
            raise HTTPException(status_code=202, detail="Analysis not yet completed")
        elif task_result.state == 'PROCESSING':
            raise HTTPException(status_code=202, detail="Analysis in progress")
        elif task_result.state == 'FAILURE':
            raise HTTPException(status_code=400, detail=f"Analysis failed: {str(task_result.info)}")
        elif task_result.state != 'SUCCESS':
            raise HTTPException(status_code=400, detail="Analysis not completed")

        if not task_result.result:
            raise HTTPException(status_code=400, detail="No analysis result available")

        analysis_result = task_result.result

        # Extract data for PDF conversion (same logic as MusicXML)
        pitch_contour = analysis_result.get("pitch_contour", [])
        onsets = analysis_result.get("onsets", [])
        metadata_info = analysis_result.get("metadata", {})

        # For V3 format, convert the data structure
        if isinstance(onsets, list) and len(onsets) > 0:
            if isinstance(onsets[0], (int, float)):
                converted_onsets = []
                for i, onset_time in enumerate(onsets):
                    corresponding_pitch = None
                    if pitch_contour and i < len(pitch_contour):
                        pitch_data = pitch_contour[i]
                        if isinstance(pitch_data, list) and len(pitch_data) >= 2:
                            if pitch_data[1] is not None:
                                corresponding_pitch = {
                                    "time": float(onset_time),
                                    "frequency": float(pitch_data[1]),
                                    "note": _frequency_to_note(float(pitch_data[1]))
                                }

                    if corresponding_pitch:
                        converted_onsets.append(corresponding_pitch)
                    else:
                        converted_onsets.append({
                            "time": float(onset_time),
                            "frequency": 440.0,
                            "note": "A4"
                        })
                onsets = converted_onsets

        # Create tempo info
        tempo_info = {
            "global_tempo": 120.0,
            "beat_times": [],
            "tempo_curve": [],
            "beat_count": 0
        }

        # Initialize MusicNotationService
        music_service = MusicNotationService()

        # Generate PDF
        pdf_bytes = music_service.convert_to_pdf(
            pitch_contour=[],
            onsets=onsets,
            tempo_info=tempo_info,
            metadata_info=metadata_info
        )

        # Return PDF with appropriate content type
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{task_id}.pdf"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )


def _frequency_to_note(frequency: float) -> str:
    """
    Convert frequency to note name.
    This is a helper function for the MusicXML endpoint.
    """
    import numpy as np

    if frequency <= 0:
        return "C4"

    A4 = 440.0
    C0 = A4 * np.power(2, -4.75)

    if frequency > C0:
        h = round(12 * np.log2(frequency / C0))
    else:
        return "C4"

    octave = h // 12
    n = h % 12

    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    note_name = note_names[n]

    return f"{note_name}{octave}"