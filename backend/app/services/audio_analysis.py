import librosa
import numpy as np
from typing import List, Dict, Any


class AudioAnalysisService:
    """Service responsible for analyzing audio files and extracting musical features."""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def analyze_vocal_melody(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Analyze audio file to extract pitch contour, onsets, waveform, and spectrogram data.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Dictionary containing analyzed audio data
        """
        # Load audio file
        y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

        # Extract pitch contour
        pitch_contour = self._extract_pitch_contour(y, sr)

        # Extract onsets
        onsets = self._extract_onsets(y, sr)

        # Generate waveform data (downsampled for visualization)
        waveform = self._prepare_waveform_data(y)

        # Generate spectrogram data
        spectrogram = self._generate_spectrogram(y, sr)

        # Calculate time axis for waveform
        waveform_times = self._generate_time_axis(len(waveform), len(y), sr)

        # Calculate frequency axis for spectrogram
        freq_axis = self._generate_frequency_axis(sr)

        return {
            "pitch_contour": pitch_contour,
            "onsets": onsets,
            "waveform": {
                "data": waveform,
                "times": waveform_times
            },
            "spectrogram": {
                "data": spectrogram,
                "frequencies": freq_axis
            }
        }

    def _extract_pitch_contour(self, y: np.ndarray, sr: int) -> List[Dict[str, Any]]:
        """Extract pitch contour with time, frequency, and note information."""
        # Extract pitch using librosa
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

        # Calculate time frames
        hop_length = 512
        times = librosa.frames_to_time(np.arange(pitches.shape[1]), sr=sr, hop_length=hop_length)

        pitch_contour = []
        for i, time in enumerate(times):
            # Find the most prominent pitch in this frame
            frame_pitches = pitches[:, i]
            frame_magnitudes = magnitudes[:, i]

            if frame_magnitudes.max() > 0:
                # Get the pitch with highest magnitude
                max_idx = np.argmax(frame_magnitudes)
                frequency = frame_pitches[max_idx]

                if frequency > 0:  # Valid pitch detected
                    note = self._frequency_to_note(frequency)
                    pitch_contour.append({
                        "time": round(time, 3),
                        "frequency": round(frequency, 2),
                        "note": note
                    })

        return pitch_contour

    def _extract_onsets(self, y: np.ndarray, sr: int) -> List[Dict[str, Any]]:
        """Extract onset times and associated notes."""
        # Detect onset times
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)

        # For each onset, try to determine the pitch
        onsets = []
        for onset_time in onset_times:
            # Get a small window around the onset to analyze pitch
            start_sample = int((onset_time + 0.05) * sr)  # Start slightly after onset
            end_sample = int((onset_time + 0.2) * sr)    # 150ms window

            if end_sample < len(y):
                window = y[start_sample:end_sample]

                # Extract pitch from this window
                pitches, magnitudes = librosa.piptrack(y=window, sr=sr)

                if magnitudes.max() > 0:
                    # Find the most prominent pitch
                    max_idx = np.unravel_index(np.argmax(magnitudes), magnitudes.shape)
                    frequency = pitches[max_idx]

                    if frequency > 0:
                        note = self._frequency_to_note(frequency)
                        onsets.append({
                            "time": round(onset_time, 2),
                            "note": note,
                            "frequency": round(frequency, 2)
                        })

        return onsets

    def _prepare_waveform_data(self, y: np.ndarray) -> List[float]:
        """Prepare waveform data for visualization (downsampled)."""
        # Downsample to max 2000 points for efficient visualization
        if len(y) > 2000:
            step = len(y) // 2000
            downsampled = y[::step]
        else:
            downsampled = y

        return downsampled.tolist()

    def _generate_spectrogram(self, y: np.ndarray, sr: int) -> List[List[float]]:
        """Generate spectrogram data for visualization."""
        # Compute spectrogram
        stft = librosa.stft(y)
        spectrogram_db = librosa.amplitude_to_db(np.abs(stft))

        # Downsample for visualization (max 100x100)
        height, width = spectrogram_db.shape
        if width > 100:
            step_w = width // 100
            spectrogram_db = spectrogram_db[:, ::step_w]
        if height > 100:
            step_h = height // 100
            spectrogram_db = spectrogram_db[::step_h, :]

        return spectrogram_db.tolist()

    def _frequency_to_note(self, frequency: float) -> str:
        """Convert frequency to musical note name."""
        if frequency <= 0:
            return "N/A"

        # A4 = 440 Hz
        A4 = 440.0
        C0 = A4 * np.power(2, -4.75)  # C0 frequency

        # Calculate semitone offset from C0
        if frequency > C0:
            h = round(12 * np.log2(frequency / C0))
        else:
            return "N/A"

        octave = h // 12
        n = h % 12

        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        note_name = note_names[n]

        return f"{note_name}{octave}"

    def _generate_time_axis(self, waveform_length: int, original_length: int, sr: int) -> List[float]:
        """Generate time axis for waveform data."""
        total_duration = original_length / sr
        time_step = total_duration / waveform_length
        return [round(i * time_step, 3) for i in range(waveform_length)]

    def _generate_frequency_axis(self, sr: int) -> List[float]:
        """Generate frequency axis for spectrogram data."""
        # Using librosa's default parameters for STFT
        n_fft = 2048
        freq_bins = n_fft // 2 + 1
        freq_axis = np.linspace(0, sr // 2, freq_bins)

        # Downsample to match spectrogram downsampling (max 100 bins)
        if len(freq_axis) > 100:
            step = len(freq_axis) // 100
            freq_axis = freq_axis[::step]

        return freq_axis.tolist()