
from datetime import datetime,timedelta
from typing import Optional, Dict, Any, Tuple, BinaryIO,List
from pathlib import Path
import os
from uuid import uuid4
import uuid
from ..models.universal.document import IdentityDocument,DocumentType,VerificationStatus
import hashlib

# ============== UTILITY FUNCTIONS ==============

class DocumentManager:
    """Manages document storage and retrieval operations"""
    
    # Default configuration
    BASE_UPLOAD_DIR = "uploads/documents"
    ALLOWED_EXTENSIONS = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'tiff': 'image/tiff',
        'bmp': 'image/bmp',
        'txt': 'text/plain',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def get_storage_path(cls, user_id: str, document_type: str, filename: str) -> Path:
        """Generate storage path for a document"""
        today = datetime.utcnow()
        year = today.year
        month = today.month
        day = today.day
        
        path = Path(cls.BASE_UPLOAD_DIR) / str(user_id) / document_type / str(year) / str(month) / str(day)
        path.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(today.timestamp())
        file_ext = Path(filename).suffix
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"
        
        return path / unique_filename

    @classmethod
    def is_allowed_file(cls, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS

    @classmethod
    def calculate_file_hash(cls, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @classmethod
    async def save_document(
        cls,
        file_data: BinaryIO,
        filename: str,
        user_id: str,
        document_type: DocumentType,
        document_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_public: bool = False
    ) -> IdentityDocument:
        """
        Save a document to storage and create database record
        
        Args:
            file_data: Binary file data
            filename: Original filename
            user_id: User ID who uploaded the document
            document_type: Type of document
            document_number: Document number (optional)
            metadata: Additional metadata (optional)
            is_public: Whether document is publicly accessible
            
        Returns:
            IdentityDocument instance
        """
        
        if not cls.is_allowed_file(filename):
            raise ValueError(f"File type not allowed: {filename}")
        
        file_ext = filename.rsplit('.', 1)[1].lower()
        mime_type = cls.ALLOWED_EXTENSIONS.get(file_ext)
        
        storage_path = cls.get_storage_path(user_id, document_type.name, filename)
        
        file_size = 0
        file_data.seek(0)
        
        with open(storage_path, 'wb') as f:
            while True:
                chunk = file_data.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                file_size += len(chunk)
                
                if file_size > cls.MAX_FILE_SIZE:
                    os.remove(storage_path)
                    raise ValueError(f"File size exceeds {cls.MAX_FILE_SIZE} bytes limit")
        
        file_hash = cls.calculate_file_hash(storage_path)
        
        document = await IdentityDocument.create(
            document_type=document_type,
            document_number=document_number,
            original_filename=filename,
            file_path=str(storage_path),
            file_url=f"/documents/{storage_path.relative_to(cls.BASE_UPLOAD_DIR)}",
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            uploaded_by_id=user_id,
            metadata=metadata or {},
            is_public=is_public
        )
        
        if mime_type.startswith('image/'):
            await cls.generate_thumbnail(document, storage_path)
        
        return document

    @classmethod
    async def generate_thumbnail(cls, document: IdentityDocument, source_path: Path):
        """Generate thumbnail for image documents"""
        try:
            from PIL import Image
            import io
            
            with Image.open(source_path) as img:
                img.thumbnail((200, 200))
                
                thumb_dir = source_path.parent / "thumbnails"
                thumb_dir.mkdir(exist_ok=True)
                
                thumb_path = thumb_dir / f"thumb_{source_path.name}"
                
                if document.mime_type == 'image/jpeg':
                    img.save(thumb_path, 'JPEG', quality=85)
                elif document.mime_type == 'image/png':
                    img.save(thumb_path, 'PNG', optimize=True)
                else:
                    img.convert('RGB').save(thumb_path, 'JPEG', quality=85)
                
                document.thumbnail_path = str(thumb_path)
                document.thumbnail_url = f"/documents/thumbnails/{thumb_path.relative_to(cls.BASE_UPLOAD_DIR)}"
                await document.save(update_fields=["thumbnail_path", "thumbnail_url"])
                
        except ImportError:
            print("PIL/Pillow not installed, thumbnail generation skipped")
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")

    @classmethod
    async def get_document_by_id(cls, document_id: str) -> Optional[IdentityDocument]:
        """Get document by ID"""
        return await IdentityDocument.filter(id=document_id).first()

    @classmethod
    async def get_document_file(cls, document_id: str) -> Optional[Tuple[Path, str]]:
        """
        Get document file path and mime type
        
        Args:
            document_id: Document ID
            
        Returns:
            Tuple of (file_path, mime_type) or None if not found
        """
        document = await cls.get_document_by_id(document_id)
        
        if not document:
            return None
        
        if not document.can_access:
            raise PermissionError("Document access has expired")
        
        if document.is_deleted:
            raise FileNotFoundError("Document has been deleted")
        
        file_path = Path(document.file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found at {file_path}")
        
        return file_path, document.mime_type

    @classmethod
    async def get_document_with_token(cls, document_id: str, access_token: str) -> Optional[IdentityDocument]:
        """Get document by ID with access token verification"""
        document = await IdentityDocument.filter(
            id=document_id,
            access_token=access_token,
            access_expires_at__gte=datetime.utcnow()
        ).first()
        
        return document

    @classmethod
    async def get_user_documents(
        cls,
        user_id: str,
        document_type: Optional[DocumentType] = None,
        verification_status: Optional[VerificationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[IdentityDocument]:
        """Get documents for a specific user"""
        query = IdentityDocument.filter(uploaded_by_id=user_id, is_deleted=False)
        
        if document_type:
            query = query.filter(document_type=document_type)
        
        if verification_status:
            query = query.filter(verification_status=verification_status)
        
        return await query.order_by("-uploaded_at").offset(offset).limit(limit).all()

    @classmethod
    async def delete_document(cls, document_id: str, soft_delete: bool = True) -> bool:
        """Delete a document"""
        document = await cls.get_document_by_id(document_id)
        
        if not document:
            return False
        
        if soft_delete:
            document.is_deleted = True
            document.deleted_at = datetime.utcnow()
            await document.save(update_fields=["is_deleted", "deleted_at"])
        else:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            if document.thumbnail_path and os.path.exists(document.thumbnail_path):
                os.remove(document.thumbnail_path)
            
            await document.delete()
        
        return True

    @classmethod
    async def cleanup_expired_documents(cls):
        """Clean up expired documents"""
        expired_docs = await IdentityDocument.filter(
            expires_at__lt=datetime.utcnow(),
            is_deleted=False
        ).all()
        
        for doc in expired_docs:
            await cls.delete_document(str(doc.id), soft_delete=False)

    @classmethod
    def get_document_url(cls, document: IdentityDocument) -> str:
        """Get document URL with access token if required"""
        if document.is_public or document.can_access:
            return document.file_url
        
        if document.access_token:
            return f"{document.file_url}?token={document.access_token}"
        
        return document.file_url

    @classmethod
    async def extract_document_data(cls, document_id: str) -> Dict[str, Any]:
        """Extract data from document using OCR (placeholder implementation)"""
        document = await cls.get_document_by_id(document_id)
        
        if not document:
            return {}
        
        extracted_data = {
            "document_type": document.document_type.name,
            "document_number": document.document_number,
            "uploaded_by": str(document.uploaded_by_id),
            "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
            "verification_status": document.verification_status.name,
            "file_info": document.file_info
        }
        
        if document.ocr_data:
            extracted_data["ocr_text"] = document.ocr_data.get("text", "")
            extracted_data["confidence"] = document.ocr_data.get("confidence", 0)
        
        if document.extracted_data:
            extracted_data.update(document.extracted_data)
        
        return extracted_data
