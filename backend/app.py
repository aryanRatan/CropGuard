from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import base64

app = Flask(__name__)
CORS(app)

# 🔹 Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# 🔹 CONFIG
GEMINI_API_KEY = "AIzaSyC1hfvFQaFLO_eY4oP7EifLTvkTtitFyKY"
GEMINI_MODEL = "gemini-2.5-flash"

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


@app.route('/predict', methods=['POST'])
def predict():
    try:
        text_input = request.form.get("text")
        file = request.files.get("file")

        if not text_input and not file:
            return jsonify({"error": "No input provided"}), 400

        logging.info("Request received")

        parts = []

        # 🔹 Add text if exists
        if text_input:
            parts.append({
                "text": f"User symptoms: {text_input}"
            })

        # 🔹 Add image if exists
        if file and file.filename != "":
            image_bytes = file.read()

            if image_bytes:
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")

                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_base64
                    }
                })

        # 🔹 Final prompt
        parts.insert(0, {
            "text": """
             A plant leaf is labeled as: {label}.

             Give output in this EXACT format:

             Disease: <name>

             Symptoms:
             - point 1
             - point 2

             Causes:
             - point 1
             - point 2

             Treatment:
             - step 1
             - step 2

             Prevention:
             - tip 1
             - tip 2

             Keep it short and clean.
            """
        })

        payload = {
            "contents": [
                {
                    "parts": parts
                }
            ]
        }

        try:
            response = requests.post(GEMINI_URL, json=payload, timeout=15)

            if response.status_code != 200:
                logging.error(response.text)
                return jsonify({"error": "Gemini API failed"}), 502

            result = response.json()

            explanation = result["candidates"][0]["content"]["parts"][0]["text"]

            print("\n===== AI RESPONSE =====")
            print(explanation)
            print("=======================\n")

            return jsonify({
                "status": "success",
                "result": explanation
            }), 200

        except Exception as e:
            logging.exception("Gemini error")
            return jsonify({"error": "Gemini request failed"}), 500

    except Exception as e:
        logging.exception("Internal error")
        return jsonify({"error": "Internal server error"}), 500


import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))