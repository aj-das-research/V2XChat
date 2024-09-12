# File: audio_preprocessor.py

import os
import tempfile
import ffmpeg # type: ignore

class AudioPreprocessor:
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.mp4', '.m4a', '.aac', '.ogg', '.flac']

    @staticmethod
    def convert_to_wav(input_file, output_file=None):
        """
        Convert any supported audio format to a standard WAV format.
        
        :param input_file: Path to the input audio file
        :param output_file: Path to the output WAV file (optional)
        :return: Path to the output WAV file
        """
        if output_file is None:
            # Create a temporary file with .wav extension
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            output_file = temp_file.name
            temp_file.close()

        try:
            # Convert to standard WAV format
            (
                ffmpeg
                .input(input_file)
                .output(output_file, acodec='pcm_s16le', ac=1, ar='16000')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            return output_file

        except ffmpeg.Error as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise

    @classmethod
    def is_supported_format(cls, filename):
        """Check if the file format is supported."""
        return any(filename.lower().endswith(ext) for ext in cls.SUPPORTED_FORMATS)