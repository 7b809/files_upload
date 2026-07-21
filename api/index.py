from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from io import BytesIO
import base64, json, os
from utils.github_upload import upload_to_github
from utils.crypto_utils import encrypt_bytes
from dotenv import load_dotenv
from werkzeug.datastructures import FileStorage

load_dotenv()


# ===========================
# Secrets Configuration
# ===========================
app_data = os.getenv("app_data")

if not app_data:
    raise RuntimeError("Environment variable 'app_data' not found!")

secrets = json.loads(app_data)

app = Flask(__name__, template_folder="templates")

CORS(app, resources={r"/*": {"origins": "*"}})


# ==================================
# Single endpoint for sequential chunks
# ==================================
@app.route("/upload_file", methods=["POST"])
def upload_file():
    try:
        data = request.get_json()

        file_name = data.get("file_name")
        total_chunks = data.get("total_chunks")
        chunks = data.get("chunks")

        secure_upload = data.get("secure_upload", False)
        encryption_key = data.get("encryption_key")

        # ===========================
        # Validate request
        # ===========================
        if not all([file_name, total_chunks, chunks]):
            return jsonify({
                "success": False,
                "error": "Missing parameters"
            }), 400

        # ===========================
        # Validate secure upload
        # ===========================
        if secure_upload:
            if not file_name.lower().endswith(".zip"):
                return jsonify({
                    "success": False,
                    "error": "Secure encrypted upload is only allowed for ZIP files"
                }), 400

            if not encryption_key:
                return jsonify({
                    "success": False,
                    "error": "Encryption string is required for secure upload"
                }), 400

        # ===========================
        # Combine chunks in memory
        # ===========================
        combined = BytesIO()

        for chunk_data in chunks:
            chunk_bytes = base64.b64decode(chunk_data)
            combined.write(chunk_bytes)

        raw_file_bytes = combined.getvalue()

        # ===========================
        # Encrypt ZIP if selected
        # ===========================
        if secure_upload:
            encrypted_bytes = encrypt_bytes(raw_file_bytes, encryption_key)

            upload_stream = BytesIO(encrypted_bytes)
            upload_file_name = f"{file_name}.enc"
        else:
            upload_stream = BytesIO(raw_file_bytes)
            upload_file_name = file_name

        upload_stream.seek(0)

        # ===========================
        # Upload to GitHub directly
        # ===========================
        uploaded_file = FileStorage(
            stream=upload_stream,
            filename=upload_file_name
        )

        result = upload_to_github(
            uploaded_file,
            secrets["github_repo"],
            secrets["branch"],
            secrets["pat_token"]
        )

        if not result.get("success"):
            return jsonify({
                "success": False,
                "error": result.get("error", "GitHub upload failed")
            }), 500

        return jsonify({
            "success": True,
            "encrypted": secure_upload,
            "uploaded_file": upload_file_name,
            "result": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================================
# Home route — Serve index.html
# ==================================
@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
