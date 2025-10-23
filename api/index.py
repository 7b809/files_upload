from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os, base64, json

from .utils.github_upload import upload_to_github
from .utils.file_utils import save_chunk, merge_chunks

app = Flask(__name__)
CORS(app)

# Load secrets from environment
secrets = json.loads(os.getenv("app_data", "{}"))
app.secret_key = secrets.get("secret_key", "default")

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    """Receive one 50KB base64 chunk"""
    data = request.json
    filename = data["filename"]
    chunk_data = data["data"]
    chunk_number = int(data["chunk_number"])
    total_chunks = int(data["total_chunks"])

    save_chunk(filename, chunk_number, chunk_data, UPLOAD_DIR)

    # Check if all chunks are received
    all_received = merge_chunks(filename, total_chunks, UPLOAD_DIR)

    if all_received:
        zip_path = os.path.join(UPLOAD_DIR, filename)
        result = upload_to_github(
            open(zip_path, "rb"), 
            secrets["github_repo"], 
            secrets["branch"], 
            secrets["pat_token"]
        )
        return jsonify({"status": "complete", "result": result})

    return jsonify({"status": "in_progress", "chunk": chunk_number})
