import os

ALLOWED_DELIVERABLE_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.rtf', '.png', '.jpg', '.jpeg', '.gif',
    '.webp', '.zip', '.rar', '.7z', '.tar', '.gz'
}

ALLOWED_IMAGE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.webp', '.gif'
}

MAX_DELIVERABLE_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024        # 5 MB

def validate_deliverable_file(file_obj):
    """
    Validates deliverable file attachments.
    Returns (True, None) if valid, or (False, error_message).
    """
    if not file_obj or not hasattr(file_obj, 'name'):
        return False, "Invalid file object."

    name = file_obj.name.strip()
    ext = os.path.splitext(name)[1].lower()

    if not ext:
        return False, "File must have a valid extension."

    if ext not in ALLOWED_DELIVERABLE_EXTENSIONS:
        return False, (
            f"File type '{ext}' is not permitted. "
            f"Allowed types: PDF, Office documents, text files, images, and archives."
        )

    size = getattr(file_obj, 'size', None)
    if size is not None and size > MAX_DELIVERABLE_SIZE:
        return False, "File size exceeds the 25 MB limit."

    return True, None


def validate_image_file(file_obj):
    """
    Validates user avatars and startup logos.
    Returns (True, None) if valid, or (False, error_message).
    """
    if not file_obj or not hasattr(file_obj, 'name'):
        return False, "Invalid image object."

    name = file_obj.name.strip()
    ext = os.path.splitext(name)[1].lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, (
            f"Image type '{ext}' is not permitted. "
            f"Allowed formats: PNG, JPG, JPEG, WEBP, GIF."
        )

    size = getattr(file_obj, 'size', None)
    if size is not None and size > MAX_IMAGE_SIZE:
        return False, "Image size exceeds the 5 MB limit."

    return True, None
