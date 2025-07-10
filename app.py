import os
from flask import Flask, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse
from elevenlabs.client import ElevenLabs

app = Flask(__name__)

# API-Key setzen
eleven = ElevenLabs(
    api_key="sk_a0bab7fed7b0b7edc42310dcf5f87a8d9b94aeebd799d577"  # sicher speichern in .env später empfohlen
)

GREETING_TEXT = (
    "Hello and welcome to BiK Solution. "
    "This is your AI assistant. "
    "Please tell me your preferred language: English, Hrvatski or Deutsch."
)

VOICE_ID = "Rachel"
AUDIO_FILE = "greeting.mp3"

@app.route('/')
def index():
    return "✅ BiK-Twilio-Agent läuft auf Render.com"

@app.route("/twilio-voice", methods=["POST"])
def twilio_voice():
    # Audio generieren, falls noch nicht vorhanden
    if not os.path.exists(AUDIO_FILE):
        audio = eleven.generate(
            text=GREETING_TEXT,
            voice=VOICE_ID,
            model="eleven_monolingual_v1",
        )
        with open(AUDIO_FILE, "wb") as f:
            f.write(audio)

    # Twilio XML-Antwort zum Abspielen der Datei
    response = VoiceResponse()
    response.play(f"{request.url_root}audio/{AUDIO_FILE}")
    return Response(str(response), mimetype="text/xml")

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_file(filename, mimetype="audio/mpeg")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
