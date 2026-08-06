from common.exceptions import ValidationError

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

def validate_file_size_and_type(file) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(f"Unsupported file type: {file.content_type}. Allowed: image or PDF.")
    if file.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File too large ({file.size} bytes). Max size is {MAX_FILE_SIZE_BYTES} bytes.")