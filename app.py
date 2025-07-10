from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import os
import uuid
from google.cloud import texttospeech
import openai
import requests

# API-Key für OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask App
app = Flask(__name__)

# Begrüßungstext
GREETING_TEXT = (
    "Hello and welcome to BiK Solution. "
    "This is your AI assistant. "
    "Please tell me your preferred language: English, Hrvatski or Deutsch."
)

# --- Google Cloud TTS ---
def generate_speech_google(text):
    client = texttospeech.TextToSpeechClient()
    
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    
    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config
    )
    
    os.makedirs("static", exist_ok=True)
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join("static", filename)
    
    with open(filepath, "wb") as out:
        out.write(response.audio_content)
    
    return request.url_root + f"static/{filename}"

@app.route("/twilio-voice", methods=["POST"])
def twilio_voice():
    response = VoiceResponse()
    greeting_url = generate_speech_google(GREETING_TEXT)
    response.play(greeting_url)
    
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
    print(f"📞 Aufnahme: {recording_url}")

    # Download und Transkription mit Whisper
    audio_data = requests.get(recording_url + ".mp3").content
    with open("recording.mp3", "wb") as f:
        f.write(audio_data)

    with open("recording.mp3", "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)["text"]
    print(f"✏️ Transkript: {transcript}")

    # GPT-Antwort
    reply = ask_gpt(transcript)
    print(f"🤖 Antwort: {reply}")

    # Antwort generieren
    reply_url = generate_speech_google(reply)

    # Twilio Antwort
    response = VoiceResponse()
    response.play(reply_url)
    return str(response)

def ask_gpt(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a multilingual assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content.strip()

# Flask starten
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
