"""
publishers.py — YouTube Shorts + Instagram Reels upload
"""
from __future__ import annotations
import time
from pathlib import Path

import httpx
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config

GRAPH = "https://graph.facebook.com/v19.0"


# =============================================================================
# YOUTUBE
# =============================================================================
def upload_youtube(video_path: Path, title: str, description: str, tags: list[str]) -> str:
    creds = Credentials(
        token=None,
        refresh_token=config.YT_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.YT_CLIENT_ID,
        client_secret=config.YT_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    creds.refresh(Request())
    yt = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": f"{title} #Shorts"[:100],
            "description": description,
            "tags": ["CaptainRaccoon", "Shorts"] + tags,
            "categoryId": "22",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    vid_id = response["id"]
    print(f"  ✅ YouTube: https://youtube.com/watch?v={vid_id}")
    return f"https://youtube.com/watch?v={vid_id}"


# =============================================================================
# INSTAGRAM REELS
# =============================================================================
def upload_instagram(video_path: Path, caption: str) -> str:
    """Two-phase Graph API upload. Requires a publicly accessible video URL."""
    public_url = _upload_to_storage(video_path)

    # Phase 1 — create container
    r = httpx.post(
        f"{GRAPH}/{config.IG_ACCOUNT_ID}/media",
        params={
            "access_token": config.IG_ACCESS_TOKEN,
            "media_type": "REELS",
            "video_url": public_url,
            "caption": caption,
            "share_to_feed": "true",
        },
        timeout=60,
    )
    r.raise_for_status()
    container_id = r.json()["id"]

    # Phase 2 — poll until FINISHED
    for _ in range(60):
        status_r = httpx.get(
            f"{GRAPH}/{container_id}",
            params={"fields": "status_code", "access_token": config.IG_ACCESS_TOKEN},
        )
        status = status_r.json().get("status_code", "")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram container {status}")
        time.sleep(10)

    # Phase 3 — publish
    pub = httpx.post(
        f"{GRAPH}/{config.IG_ACCOUNT_ID}/media_publish",
        params={"access_token": config.IG_ACCESS_TOKEN, "creation_id": container_id},
    )
    pub.raise_for_status()
    media_id = pub.json()["id"]
    print(f"  ✅ Instagram: https://instagram.com/p/{media_id}/")
    return f"https://instagram.com/p/{media_id}/"


def _upload_to_storage(video_path: Path) -> str:
    """Upload to Azure Blob → return public URL. DO Spaces if Azure unavailable."""
    if config.AZURE_STORAGE_CONN:
        from azure.storage.blob import BlobServiceClient
        client = BlobServiceClient.from_connection_string(config.AZURE_STORAGE_CONN)
        key = f"mini/{video_path.name}"
        blob = client.get_blob_client(config.AZURE_CONTAINER, key)
        blob.upload_blob(video_path.read_bytes(), overwrite=True)
        acct = client.account_name
        return f"https://{acct}.blob.core.windows.net/{config.AZURE_CONTAINER}/{key}"
    raise RuntimeError("No storage configured for Instagram video URL")
