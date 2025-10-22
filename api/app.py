from flask import Flask, render_template, request, redirect, url_for, flash
from flask_cors import CORS
from utils.github_upload import upload_to_github
import os,json

# ===========================
# 🔒 Secrets Configuration
# ===========================
app_data = os.getenv("app_data")
if not app_data:
    raise RuntimeError("Environment variable 'app_data' not found!")

secrets = json.loads(app_data)
app = Flask(__name__)
app.secret_key = secrets["secret_key"]

# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        zip_file = request.files.get("zip_file")

        if not zip_file:
            flash("ZIP file is required!", "danger")
            return redirect(url_for("index"))

        # Use secrets object for GitHub credentials
        github_repo = secrets["github_repo"]
        github_branch = secrets["branch"]
        pat_token = secrets["pat_token"]

        # Upload file to GitHub
        result = upload_to_github(zip_file, github_repo, github_branch, pat_token)

        if result["success"]:
            flash("File uploaded successfully!", "success")
        else:
            flash(f"Failed to upload: {result['error']}", "danger")
        
        return redirect(url_for("index"))

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
