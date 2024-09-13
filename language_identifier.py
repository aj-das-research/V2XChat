# File: language_identifier.py

import os
from groq import Groq
from dotenv import load_dotenv

class LanguageIdentifier:
    def __init__(self):
        load_dotenv()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        print(f"Groq API Key: {os.getenv('GROQ_API_KEY')[:5]}...") # Print first 5 characters of API key

    def identify_language(self, file_path):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in ['.mp3', '.wav']:
            print(f"Unsupported file format: {file_extension}")
            return None

        try:
            with open(file_path, "rb") as file:
                print(f"File opened successfully: {file_path}")
                response = self.client.audio.transcriptions.create(
                    file=(file_path, file.read()),
                    model="whisper-large-v3",
                    prompt = "Identify the language of this audio if it is Hindi, Gujrati, Bengali or English. Please give attention to the greetings and words carefully to recognise the language. Respond with only the two-letter language code (e.g., 'en' for English, 'hi' for Hindi).",
                    response_format="text",
                    temperature=0.0
                )
            print(f"Raw API response: {response}")
            
            identified_language = response.lower() if isinstance(response, str) else response.text.lower()
            print(f"Identified language (lowercase): {identified_language}")
            
            language_mapping = {
                "hindi": "hi-IN",
                "bengali": "bn-IN",
                "kannada": "kn-IN",
                "malayalam": "ml-IN",
                "marathi": "mr-IN",
                "odia": "od-IN",
                "punjabi": "pa-IN",
                "tamil": "ta-IN",
                "telugu": "te-IN",
                "gujarati": "gu-IN",
                "english": "en-IN"
            }
            
            for lang, code in language_mapping.items():
                if lang in identified_language:
                    print(f"Matched language: {lang}")
                    return code
            
            print(f"Unsupported language identified: {identified_language}")
            return "hi-IN"  # Default to Hindi if language is not in our mapping
        except Exception as e:
            print(f"An error occurred during language identification: {str(e)}")
            return "hi-IN"  # Default to Hindi in case of any error

def identify_language(audio_path):
    identifier = LanguageIdentifier()
    return identifier.identify_language(audio_path)