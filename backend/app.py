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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


@app.route('/')
def home():
    return "CropGuard Backend is Running 🚀"

@app.route('/predict', methods=['POST'])
def predict():
    try:
        text_input = request.form.get("text")
        file = request.files.get("file")

        if not text_input and not file:
            return jsonify({"error": "No input provided"}), 400

        parts = []

        if text_input:
            parts.append({"text": f"User input: {text_input}"})

        if file and file.filename != "":
            image_bytes = file.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_base64
                }
            })

        # 🔥 BETTER PROMPT
        parts.insert(0, {
            "text": """
        Analyse the input (text and/or image).
            if user asks for diseases of a crop:
            -List 4-6 common diseases for that crop.
            -For each disease, provide:
            -short symptoms
            -treatment steps
            -prevention tips
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

        payload = {"contents": [{"parts": parts}]}

        response = requests.post(GEMINI_URL, json=payload, timeout=20)

        print("RAW RESPONSE:", response.text)

        if response.status_code != 200:
            return jsonify({"error": response.text}), 500

        try:
            result = response.json()

            explanation = (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "No response generated")
            )

        except Exception:
            return jsonify({"error": "Parsing failed"}), 500

        return jsonify({
            "status": "success",
            "result": explanation
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))