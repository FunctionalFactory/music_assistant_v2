import os
from celery import current_task
from ..celery_app import celery_app
from ..services.audio_analysis import AudioAnalysisService


@celery_app.task(bind=True)
def analyze_audio_async(
    self,
    audio_file_path: str,
    delta: float = 1.14,
    wait: float = 0.03,
    bpm: float = None,
    grid_resolution: str = "1/16"
):
    """
    Asynchronous audio analysis task with rhythm quantization.

    Args:
        audio_file_path: Path to the temporary audio file
        delta: Onset detection sensitivity (higher = less sensitive)
        wait: Minimum time between onsets in seconds
        bpm: Manual tempo in BPM (auto-estimated if None)
        grid_resolution: Quantization grid resolution

    Returns:
        Analysis result dictionary with rhythm quantization
    """
    try:
        current_task.update_state(state='PROCESSING')

        service = AudioAnalysisService()
        result = service.analyze(
            audio_file_path,
            delta=delta,
            wait=wait,
            bpm=bpm,
            grid_resolution=grid_resolution
        )

        # Clean up temporary file
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)

        return result

    except Exception as e:
        # Clean up on error
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)
        raise Exception(f"Audio analysis failed: {str(e)}")