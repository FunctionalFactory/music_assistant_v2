import math
from typing import Dict, List, Any, Optional, Union
from music21 import stream, note, tempo, meter, duration, pitch, bar, metadata, converter


class MusicNotationService:
    """
    Service for converting audio analysis results to MusicXML format.
    Handles tempo variations and note duration calculations.
    """

    def __init__(self):
        self.default_tempo = 120.0
        self.default_time_signature = "4/4"

    def convert_to_musicxml(
        self,
        pitch_contour: List[Dict[str, Any]],
        onsets: List[Dict[str, Any]],
        tempo_info: Dict[str, Any],
        metadata_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert analyzed audio data to MusicXML string format.

        Args:
            pitch_contour: List of pitch points with time, frequency, note
            onsets: List of onset points with time, note, frequency
            tempo_info: Tempo and beat tracking information
            metadata_info: Optional metadata about the analysis

        Returns:
            MusicXML string representation of the musical score
        """
        try:
            # Create a new music21 stream
            score = stream.Score()

            # Add metadata
            self._add_metadata(score, metadata_info)

            # Create a part for the melody
            melody_part = stream.Part()

            # Set time signature
            melody_part.append(meter.TimeSignature(self.default_time_signature))

            # Set initial tempo
            initial_tempo = tempo_info.get("global_tempo", self.default_tempo)
            melody_part.append(tempo.TempoIndication(number=initial_tempo))

            # Convert onsets to notes
            notes = self._convert_onsets_to_notes(onsets, tempo_info)

            # Add notes to the melody part
            for note_obj in notes:
                melody_part.append(note_obj)

            # Add the melody part to the score
            score.append(melody_part)

            # Convert to MusicXML string
            # music21's write method with 'musicxml' format returns the content as string
            # when no file path is provided
            from io import StringIO
            import tempfile

            # Use a temporary file approach to get the MusicXML string
            with tempfile.NamedTemporaryFile(mode='w', suffix='.musicxml', delete=False) as tmp_file:
                score.write('musicxml', fp=tmp_file.name)

            # Read the generated file content
            with open(tmp_file.name, 'r', encoding='utf-8') as f:
                musicxml_content = f.read()

            # Clean up the temporary file
            import os
            os.unlink(tmp_file.name)

            return musicxml_content

        except Exception as e:
            raise Exception(f"Failed to convert to MusicXML: {str(e)}")

    def _add_metadata(self, score: stream.Score, metadata_info: Optional[Dict[str, Any]]):
        """Add metadata information to the score."""
        score.append(metadata.Metadata())
        score.metadata.title = "Audio Analysis Result"
        score.metadata.composer = "Music Assistant v3"

        if metadata_info:
            if "sample_rate" in metadata_info:
                score.metadata.software = [f"Music Assistant v3 (SR: {metadata_info['sample_rate']}Hz)"]
        else:
            score.metadata.software = ["Music Assistant v3"]

    def _convert_onsets_to_notes(
        self,
        onsets: List[Dict[str, Any]],
        tempo_info: Dict[str, Any]
    ) -> List[note.Note]:
        """
        Convert onset data to music21 Note objects with proper durations.
        """
        notes = []
        global_tempo = tempo_info.get("global_tempo", self.default_tempo)
        beat_times = tempo_info.get("beat_times", [])

        # Sort onsets by time
        sorted_onsets = sorted(onsets, key=lambda x: x.get("time", 0))

        for i, onset in enumerate(sorted_onsets):
            try:
                # Extract note information
                note_name = onset.get("note", "C4")
                onset_time = onset.get("time", 0)
                frequency = onset.get("frequency", 440.0)

                # Skip invalid notes
                if note_name == "N/A" or frequency <= 0:
                    continue

                # Calculate note duration
                note_duration = self._calculate_note_duration(
                    onset_time,
                    sorted_onsets,
                    i,
                    global_tempo,
                    beat_times
                )

                # Create music21 note
                note_obj = self._create_note(note_name, note_duration, onset_time)
                if note_obj:
                    notes.append(note_obj)

            except Exception as e:
                # Skip problematic notes and continue
                continue

        return notes

    def _calculate_note_duration(
        self,
        onset_time: float,
        all_onsets: List[Dict[str, Any]],
        current_index: int,
        global_tempo: float,
        beat_times: List[float]
    ) -> float:
        """
        Calculate the duration of a note based on onset timing and tempo.
        """
        # Default duration (quarter note)
        default_duration = 1.0

        try:
            # If there's a next onset, calculate duration until next onset
            if current_index + 1 < len(all_onsets):
                next_onset_time = all_onsets[current_index + 1].get("time", onset_time + 0.5)
                duration_seconds = next_onset_time - onset_time
            else:
                # Last note, use default duration
                duration_seconds = 60.0 / global_tempo  # One beat duration

            # Convert seconds to musical duration (quarter notes)
            beats_per_second = global_tempo / 60.0
            musical_duration = duration_seconds * beats_per_second

            # Quantize to common note values (whole, half, quarter, eighth, sixteenth)
            return self._quantize_duration(musical_duration)

        except Exception:
            return default_duration

    def _quantize_duration(self, raw_duration: float) -> float:
        """
        Quantize duration to common musical note values.
        """
        # Common note durations (in quarter note units)
        note_values = [
            4.0,    # Whole note
            2.0,    # Half note
            1.0,    # Quarter note
            0.5,    # Eighth note
            0.25,   # Sixteenth note
        ]

        # Find the closest standard duration
        closest_duration = min(note_values, key=lambda x: abs(x - raw_duration))

        # Don't allow notes longer than a whole note or shorter than a sixteenth
        if closest_duration > 4.0:
            return 4.0
        elif closest_duration < 0.25:
            return 0.25

        return closest_duration

    def _create_note(self, note_name: str, note_duration: float, offset_time: float) -> Optional[note.Note]:
        """
        Create a music21 Note object from note name and duration.
        """
        try:
            # Create the note
            note_obj = note.Note(note_name)

            # Set duration
            note_obj.duration = duration.Duration(quarterLength=note_duration)

            # Set offset (position in the score)
            note_obj.offset = offset_time

            return note_obj

        except Exception:
            # Return None for invalid notes
            return None

    def _physical_time_to_musical_time(
        self,
        physical_time: float,
        tempo_curve: List[Dict[str, float]],
        global_tempo: float
    ) -> float:
        """
        Convert physical time (seconds) to musical time (quarter note beats).
        Considers tempo variations for rubato support.
        """
        if not tempo_curve:
            # Use global tempo if no tempo curve available
            return physical_time * (global_tempo / 60.0)

        musical_time = 0.0
        prev_time = 0.0

        for tempo_point in tempo_curve:
            point_time = tempo_point["time"]
            point_tempo = tempo_point["tempo"]

            if point_time >= physical_time:
                # Interpolate between previous and current tempo point
                time_diff = physical_time - prev_time
                musical_time += time_diff * (point_tempo / 60.0)
                break
            else:
                # Add full segment duration
                time_diff = point_time - prev_time
                musical_time += time_diff * (point_tempo / 60.0)
                prev_time = point_time

        return musical_time

    def convert_to_pdf(
        self,
        pitch_contour: List[Dict[str, Union[float, str]]],
        onsets: List[Dict[str, Union[float, str]]],
        tempo_info: Dict[str, Union[float, List]],
        metadata_info: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Convert analysis data to PDF format.

        Args:
            pitch_contour: List of pitch analysis points
            onsets: List of detected onsets
            tempo_info: Tempo analysis information
            metadata_info: Additional metadata

        Returns:
            PDF file as bytes

        Raises:
            Exception: If PDF generation fails
        """
        try:
            # First generate MusicXML
            musicxml_string = self.convert_to_musicxml(
                pitch_contour=pitch_contour,
                onsets=onsets,
                tempo_info=tempo_info,
                metadata_info=metadata_info
            )

            # Load the MusicXML into music21
            score = converter.parse(musicxml_string)

            # Create a temporary file for PDF output
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf_path = temp_pdf.name

            try:
                # Convert to PDF using music21
                score.write('musicxml.pdf', fp=temp_pdf_path)

                # Read the PDF file
                with open(temp_pdf_path, 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()

                return pdf_bytes

            finally:
                # Clean up temporary file
                if os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)

        except Exception as e:
            error_msg = str(e)
            if "mscore" in error_msg or "MuseScore" in error_msg:
                raise Exception("PDF generation requires MuseScore to be installed. Please install MuseScore from https://musescore.org/ to enable PDF export functionality.")
            else:
                raise Exception(f"PDF generation failed: {error_msg}")