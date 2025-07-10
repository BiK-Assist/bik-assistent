from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse
import openai
import os
import uuid
import requests
from google.cloud import texttospeech
import json

# --- Umgebungsvariablen laden ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

# --- Google Cloud TTS konfigurieren ---
credentials_path = "/tmp/google_credentials.json"
with open(credentials_path, "w") as f:
    f.write(GOOGLE_CREDENTIALS_JSON)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

tts_client = texttospeech.TextToSpeechClient()

# --- Initialisierung ---
app = Flask(__name__)
openai.api_key = OPENAI_API_KEY

# --- Begrüßungstext ---
GREETING_TEXT = (
    "Hello and welcome to BiK Solution. "
    "This is your AI assistant. "
    "Please tell me your preferred language: English, Hrvatski or Deutsch."
)

# --- TTS: Text in Sprache umwandeln ---
def generate_speech(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join("static", filename)
    os.makedirs("static", exist_ok=True)
    with open(filepath, "wb") as out:
        out.write(response.audio_content)

    return request.url_root + f"static/{filename}"

# --- GPT antwortet auf das Transkript ---
def ask_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            { "role": "system", "content": "You are a multilingual customer service assistant." },
            { "role": "user", "content": prompt }
        ]
    )
    return response.choices[0].message.content.strip()

# --- OpenAI Whisper Transkription ---
def transcribe_audio(url):
    audio = requests.get(url + ".mp3").content
    with open("recording.mp3", "wb") as f:
        f.write(audio)

    with open("recording.mp3", "rb") as f:
        result = openai.Audio.transcribe("whisper-1", f)
    return result["text"]

# --- Twilio Voice Webhook ---
@app.route("/twilio-voice", methods=["POST"])
def twilio_voice():
    response = VoiceResponse()

    # Begrüßung generieren
    greeting_url = generate_speech(GREETING_TEXT)
    response.play(greeting_url)

    # Aufnahme starten
    response.record(
        action="/handle-recording",
        method="POST",
        max_length=10,
        play_beep=True
    )
    return str(response)

# --- Aufnahme behandeln ---
@app.route("/handle-recording", methods=["POST"])
def handle_recording():
    recording_url = request.form.get("RecordingUrl")
    print(f"📞 Aufnahme empfangen: {recording_url}")

    transcript = transcribe_audio(recording_url)
    print(f"✏️ Transkribierter Text: {transcript}")

    reply = ask_gpt(transcript)
    print(f"🤖 GPT-Antwort: {reply}")

    reply_url = generate_speech(reply)

    response = VoiceResponse()
    response.play(reply_url)
    return str(response)

# --- Startpunkt ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
