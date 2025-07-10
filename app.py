from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse
import openai
from elevenlabs.client import ElevenLabs
import os
import uuid

# --- API-Keys aus Umgebungsvariablen laden ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

# --- Initialisierung ---
app = Flask(__name__)
openai.api_key = OPENAI_API_KEY
eleven = ElevenLabs(api_key=ELEVEN_API_KEY)

# --- Begrüßungstext (Initialausgabe) ---
GREETING_TEXT = (
    "Hello and welcome to BiK Solution. "
    "This is your AI assistant. "
    "Please tell me your preferred language: English, Hrvatski or Deutsch."
)

VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Beispielstimme ElevenLabs

@app.route("/twilio-voice", methods=["POST"])
def twilio_voice():
    response = VoiceResponse()
    
    # Begrüßung erzeugen
    greeting_path = generate_speech(GREETING_TEXT)
    response.play(greeting_path)
    
    # Aufnahme starten
    response.record(
        action="/handle-recording",
        method="POST",
        max_length=10,
        play_beep=True
    )
    return str(response)

@app.route("/handle-recording", methods=["POST"])
def handle_recording():
    recording_url = request.form.get("RecordingUrl")
    print(f"📞 Aufnahme erhalten: {recording_url}")

    # Nutzung des OpenAI Whisper API zur Transkription
    transcript = transcribe_audio(recording_url)
    print(f"✏️ Transkript: {transcript}")

    # GPT antwortet
    reply = ask_gpt(transcript)
    print(f"🤖 Antwort: {reply}")

    # Antwort mit ElevenLabs generieren
    reply_path = generate_speech(reply)

    # Twilio-Antwort senden
    response = VoiceResponse()
    response.play(reply_path)
    return str(response)

# --- GPT antwortet auf das gesprochene Anliegen ---
def ask_gpt(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            { "role": "system", "content": "You are a multilingual customer service assistant." },
            { "role": "user", "content": prompt }
        ]
    )
    return completion.choices[0].message.content.strip()

# --- Sprachsynthese mit ElevenLabs ---
def generate_speech(text):
    audio_stream = eleven.text_to_speech.convert(
        voice_id=VOICE_ID,
        text=text,
        model_id="eleven_monolingual_v1",
        output_format="mp3_44100_128"
    )
    audio_bytes = b"".join(audio_stream)
    
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join("static", filename)

    os.makedirs("static", exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)
    
    return request.url_root + f"static/{filename}"

# --- Transkription mit OpenAI Whisper (per Audio-URL) ---
def transcribe_audio(url):
    import requests
    audio_data = requests.get(url + ".mp3").content
    with open("recording.mp3", "wb") as f:
        f.write(audio_data)

    with open("recording.mp3", "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    return transcript["text"]

# --- Start ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
