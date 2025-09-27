import librosa
import numpy as np
from typing import List, Dict, Any


class AudioAnalysisService:
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def analyze_vocal_melody(self, audio_file_path: str) -> Dict[str, Any]:
        y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

        if len(y) < 2048:
            raise ValueError(f"Audio file too short for analysis. Minimum duration: {2048/sr:.2f} seconds")

        pitch_contour = self._extract_pitch_contour(y, sr)
        onsets = self._extract_onsets(y, sr)
        waveform = self._prepare_waveform_data(y)
        spectrogram = self._generate_spectrogram(y, sr)
        waveform_times = self._generate_time_axis(len(waveform), len(y), sr)
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
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        hop_length = 512
        times = librosa.frames_to_time(np.arange(pitches.shape[1]), sr=sr, hop_length=hop_length)

        pitch_contour = []
        for i, time in enumerate(times):
            frame_pitches = pitches[:, i]
            frame_magnitudes = magnitudes[:, i]

            if frame_magnitudes.max() > 0:
                max_idx = np.argmax(frame_magnitudes)
                frequency = frame_pitches[max_idx]

                if frequency > 0:
                    note = self._frequency_to_note(frequency)
                    pitch_contour.append({
                        "time": round(time, 3),
                        "frequency": round(frequency, 2),
                        "note": note
                    })

        return pitch_contour

    def _extract_onsets(self, y: np.ndarray, sr: int) -> List[Dict[str, Any]]:
        onset_frames = librosa.onset.onset_detect(
            y=y,
            sr=sr,
            units='frames',
            hop_length=512,
            backtrack=True,
            pre_max=0.03,
            post_max=0.01,
            pre_avg=0.10,
            post_avg=0.10,
            delta=0.14,
            wait=0.03
        )

        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)

        onsets = []
        for onset_time in onset_times:
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
                    max_idx = np.unravel_index(np.argmax(magnitudes), magnitudes.shape)
                    frequency = pitches[max_idx]

                    if frequency > 80 and frequency < 2000:
                        note = self._frequency_to_note(frequency)
                        onsets.append({
                            "time": round(onset_time, 3),
                            "note": note,
                            "frequency": round(frequency, 2)
                        })

        return onsets

    def _prepare_waveform_data(self, y: np.ndarray) -> List[float]:
        if len(y) > 2000:
            step = len(y) // 2000
            downsampled = y[::step]
        else:
            downsampled = y

        return downsampled.tolist()

    def _generate_spectrogram(self, y: np.ndarray, sr: int) -> List[List[float]]:
        n_fft = min(2048, len(y))
        stft = librosa.stft(y, n_fft=n_fft)
        spectrogram_db = librosa.amplitude_to_db(np.abs(stft))

        height, width = spectrogram_db.shape
        if width > 100:
            step_w = width // 100
            spectrogram_db = spectrogram_db[:, ::step_w]
        if height > 100:
            step_h = height // 100
            spectrogram_db = spectrogram_db[::step_h, :]

        return spectrogram_db.tolist()

    def _frequency_to_note(self, frequency: float) -> str:
        if frequency <= 0:
            return "N/A"

        A4 = 440.0
        C0 = A4 * np.power(2, -4.75)

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
        total_duration = original_length / sr
        time_step = total_duration / waveform_length
        return [round(i * time_step, 3) for i in range(waveform_length)]

    def _generate_frequency_axis(self, sr: int) -> List[float]:
        n_fft = 2048
        freq_bins = n_fft // 2 + 1
        freq_axis = np.linspace(0, sr // 2, freq_bins)

        if len(freq_axis) > 100:
            step = len(freq_axis) // 100
            freq_axis = freq_axis[::step]

        return freq_axis.tolist()