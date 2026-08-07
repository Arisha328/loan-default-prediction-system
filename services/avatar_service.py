"""
services/avatar_service.py
---------------------------
Handles profile-picture uploads: validates the file, center-crops it to a
square, resizes it to a fixed dimension, and writes it to disk as an
optimized JPEG. Keeps every stored avatar small and consistent in size
regardless of what the user uploads.
"""

import os
import uuid

from flask import current_app
from PIL import Image, ImageOps


def save_avatar(file_storage, previous_filename=None):
    """
    Processes and saves an uploaded avatar image.

    Returns the new filename (to store on User.profile_image).
    Deletes the user's previous avatar file, if any, once the new one is
    saved successfully.
    """
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    size = current_app.config.get("AVATAR_SIZE", 320)

    image = Image.open(file_storage.stream)
    image = ImageOps.exif_transpose(image)  # respect phone camera orientation
    image = image.convert("RGB")
    image = ImageOps.fit(image, (size, size), Image.LANCZOS)

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(upload_folder, filename)
    image.save(filepath, format="JPEG", quality=87, optimize=True)

    if previous_filename:
        old_path = os.path.join(upload_folder, previous_filename)
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass  # non-fatal — stale file cleanup is best-effort

    return filename


def delete_avatar(filename):
    if not filename:
        return
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    path = os.path.join(upload_folder, filename)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass
