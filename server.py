from flask import Flask, request
from flask_cors import CORS
import time
import os
from flask import send_from_directory
from supabase import create_client

app = Flask(__name__)
CORS(app)

# --------------------------------------------------
# SUPABASE CONFIG
# --------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------------------------------
# SAVE RESULT (Autosuggest / Autocomplete / Instant)
# --------------------------------------------------
@app.route("/save", methods=["POST"])
def save():
    data = request.json

    supabase.table("results").insert({
        "variant": data.get("variant"),
        "time": data.get("time"),
        "errors": data.get("errors"),
        "device": data.get("device"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }).execute()

    return {"status": "saved"}

# --------------------------------------------------
# ADMIN PAGE
# --------------------------------------------------
@app.route("/admin")
def admin():
    response = supabase.table("results").select("*").order("id").execute()
    rows = response.data

    mobile_times, mobile_errors = [], []
    desktop_times, desktop_errors = [], []

    for r in rows:
        device = (r.get("device") or "").lower()
        if device == "mobile":
            mobile_times.append(r["time"])
            mobile_errors.append(r["errors"])
        elif device == "desktop":
            desktop_times.append(r["time"])
            desktop_errors.append(r["errors"])

    def avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0

    mobile_avg_time = avg(mobile_times)
    mobile_avg_errors = avg(mobile_errors)
    desktop_avg_time = avg(desktop_times)
    desktop_avg_errors = avg(desktop_errors)
    total_avg_time = avg(mobile_times + desktop_times)
    total_avg_errors = avg(mobile_errors + desktop_errors)

    html = """
    <h1 style='color:#4c6fff;'>📊 AUTOSUGGEST – ADMIN PANEL</h1>
    <style>
        body { font-family: Arial; padding: 20px; }
        table { border-collapse: collapse; width: 80%; margin-bottom: 25px; }
        th, td { border: 1px solid #555; padding: 6px 8px; text-align: center; }
        th { background: #4c6fff; color: white; }
        h2 { color: #4c6fff; margin-top: 30px; }
    </style>

    <h2>📄 DETAILLIERTE ERGEBNISSE</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Variante</th>
            <th>Zeit (s)</th>
            <th>Fehler</th>
            <th>Gerät</th>
            <th>Timestamp</th>
        </tr>
    """

    for r in rows:
        html += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{r['variant']}</td>
            <td>{r['time']}</td>
            <td>{r['errors']}</td>
            <td>{r['device']}</td>
            <td>{r['timestamp']}</td>
        </tr>
        """

    html += f"""
    </table>

    <h2>📱 MOBILE</h2>
    Durchschnittszeit: {mobile_avg_time} s<br>
    Durchschnittliche Fehler: {mobile_avg_errors}

    <h2>💻 DESKTOP</h2>
    Durchschnittszeit: {desktop_avg_time} s<br>
    Durchschnittliche Fehler: {desktop_avg_errors}

    <h2>📊 GESAMT</h2>
    Gesamt-Mittelwert Zeit: {total_avg_time} s<br>
    Gesamt-Fehlerdurchschnitt: {total_avg_errors}
    """

    return html

# --------------------------------------------------
# SAVE UMUX
# --------------------------------------------------
@app.route("/save_umux", methods=["POST"])
def save_umux():
    data = request.json

    umux_score = 50 + ((data["q1"] - data["q2"] + data["q3"] - data["q4"]) * 24)

    supabase.table("umux").insert({
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
    }).execute()

    return {"status": "saved", "score": umux_score}

# --------------------------------------------------
# PAGES
# --------------------------------------------------
@app.route("/")
def home():
    return send_from_directory(".", "autosuggest.html")

@app.route("/umux")
def umux_page():
    return send_from_directory(".", "umux.html")

# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)







