from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from google.cloud import texttospeech
import openai
import os
import uuid
import requests

# --- Google Credentials Datei setzen ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcloud-key.json"

# --- API-Keys ---
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Google Text-to-Speech Client ---
tts_client = texttospeech.TextToSpeechClient()

# --- Flask App ---
app = Flask(__name__)

# --- Begrüßungstext ---
GREETING_TEXT = (
    "Hallo und willkommen bei BiK Solution. "
    "Dies ist Dein KI-Assistent. "
    "Bitte nenne Deine bevorzugte Sprache: Deutsch, English oder Hrvatski."
)

@app.route("/twilio-voice", methods=["POST"])
def twilio_voice():
    response = VoiceResponse()

    # Begrüßung als Audio generieren
    greeting_url = generate_speech_google(GREETING_TEXT)
    response.play(greeting_url)

    # Sprachaufnahme starten
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
    print(f"📞 Aufnahme empfangen: {recording_url}")

    transcript = transcribe_audio(recording_url)
    print(f"✏️ Transkribiert: {transcript}")

    reply = ask_gpt(transcript)
    print(f"🤖 GPT-Antwort: {reply}")

    reply_url = generate_speech_google(reply)

    response = VoiceResponse()
    response.play(reply_url)
    return str(response)

def transcribe_audio(url):
    audio_data = requests.get(url + ".mp3").content
    with open("recording.mp3", "wb") as f:
        f.write(audio_data)
    with open("recording.mp3", "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    return transcript["text"]

def ask_gpt(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful multilingual assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content.strip()

def generate_speech_google(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="de-DE",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
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

    return request.url_root + "static/" + filename

# --- Start ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
