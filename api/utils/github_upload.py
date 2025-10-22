import base64
import requests

def upload_to_github(zip_file, repo, branch, token):
    try:
        file_path = f"uploads/{zip_file.filename}"
        content = base64.b64encode(zip_file.read()).decode("utf-8")
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

        # Check if file exists
        response = requests.get(url, headers={"Authorization": f"token {token}"})
        sha = response.json().get("sha") if response.status_code == 200 else None

        data = {
            "message": f"Upload {zip_file.filename}",
            "content": content,
            "branch": branch
        }

        if sha:
            data["sha"] = sha  # update existing file

        resp = requests.put(url, json=data, headers={"Authorization": f"token {token}"})
        resp.raise_for_status()
        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}
