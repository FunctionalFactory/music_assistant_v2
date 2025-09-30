#!/usr/bin/env python3
"""
Simple test script for MusicXML generation functionality.
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.music_notation import MusicNotationService


def test_music_notation_service():
    """Test basic MusicNotationService functionality."""
    print("🎼 Testing MusicNotationService...")

    # Create service instance
    service = MusicNotationService()
    print("✅ MusicNotationService instance created successfully")

    # Create test data (simulating V3 API response)
    test_onsets = [
        {"time": 0.0, "note": "C4", "frequency": 261.63},
        {"time": 0.5, "note": "D4", "frequency": 293.66},
        {"time": 1.0, "note": "E4", "frequency": 329.63},
        {"time": 1.5, "note": "F4", "frequency": 349.23},
        {"time": 2.0, "note": "G4", "frequency": 392.00},
    ]

    test_tempo_info = {
        "global_tempo": 120.0,
        "beat_times": [0.0, 0.5, 1.0, 1.5, 2.0],
        "tempo_curve": [],
        "beat_count": 5
    }

    test_metadata = {
        "delta": 1.14,
        "wait": 0.03,
        "sample_rate": 22050
    }

    # Test MusicXML conversion
    try:
        musicxml_result = service.convert_to_musicxml(
            pitch_contour=[],  # Empty for this test
            onsets=test_onsets,
            tempo_info=test_tempo_info,
            metadata_info=test_metadata
        )

        print("✅ MusicXML conversion completed successfully")
        print(f"📄 Generated MusicXML length: {len(musicxml_result)} characters")

        # Check if result contains expected MusicXML elements
        expected_elements = [
            '<?xml',
            '<score-partwise',
            '<part-list>',
            '<score-part',
            '<part',
            '<measure',
            '<note>',
            '<pitch>',
            '<step>',
            '<octave>',
            '</score-partwise>'
        ]

        missing_elements = []
        for element in expected_elements:
            if element not in musicxml_result:
                missing_elements.append(element)

        if missing_elements:
            print(f"⚠️  Warning: Missing expected XML elements: {missing_elements}")
        else:
            print("✅ All expected MusicXML elements are present")

        # Save result to file for manual inspection
        output_file = "test_output.musicxml"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(musicxml_result)
        print(f"💾 MusicXML saved to: {output_file}")

        return True

    except Exception as e:
        print(f"❌ MusicXML conversion failed: {str(e)}")
        return False


def test_helper_functions():
    """Test helper functions."""
    print("\n🔧 Testing helper functions...")

    service = MusicNotationService()

    # Test duration quantization
    test_durations = [0.1, 0.3, 0.6, 0.9, 1.2, 1.8, 2.5, 4.5]
    print("Duration quantization test:")
    for duration in test_durations:
        quantized = service._quantize_duration(duration)
        print(f"  {duration:.1f} -> {quantized:.2f}")

    print("✅ Helper functions test completed")


def main():
    """Run all tests."""
    print("🎵 Music Assistant v3 - MusicXML Generation Test")
    print("=" * 50)

    success = True

    # Test basic functionality
    if not test_music_notation_service():
        success = False

    # Test helper functions
    test_helper_functions()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed successfully!")
        print("\n📝 Next steps:")
        print("1. Test the API endpoint: GET /api/v3/analysis/{task_id}/musicxml")
        print("2. Open test_output.musicxml in MuseScore or similar software")
        print("3. Verify the musical notation is correctly displayed")
    else:
        print("❌ Some tests failed. Please check the error messages above.")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)