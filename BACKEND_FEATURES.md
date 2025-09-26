# Music Assistant v2 - Python 백엔드 기능 설명서

## 개요

Music Assistant v2는 오디오 파일을 분석하여 음악적 특징을 추출하는 웹 애플리케이션의 백엔드 시스템입니다. Python과 FastAPI를 기반으로 구축되었으며, librosa 라이브러리를 활용한 고급 오디오 신호 처리 기능을 제공합니다.

## 시스템 아키텍처

### 프레임워크 및 기술 스택
- **FastAPI**: 현대적이고 성능이 뛰어난 웹 프레임워크
- **Librosa**: 음악 및 오디오 분석을 위한 Python 라이브러리
- **Pydantic**: 데이터 검증 및 직렬화
- **NumPy/SciPy**: 수치 계산 및 신호 처리

### 모듈 구조 (SOLID 원칙 적용)
```
backend/
├── main.py                 # 애플리케이션 진입점
├── app/
│   ├── main.py            # FastAPI 앱 설정 및 CORS
│   ├── api/
│   │   └── endpoints.py   # API 엔드포인트 정의
│   ├── services/
│   │   └── audio_analysis.py  # 핵심 오디오 분석 로직
│   └── models/
│       └── audio_models.py    # 데이터 모델 정의
└── requirements.txt       # 의존성 관리
```

## 핵심 기능 상세 설명

### 1. AudioAnalysisService 클래스

#### 목적
단일 책임 원칙(SRP)에 따라 오디오 분석 로직만을 담당하는 서비스 클래스

#### 주요 메서드

##### `analyze_vocal_melody(audio_file_path: str)`
**기능**: 오디오 파일의 종합적 분석을 수행하는 메인 메서드
**반환값**: 피치 컨투어, 온셋, 파형, 스펙트로그램 데이터가 포함된 딕셔너리

**처리 과정**:
1. `librosa.load()`를 통한 오디오 파일 로딩 (기본 22.05kHz 샘플링)
2. 각종 음악적 특징 추출 메서드 호출
3. 시각화에 적합한 데이터 구조로 가공

##### `_extract_pitch_contour(y: np.ndarray, sr: int)`
**기능**: 시간에 따른 피치(음고) 변화 추출
**알고리즘**:
- `librosa.piptrack()` 사용하여 주파수 추적
- 각 시간 프레임에서 가장 강한 신호의 피치 추출
- 프레임당 512 샘플의 hop_length로 시간 해상도 설정

**데이터 구조**:
```python
[
    {"time": 0.01, "frequency": 261.63, "note": "C4"},
    {"time": 0.02, "frequency": 262.10, "note": "C4"}
]
```

##### `_extract_onsets(y: np.ndarray, sr: int)`
**기능**: 음악적 이벤트(노트 시작점) 탐지
**알고리즘**:
- `librosa.onset.onset_detect()` 사용하여 온셋 시점 탐지
- 각 온셋 후 150ms 윈도우에서 피치 분석
- 온셋 후 50ms 지연을 두어 transient 효과 제거

**특징**:
- 타격, 발성, 악기 연주 등의 시작점을 정확히 탐지
- 각 온셋과 연관된 음표 정보 제공

##### `_prepare_waveform_data(y: np.ndarray)`
**기능**: 시각화를 위한 파형 데이터 최적화
**최적화 전략**:
- 최대 2000개 포인트로 다운샘플링
- 메모리 효율성과 시각화 성능 균형 유지
- 원본 파형의 주요 특징 보존

##### `_generate_spectrogram(y: np.ndarray, sr: int)`
**기능**: 주파수-시간 표현의 스펙트로그램 생성
**처리 과정**:
- Short-Time Fourier Transform (STFT) 적용
- 진폭을 dB 스케일로 변환
- 100x100 해상도로 다운샘플링하여 효율적인 시각화 지원

