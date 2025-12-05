
from elevenlabs import ElevenLabs
import os

client = ElevenLabs(
    api_key = os.getenv("ELEVENLABS_API_KEY")
)

def synthesize_speech(reply_text):
    voice_id = "nzeAacJi50IvxcyDnMXa"
    
    response = client.text_to_speech.convert(
        voice_id = voice_id,
        model_id = "eleven_multilingual_v2",
        text = reply_text,
        output_format="pcm_16000"
    )
    
    audio_bytes = b"".join(response)
    
    output_path = "robot_reply.pcm"
    with open(output_path, "wb") as reply_path:
        reply_path.write(audio_bytes)
    
    return output_path