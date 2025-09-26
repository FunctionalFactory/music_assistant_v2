import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from ..services.audio_analysis import AudioAnalysisService
from ..models.audio_models import AudioAnalysisResponse, ErrorResponse

router = APIRouter()
audio_service = AudioAnalysisService()

ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac'}


@router.post("/analyze", response_model=AudioAnalysisResponse)
async def analyze_audio(file: UploadFile = File(...)):
    """
    Analyze uploaded audio file for pitch contour, onsets, waveform, and spectrogram data.

    Args:
        file: Audio file (.wav, .mp3, .flac)

    Returns:
        JSON response with analyzed audio data
    """
    # Validate file extension
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File format not supported. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size (max 50MB)
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size too large. Maximum size: 50MB")

    # Create temporary file to save upload
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # Read and save file content
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Analyze audio file
        analysis_result = audio_service.analyze_vocal_melody(temp_file_path)

        # Clean up temporary file
        os.unlink(temp_file_path)

        return AudioAnalysisResponse(**analysis_result)

    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing audio file: {str(e)}"
        )