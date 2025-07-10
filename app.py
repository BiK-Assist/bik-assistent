from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
import datetime

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    response = VoiceResponse()
    now = datetime.datetime.now().strftime("%A, %d.%m.%Y %H:%M")

    response.say(f"Willkommen beim BiK Assistenten. Heute ist {now}. Ich bin Dein persönlicher KI-Telefonagent.", language="de-DE")
    response.pause(length=1)
    response.say("Momentan ist die Sprachverarbeitung noch in Vorbereitung. Du wirst bald mit mir sprechen können.", language="de-DE")
    return Response(str(response), mimetype="text/xml")

@app.route("/")
def hello():
    return "BiK Assistent läuft."

if __name__ == "__main__":
    app.run()
