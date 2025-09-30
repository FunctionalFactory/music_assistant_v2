import librosa
import numpy as np
from typing import Dict, Any, Optional, List, Tuple


class AudioAnalysisService:
    """Basic audio analysis service for pitch and onset detection."""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def analyze(
        self,
        audio_file_path: str,
        delta: float = 1.14,
        wait: float = 0.03,
        bpm: Optional[float] = None,
        grid_resolution: str = "1/16"
    ) -> Dict[str, Any]:
        """
        Analyze audio file and extract pitch, onset, and rhythm information.

        Args:
            audio_file_path: Path to audio file
            delta: Onset detection sensitivity threshold (higher = less sensitive)
            wait: Minimum time between onsets in seconds
            bpm: Manual tempo in BPM (auto-estimated if None)
            grid_resolution: Quantization grid resolution (e.g., "1/4", "1/8", "1/16", "1/8t")

        Returns:
            Dictionary containing pitch contour, onsets, and rhythm info
        """
        y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

        if len(y) < 2048:
            raise ValueError(f"Audio file too short. Minimum duration: {2048/sr:.2f}s")

        duration = len(y) / sr

        # Extract basic features
        pitch_contour = self._extract_pitch(y, sr)
        onsets = self._extract_onsets(y, sr, delta, wait)

        # Rhythm quantization
        tempo = bpm if bpm is not None else self._estimate_tempo(y, sr)
        beat_grid = self._generate_beat_grid(tempo, duration)
        quant_grid = self._generate_quantization_grid(beat_grid, grid_resolution)
        quantized_onsets = self._quantize_onsets(onsets, quant_grid, tempo)

        # Phase 4: Create quantized notes with duration info
        quantized_notes = self._create_quantized_notes(quantized_onsets, tempo, duration)

        # Phase 4: Prepare waveform data for visualization
        waveform_data = self._prepare_waveform_data(y)
        waveform_times = self._generate_time_axis(len(waveform_data), len(y), sr)

        return {
            "waveform": {
                "data": waveform_data,
                "times": waveform_times
            },
            "pitch_contour": pitch_contour,
            "onsets": onsets,
            "quantized_onsets": quantized_onsets,
            "rhythm_info": {
                "bpm": float(tempo),
                "beat_grid": [round(float(t), 3) for t in beat_grid],
                "grid_resolution": grid_resolution,
                "quantized_notes": quantized_notes
            },
            "metadata": {
                "sample_rate": int(sr),
                "duration": float(duration),
                "delta": float(delta),
                "wait": float(wait)
            }
        }

    def _extract_pitch(self, y: np.ndarray, sr: int) -> list:
        """Extract pitch contour from audio signal."""
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        hop_length = 512
        times = librosa.frames_to_time(
            np.arange(pitches.shape[1]),
            sr=sr,
            hop_length=hop_length
        )

        pitch_data = []
        for i, time in enumerate(times):
            frame_pitches = pitches[:, i]
            frame_magnitudes = magnitudes[:, i]

            if frame_magnitudes.max() > 0:
                max_idx = np.argmax(frame_magnitudes)
                frequency = frame_pitches[max_idx]

                if frequency > 0:
                    pitch_data.append({
                        "time": round(float(time), 3),
                        "frequency": round(float(frequency), 2)
                    })

        return pitch_data

    def _extract_onsets(
        self,
        y: np.ndarray,
        sr: int,
        delta: float,
        wait: float
    ) -> list:
        """
        Extract onset times using spectral flux with peak picking.

        Uses librosa.onset.onset_strength for spectral flux calculation
        and librosa.util.peak_pick for precise onset detection.
        """
        hop_length = 512

        # Calculate onset strength envelope (spectral flux)
        onset_strength = librosa.onset.onset_strength(
            y=y,
            sr=sr,
            hop_length=hop_length
        )

        # Peak picking with dynamic sensitivity parameters
        onset_frames = librosa.util.peak_pick(
            onset_strength,
            pre_max=max(1, int(0.03 * sr / hop_length)),
            post_max=max(1, int(0.01 * sr / hop_length)),
            pre_avg=max(1, int(0.10 * sr / hop_length)),
            post_avg=max(1, int(0.10 * sr / hop_length)),
            delta=delta,
            wait=max(1, int(wait * sr / hop_length))
        )

        onset_times = librosa.frames_to_time(
            onset_frames,
            sr=sr,
            hop_length=hop_length
        )

        # Extract pitch at each onset
        onsets = []
        for onset_time in onset_times:
            # Analyze short window after onset for pitch
            start_sample = int((onset_time + 0.02) * sr)
            end_sample = int((onset_time + 0.15) * sr)

            if end_sample < len(y):
                window = y[start_sample:end_sample]

                pitches, magnitudes = librosa.piptrack(
                    y=window,
                    sr=sr,
                    hop_length=128,
                    threshold=0.1,
                    ref=np.max
                )

                if magnitudes.max() > 0:
                    max_idx = np.unravel_index(
                        np.argmax(magnitudes),
                        magnitudes.shape
                    )
                    frequency = pitches[max_idx]

                    # Filter valid frequency range
                    if 80 < frequency < 2000:
                        onsets.append({
                            "time": round(float(onset_time), 3),
                            "frequency": round(float(frequency), 2)
                        })

        return onsets

    def _estimate_tempo(self, y: np.ndarray, sr: int) -> float:
        """
        Estimate tempo using librosa beat tracking.

        Returns:
            Estimated tempo in BPM
        """
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            # Ensure tempo is scalar
            if isinstance(tempo, np.ndarray):
                tempo = float(tempo.item())
            return float(tempo) if tempo > 0 else 120.0
        except Exception:
            return 120.0  # Default fallback

    def _generate_beat_grid(self, bpm: float, duration: float) -> np.ndarray:
        """
        Generate beat grid based on BPM.

        Args:
            bpm: Tempo in beats per minute
            duration: Audio duration in seconds

        Returns:
            Array of beat times in seconds
        """
        beat_duration = 60.0 / bpm  # seconds per beat
        num_beats = int(np.ceil(duration / beat_duration))
        return np.arange(num_beats) * beat_duration

    def _generate_quantization_grid(
        self,
        beat_grid: np.ndarray,
        grid_resolution: str
    ) -> np.ndarray:
        """
        Generate quantization grid based on resolution.

        Args:
            beat_grid: Beat times array
            grid_resolution: Resolution string (e.g., "1/4", "1/8", "1/16", "1/8t")

        Returns:
            Quantization grid times in seconds
        """
        # Parse grid resolution
        subdivisions = self._parse_grid_resolution(grid_resolution)

        if len(beat_grid) < 2:
            return beat_grid

        beat_duration = beat_grid[1] - beat_grid[0]
        grid_points = []

        for beat_time in beat_grid:
            for i in range(subdivisions):
                grid_time = beat_time + (i * beat_duration / subdivisions)
                grid_points.append(grid_time)

        return np.array(grid_points)

    def _parse_grid_resolution(self, grid_resolution: str) -> int:
        """
        Parse grid resolution string to number of subdivisions per beat.

        Args:
            grid_resolution: Resolution string

        Returns:
            Number of subdivisions per beat
        """
        resolution_map = {
            "1/4": 1,    # Quarter note (1 per beat)
            "1/8": 2,    # Eighth note (2 per beat)
            "1/16": 4,   # Sixteenth note (4 per beat)
            "1/8t": 3,   # Eighth note triplet (3 per beat)
            "1/32": 8    # Thirty-second note (8 per beat)
        }
        return resolution_map.get(grid_resolution, 4)  # Default to 1/16

    def _quantize_onsets(
        self,
        onsets: List[Dict[str, Any]],
        quant_grid: np.ndarray,
        bpm: float
    ) -> List[Dict[str, Any]]:
        """
        Quantize onsets to nearest grid point.

        Args:
            onsets: List of onset dictionaries with 'time' and 'frequency'
            quant_grid: Quantization grid times
            bpm: Tempo for beat calculation

        Returns:
            List of quantized onset dictionaries
        """
        if len(quant_grid) == 0 or len(onsets) == 0:
            return []

        beat_duration = 60.0 / bpm
        quantized = []

        for onset in onsets:
            original_time = onset["time"]

            # Find nearest grid point
            distances = np.abs(quant_grid - original_time)
            nearest_idx = np.argmin(distances)
            quantized_time = quant_grid[nearest_idx]

            # Calculate beat position
            quantized_beat = quantized_time / beat_duration

            # Calculate duration to next onset (simplified)
            duration_beats = 0.25  # Default to 1/16 note

            quantized.append({
                "original_time": round(float(original_time), 3),
                "quantized_time": round(float(quantized_time), 3),
                "quantized_beat": round(float(quantized_beat), 3),
                "duration_beats": round(float(duration_beats), 3),
                "frequency": onset.get("frequency", 0.0)
            })

        return quantized

    def _prepare_waveform_data(self, y: np.ndarray) -> List[float]:
        """
        Downsample waveform data to ~2000 points for visualization.

        Args:
            y: Audio signal array

        Returns:
            Downsampled waveform as list of floats
        """
        if len(y) > 2000:
            step = len(y) // 2000
            downsampled = y[::step]
        else:
            downsampled = y

        return [float(x) for x in downsampled.tolist()]

    def _generate_time_axis(
        self,
        waveform_length: int,
        original_length: int,
        sr: int
    ) -> List[float]:
        """
        Generate time axis for waveform data.

        Args:
            waveform_length: Length of downsampled waveform
            original_length: Length of original audio signal
            sr: Sample rate

        Returns:
            List of time values in seconds
        """
        total_duration = original_length / sr
        time_step = total_duration / waveform_length
        return [float(round(i * time_step, 3)) for i in range(waveform_length)]

    def _create_quantized_notes(
        self,
        quantized_onsets: List[Dict[str, Any]],
        bpm: float,
        duration: float
    ) -> List[Dict[str, Any]]:
        """
        Create quantized notes with duration information.

        Args:
            quantized_onsets: List of quantized onset dictionaries
            bpm: Tempo in BPM
            duration: Total audio duration in seconds

        Returns:
            List of quantized note dictionaries with duration info
        """
        if not quantized_onsets:
            return []

        beat_duration = 60.0 / bpm
        notes = []

        for i, onset in enumerate(quantized_onsets):
            # Calculate duration until next onset
            if i < len(quantized_onsets) - 1:
                next_onset = quantized_onsets[i + 1]
                duration_sec = next_onset["quantized_time"] - onset["quantized_time"]
            else:
                # Last note: use remaining duration or default
                duration_sec = min(beat_duration, duration - onset["quantized_time"])

            duration_beat = duration_sec / beat_duration

            notes.append({
                "pitch_hz": onset["frequency"],
                "start_time_sec": onset["quantized_time"],
                "duration_sec": round(float(duration_sec), 3),
                "start_time_beat": onset["quantized_beat"],
                "duration_beat": round(float(duration_beat), 3)
            })

        return notes