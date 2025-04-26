from flask import Flask, render_template, request, jsonify
from ai import get_ai_reply
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data["message"]

    try:
        print(f"📥 Message: {user_message}")
        ai_reply = get_ai_reply(user_message)
        return jsonify({"reply": ai_reply})
    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"reply": "⚠️ Sorry, an error occurred."})

if __name__ == "__main__":
    app.run(port=5001)
