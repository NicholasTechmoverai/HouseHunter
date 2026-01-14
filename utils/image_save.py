import base64
import os
import re
import uuid
import mimetypes
from pathlib import Path
import logging
from fastapi import UploadFile
from core.config import Config
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class FileUploadError(Exception):
    pass


class FileType(str, Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"


class FileUploadResult:
    def __init__(
        self,
        image_url: str = None,
        file_type: FileType = None,
        mime_type: str = None,
        original_filename: str = None,
        file_size: int = 0,
        success: bool = False,
        error_message: str = None,
        is_primary: Optional[bool] = False
    ):
        self.image_url = image_url
        self.file_type = file_type
        self.mime_type = mime_type
        self.original_filename = original_filename
        self.file_size = file_size
        self.success = success
        self.error_message = error_message
        self.is_primary = is_primary
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_url": self.image_url,
            "file_type": self.file_type.value if self.file_type else None,
            "mime_type": self.mime_type,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "success": self.success,
            "error_message": self.error_message,
            "is_primary": self.is_primary
        }


def get_file_type_from_mime(mime_type: str) -> FileType:
    if not mime_type:
        return FileType.OTHER
    
    mime_lower = mime_type.lower()
    
    if mime_lower.startswith('image/'):
        return FileType.IMAGE
    elif mime_lower.startswith('video/'):
        return FileType.VIDEO
    elif mime_lower.startswith('audio/'):
        return FileType.AUDIO
    elif mime_lower in ['application/pdf']:
        return FileType.PDF
    elif mime_lower.startswith('application/') or mime_lower.startswith('text/'):
        return FileType.DOCUMENT
    else:
        return FileType.OTHER


def validate_base64_image(base64_str: str) -> Tuple[bool, str, Optional[dict]]:
    if not base64_str:
        return False, "Empty base64 string", None
    
    if not base64_str.startswith("data:image/"):
        return False, "Invalid base64 format. Must start with 'data:image/'", None
    
    try:
        header, encoded = base64_str.split(",", 1)
        
        mime_type = header.split(";")[0].split(":")[1] if ":" in header else header.split(";")[0]
        file_type = mime_type.split("/")[1] if "/" in mime_type else ""
        
        encoding = header.split(";")[1] if ";" in header else ""
        if "base64" not in encoding:
            return False, "Base64 encoding required", None
        
        allowed_types = ['jpeg', 'jpg', 'png', 'gif', 'webp', 'svg+xml']
        if file_type not in allowed_types:
            return False, f"Unsupported image type: {file_type}", None
        
        metadata = {
            'mime_type': mime_type,
            'file_type': file_type,
            'encoding': encoding,
            'size_bytes': len(encoded) * 3 // 4
        }
        
        return True, "", metadata
        
    except Exception as e:
        return False, f"Invalid base64 format: {str(e)}", None


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    return filename


async def save_base64_image(
    base64_str: str, 
    folder: str = "...", 
    filename: Optional[str] = None,
    subfolder: Optional[str] = None,
    max_size_mb: int = 10
) -> Optional[str]:
    is_valid, error_msg, metadata = validate_base64_image(base64_str)
    if not is_valid:
        logger.warning(f"Invalid base64 image: {error_msg}")
        return None
    
    try:
        header, encoded = base64_str.split(",", 1)
        file_type = metadata['file_type']
        
        max_size_bytes = max_size_mb * 1024 * 1024
        actual_size = len(base64.b64decode(encoded))
        if actual_size > max_size_bytes:
            logger.warning(f"File size {actual_size} exceeds limit {max_size_bytes}")
            return None
        
        if filename:
            filename = sanitize_filename(filename)
            filename = os.path.splitext(filename)[0]
        else:
            filename = uuid.uuid4().hex
        
        final_filename = f"{filename}.{file_type}"
        
        path_parts = [folder]
        if subfolder:
            path_parts.append(subfolder.strip("/"))
        
        relative_path = os.path.join(*path_parts, final_filename)
        full_path = Path(Config.UPLOADS_DIR) / relative_path
        
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(base64.b64decode(encoded))
        
        logger.info(f"Base64 image saved: {relative_path} ({actual_size} bytes)")
        return str(relative_path).replace("\\", "/")
        
    except base64.binascii.Error as e:
        logger.error(f"Base64 decode error: {e}")
        return None
    except IOError as e:
        logger.error(f"File write error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error saving base64 image: {e}")
        return None


