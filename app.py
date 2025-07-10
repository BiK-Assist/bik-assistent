from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import os

app = Flask(__name__)

@app.route("/twilio-voice", methods=["POST"])
def twilio_voice():
    response = VoiceResponse()
    gather = Gather(input="speech", action="/handle-language", timeout=5, language="en-US")
    gather.say("Welcome to BiK Solution. Please tell me in wich language do you want support: English, Hrvatski or Deutsch.")
    response.append(gather)
    response.say("We did not receive your input. Goodbye!")
    return str(response)

@app.route("/handle-language", methods=["POST"])
def handle_language():
    speech_result = request.form.get("SpeechResult", "").lower()
    print(f"User said: {speech_result}")

    response = VoiceResponse()

    if "english" in speech_result:
        response.say("You selected English.", language="en-US")
    elif "deutsch" in speech_result or "german" in speech_result:
        response.say("Du hast Deutsch gewählt.", language="de-DE")
    elif "hrvatski" in speech_result or "croatian" in speech_result:
        response.say("Odabrali ste Hrvatski.", language="hr-HR")
    else:
        response.say("Sorry, I did not understand.", language="en-US")

    return str(response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
