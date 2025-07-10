import os
from flask import Flask, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse
from elevenlabs.client import ElevenLabs

app = Flask(__name__)

# API-Key (nicht öffentlich posten)
eleven = ElevenLabs(api_key="sk_a0bab7fed7b0b7edc42310dcf5f87a8d9b94aeebd799d577")

GREETING_TEXT = (
    "Hello and welcome to BiK Solution. "
    "This is your AI assistant. "
    "Please tell me your preferred language: English, Hrvatski or Deutsch."
)

VOICE_ID = "Rachel"
AUDIO_FILE = "greeting.mp3"

@app.route('/')
def index():
    return "✅ BiK-Twilio-Agent läuft – Debug aktiviert."

@app.route("/twilio-voice", methods=["POST"])
def twilio_voice():
    try:
        if not os.path.exists(AUDIO_FILE):
            print("🔊 Erzeuge Audio über ElevenLabs...")
            audio_stream = eleven.text_to_speech.convert(
                voice_id=VOICE_ID,
                text=GREETING_TEXT,
                model_id="eleven_monolingual_v1",
                output_format="mp3"
            )
            audio_bytes = b"".join(audio_stream)

            with open(AUDIO_FILE, "wb") as f:
                f.write(audio_bytes)
            print("✅ Audio gespeichert.")

        response = VoiceResponse()
        response.play(f"{request.url_root}audio/{AUDIO_FILE}")
        return Response(str(response), mimetype="text/xml")

    except Exception as e:
        print(f"❌ Fehler in /twilio-voice: {e}")
        return Response(f"Internal Server Error: {e}", status=500)

@app.route("/audio/<filename>")
def serve_audio(filename):
    try:
        return send_file(filename, mimetype="audio/mpeg")
    except Exception as e:
        print(f"❌ Fehler beim Abspielen der Datei: {e}")
        return Response(f"Dateifehler: {e}", status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
