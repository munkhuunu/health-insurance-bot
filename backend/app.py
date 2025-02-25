from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# ✅ Rasa API зөв хаягтай эсэхийг шалгах
RASA_SERVER_URL = "http://127.0.0.1:5005/webhooks/rest/webhook"

@app.route("/chat", methods=["POST"])
def chat():
    """Flask API Rasa chatbot-той холбогдож байгааг шалгах."""
    user_input = request.json.get("message")
    sender_id = request.json.get("sender", "user")

    payload = {"sender": sender_id, "message": user_input}

    try:
        # ✅ Rasa API руу хүсэлт илгээх
        rasa_response = requests.post(RASA_SERVER_URL, json=payload, timeout=10)
        rasa_response.raise_for_status()

        messages = rasa_response.json()
        bot_responses = [msg.get("text", "") for msg in messages if "text" in msg]

        if not bot_responses:
            bot_responses = ["Уучлаарай, би таны асуултад хариулж чадсангүй."]

        return jsonify({"response": bot_responses})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Rasa chatbot-д холбогдож чадсангүй: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
