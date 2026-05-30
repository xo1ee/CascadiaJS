import os
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List


BOX_API_BASE = "https://api.box.com/2.0"
BOX_UPLOAD_BASE = "https://upload.box.com/api/2.0"


def get_headers() -> dict:
    token = os.getenv("BOX_DEVELOPER_TOKEN")
    if not token:
        raise RuntimeError("Missing BOX_DEVELOPER_TOKEN in environment")
    return {"Authorization": f"Bearer {token}"}


def download_box_file(file_id: str, output_path: str) -> str:
    url = f"{BOX_API_BASE}/files/{file_id}/content"
    response = requests.get(url, headers=get_headers(), allow_redirects=True)

    if response.status_code >= 400:
        raise RuntimeError(f"Box download failed: {response.status_code} {response.text}")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path


def upload_file_to_box(local_path: str, folder_id: str, box_filename: str | None = None) -> dict:
    filename = box_filename or Path(local_path).name

    attributes = {
        "name": filename,
        "parent": {"id": folder_id}
    }

    with open(local_path, "rb") as file_content:
        files = {
            "attributes": (None, json.dumps(attributes), "application/json"),
            "file": (filename, file_content, "application/json")
        }

        response = requests.post(
            f"{BOX_UPLOAD_BASE}/files/content",
            headers=get_headers(),
            files=files
        )

    if response.status_code >= 400:
        raise RuntimeError(f"Box upload failed: {response.status_code} {response.text}")

    return response.json()


def create_output_folder(parent_folder_id: str, folder_name: str) -> str:
    """
    Create a subfolder under parent_folder_id and return its Box folder id.

    Each analysis run should get its own unique folder so repeated runs do
    not overwrite each other. If the name already exists (HTTP 409), a
    timestamp suffix is appended and creation is retried once.
    """
    def _create(name: str):
        return requests.post(
            f"{BOX_API_BASE}/folders",
            headers={**get_headers(), "Content-Type": "application/json"},
            data=json.dumps({"name": name, "parent": {"id": parent_folder_id}}),
        )

    response = _create(folder_name)

    if response.status_code == 409:
        # Name collision — append a timestamp and try once more.
        unique_name = f"{folder_name}_{datetime.now().strftime('%H%M%S')}"
        response = _create(unique_name)

    if response.status_code >= 400:
        raise RuntimeError(
            f"Box folder creation failed: {response.status_code} {response.text}"
        )

    return response.json()["id"]


def upload_content_to_box(content, folder_id: str, box_filename: str) -> dict:
    """
    Upload in-memory content (str or bytes) to Box as a file, without needing
    a local copy. Consumes report_service.build_packet_files() output directly.
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    attributes = {"name": box_filename, "parent": {"id": folder_id}}

    files = {
        "attributes": (None, json.dumps(attributes), "application/json"),
        "file": (box_filename, content, "application/octet-stream"),
    }

    response = requests.post(
        f"{BOX_UPLOAD_BASE}/files/content",
        headers=get_headers(),
        files=files,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Box upload failed: {response.status_code} {response.text}"
        )

    return response.json()


def upload_packet_to_box(
    parent_folder_id: str,
    folder_name: str,
    files: Dict[str, str],
) -> dict:
    """
    Create a unique output folder and upload an entire packet to it.

    Args:
        parent_folder_id: Box folder id to create the run folder under.
        folder_name:      Desired (ideally unique) subfolder name.
        files:            {filename: content} from build_packet_files().

    Returns:
        {
          "folder_id": "...",
          "box_outputs": [  # matches frontend BoxOutput type
            {"name": "...", "box_file_id": "...", "url": "..."}
          ],
        }
    """
    folder_id = create_output_folder(parent_folder_id, folder_name)

    box_outputs: List[dict] = []
    for filename, content in files.items():
        result = upload_content_to_box(content, folder_id, filename)
        # Box returns {"entries": [{"id": ...}]} for content uploads.
        entry = result.get("entries", [{}])[0]
        file_id = entry.get("id", "")
        box_outputs.append({
            "name": filename,
            "box_file_id": file_id,
            "url": f"https://app.box.com/file/{file_id}" if file_id else "",
        })

    return {"folder_id": folder_id, "box_outputs": box_outputs}