"""
Upload scraped POI data to Box (cloud storage).

You do NOT build anything on the Box side — Box exposes a ready-made upload API.
This module authenticates with a Box token and uploads a JSON file into a Box
folder. It's independent of scraper.py: hand it a places list (or any bytes).

Auth: Box Developer Token (BOX_DEVELOPER_TOKEN) — simplest, but expires ~60 min,
so it's best for a hackathon/demo. For production use a Client Credentials Grant
(CCG) or JWT app instead (those need an enterprise/user id, not just these vars).

Env (read from the repo-root .env):
    BOX_DEVELOPER_TOKEN   developer token from the Box developer console
    BOX_FOLDER_ID         destination folder id ("0" = the All Files root)

Requires: pip install box-sdk-gen   (see apify_data/requirements.txt)

CLI:
    python apify_data/box_uploader.py apify_data/venue_a_scraped.json
"""

from __future__ import annotations

import os
import io
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent


def _load_env(path: Path) -> None:
    """Tiny stdlib .env loader so this module is usable standalone."""
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env(_REPO_ROOT / ".env")

BOX_DEVELOPER_TOKEN = os.getenv("BOX_DEVELOPER_TOKEN")
BOX_FOLDER_ID = os.getenv("BOX_FOLDER_ID") or "0"


def upload_places(
    places: list[dict],
    file_name: str = "venue_scraped.json",
    folder_id: str | None = None,
) -> str:
    """Upload ``places`` as a JSON file to Box; return the Box file id."""
    data = json.dumps(places, ensure_ascii=False, indent=2).encode("utf-8")
    return upload_bytes(data, file_name, folder_id)


def upload_bytes(data: bytes, file_name: str, folder_id: str | None = None) -> str:
    """Upload raw bytes as ``file_name`` into the Box folder; return the file id.

    If a file with the same name already exists in the folder, a new *version*
    is uploaded instead of failing with a name conflict.
    """
    # Imported lazily so the module loads even when box-sdk-gen isn't installed.
    from box_sdk_gen import BoxClient, BoxDeveloperTokenAuth
    from box_sdk_gen.schemas import (
        UploadFileAttributes,
        UploadFileAttributesParentField,
        UploadFileVersionAttributes,
    )

    if not BOX_DEVELOPER_TOKEN:
        raise RuntimeError(
            "BOX_DEVELOPER_TOKEN missing — paste a token into the repo-root .env"
        )

    folder_id = folder_id or BOX_FOLDER_ID
    client = BoxClient(auth=BoxDeveloperTokenAuth(token=BOX_DEVELOPER_TOKEN))

    existing_id = _find_file_id(client, folder_id, file_name)
    if existing_id:
        result = client.uploads.upload_file_version(
            file_id=existing_id,
            attributes=UploadFileVersionAttributes(name=file_name),
            file=io.BytesIO(data),
        )
    else:
        result = client.uploads.upload_file(
            UploadFileAttributes(
                name=file_name,
                parent=UploadFileAttributesParentField(id=folder_id),
            ),
            io.BytesIO(data),
        )
    return result.entries[0].id


def _find_file_id(client, folder_id: str, file_name: str) -> str | None:
    """Return the id of a file named ``file_name`` in the folder, else None."""
    for item in client.folders.get_folder_items(folder_id).entries:
        if getattr(item, "name", None) == file_name:
            return item.id
    return None


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Upload a JSON file to Box.")
    p.add_argument("path", help="local JSON file, e.g. apify_data/venue_a_scraped.json")
    p.add_argument("--name", default=None, help="name to store in Box (default: same filename)")
    p.add_argument("--folder", default=None, help="Box folder id (default: BOX_FOLDER_ID / root)")
    args = p.parse_args()

    raw = Path(args.path).read_bytes()
    file_id = upload_bytes(raw, args.name or Path(args.path).name, args.folder)
    print(f"Uploaded → Box file id {file_id}")
