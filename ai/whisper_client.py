

from openai import OpenAI
import os

client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY")
)

def transcribe_audio(audio_path):
    with open(audio_path, 'rb') as audio_file:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file = audio_file
        )
    
    return result.text