##### `_frequency_to_note(frequency: float)`
**기능**: 주파수를 음표 이름으로 변환
**수학적 배경**:
- A4 = 440Hz를 기준으로 하는 12-TET (12-Tone Equal Temperament) 사용
- 공식: `h = 12 * log2(f / C0)` (C0 = 16.35Hz)
- 세미톤 단위로 옥타브와 음표 이름 계산

**지원 음표 범위**: C0 ~ B9 (약 16Hz ~ 7902Hz)

##### `_generate_time_axis()` / `_generate_frequency_axis()`
**기능**: 시각화를 위한 시간 및 주파수 축 생성
**시간 축**: 원본 오디오 길이 기준으로 균등 분할
**주파수 축**: Nyquist 주파수(sr/2)까지의 선형 분할

## API 엔드포인트

### POST /analyze
**기능**: 오디오 파일 업로드 및 분석 수행
**지원 형식**: .wav, .mp3, .flac
**최대 파일 크기**: 50MB

**요청 형식**: multipart/form-data
**응답 형식**: JSON

**보안 및 검증**:
- 파일 확장자 검증
- 파일 크기 제한
- 임시 파일 자동 정리
- 예외 상황 처리

## 데이터 모델 (Pydantic)

### AudioAnalysisResponse
메인 응답 모델로 모든 분석 결과를 포함합니다.

```python
class AudioAnalysisResponse(BaseModel):
    pitch_contour: List[PitchPoint]  # 피치 컨투어 데이터
    onsets: List[OnsetPoint]         # 온셋 정보
    waveform: WaveformData           # 파형 데이터 + 시간 축
    spectrogram: SpectrogramData     # 스펙트로그램 + 주파수 축
```

### 하위 모델들
- **PitchPoint**: 시간, 주파수, 음표 정보
- **OnsetPoint**: 온셋 시간, 음표, 주파수 정보
- **WaveformData**: 파형 데이터와 해당 시간 축
- **SpectrogramData**: 스펙트로그램 데이터와 주파수 축

## 성능 최적화

### 메모리 최적화
- 파형 데이터: 최대 2000 포인트로 제한
- 스펙트로그램: 100x100 해상도로 다운샘플링
- 임시 파일 자동 정리로 디스크 공간 절약

### 계산 최적화
- librosa의 최적화된 알고리즘 활용
- NumPy 벡터화 연산 사용
- 필요한 데이터만 계산하는 지연 평가 패턴

### 확장성 고려사항
- 서비스 클래스를 통한 비즈니스 로직 분리
- 의존성 주입 가능한 구조
- 비동기 처리 준비 (FastAPI 기반)

## 제한사항

### 기술적 제한
- 샘플링 레이트: 기본 22.05kHz로 고정
- 지원 형식: WAV, MP3, FLAC만 지원
- 단일 채널 분석 (모노로 변환)

### 알고리즘 한계
- 폴리포닉(화성) 음악에서 주 멜로디 추출의 정확도 제한
- 노이즈가 많은 환경에서의 피치 탐지 정확도 저하
- 매우 낮거나 높은 주파수 대역의 탐지 한계

## 확장 가능성

### Phase 4/5 준비사항
- Docker 컨테이너화 지원
- 비동기 작업 큐 (Celery) 통합 준비
- 프로덕션 서버 (Gunicorn) 설정 가능
- 로깅 및 모니터링 시스템 통합 준비

### AI/ML 확장
- 딥러닝 기반 피치 추정 모델 통합 가능
- 음색 분석 및 악기 분류 기능 확장
- 화성 분석 및 코드 진행 추출 기능 추가

이 문서는 Music Assistant v2 백엔드의 핵심 기능과 설계 원칙을 AI가 이해할 수 있도록 구체적이고 기술적인 관점에서 설명합니다. 각 구성요소는 SOLID 원칙을 준수하며, 확장 가능하고 유지보수 가능한 구조로 설계되었습니다.