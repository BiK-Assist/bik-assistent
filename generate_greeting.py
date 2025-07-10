import os
from elevenlabs.client import ElevenLabs

# Deinen API-Schlüssel hier einfügen
eleven = ElevenLabs(api_key="sk_a0bab7fed7b0b7edc42310dcf5f87a8d9b94aeebd799d577")

GREETING_TEXT = (
    "Hello and welcome to BiK Solution. "
    "This is your AI assistant. "
    "Please tell me your preferred language: English, Hrvatski or Deutsch."
)

# Audio-Datei erzeugen
audio_stream = eleven.text_to_speech.convert(
    voice_id="EXAVITQu4vr4xnSDxMaL",
    text=GREETING_TEXT,
    model_id="eleven_monolingual_v1",
    output_format="mp3_44100_128"  # gültiges Format
)

audio_bytes = b"".join(audio_stream)

# Speichern im Verzeichnis "static"
with open("static/greeting.mp3", "wb") as f:
    f.write(audio_bytes)

print("✅ greeting.mp3 erfolgreich erstellt.")
