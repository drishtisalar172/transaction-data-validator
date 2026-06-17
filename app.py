from flask import Flask, render_template, request, send_file
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# Vercel temporary storage
UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

PHONE_RULES = {
    "India": 10,
    "Singapore": 8,
    "USA": 10,
    "Canada": 10,
    "Australia": 9,
    "UK": 11
}


def validate_phone(phone, country):
    phone = str(phone).strip()

    if country not in PHONE_RULES:
        return False

    return phone.isdigit() and len(phone) == PHONE_RULES[country]


def validate_date(date_text):
    try:
        datetime.strptime(str(date_text), "%Y-%m-%d")
        return True
    except:
        return False


def split_csv(df, chunk_size=100):
    chunk_number = 1

    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start:start + chunk_size]

        chunk.to_csv(
            f"{OUTPUT_FOLDER}/chunk_{chunk_number}.csv",
            index=False
        )

        chunk_number += 1


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def upload_file():

    if "file" not in request.files:
        return "No file uploaded"

    file = request.files["file"]

    if file.filename == "":
        return "No file selected"

    filepath = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    file.save(filepath)

    df = pd.read_csv(filepath)

    validation_results = []

    for _, row in df.iterrows():

        phone_valid = validate_phone(
            row["phone_number"],
            row["country"]
        )

        date_valid = validate_date(
            row["order_date"]
        )

        if phone_valid and date_valid:
            validation_results.append("Valid")
        else:
            validation_results.append("Invalid")

    df["validation_status"] = validation_results

    output_file = os.path.join(
        OUTPUT_FOLDER,
        "validated_" + file.filename
    )

    df.to_csv(output_file, index=False)

    split_csv(df)

    return send_file(
        output_file,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)