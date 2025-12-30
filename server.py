from flask import Flask, request
from flask_cors import CORS
import sqlite3
import time
import pandas as pd
import os
from flask import send_from_directory
from flask import send_file

app = Flask(__name__)
CORS(app)

# ------------------------------------------
# INIT DATABASE (with DEVICE column)
# ------------------------------------------
def init_db():
    supabase.table("results").insert(...)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant TEXT,
            time REAL,
            errors INTEGER,
            device TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------------------------------
# SAVE RESULT (with device)
# ------------------------------------------
@app.route("/save", methods=["POST"])
def save():
    data = request.json

    variant = data.get("variant")
    time_val = data.get("time")
    errors = data.get("errors")
    device = data.get("device")  # NEW

    conn = sqlite3.connect("results.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO results (variant, time, errors, device, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        variant,
        time_val,
        errors,
        device,
        time.strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return {"status": "saved"}

# ------------------------------------------
# ADMIN PAGE
# ------------------------------------------
@app.route("/admin")
def admin():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    c.execute("SELECT id, variant, time, errors, device, timestamp FROM results")
    rows = c.fetchall()
    conn.close()

    # Séparation mobile / desktop
    mobile_times = []
    mobile_errors = []
    desktop_times = []
    desktop_errors = []

    for _id, variant, t, e, device, ts in rows:
        device = str(device).lower()   # IMPORTANT : fix des stats ❗

        if device == "mobile":
            mobile_times.append(t)
            mobile_errors.append(e)
        elif device == "desktop":
            desktop_times.append(t)
            desktop_errors.append(e)

    def avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0

    mobile_avg_time = avg(mobile_times)
    mobile_avg_errors = avg(mobile_errors)

    desktop_avg_time = avg(desktop_times)
    desktop_avg_errors = avg(desktop_errors)

    total_avg_time = avg(mobile_times + desktop_times)
    total_avg_errors = avg(mobile_errors + desktop_errors)

    # -------------------------------------------
    # HTML + CSS
    # -------------------------------------------
    html = """
    <h1 style='color:#4c6fff;'>📊 AUTOSUGGEST – ADMIN PANEL</h1>

    <style>
        body { font-family: Arial; padding: 20px; }
        table {
            border-collapse: collapse;
            width: 60%;
            margin-bottom: 25px;
            font-size: 14px;
        }
        th, td {
            border: 1px solid #555;
            padding: 6px 8px;
            text-align: center;
        }
        th {
            background: #4c6fff;
            color: white;
            font-size: 14px;
        }
        h2 { color: #4c6fff; margin-top: 30px; }
        .small-table {
            width: 35%;
        }
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

    # TABLEAU DÉTAILLÉ
    for r in rows:
        html += "<tr>"
        for col in r:
            html += f"<td>{col}</td>"
        html += "</tr>"

    # TABLEAUX STATISTIQUES COMPACTS
    html += f"""
    </table>

    <h2>📱 MOBILE – Statistiken</h2>
    <table class="small-table">
        <tr><th>Metrik</th><th>Wert</th></tr>
        <tr><td>⏱ Durchschnittszeit</td><td>{mobile_avg_time} s</td></tr>
        <tr><td>❌ Durchschnittliche Fehler</td><td>{mobile_avg_errors}</td></tr>
    </table>

    <h2>💻 DESKTOP – Statistiken</h2>
    <table class="small-table">
        <tr><th>Metrik</th><th>Wert</th></tr>
        <tr><td>⏱ Durchschnittszeit</td><td>{desktop_avg_time} s</td></tr>
        <tr><td>❌ Durchschnittliche Fehler</td><td>{desktop_avg_errors}</td></tr>
    </table>

    <h2>📊 GESAMT (Mobile + Desktop)</h2>
    <table class="small-table">
        <tr><th>Metrik</th><th>Wert</th></tr>
        <tr><td>⏱ Gesamt-Mittelwert Zeit</td><td>{total_avg_time} s</td></tr>
        <tr><td>❌ Gesamt-Fehlerdurchschnitt</td><td>{total_avg_errors}</td></tr>
    </table>
    """

    return html
# ---------------------------------------------------------
#  SAVE UMUX – stocke les résultats dans un Excel séparé
# ---------------------------------------------------------
@app.route("/save_umux", methods=["POST"])
def save_umux():
    data = request.json

    q1 = data.get("q1")
    q2 = data.get("q2")
    q3 = data.get("q3")
    q4 = data.get("q4")
    good = data.get("good")
    bad = data.get("bad")
    sat = data.get("satisfaction")
    device = data.get("device")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    umux_score = 50 + ((q1 - q2 + q3 - q4) * 24)

    file = "umux_results.xlsx"

    new_row = {
        "Timestamp": timestamp,
        "Device": device,
        "Q1": q1,
        "Q2": q2,
        "Q3": q3,
        "Q4": q4,
        "UMUX Score": umux_score,
        "Good": good,
        "Bad": bad,
        "Satisfaction": sat
    }

    if os.path.exists(file):
        df = pd.read_excel(file)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])

    df.to_excel(file, index=False)

    return {"status":"saved", "score":umux_score}


@app.route("/umux")
def umux_page():
    return send_from_directory("", "umux.html")
@app.route("/")
def home():
    return send_from_directory(".", "autosuggest.html")
@app.route("/download_excel")
def download_excel():
    file_path = "umux_results.xlsx"
    return send_file(
        file_path,
        as_attachment=True
    )    
#------------------------------------------
# RUN
# ------------------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)




