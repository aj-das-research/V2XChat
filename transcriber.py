# File: transcriber.py

import os
import json
import tempfile
import requests
import time
import io
import threading
import queue
import wave
import numpy as np
from audio_preprocessor import AudioPreprocessor
from language_identifier import identify_language

class SarvamTranscriber:
    API_KEY = "e8ece64e-6ff8-495b-9159-9d034c3f83dc"
    CHUNK_LENGTH_MS = 30000  # 30 seconds
    MAX_AUDIO_LENGTH_MS = 1800000  # 30 minutes

    def __init__(self):
        self.transcription_queue = queue.Queue()
        self.translation_queue = queue.Queue()
        self.is_processing = False
        self.total_chunks = 0
        self.processed_chunks = 0
        self.language_code = None

    @staticmethod
    def split_audio(file_path, chunk_length_ms=30000):
        with wave.open(file_path, 'rb') as wf:
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            
            total_duration_ms = (n_frames / framerate) * 1000
            if total_duration_ms > SarvamTranscriber.MAX_AUDIO_LENGTH_MS:
                raise ValueError(f"Audio file is too long. Maximum length is {SarvamTranscriber.MAX_AUDIO_LENGTH_MS/60000} minutes.")
            
            chunks = []
            for i in range(0, n_frames, int(framerate * chunk_length_ms / 1000)):
                wf.setpos(i)
                chunk_frames = wf.readframes(int(framerate * chunk_length_ms / 1000))
                chunk = io.BytesIO()
                with wave.open(chunk, 'wb') as chunk_wf:
                    chunk_wf.setnchannels(wf.getnchannels())
                    chunk_wf.setsampwidth(wf.getsampwidth())
                    chunk_wf.setframerate(framerate)
                    chunk_wf.writeframes(chunk_frames)
                chunk.seek(0)
                chunks.append(chunk)
            
            return chunks

    @classmethod
    def api_request(cls, url, files, data, headers, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"Error: {e}")
                    return None
            time.sleep(2 ** attempt)

    def process_audio_chunk(self, chunk, is_translation):
        url = "https://api.sarvam.ai/speech-to-text-translate" if is_translation else "https://api.sarvam.ai/speech-to-text"
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(chunk.getvalue())
            temp_file_path = temp_file.name

        with open(temp_file_path, 'rb') as file:
            files = {'file': ('chunk.wav', file, 'audio/wav')}
            data = {'language_code': self.language_code, 'model': 'saarika:v1'} if not is_translation else {'model': 'saaras:v1'}
            headers = {"api-subscription-key": self.API_KEY}

            result = self.api_request(url, files, data, headers)

        os.unlink(temp_file_path)
        self.processed_chunks += 1
        return result

    def process_file(self, file_path):
        self.is_processing = True
        
        # Identify the language
        self.language_code = identify_language(file_path)
        print(f"Identified language code: {self.language_code}")

        audio_chunks = self.split_audio(file_path)
        self.total_chunks = len(audio_chunks)

        def process_chunks():
            for chunk in audio_chunks:
                transcription = self.process_audio_chunk(chunk, is_translation=False)
                translation = self.process_audio_chunk(chunk, is_translation=True)
                if transcription:
                    self.transcription_queue.put(transcription.get('transcript', ''))
                if translation:
                    self.translation_queue.put(translation.get('transcript', ''))
            self.is_processing = False

        threading.Thread(target=process_chunks, daemon=True).start()

    def get_transcription(self):
        return self.transcription_queue.get() if not self.transcription_queue.empty() else None

    def get_translation(self):
        return self.translation_queue.get() if not self.translation_queue.empty() else None

    def is_finished(self):
        return not self.is_processing and self.transcription_queue.empty() and self.translation_queue.empty()

    def get_progress(self):
        return self.processed_chunks / (self.total_chunks * 2) if self.total_chunks > 0 else 0

    def get_language_code(self):
        return self.language_code