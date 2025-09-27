# Music Assistant Backend V3

Asynchronous audio analysis API using FastAPI, Celery, and Redis to resolve server timeout issues with large audio files.

## Features

- **Asynchronous Processing**: Upload large audio files without timeouts
- **Real-time Status**: Check task progress via polling endpoint
- **Audio Analysis**: Pitch contour, onset detection, waveform, and spectrogram analysis
- **Redis Backend**: Reliable task queue and result storage

## Requirements

- Python 3.8+
- Redis server running on localhost:6379

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Redis server:
```bash
redis-server
```

## Usage

### Start the application (2 separate terminals):

1. **Terminal 1 - Start FastAPI server:**
```bash
python start_server.py
```
Server will run on http://localhost:8000

2. **Terminal 2 - Start Celery worker:**
```bash
python start_worker.py
```

### API Endpoints

#### Upload Audio for Analysis
```
POST /api/v3/analysis
Content-Type: multipart/form-data

file: audio file (.wav, .mp3, .flac)
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Analysis task queued successfully"
}
```

#### Check Task Status
```
GET /api/v3/analysis/{task_id}
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "result": {
    "pitch_contour": [...],
    "onsets": [...],
    "waveform": {...},
    "spectrogram": {...}
  },
  "error": null
}
```

Status values: `pending`, `processing`, `success`, `failed`

## Testing

Test with large audio files to verify no 500 errors occur:

```bash
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@large_audio_file.wav"
```

## Health Check

```
GET /health
```