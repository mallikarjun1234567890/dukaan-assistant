"""Cloudinary image uploads. Secrets stay on the backend."""

from __future__ import annotations

from typing import BinaryIO

from app.config import Settings


class UploadError(Exception):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 2_000_000


def configured(settings: Settings) -> bool:
    return bool(
        settings.cloudinary_cloud_name.strip()
        and settings.cloudinary_api_key.strip()
        and settings.cloudinary_api_secret.strip()
    )


def upload_image(
    *,
    settings: Settings,
    file_obj: BinaryIO,
    content_type: str,
    folder: str,
) -> str:
    if content_type not in ALLOWED_TYPES:
        raise UploadError("Only JPG, PNG, or WebP images are allowed", 400)
    data = file_obj.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise UploadError("Image must be 2 MB or smaller", 413)
    if not data:
        raise UploadError("The image file is empty", 400)
    if not configured(settings):
        raise UploadError(
            "Cloudinary is not configured. Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, "
            "and CLOUDINARY_API_SECRET to backend/.env.",
            503,
        )
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError as exc:
        raise UploadError("Cloudinary SDK is not installed", 503) from exc

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    try:
        result = cloudinary.uploader.upload(
            data,
            folder=folder,
            resource_type="image",
            overwrite=True,
        )
    except Exception as exc:
        message = str(exc).strip() or type(exc).__name__
        if "cloud_name" in message.lower() or "authorization" in message.lower():
            raise UploadError(
                "Cloudinary rejected the account details. CLOUDINARY_CLOUD_NAME must be the "
                "cloud name from the Cloudinary dashboard (not a folder label).",
                503,
            ) from exc
        raise UploadError(f"Cloudinary upload failed: {message}", 503) from exc
    url = result.get("secure_url") or result.get("url")
    if not url:
        raise UploadError("Cloudinary did not return an image URL", 503)
    return str(url)
