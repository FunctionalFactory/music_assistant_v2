import librosa
import numpy as np
from typing import List, Dict, Any, Optional


class AudioAnalysisService:
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def analyze_vocal_melody(self, audio_file_path: str, delta: float = 1.14, wait: float = 0.03) -> Dict[str, Any]:
        y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

        if len(y) < 2048:
            raise ValueError(f"Audio file too short for analysis. Minimum duration: {2048/sr:.2f} seconds")

        pitch_contour = self._extract_pitch_contour(y, sr)
        onsets = self._extract_onsets(y, sr, delta, wait)
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

    def _extract_onsets(self, y: np.ndarray, sr: int, delta: float = 1.14, wait: float = 0.03) -> List[Dict[str, Any]]:
        hop_length = 512

        onset_strength = librosa.onset.onset_strength(
            y=y,
            sr=sr,
            hop_length=hop_length
        )

        onset_frames = librosa.util.peak_pick(
            onset_strength,
            pre_max=max(1, int(0.03 * sr / hop_length)),
            post_max=max(1, int(0.01 * sr / hop_length)),
            pre_avg=max(1, int(0.10 * sr / hop_length)),
            post_avg=max(1, int(0.10 * sr / hop_length)),
            delta=delta,
            wait=max(1, int(wait * sr / hop_length))
        )

        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)

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

        return [float(x) for x in downsampled.tolist()]

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
        return [float(round(i * time_step, 3)) for i in range(waveform_length)]

    def _generate_frequency_axis(self, sr: int) -> List[float]:
        n_fft = 2048
        freq_bins = n_fft // 2 + 1
        freq_axis = np.linspace(0, sr // 2, freq_bins)

        if len(freq_axis) > 100:
            step = len(freq_axis) // 100
            freq_axis = freq_axis[::step]

        return [float(x) for x in freq_axis.tolist()]

    def analyze_for_visualization(self, audio_file_path: str, delta: float = 1.14, wait: float = 0.03) -> Dict[str, Any]:
        y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

        if len(y) < 2048:
            raise ValueError(f"Audio file too short for analysis. Minimum duration: {2048/sr:.2f} seconds")

        pitch_contour = self._extract_pitch_contour(y, sr)
        onsets = self._extract_onsets(y, sr, delta, wait)
        waveform = self._prepare_waveform_data(y)
        waveform_times = self._generate_time_axis(len(waveform), len(y), sr)

        return self._format_for_visualization(pitch_contour, onsets, waveform, waveform_times, delta, wait, sr)

    def _format_for_visualization(
        self,
        pitch_contour: List[Dict[str, Any]],
        onsets: List[Dict[str, Any]],
        waveform: List[float],
        waveform_times: List[float],
        delta: float,
        wait: float,
        sample_rate: int
    ) -> Dict[str, Any]:

        # Convert pitch contour to [time, frequency] pairs with null for gaps
        formatted_pitch = self._format_pitch_contour_for_visualization(pitch_contour)

        # Extract only onset times
        onset_times = [float(onset["time"]) for onset in onsets]

        return {
            "waveform": {
                "data": waveform,
                "times": waveform_times
            },
            "pitch_contour": formatted_pitch,
            "onsets": onset_times,
            "metadata": {
                "delta": float(delta),
                "wait": float(wait),
                "sample_rate": int(sample_rate)
            }
        }

    def _format_pitch_contour_for_visualization(self, pitch_contour: List[Dict[str, Any]]) -> List[List[Optional[float]]]:
        if not pitch_contour:
            return []

        # Create continuous time series with null for missing pitches
        result = []

        # Find the time range
        if pitch_contour:
            start_time = pitch_contour[0]["time"]
            end_time = pitch_contour[-1]["time"]

            # Create time grid with 0.05 second intervals
            time_step = 0.05
            current_time = start_time
            pitch_index = 0

            while current_time <= end_time:
                # Find closest pitch data point
                closest_pitch = None

                # Look for pitch within small time window
                for i in range(pitch_index, len(pitch_contour)):
                    if abs(pitch_contour[i]["time"] - current_time) <= time_step / 2:
                        closest_pitch = pitch_contour[i]["frequency"]
                        break
                    elif pitch_contour[i]["time"] > current_time + time_step / 2:
                        break

                result.append([float(round(current_time, 3)), float(closest_pitch) if closest_pitch is not None else None])
                current_time += time_step

        return result