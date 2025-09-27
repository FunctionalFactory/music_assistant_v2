# Music Assistant V2 Development Specification

## Overview
This specification outlines the development plan for Music Assistant V2, focusing on improving onset detection algorithms and implementing sheet music generation capabilities. The work will be done in a separate `backend_v2` directory to avoid impacting the existing stable system.

---

## Phase 1: 온셋 탐지 알고리즘 개선 (Backend V2)

**목표:** 기존의 단순 피크 찾기 방식이 아닌, 음악적으로 더 의미 있는 온셋을 탐지하는 고도화된 알고리즘을 적용하여 백엔드 분석 엔진을 업그레이드합니다.

### Backend (Python):
- [x] **새로운 작업 환경 구성:** 기존 `backend` 디렉토리는 그대로 두고, `backend_v2` 디렉토리를 생성
- [x] **핵심 로직 교체:** `scipy.signal.find_peaks`를 `librosa.onset.onset_detect`로 교체
  - [x] Spectral Flux 기반 온셋 탐지 구현
  - [x] 음악적으로 의미 있는 온셋 추출 로직 개발
- [x] **API 엔드포인트 업데이트:**
  - [x] `POST /v2/analyze` 엔드포인트 생성
  - [x] JSON 형태의 개선된 온셋 데이터 반환
- [x] **의존성 관리:** `backend_v2` 디렉토리 내 `requirements.txt` 유지

### Frontend (Next.js):
- [x] 이 단계에서는 프론트엔드 개발 진행하지 않음

### 실행 및 테스트:
- [x] `backend_v2` 서버 독립 실행
- [x] Postman/curl을 사용한 `/v2/analyze` 엔드포인트 테스트
- [x] 온셋 개수 감소 및 정확도 향상 확인

### 결과물:
- [x] 정확하고 음악적으로 의미 있는 온셋 데이터를 반환하는 개선된 V2 백엔드 API

---

## Phase 2: 개선된 분석 결과 시각화 연동

**목표:** 프론트엔드가 새로운 V2 백엔드 API와 통신하여, 개선된 온셋 탐지 결과를 기존 시각화 차트에 표시

### Backend (Python / `backend_v2`):
- [x] 프론트엔드 요청을 위한 CORS 설정 확인

### Frontend (Next.js):
- [x] **API 호출 수정:** 기존 `/analyze`에서 `/v2/analyze`로 변경
- [x] **UI/UX:** V1과 V2 선택 토글/버튼 추가 (선택사항)
- [x] **결과 확인:** 기존 시각화 컴포넌트에 API 응답 전달

### 실행 및 테스트:
- [x] `backend_v2`와 Next.js 개발 서버 동시 실행
- [x] 웹 브라우저에서 오디오 파일 업로드 테스트
- [x] 온셋 수직선 개수 감소 및 정확도 향상 시각 확인

### 결과물:
- [x] 개선된 온셋 탐지 결과를 시각적으로 확인할 수 있는 웹 애플리케이션

---

## Phase 3: 음표 데이터 구조화 (Note Segmentation)

**목표:** 정확하게 추출된 온셋과 음고 데이터를 결합하여, 악보 생성을 위한 중간 데이터 형태인 '음표 리스트' 생성

### Backend (Python / `backend_v2`):
- [ ] **새로운 로직 추가:** 음표 분할(Note Segmentation) 로직 구현
  - [ ] `librosa.onset.onset_detect`로 온셋 시간 배열 획득
  - [ ] 각 온셋 시간에 해당하는 음고(pitch) 추출
  - [ ] 음표 지속 시간(duration) 계산 (다음 온셋과의 시간 차이)
  - [ ] 구조화된 음표 데이터 배열 생성 `[{"start_time": 0.52, "pitch": "C4", "duration": 0.58}, ...]`
- [ ] **API 엔드포인트 추가:**
  - [ ] `POST /v2/generate_notes` 엔드포인트 생성
  - [ ] 구조화된 음표 리스트 JSON 반환

