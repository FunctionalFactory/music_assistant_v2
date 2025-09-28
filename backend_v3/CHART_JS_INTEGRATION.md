# Chart.js 통합 가이드 - Phase 3

## 개요
Backend V3 API에서 제공하는 구조화된 JSON 데이터를 Chart.js를 사용하여 시각화하는 방법을 안내합니다.

## 데이터 구조
API 응답 형식:
```json
{
  "task_id": "uuid",
  "status": "success",
  "result": {
    "waveform": {
      "data": [0.1, 0.2, -0.1, ...],
      "times": [0.0, 0.1, 0.2, ...]
    },
    "pitch_contour": [
      [0.1, 440.0],
      [0.15, null],
      [0.2, 523.25]
    ],
    "onsets": [0.5, 1.2, 2.1],
    "metadata": {
      "delta": 0.14,
      "wait": 0.03,
      "sample_rate": 22050
    }
  }
}
```

## Chart.js 구현 예제

### 1. 파형(Waveform) 차트
```javascript
// 파형 데이터 시각화
function createWaveformChart(canvasId, waveformData) {
  const ctx = document.getElementById(canvasId).getContext('2d');

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: waveformData.times,
      datasets: [{
        label: 'Waveform',
        data: waveformData.data,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        borderWidth: 1,
        pointRadius: 0,
        tension: 0
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: {
            display: true,
            text: 'Time (seconds)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Amplitude'
          }
        }
      },
      elements: {
        point: {
          radius: 0
        }
      }
    }
  });
}
```

### 2. 음고 윤곽선(Pitch Contour) 차트
```javascript
// 음고 데이터를 Chart.js 형식으로 변환
function createPitchChart(canvasId, pitchContour) {
  const ctx = document.getElementById(canvasId).getContext('2d');

  // null 값 제거하고 유효한 데이터만 추출
  const validPitchData = pitchContour
    .filter(point => point[1] !== null)
    .map(point => ({
      x: point[0],
      y: point[1]
    }));

  return new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: 'Pitch Contour',
        data: validPitchData,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.1)',
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          type: 'linear',
          title: {
            display: true,
            text: 'Time (seconds)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Frequency (Hz)'
          }
        }
      }
    }
  });
}
```

### 3. 온셋 마커 오버레이
```javascript
// 기존 차트에 온셋 마커 추가
function addOnsetMarkers(chart, onsets) {
  const annotations = onsets.map(time => ({
    type: 'line',
    mode: 'vertical',
    scaleID: 'x',
    value: time,
    borderColor: 'red',
    borderWidth: 2,
    borderDash: [5, 5],
    label: {
      content: 'Onset',
      enabled: true,
      position: 'top'
    }
  }));

  // Chart.js annotation plugin 필요
  chart.options.plugins.annotation = {
    annotations: annotations
  };

  chart.update();
}
```

### 4. 통합 시각화 예제
```javascript
// 전체 분석 결과를 한 번에 시각화
async function visualizeAnalysisResult(taskId) {
  try {
    const response = await fetch(`/api/v3/analysis/${taskId}`);
    const data = await response.json();

    if (data.status === 'success') {
      const result = data.result;

      // 파형 차트 생성
      const waveformChart = createWaveformChart('waveform-canvas', result.waveform);

      // 음고 차트 생성
      const pitchChart = createPitchChart('pitch-canvas', result.pitch_contour);

      // 온셋 마커 추가
      addOnsetMarkers(waveformChart, result.onsets);
      addOnsetMarkers(pitchChart, result.onsets);

      // 메타데이터 표시
      displayMetadata(result.metadata);
    }
  } catch (error) {
    console.error('Error visualizing analysis result:', error);
  }
}

function displayMetadata(metadata) {
  document.getElementById('metadata').innerHTML = `
    <p>Delta: ${metadata.delta}</p>
    <p>Wait: ${metadata.wait}</p>
    <p>Sample Rate: ${metadata.sample_rate} Hz</p>
  `;
}
```

## 민감도 조절 UI with 디바운싱

### React Hook 예제
```javascript
import { useState, useCallback } from 'react';
import { debounce } from 'lodash';

function SensitivityControl({ onAnalyze }) {
  const [delta, setDelta] = useState(0.14);
  const [wait, setWait] = useState(0.03);

  // 디바운싱된 분석 함수
  const debouncedAnalyze = useCallback(
    debounce((newDelta, newWait) => {
      onAnalyze({ delta: newDelta, wait: newWait });
    }, 500), // 500ms 디바운싱
    [onAnalyze]
  );

  const handleDeltaChange = (value) => {
    setDelta(value);
    debouncedAnalyze(value, wait);
  };

  const handleWaitChange = (value) => {
    setWait(value);
    debouncedAnalyze(delta, value);
  };

  return (
    <div>
      <label>
        Onset Sensitivity (Delta): {delta}
        <input
          type="range"
          min="0.01"
          max="1.0"
          step="0.01"
          value={delta}
          onChange={(e) => handleDeltaChange(parseFloat(e.target.value))}
        />
      </label>
      <label>
        Minimum Time Between Onsets (Wait): {wait}s
        <input
          type="range"
          min="0.01"
          max="0.5"
          step="0.01"
          value={wait}
          onChange={(e) => handleWaitChange(parseFloat(e.target.value))}
        />
      </label>
    </div>
  );
}
```

## 필요한 의존성
```bash
npm install chart.js chartjs-adapter-date-fns chartjs-plugin-annotation
```

## HTML 템플릿
```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@2"></script>
</head>
<body>
  <div>
    <canvas id="waveform-canvas"></canvas>
    <canvas id="pitch-canvas"></canvas>
    <div id="metadata"></div>
  </div>
</body>
</html>
```

## 성능 최적화 팁

1. **대용량 데이터 처리**: 파형 데이터가 너무 클 경우 추가 다운샘플링
2. **실시간 업데이트**: 민감도 변경 시 디바운싱으로 API 호출 최소화
3. **차트 재사용**: 기존 차트 인스턴스 업데이트로 메모리 절약
4. **레이지 로딩**: 큰 차트는 사용자가 요청할 때만 렌더링