# MusicXML Integration Guide for Frontend

이 가이드는 Music Assistant v3 백엔드에서 생성된 MusicXML 데이터를 프론트엔드에서 악보로 시각화하는 방법을 설명합니다.

## 개요

Phase 4에서 구현된 MusicXML API를 통해 분석된 오디오 데이터를 표준 악보 형식으로 변환할 수 있습니다. 이 문서는 프론트엔드에서 해당 데이터를 렌더링하는 방법을 제공합니다.

## API 엔드포인트

### MusicXML 생성 엔드포인트

```
GET /api/v3/analysis/{task_id}/musicxml
```

**응답:**
- Content-Type: `application/vnd.recordare.musicxml+xml`
- Body: MusicXML 형식의 악보 데이터 (문자열)

**상태 코드:**
- `200`: 성공적으로 MusicXML 생성
- `202`: 분석이 아직 완료되지 않음
- `400`: 분석 실패 또는 완료되지 않음
- `404`: 분석 결과를 찾을 수 없음
- `500`: MusicXML 생성 중 오류

## 프론트엔드 통합

### 1. OpenSheetMusicDisplay (OSMD) 라이브러리 설치

```bash
npm install opensheetmusicdisplay
```

### 2. 기본 구현 예제

```typescript
import { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';

interface MusicXMLDisplayProps {
  taskId: string;
  apiBaseUrl?: string;
}

export function MusicXMLDisplay({
  taskId,
  apiBaseUrl = 'http://localhost:8000'
}: MusicXMLDisplayProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [osmd, setOsmd] = useState<OpenSheetMusicDisplay | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      // OSMD 인스턴스 생성
      const osmDisplay = new OpenSheetMusicDisplay(containerRef.current, {
        autoResize: true,
        backend: 'svg',
        drawTitle: true,
        drawComposer: true,
        drawPartNames: true,
        followCursor: true,
        cursorsOptions: {
          type: 'standard',
          color: '#FF0000',
          alpha: 0.7
        }
      });

      setOsmd(osmDisplay);
    }

    return () => {
      // 클린업
      if (osmd) {
        osmd.clear();
      }
    };
  }, []);

  const loadMusicXML = async () => {
    if (!osmd || !taskId) return;

    setIsLoading(true);
    setError(null);

    try {
      // MusicXML 데이터 가져오기
      const response = await fetch(`${apiBaseUrl}/api/v3/analysis/${taskId}/musicxml`);

      if (response.status === 202) {
        setError('분석이 아직 완료되지 않았습니다. 잠시 후 다시 시도해주세요.');
        return;
      }

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`악보 로드 실패: ${response.status} - ${errorText}`);
      }

      const musicXMLString = await response.text();

      // OSMD로 MusicXML 로드 및 렌더링
      await osmd.load(musicXMLString);
      osmd.render();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="musicxml-display">
      <div className="controls mb-4">
        <button
          onClick={loadMusicXML}
          disabled={isLoading || !taskId}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {isLoading ? '악보 로딩 중...' : '악보 보기'}
        </button>
      </div>

      {error && (
        <div className="error-message bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div
        ref={containerRef}
        className="music-sheet-container"
        style={{ minHeight: '400px', border: '1px solid #e0e0e0', padding: '20px' }}
      />
    </div>
  );
}
```

### 3. 고급 구현 - 재생 기능 포함

