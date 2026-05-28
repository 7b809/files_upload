from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from io import BytesIO
import base64, json, os
from .utils.github_upload import upload_to_github
from dotenv import load_dotenv

load_dotenv()


# ===========================
# 🔒 Secrets Configuration
# ===========================
app_data = os.getenv("app_data")

if not app_data:
    raise RuntimeError("Environment variable 'app_data' not found!")

secrets = json.loads(app_data)

app = Flask(__name__, template_folder="templates")

CORS(app, resources={r"/*": {"origins": "*"}})

# ==================================
# 🚀 Single endpoint for sequential chunks
# ==================================
@app.route("/upload_file", methods=["POST"])
def upload_file():

    try:

        data = request.get_json()

        file_name = data.get("file_name")

        total_chunks = data.get("total_chunks")

        chunks = data.get("chunks")

        # ===========================
        # Validate request
        # ===========================
        if not all([file_name, total_chunks, chunks]):

            return jsonify({
                "success": False,
                "error": "Missing parameters"
            }), 400

        # ===========================
        # Combine chunks in memory
        # ===========================
        combined = BytesIO()

        for idx, chunk_data in enumerate(chunks):

            chunk_bytes = base64.b64decode(chunk_data)

            combined.write(chunk_bytes)

        combined.seek(0)

        # ===========================
        # Upload to GitHub directly
        # ===========================
        from werkzeug.datastructures import FileStorage

        uploaded_file = FileStorage(
            stream=combined,
            filename=file_name
        )

        result = upload_to_github(
            uploaded_file,
            secrets["github_repo"],
            secrets["branch"],
            secrets["pat_token"]
        )

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================================
# 🏠 Home route — Serve index.html
# ==================================
@app.route("/")
def home():

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)