"""
Upload a local file to Box over plain HTTP (Box Content API).

Final flow: scraper.py saves results to a local JSON file, then this module
HTTP-POSTs that file to Box. You do NOT build anything on the Box side — Box
provides the upload REST API. You only need an access token and a destination
folder id, both read from the repo-root .env. Standard library only — no SDK,
no pip install.

Box endpoints used:
    new file     POST https://upload.box.com/api/2.0/files/content
    new version  POST https://upload.box.com/api/2.0/files/{file_id}/content
Auth: header  Authorization: Bearer <BOX_DEVELOPER_TOKEN>

Env (repo-root .env):
    BOX_DEVELOPER_TOKEN   developer token from the Box developer console
                          (simplest; expires ~60 min — refresh it for a new run)
    BOX_FOLDER_ID         destination folder id ("0" = the All Files root)

CLI:
    python apify_data/box_uploader.py apify_data/venue_a_scraped.json
"""

from __future__ import annotations

import os
import json
import uuid
import urllib.error
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent

_UPLOAD_NEW_URL = "https://upload.box.com/api/2.0/files/content"
_UPLOAD_VERSION_URL = "https://upload.box.com/api/2.0/files/{file_id}/content"


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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def upload_file(
    local_path: str | Path,
    box_name: str | None = None,
    folder_id: str | None = None,
    token: str | None = None,
) -> str:
    """HTTP-upload a local file to Box; return the Box file id.

    Uploads a new file, or a new *version* if a file with the same name already
    exists in the folder (Box answers 409 on a name conflict).
    """
    local_path = Path(local_path)
    data = local_path.read_bytes()
    return upload_bytes(data, box_name or local_path.name, folder_id=folder_id, token=token)


def upload_bytes(
    data: bytes,
    box_name: str,
    folder_id: str | None = None,
    token: str | None = None,
) -> str:
    """HTTP-upload raw bytes to Box as ``box_name``; return the Box file id."""
    token = token or BOX_DEVELOPER_TOKEN
    folder_id = folder_id or BOX_FOLDER_ID
    if not token:
        raise RuntimeError(
            "BOX_DEVELOPER_TOKEN missing — paste a token into the repo-root .env"
        )

    attributes = json.dumps({"name": box_name, "parent": {"id": folder_id}})
    try:
        resp = _post_multipart(
            _UPLOAD_NEW_URL, token, box_name, data, {"attributes": attributes}
        )
    except urllib.error.HTTPError as e:
        if e.code != 409:  # something other than a name conflict
            raise
        existing_id = _conflict_file_id(e)
        url = _UPLOAD_VERSION_URL.format(file_id=existing_id)
        resp = _post_multipart(url, token, box_name, data, {})
    return resp["entries"][0]["id"]


# ---------------------------------------------------------------------------
# Internal helpers — raw multipart/form-data over urllib
# ---------------------------------------------------------------------------

def _post_multipart(url, token, file_name, file_bytes, extra_fields):
    boundary = "----SiteLensBox" + uuid.uuid4().hex
    body = _encode_multipart(boundary, extra_fields, "file", file_name, file_bytes)
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def _encode_multipart(
    boundary, fields, file_field, file_name, file_bytes, content_type="application/json"
):
    """Build a multipart/form-data body: string fields first, then the file."""
    b = boundary.encode()
    parts: list[bytes] = []
    for name, value in fields.items():
        parts += [
            b"--" + b,
            f'Content-Disposition: form-data; name="{name}"'.encode(),
            b"",
            value.encode("utf-8"),
        ]
    parts += [
        b"--" + b,
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_name}"'.encode(),
        f"Content-Type: {content_type}".encode(),
        b"",
        file_bytes,
        b"--" + b + b"--",
        b"",
    ]
    return b"\r\n".join(parts)


def _conflict_file_id(err: urllib.error.HTTPError) -> str:
    """Pull the existing file id out of a Box 409 (name conflict) response."""
    info = json.loads(err.read().decode("utf-8"))
    conflicts = info.get("context_info", {}).get("conflicts")
    if isinstance(conflicts, list) and conflicts:
        return conflicts[0]["id"]
    if isinstance(conflicts, dict):
        return conflicts["id"]
    raise RuntimeError(f"Box returned 409 but no conflict id was found: {info}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="HTTP-upload a local file to Box.")
    p.add_argument("path", help="local file, e.g. apify_data/venue_a_scraped.json")
    p.add_argument("--name", default=None, help="name to store in Box (default: same filename)")
    p.add_argument("--folder", default=None, help="Box folder id (default: BOX_FOLDER_ID / root)")
    p.add_argument("--token", default=None, help="Box token (overrides BOX_DEVELOPER_TOKEN)")
    args = p.parse_args()

    file_id = upload_file(args.path, box_name=args.name, folder_id=args.folder, token=args.token)
    print(f"Uploaded {args.path} → Box file id {file_id}")