```typescript
import { OpenSheetMusicDisplay, PlaybackManager } from 'opensheetmusicdisplay';

export function AdvancedMusicXMLDisplay({ taskId }: { taskId: string }) {
  const [osmd, setOsmd] = useState<OpenSheetMusicDisplay | null>(null);
  const [playbackManager, setPlaybackManager] = useState<PlaybackManager | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (containerRef.current) {
      const osmDisplay = new OpenSheetMusicDisplay(containerRef.current, {
        autoResize: true,
        backend: 'svg',
        drawTitle: true,
        followCursor: true,
        cursorsOptions: {
          type: 'standard',
          color: '#33C3F0',
          alpha: 0.8
        }
      });

      // 재생 매니저 설정
      const manager = new PlaybackManager();
      manager.osmd = osmDisplay;

      setOsmd(osmDisplay);
      setPlaybackManager(manager);
    }
  }, []);

  const loadAndRenderScore = async () => {
    // ... (이전 예제와 동일한 로드 로직)

    // 추가: 재생 준비
    if (playbackManager) {
      playbackManager.initialize();
    }
  };

  const playPause = () => {
    if (!playbackManager) return;

    if (isPlaying) {
      playbackManager.pause();
    } else {
      playbackManager.play();
    }
    setIsPlaying(!isPlaying);
  };

  const stop = () => {
    if (playbackManager) {
      playbackManager.stop();
      setIsPlaying(false);
    }
  };

  return (
    <div className="advanced-musicxml-display">
      <div className="controls mb-4 space-x-2">
        <button onClick={loadAndRenderScore} className="btn-primary">
          악보 로드
        </button>
        <button onClick={playPause} className="btn-secondary">
          {isPlaying ? '일시정지' : '재생'}
        </button>
        <button onClick={stop} className="btn-secondary">
          정지
        </button>
      </div>

      <div ref={containerRef} className="music-sheet-container" />
    </div>
  );
}
```

### 4. Next.js 프로젝트에서 사용하기

```jsx
// pages/analysis-result.tsx 또는 components/AnalysisResult.tsx

import dynamic from 'next/dynamic';
import { useState, useEffect } from 'react';

// OSMD는 브라우저에서만 작동하므로 동적 import 사용
const MusicXMLDisplay = dynamic(
  () => import('../components/MusicXMLDisplay').then(mod => mod.MusicXMLDisplay),
  {
    ssr: false,
    loading: () => <div>악보 컴포넌트 로딩 중...</div>
  }
);

export default function AnalysisResult({ taskId }: { taskId: string }) {
  const [showSheet, setShowSheet] = useState(false);

  return (
    <div className="analysis-result">
      {/* 기존 분석 결과 표시 */}

      <div className="musicxml-section mt-8">
        <h3 className="text-xl font-bold mb-4">악보 보기</h3>

        <button
          onClick={() => setShowSheet(!showSheet)}
          className="mb-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          {showSheet ? '악보 숨기기' : '악보 표시하기'}
        </button>

        {showSheet && (
          <MusicXMLDisplay taskId={taskId} />
        )}
      </div>
    </div>
  );
}
```

## 주의사항 및 팁

### 1. 라이브러리 호환성
- OSMD는 브라우저 환경에서만 작동합니다 (SSR 지원 없음)
- Next.js에서는 반드시 `dynamic import`와 `ssr: false` 옵션을 사용하세요

### 2. 스타일링
```css
/* 악보 컨테이너 스타일링 */
.music-sheet-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  overflow: auto;
}

/* OSMD SVG 요소 스타일링 */
.music-sheet-container svg {
  max-width: 100%;
  height: auto;
}
```

### 3. 반응형 디자인
```typescript
// 창 크기 변경 시 악보 재렌더링
useEffect(() => {
  const handleResize = () => {
    if (osmd) {
      osmd.render();
    }
  };

  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, [osmd]);
```

### 4. 오류 처리
- 네트워크 오류 및 API 응답 오류를 적절히 처리하세요
- MusicXML 파싱 오류에 대한 fallback UI를 제공하세요
- 분석이 완료되지 않은 경우 적절한 안내 메시지를 표시하세요

## 추가 기능

### 악보 다운로드
```typescript
const downloadMusicXML = async () => {
  try {
    const response = await fetch(`/api/v3/analysis/${taskId}/musicxml`);
    const blob = await response.blob();

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_${taskId}.musicxml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('다운로드 실패:', error);
  }
};
```

### PDF 내보내기
```typescript
// OSMD에서 제공하는 PDF 내보내기 기능 사용
const exportToPDF = async () => {
  if (osmd) {
    try {
      const pdfData = await osmd.createPDF();
      // PDF 다운로드 로직
    } catch (error) {
      console.error('PDF 내보내기 실패:', error);
    }
  }
};
```

이 가이드를 따라 구현하면 Music Assistant v3에서 생성된 MusicXML 데이터를 프론트엔드에서 아름다운 악보로 시각화할 수 있습니다.