from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

EXCEL_FILE = "batch_log.xlsx"

@app.route("/api/dashboard")
def dashboard():

    df = pd.read_excel(EXCEL_FILE)

    total = len(df)
    states = df['State_of_Origin'].value_counts().to_dict()
    avg_conf = round(df['Confidence'].astype(float).mean(), 2)

    recent = df.tail(10).to_dict(orient="records")

    return jsonify({
        "total": total,
        "states": states,
        "avg_confidence": avg_conf,
        "recent": recent
    })

if __name__ == "__main__":
    app.run(debug=True)