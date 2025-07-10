from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

input_text = texttospeech.SynthesisInput(text="Hello and welcome to BiK Solution. Please say your language: English, Hrvatski or Deutsch.")

voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

response = client.synthesize_speech(
    input=input_text,
    voice=voice,
    audio_config=audio_config
)

with open("static/greeting.mp3", "wb") as out:
    out.write(response.audio_content)
    print("✅ greeting.mp3 erfolgreich gespeichert")
