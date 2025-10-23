from flask import Flask, request, jsonify
from flask_cors import CORS
from .utils.github_upload import upload_to_github
import os, json, base64

# ===========================
# 🔒 Secrets Configuration
# ===========================
app_data = os.getenv("app_data")
if not app_data:
    raise RuntimeError("Environment variable 'app_data' not found!")

secrets = json.loads(app_data)
app = Flask(__name__)
app.secret_key = secrets["secret_key"]

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Temp directory to store chunks
UPLOAD_TMP_DIR = "temp_chunks"
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)

# ==================================
# 🚀 Chunk upload endpoint
# ==================================
@app.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    try:
        data = request.get_json()
        file_id = data.get("file_id")
        chunk_index = data.get("chunk_index")
        total_chunks = data.get("total_chunks")
        chunk_data = data.get("chunk_data")

        if not all([file_id, chunk_data, chunk_index is not None, total_chunks]):
            return jsonify({"success": False, "error": "Missing parameters"}), 400

        # Decode base64 data
        chunk_bytes = base64.b64decode(chunk_data)
        chunk_path = os.path.join(UPLOAD_TMP_DIR, f"{file_id}_{chunk_index}.part")

        # Save this chunk
        with open(chunk_path, "wb") as f:
            f.write(chunk_bytes)

        # Check if all chunks are received
        all_received = all(
            os.path.exists(os.path.join(UPLOAD_TMP_DIR, f"{file_id}_{i}.part"))
            for i in range(total_chunks)
        )

        if all_received:
            assembled_path = os.path.join(UPLOAD_TMP_DIR, f"{file_id}.zip")
            with open(assembled_path, "wb") as final_file:
                for i in range(total_chunks):
                    part_path = os.path.join(UPLOAD_TMP_DIR, f"{file_id}_{i}.part")
                    with open(part_path, "rb") as part_file:
                        final_file.write(part_file.read())

            # Upload to GitHub
            with open(assembled_path, "rb") as f:
                from werkzeug.datastructures import FileStorage
                zip_file = FileStorage(stream=f, filename=f"{file_id}.zip")
                result = upload_to_github(
                    zip_file, 
                    secrets["github_repo"], 
                    secrets["branch"], 
                    secrets["pat_token"]
                )

            # Cleanup
            for i in range(total_chunks):
                os.remove(os.path.join(UPLOAD_TMP_DIR, f"{file_id}_{i}.part"))
            os.remove(assembled_path)

            return jsonify({"success": True, "uploaded": True})

        return jsonify({"success": True, "uploaded": False, "chunk_index": chunk_index})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/")
def home():
    return jsonify({"message": "Chunked uploader running!"})
