from flask import Flask, render_template, request, redirect, session, jsonify
import pandas as pd
import joblib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "crime_tracker_secret"

# -----------------------------
# LOAD DATASET
# -----------------------------
DATA_FILE = "Data/South Crime Details.xlsx"
df = pd.read_excel(DATA_FILE)

# Normalize column names
df.columns = df.columns.str.strip().str.lower()

# Ensure correct datatypes
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df = df.dropna(subset=["latitude", "longitude"])

# Convert date/time safely
df["date"] = df["date"].astype(str)
df["time"] = df["time"].astype(str)

# Create station list for dropdown
station_list = sorted(df["police station"].dropna().unique().tolist())

# -----------------------------
# LOAD MODEL (PIPELINE)
# -----------------------------
model = joblib.load("model.pkl")

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form.get("email")
        return redirect("/dashboard")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        return redirect("/login")
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", police_stations=station_list)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -----------------------------
# API: Predict Risk
# -----------------------------
@app.route("/api/predict_risk", methods=["POST"])
def predict_risk():
    try:
        data = request.json

        police_station = data.get("police_station")
        date_str = data.get("date")   # yyyy-mm-dd
        time_str = data.get("time")   # HH:MM
        crime_type = data.get("type", "Unknown")  # default if not provided

        if not police_station or not date_str or not time_str:
            return jsonify({"error": "Missing inputs"}), 400

        # Date parsing
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        month = date_obj.month
        dayofweek = date_obj.weekday()  # Monday=0 ... Sunday=6

        # Time parsing
        hour = int(time_str.split(":")[0])

        # ✅ Input must match your model training columns
        X_input = pd.DataFrame([{
            "Police Station": police_station,
            "month": month,
            "dayofweek": dayofweek,
            "Type": crime_type
        }])

        pred = model.predict(X_input)[0]

        risk_labels = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
        risk_text = risk_labels.get(int(pred), str(pred))

        return jsonify({"risk": risk_text})

    except Exception as e:
        print("Prediction Error:", str(e))
        return jsonify({"error": str(e)}), 500


# -----------------------------
# API: Heatmap points
# -----------------------------
@app.route("/api/heatmap", methods=["GET"])
def heatmap():
    points = df[["latitude", "longitude"]].head(5000).values.tolist()
    return jsonify(points)


# -----------------------------
# API: Crimes by station markers
# -----------------------------
@app.route("/api/crimes", methods=["GET"])
def crimes():
    station = request.args.get("station")

    if not station:
        return jsonify([])

    filtered = df[df["police station"] == station].head(300)

    result = filtered[["place", "latitude", "longitude", "date", "time"]].to_dict(orient="records")
    return jsonify(result)


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
