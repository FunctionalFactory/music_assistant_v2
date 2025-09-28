import os
from celery import current_task
from ..celery_app import celery_app
from ..services.audio_analysis import AudioAnalysisService


@celery_app.task(bind=True)
def analyze_audio_async(self, audio_file_path: str, delta: float = 1.14, wait: float = 0.03):
    try:
        current_task.update_state(state='PROCESSING')

        audio_service = AudioAnalysisService()
        result = audio_service.analyze_for_visualization(audio_file_path, delta=delta, wait=wait)

        os.unlink(audio_file_path)

        return result
    except Exception as e:
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)
        raise Exception(f"Audio analysis failed: {str(e)}")