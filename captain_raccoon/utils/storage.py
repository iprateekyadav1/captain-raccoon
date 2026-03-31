"""
Captain Raccoon — Storage Manager
Handles upload/download to Azure Blob Storage (primary) + DigitalOcean Spaces (fallback).
Provides public URLs for Instagram's Graph API video upload requirement.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import structlog

from captain_raccoon.config.settings import get_settings

log = structlog.get_logger(__name__)


class StorageManager:
    """
    Primary:  Azure Blob Storage
    Fallback: DigitalOcean Spaces (S3-compatible)
    """

    def __init__(self):
        self._settings = get_settings()

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────
    def upload(self, local_path: Path, object_key: str) -> str:
        """Upload file and return public URL. Tries Azure then DO Spaces."""
        try:
            return self._upload_azure(local_path, object_key)
        except Exception as e:
            log.warning("storage.azure_failed", error=str(e), key=object_key)
            return self._upload_do_spaces(local_path, object_key)

    def upload_for_instagram(self, local_path: Path, object_key: str) -> str:
        """
        Upload video and return a publicly-accessible URL.
        Instagram requires a direct HTTPS URL to fetch the video from.
        """
        url = self.upload(local_path, object_key)
        log.info("storage.uploaded_for_instagram", url=url, key=object_key)
        return url

    def upload_thumbnail(self, local_path: Path, episode_id: str) -> str:
        return self.upload(local_path, f"thumbnails/{episode_id}.jpg")

    def download(self, object_key: str, local_path: Path) -> Path:
        """Download file from storage to local path."""
        try:
            return self._download_azure(object_key, local_path)
        except Exception as e:
            log.warning("storage.azure_download_failed", error=str(e))
            return self._download_do_spaces(object_key, local_path)

    # ─────────────────────────────────────────────────────────────────────────
    # AZURE BLOB STORAGE
    # ─────────────────────────────────────────────────────────────────────────
    def _upload_azure(self, local_path: Path, object_key: str) -> str:
        conn_str = self._settings.azure_storage_connection_string
        if not conn_str:
            raise ValueError("No Azure storage connection string configured")

        from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
        from datetime import datetime, timedelta, timezone

        client = BlobServiceClient.from_connection_string(conn_str)
        container = self._settings.azure_storage_container
        blob_client = client.get_blob_client(container=container, blob=object_key)

        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # Generate URL (public or SAS if private container)
        url = f"https://{client.account_name}.blob.core.windows.net/{container}/{object_key}"
        log.debug("storage.azure_uploaded", url=url)
        return url

    def _download_azure(self, object_key: str, local_path: Path) -> Path:
        conn_str = self._settings.azure_storage_connection_string
        if not conn_str:
            raise ValueError("No Azure storage connection string")

        from azure.storage.blob import BlobServiceClient

        client = BlobServiceClient.from_connection_string(conn_str)
        container = self._settings.azure_storage_container
        blob_client = client.get_blob_client(container=container, blob=object_key)

        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())

        return local_path

    # ─────────────────────────────────────────────────────────────────────────
    # DIGITALOCEAN SPACES  (S3-compatible)
    # ─────────────────────────────────────────────────────────────────────────
    def _upload_do_spaces(self, local_path: Path, object_key: str) -> str:
        key = self._settings.do_spaces_key
        secret = self._settings.do_spaces_secret
        if not key or not secret:
            raise ValueError("No DigitalOcean Spaces credentials configured")

        import boto3
        from botocore.client import Config

        session = boto3.session.Session()
        s3 = session.client(
            "s3",
            region_name=self._settings.do_spaces_region,
            endpoint_url=self._settings.do_spaces_endpoint,
            aws_access_key_id=key,
            aws_secret_access_key=secret,
            config=Config(signature_version="s3v4"),
        )

        bucket = self._settings.do_spaces_bucket
        s3.upload_file(
            str(local_path),
            bucket,
            object_key,
            ExtraArgs={"ACL": "public-read", "ContentType": self._detect_content_type(local_path)},
        )

        url = f"{self._settings.do_spaces_endpoint}/{bucket}/{object_key}"
        log.debug("storage.do_spaces_uploaded", url=url)
        return url

    def _download_do_spaces(self, object_key: str, local_path: Path) -> Path:
        import boto3
        from botocore.client import Config

        session = boto3.session.Session()
        s3 = session.client(
            "s3",
            region_name=self._settings.do_spaces_region,
            endpoint_url=self._settings.do_spaces_endpoint,
            aws_access_key_id=self._settings.do_spaces_key,
            aws_secret_access_key=self._settings.do_spaces_secret,
            config=Config(signature_version="s3v4"),
        )
        local_path.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(self._settings.do_spaces_bucket, object_key, str(local_path))
        return local_path

    @staticmethod
    def _detect_content_type(path: Path) -> str:
        ext = path.suffix.lower()
        mapping = {
            ".mp4": "video/mp4",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".aac": "audio/aac",
        }
        return mapping.get(ext, "application/octet-stream")
