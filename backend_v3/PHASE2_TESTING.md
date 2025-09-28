# Phase 2 테스트 가이드: 민감도 조절 기능

## 개선된 기능 테스트

### 1. API 엔드포인트 확장 검증

#### 기본 테스트 (기존 Phase 1 호환성)
```bash
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_audio.wav"
```

#### 민감도 파라미터 포함 테스트
```bash
# 높은 민감도 (더 많은 온셋 탐지)
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_audio.wav" \
  -F "delta=0.05" \
  -F "wait=0.01"

# 기본 민감도
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_audio.wav" \
  -F "delta=0.14" \
  -F "wait=0.03"

# 낮은 민감도 (더 적은 온셋 탐지)
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_audio.wav" \
  -F "delta=0.30" \
  -F "wait=0.10"
```

### 2. 결과 비교 검증

각 민감도 설정에 대해 `GET /api/v3/analysis/{task_id}` 호출 후:

#### 예상 결과:
- **높은 민감도** (`delta=0.05`): 더 많은 온셋 개수
- **기본 민감도** (`delta=0.14`): 중간 온셋 개수
- **낮은 민감도** (`delta=0.30`): 더 적은 온셋 개수

#### 검증 방법:
```bash
# 결과에서 onsets 배열의 길이 비교
echo "High sensitivity onsets count: $(curl -s 'http://localhost:8000/api/v3/analysis/TASK_ID_1' | jq '.result.onsets | length')"
echo "Default sensitivity onsets count: $(curl -s 'http://localhost:8000/api/v3/analysis/TASK_ID_2' | jq '.result.onsets | length')"
echo "Low sensitivity onsets count: $(curl -s 'http://localhost:8000/api/v3/analysis/TASK_ID_3' | jq '.result.onsets | length')"
```

### 3. 파라미터 유효성 검사 테스트

#### 잘못된 파라미터 테스트:
```bash
# delta 범위 초과 (400 에러 예상)
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_audio.wav" \
  -F "delta=1.5"

# wait 값이 너무 작음 (400 에러 예상)
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_audio.wav" \
  -F "wait=0.005"
```

## Phase 2 성공 기준

✅ **API 호환성**: 기존 Phase 1 API가 여전히 작동
✅ **민감도 제어**: 다른 delta/wait 값으로 다른 온셋 개수 반환
✅ **파라미터 검증**: 잘못된 값에 대해 400 에러 반환
✅ **알고리즘 개선**: onset_strength + peak_pick 사용
✅ **과탐지 감소**: 기존 대비 더 정확한 온셋 탐지

## 백엔드 v2와 비교 테스트

같은 오디오 파일로 backend_v2와 backend_v3 결과 비교:
- backend_v2는 과탐지 문제 있음
- backend_v3는 개선된 알고리즘으로 더 정확한 결과 기대