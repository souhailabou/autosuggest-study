from flask import Flask, request, send_from_directory
from flask_cors import CORS
import os
import time
import requests

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

SUPABASE_REST = f"{SUPABASE_URL}/rest/v1"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# ------------------------------------------------
# SAVE SEARCH RESULT
# ------------------------------------------------
@app.route("/save", methods=["POST"])
def save():
    try:
        data = request.get_json(force=True)

        payload = {
            "variant": data["variant"],
            "time": float(data["time"]),
            "errors": int(data["errors"]),
            "device": data["device"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        r = requests.post(
            f"{SUPABASE_REST}/results",
            headers=HEADERS,
            json=payload,
            timeout=10
        )

        if not r.ok:
            print("❌ SUPABASE ERROR:", r.text)
            return {"error": r.text}, 500

        return {"status": "saved"}, 200

    except Exception as e:
        print("❌ SERVER ERROR:", str(e))
        return {"error": str(e)}, 500


# ------------------------------------------------
# SAVE UMUX
# ------------------------------------------------
@app.route("/save_umux", methods=["POST"])
def save_umux():
    try:
        data = request.get_json(force=True)

        umux_score = 50 + ((data["q1"] - data["q2"] + data["q3"] - data["q4"]) * 24)

        payload = {
            "q1": data["q1"],
            "q2": data["q2"],
            "q3": data["q3"],
            "q4": data["q4"],
            "good": data.get("feedback_pos"),
            "bad": data.get("feedback_neg"),
            "satisfaction": data.get("satisfaction"),
            "device": data.get("device"),
            "umux_score": umux_score,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        r = requests.post(
            f"{SUPABASE_REST}/umux",
            headers=HEADERS,
            json=payload,
            timeout=10
        )

        if not r.ok:
            print("❌ SUPABASE ERROR:", r.text)
            return {"error": r.text}, 500

        return {"status": "saved", "score": umux_score}, 200

    except Exception as e:
        print("❌ SERVER ERROR:", str(e))
        return {"error": str(e)}, 500


# ------------------------------------------------
# STATIC FILES
# ------------------------------------------------
@app.route("/")
def home():
    return send_from_directory(".", "autosuggest.html")

@app.route("/umux")
def umux():
    return send_from_directory(".", "umux.html")


# ------------------------------------------------
# RUN
# ------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)












