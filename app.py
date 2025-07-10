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
    "Welcome to BiK Solution. This is your AI assistant. Please tell me your preferred language: English, Hrvatski or Deutsch."
)

@app.route("/twilio-voice", methods=["POST"])
def twilio_voice():
    response = VoiceResponse()
    greeting_url = generate_speech_google(GREETING_TEXT, language_code="en-US")
    response.play(greeting_url)
    response.record(action="/handle-recording", method="POST", max_length=20, play_beep=True)
    return str(response)

@app.route("/handle-recording", methods=["POST"])
def handle_recording():
    recording_url = request.form.get("RecordingUrl")
    transcript = transcribe_audio(recording_url)
    detected_language = detect_language(transcript)
    reply = ask_gpt(transcript, detected_language)
    reply_url = generate_speech_google(reply, language_code=detected_language)
    response = VoiceResponse()
    response.play(reply_url)
    return str(response)

def transcribe_audio(url):
    audio_data = requests.get(url + ".mp3").content
    with open("recording.mp3", "wb") as f:
        f.write(audio_data)
    with open("recording.mp3", "rb") as f:
        transcript_obj = openai.audio.transcriptions.create(model="whisper-1", file=f)
    return transcript_obj.text

def detect_language(text):
    if any(word in text.lower() for word in ["hello", "please", "english"]):
        return "en-US"
    elif any(word in text.lower() for word in ["dobar", "hrvatski"]):
        return "hr-HR"
    elif any(word in text.lower() for word in ["hallo", "deutsch"]):
        return "de-DE"
    else:
        return "en-US"

def ask_gpt(prompt, language_code):
    system_prompt = "You are a helpful multilingual assistant. Answer in the detected language."
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

def generate_speech_google(text, language_code):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join("static", filename)
    os.makedirs("static", exist_ok=True)
    with open(filepath, "wb") as out:
        out.write(response.audio_content)
    return request.url_root + "static/" + filename

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
