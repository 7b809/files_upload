from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from io import BytesIO
import base64, json, os
from .utils.github_upload import upload_to_github

# ===========================
# 🔒 Secrets Configuration
# ===========================
app_data = os.getenv("app_data")
if not app_data:
    raise RuntimeError("Environment variable 'app_data' not found!")

secrets = json.loads(app_data)

app = Flask(__name__, template_folder="templates")  # 👈 use templates folder
CORS(app, resources={r"/*": {"origins": "*"}})


# ==================================
# 🚀 Single endpoint for sequential chunks
# ==================================
@app.route("/upload_zip", methods=["POST"])
def upload_zip():
    try:
        data = request.get_json()
        file_id = data.get("file_id")
        total_chunks = data.get("total_chunks")
        chunks = data.get("chunks")  # List of base64 encoded strings

        if not all([file_id, total_chunks, chunks]):
            return jsonify({"success": False, "error": "Missing parameters"}), 400

        # Combine chunks in memory
        combined = BytesIO()
        for idx, chunk_data in enumerate(chunks):
            chunk_bytes = base64.b64decode(chunk_data)
            combined.write(chunk_bytes)

        combined.seek(0)

        # Upload to GitHub directly
        from werkzeug.datastructures import FileStorage
        zip_file = FileStorage(stream=combined, filename=f"{file_id}.zip")

        result = upload_to_github(
            zip_file,
            secrets["github_repo"],
            secrets["branch"],
            secrets["pat_token"]
        )

        return jsonify({"success": True, "result": result})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================================
# 🏠 Home route — Serve index.html
# ==================================
@app.route("/")
def home():
    return render_template("index.html")  # 👈 renders HTML from /templates/index.html
