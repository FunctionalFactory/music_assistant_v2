# Testing Guide for Backend V3

## Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Redis server:
```bash
redis-server
```

## Testing Large File Processing

### Start the services:

1. **Terminal 1 - FastAPI Server:**
```bash
python start_server.py
```

2. **Terminal 2 - Celery Worker:**
```bash
python start_worker.py
```

### Test with large audio file:

```bash
# Test with a large audio file (replace with actual file path)
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/large_audio_file.wav"
```

**Expected result:**
- Immediate response with task_id (no 500 errors)
- No timeout regardless of file size

### Check task status:

```bash
# Replace TASK_ID with the actual task ID from previous response
curl "http://localhost:8000/api/v3/analysis/TASK_ID"
```

**Expected status progression:**
1. `pending` - Task queued
2. `processing` - Task running
3. `success` - Task completed with results

### Verification criteria:

✅ **Phase 1 Success Criteria:**
- [ ] No 500 Internal Server Error for large files
- [ ] Immediate task_id response (< 2 seconds)
- [ ] Task status endpoint returns correct states
- [ ] Analysis completes successfully in background
- [ ] Results available via polling endpoint

## Health Checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/
```

## API Documentation

Access interactive API docs at: http://localhost:8000/docs