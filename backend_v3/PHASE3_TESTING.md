# Phase 3 테스트 가이드: 프론트엔드 시각화 데이터

## JSON 구조 검증

### 1. API 응답 구조 확인
```bash
# 파일 업로드 후 task_id 받기
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_audio.wav" \
  -F "delta=0.14" \
  -F "wait=0.03"

# 응답 예시: {"task_id": "abc123", "message": "Analysis task queued successfully"}
```

### 2. 시각화 데이터 구조 검증
```bash
# task_id로 결과 조회
curl "http://localhost:8000/api/v3/analysis/{task_id}" | jq '.'

# 예상 응답 구조:
{
  "task_id": "abc123",
  "status": "success",
  "result": {
    "waveform": {
      "data": [0.1, 0.2, -0.1, 0.0, ...],
      "times": [0.0, 0.1, 0.2, 0.3, ...]
    },
    "pitch_contour": [
      [0.1, 440.0],
      [0.15, null],
      [0.2, 523.25],
      [0.25, null]
    ],
    "onsets": [0.5, 1.2, 2.1, 3.5],
    "metadata": {
      "delta": 0.14,
      "wait": 0.03,
      "sample_rate": 22050
    }
  },
  "error": null
}
```

### 3. 데이터 타입 검증
```bash
# jq를 사용한 데이터 타입 확인
curl -s "http://localhost:8000/api/v3/analysis/{task_id}" | jq '
{
  "waveform_data_type": (.result.waveform.data | type),
  "waveform_data_length": (.result.waveform.data | length),
  "pitch_contour_type": (.result.pitch_contour | type),
  "pitch_contour_sample": (.result.pitch_contour[0]),
  "onsets_type": (.result.onsets | type),
  "onsets_length": (.result.onsets | length),
  "metadata_keys": (.result.metadata | keys)
}'
```

### 4. Chart.js 호환성 테스트

#### 파형 데이터 호환성
```javascript
// 브라우저 콘솔에서 테스트
fetch('/api/v3/analysis/TASK_ID')
  .then(response => response.json())
  .then(data => {
    const waveform = data.result.waveform;

    // Chart.js 호환성 검증
    console.log('Waveform data length:', waveform.data.length);
    console.log('Times length:', waveform.times.length);
    console.log('Data/Times length match:', waveform.data.length === waveform.times.length);

    // 첫 번째와 마지막 데이터 포인트 확인
    console.log('First point:', [waveform.times[0], waveform.data[0]]);
    console.log('Last point:', [waveform.times[waveform.times.length-1], waveform.data[waveform.data.length-1]]);
  });
```

#### 음고 데이터 호환성
```javascript
fetch('/api/v3/analysis/TASK_ID')
  .then(response => response.json())
  .then(data => {
    const pitchContour = data.result.pitch_contour;

    // [time, frequency] 형식 검증
    const validPoints = pitchContour.filter(point =>
      Array.isArray(point) &&
      point.length === 2 &&
      typeof point[0] === 'number'
    );

    const nullPoints = pitchContour.filter(point => point[1] === null);

    console.log('Total pitch points:', pitchContour.length);
    console.log('Valid pitch points:', validPoints.length);
    console.log('Null frequency points:', nullPoints.length);
    console.log('Sample pitch points:', pitchContour.slice(0, 5));
  });
```

#### 온셋 데이터 호환성
```javascript
fetch('/api/v3/analysis/TASK_ID')
  .then(response => response.json())
  .then(data => {
    const onsets = data.result.onsets;

    // 시간값만 포함된 배열 검증
    const validOnsets = onsets.every(time => typeof time === 'number');
    const sortedOnsets = [...onsets].sort((a, b) => a - b);
    const isChronological = JSON.stringify(onsets) === JSON.stringify(sortedOnsets);

    console.log('Onsets count:', onsets.length);
    console.log('All valid times:', validOnsets);
    console.log('Chronologically ordered:', isChronological);
    console.log('Onset times:', onsets);
  });
```

### 5. 민감도 파라미터 효과 검증

#### 다른 민감도로 테스트
```bash
# 높은 민감도
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -F "file=@test_audio.wav" \
  -F "delta=0.05" \
  -F "wait=0.01"

# 낮은 민감도
curl -X POST "http://localhost:8000/api/v3/analysis" \
  -F "file=@test_audio.wav" \
  -F "delta=0.30" \
  -F "wait=0.10"

# 온셋 개수 비교
echo "High sensitivity:" && curl -s "http://localhost:8000/api/v3/analysis/TASK_ID_1" | jq '.result.onsets | length'
echo "Low sensitivity:" && curl -s "http://localhost:8000/api/v3/analysis/TASK_ID_2" | jq '.result.onsets | length'
```

### 6. 메타데이터 검증
```bash
# 메타데이터가 요청 파라미터와 일치하는지 확인
curl -s "http://localhost:8000/api/v3/analysis/{task_id}" | jq '.result.metadata'

# 예상 출력:
{
  "delta": 0.14,
  "wait": 0.03,
  "sample_rate": 22050
}
```

## Phase 3 성공 기준

✅ **구조화된 JSON**: 프론트엔드에서 사용하기 쉬운 데이터 형식
✅ **파형 데이터**: data/times 배열 길이 일치, Chart.js 호환
✅ **음고 윤곽선**: [시간, 주파수] 쌍, null 값 적절히 처리
✅ **온셋 배열**: 시간값만 포함된 간단한 배열
✅ **메타데이터**: 분석 파라미터 정확히 반영
✅ **Chart.js 호환**: 모든 데이터가 차트 라이브러리와 호환

## 수동 테스트 체크리스트

- [ ] API 응답이 정의된 JSON 구조와 일치
- [ ] 파형 데이터 배열 길이가 일치
- [ ] 음고 데이터가 [시간, 주파수] 형식
- [ ] null 값이 적절히 처리됨
- [ ] 온셋이 시간값만 포함
- [ ] 메타데이터가 정확함
- [ ] 다른 민감도로 다른 결과 생성
- [ ] Chart.js 예제 코드가 작동함