async def save_uploaded_file(
    file: UploadFile, 
    folder: str = "...", 
    filename: Optional[str] = None,
    subfolder: Optional[str] = None,
    allowed_extensions: Optional[list] = None,
    max_size_mb: int = 10
) -> FileUploadResult:
    result = FileUploadResult()
    
    if allowed_extensions is None:
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt']
    
    try:
        original_filename = file.filename or "unnamed"
        mime_type = file.content_type or mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
        file_type_enum = get_file_type_from_mime(mime_type)
        
        content = await file.read()
        await file.seek(0)
        
        file_size = len(content)
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            result.error_message = f"File size {file_size} exceeds limit {max_size_bytes}"
            return result
        
        _, original_ext = os.path.splitext(original_filename)
        original_ext = original_ext.lower()
        
        if allowed_extensions and original_ext not in allowed_extensions:
            result.error_message = f"File extension {original_ext} not allowed"
            return result
        
        if filename:
            filename = sanitize_filename(filename)
            custom_name, custom_ext = os.path.splitext(filename)
            if not custom_ext:
                filename = f"{filename}{original_ext}"
            elif custom_ext.lower() != original_ext:
                logger.warning(f"Extension mismatch: {custom_ext} vs {original_ext}")
                filename = f"{custom_name}{original_ext}"
        else:
            unique_id = uuid.uuid4().hex
            filename = f"{unique_id}{original_ext}"
        
        path_parts = [folder]
        if subfolder:
            path_parts.append(subfolder.strip("/"))
        
        relative_path = os.path.join(*path_parts, filename)
        full_path = Path(Config.UPLOADS_DIR) / relative_path
        
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as buffer:
            buffer.write(content)
        
        if not full_path.exists() or full_path.stat().st_size == 0:
            result.error_message = "File not properly saved"
            return result
        
        result.image_url = str(relative_path).replace("\\", "/")
        result.file_type = file_type_enum
        result.mime_type = mime_type
        result.original_filename = original_filename
        result.file_size = file_size
        result.success = True
        
        logger.info(f"Uploaded file saved: {result.image_url} ({file_size} bytes)")
        
    except IOError as e:
        result.error_message = f"File system error: {e}"
        logger.error(result.error_message)
    except Exception as e:
        result.error_message = f"Unexpected error: {e}"
        logger.error(result.error_message)
    
    return result


async def save_files_batch(
    files: list,
    folder: str = "...",
    subfolder: Optional[str] = None,
    file_type: str = "form",
    **kwargs
) -> List[FileUploadResult]:
    if not files:
        return []
    
    results = []
    
    for i, file in enumerate(files):
        try:
            if file_type == "form":
                result = await save_uploaded_file(
                    file, 
                    folder=folder, 
                    subfolder=subfolder,
                    **kwargs
                )
            else:
                image_path = await save_base64_image(
                    file,
                    folder=folder,
                    subfolder=subfolder,
                    **kwargs
                )
                result = FileUploadResult(
                    image_url=image_path,
                    file_type=FileType.IMAGE if image_path else None,
                    success=bool(image_path),
                    error_message=None if image_path else "Failed to save base64 image"
                )
            
            results.append(result)
            
            if result.success:
                logger.debug(f"Successfully saved file {i+1}/{len(files)}: {result.image_url}")
            else:
                logger.warning(f"Failed to save file {i+1}/{len(files)}: {result.error_message}")
                
        except Exception as e:
            error_result = FileUploadResult(
                error_message=f"Unexpected error: {e}",
                success=False
            )
            results.append(error_result)
            logger.error(f"Error saving file {i+1}: {e}")
    
    success_count = sum(1 for r in results if r.success)
    logger.info(f"Batch save complete: {success_count}/{len(files)} successful")
    
    return results


def save_files_batch_sync(
    files: List[FileUploadResult],
    rental_id: str,
    user_id: str
) -> List[Dict[str, Any]]:
    output = []
    
    for result in files:
        if result.success and result.image_url:
            file_data = {
                "image_url": result.image_url[:500],
                "file_type": result.file_type.value if result.file_type else None,
                "mime_type": (result.mime_type[:100] if result.mime_type else None),
                "original_filename": result.original_filename,
                "file_size": result.file_size,
                "rental_id": rental_id,
                "uploaded_by": user_id,
                "is_primary": result.is_primary,
                "created_at": datetime.utcnow().isoformat()
            }
            output.append(file_data)
    
    return output


def delete_file(file_path: str) -> bool:
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(Config.UPLOADS_DIR) / file_path
        
        if path.exists():
            path.unlink()
            logger.info(f"File deleted: {file_path}")
            return True
        else:
            logger.warning(f"File not found: {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False