### Frontend (Next.js):
- [ ] **결과 표시:** 음표 리스트(JSON)를 텍스트 형태로 표시하는 영역 추가

### 실행 및 테스트:
- [ ] `/v2/generate_notes` 엔드포인트 호출 테스트
- [ ] 반환된 JSON 데이터의 음악적 타당성 확인

### 결과물:
- [ ] 오디오 파일로부터 악보의 기본 정보(음표 리스트)를 추출하여 JSON으로 제공하는 API 및 화면 표시 기능

---

## Phase 4: 악보 파일 생성 및 다운로드 기능 (Backend)

**목표:** 구조화된 음표 데이터를 바탕으로 MusicXML 악보 파일 생성 및 다운로드 기능 구현

### Backend (Python / `backend_v2`):
- [ ] **라이브러리 추가:** `music21` 설치 및 `requirements.txt`에 추가
- [ ] **악보 변환 로직 구현:**
  - [ ] `/v2/generate_notes`에서 얻은 음표 리스트 입력 처리
  - [ ] `music21`을 사용하여 `music21.note.Note` 객체 변환
  - [ ] `music21.stream.Stream`에 Note 객체들 추가
  - [ ] MusicXML 파일로 내보내는 로직 작성
- [ ] **API 엔드포인트 추가:**
  - [ ] `POST /v2/generate_score` 엔드포인트 생성
  - [ ] MusicXML 파일 HTTP 응답으로 반환 (`Content-Disposition: attachment`)

### Frontend (Next.js):
- [ ] **UI 추가:** "악보 다운로드" 버튼 추가
- [ ] **기능 구현:** 버튼 클릭 시 `/v2/generate_score` 호출 및 파일 다운로드 처리

### 실행 및 테스트:
- [ ] 웹 앱에서 오디오 파일 업로드 및 "악보 다운로드" 버튼 클릭 테스트
- [ ] 다운로드된 `.musicxml` 파일을 MuseScore로 열어 악보 확인

### 결과물:
- [ ] 사용자가 오디오를 업로드하면 해당 멜로디의 악보 파일을 다운로드할 수 있는 기능

---

## Phase 5: 웹 기반 악보 뷰어 연동 (Frontend)

**목표:** 다운로드한 악보 파일을 브라우저에서 직접 시각적으로 렌더링하여 표시하는 기능 구현

### Backend (Python / `backend_v2`):
- [ ] 기존 `/v2/generate_score` 엔드포인트를 MusicXML 텍스트 형태로 반환하도록 수정 또는 별도 엔드포인트 생성

### Frontend (Next.js):
- [ ] **라이브러리 설치:** `OpenSheetMusicDisplay` (OSMD) 프로젝트에 추가
- [ ] **UI 컴포넌트 개발:** 악보 렌더링용 `ScoreViewer.js` 컴포넌트 생성
- [ ] **기능 구현:**
  - [ ] "악보 보기" 버튼 클릭 시 `/v2/generate_score` 엔드포인트 호출
  - [ ] MusicXML 텍스트 데이터를 `ScoreViewer` 컴포넌트로 전달
  - [ ] OSMD 라이브러리를 사용하여 MusicXML을 악보 이미지로 렌더링

### 실행 및 테스트:
- [ ] 오디오 파일 업로드 후 "악보 보기" 버튼 클릭 테스트
- [ ] 웹 페이지 내에서 바로 분석된 멜로디의 악보 표시 확인

### 결과물:
- [ ] 오디오 분석부터 악보 생성 및 시각화까지 모든 과정이 통합된 완전한 웹 애플리케이션

---

## 전체 프로젝트 목표

- [ ] 기존 시스템에 영향을 주지 않는 안전한 V2 시스템 개발
- [ ] 음악적으로 의미 있는 온셋 탐지 알고리즘 적용
- [ ] 오디오에서 악보까지의 완전한 변환 파이프라인 구축
- [ ] 사용자 친화적인 웹 기반 인터페이스 제공
- [ ] 표준 악보 포맷(MusicXML) 지원으로 호환성 확보