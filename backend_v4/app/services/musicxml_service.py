import math
from typing import List, Dict, Any
from music21 import stream, note, tempo, pitch


class MusicXMLService:
    """Service for generating MusicXML from quantized note data."""

    def generate_musicxml(
        self,
        quantized_notes: List[Dict[str, Any]],
        bpm: float,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate MusicXML string from quantized notes.

        Args:
            quantized_notes: List of quantized note dictionaries
            bpm: Tempo in BPM
            metadata: Analysis metadata

        Returns:
            MusicXML string
        """
        # Create score and part
        score = stream.Score()
        part = stream.Part()

        # Add tempo marking
        metronome = tempo.MetronomeMark(number=bpm)
        part.append(metronome)

        # Convert quantized notes to music21 Note objects
        for note_data in quantized_notes:
            try:
                # Convert frequency to MIDI note
                midi_number = self._hz_to_midi(note_data["pitch_hz"])

                # Create music21 Note
                n = note.Note()
                n.pitch.midi = round(midi_number)

                # Set offset (start position in beats)
                n.offset = note_data["start_time_beat"]

                # Set duration (in quarter note lengths)
                n.quarterLength = note_data["duration_beat"]

                part.append(n)
            except (ValueError, KeyError) as e:
                # Skip invalid notes
                continue

        score.append(part)

        # Export to MusicXML string
        musicxml_string = score.write('musicxml')

        return musicxml_string

    def _hz_to_midi(self, frequency: float) -> float:
        """
        Convert frequency in Hz to MIDI note number.

        Args:
            frequency: Frequency in Hz

        Returns:
            MIDI note number (float, may need rounding)
        """
        if frequency <= 0:
            raise ValueError("Frequency must be positive")

        # MIDI note 69 = A4 = 440 Hz
        # Formula: midi = 69 + 12 * log2(f / 440)
        midi = 69 + 12 * math.log2(frequency / 440.0)

        return midi
