import os
from flask import Flask, request, Response, send_file
from elevenlabs import generate, save, set_api_key
from twilio.twiml.voice_response import VoiceResponse

# Deine ElevenLabs API
set_api_key("sk_a0bab7fed7b0b7edc42310dcf5f87a8d9b94aeebd799d577")  # <-- ggf. per .env sicher speichern

app = Flask(__name__)

# Begrüßungstext
GREETING_TEXT = (
    "Hello and welcome to BiK Solution. "
    "This is your AI assistant. "
    "Please tell me your preferred language: Croatian, German, or English."
)

VOICE_ID = "Rachel"  # Englischsprachige Standardstimme (kann angepasst werden)
AUDIO_FILE = "greeting.mp3"

@app.route('/')
def index():
    return "✅ BiK-Twilio-Agent läuft auf Render.com"

@app.route("/twilio-voice", methods=["POST"])
def twilio_voice():
    # Falls MP3 noch nicht generiert wurde → jetzt erzeugen
    if not os.path.exists(AUDIO_FILE):
        audio = generate(
            text=GREETING_TEXT,
            voice=VOICE_ID,
            model="eleven_monolingual_v1"
        )
        save(audio, AUDIO_FILE)

    # Twilio-Anrufantwort: MP3 abspielen
    response = VoiceResponse()
    response.play(f"{request.url_root}audio/{AUDIO_FILE}")
    return Response(str(response), mimetype="text/xml")

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_file(filename, mimetype="audio/mpeg")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
