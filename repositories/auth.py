import random
from uuid import uuid4
from datetime import datetime, timedelta,timezone
from models.auth.verification_code import VerificationCodes, VerificationType
from repositories.user import get_user_repo

async def generate_verification_code(length: int = 6) -> str:
    range_start = 10**(length - 1)
    range_end = (10**length) - 1
    return str(random.randint(range_start, range_end))


def get_verification_repo():
    return VerificationRepository()


class VerificationRepository:
    def __init__(self):
        self.model = VerificationCodes
    
    async def create_verification_code(
        self, 
        user_id: str, 
        code_type: str, 
        identifier: str = None,
        code: str = None,
        expires_in_minutes: int = 15
    ) -> VerificationCodes:
        if code is None:
            code = await generate_verification_code()
        
        existing_codes = await self.model.filter(
            user_id=user_id,
            type=code_type,
            status="pending",
            is_used=False
        ).all()
        
        for existing_code in existing_codes:
            if not existing_code.is_expired():
                await existing_code.mark_as_expired()
        
        verification_code = await self.model.create(
            id=str(uuid4()),
            user_id=user_id,
            code=code,
            type=code_type,
            identifier=identifier,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        )
        
        return verification_code
    
    async def get_valid_code(
        self, 
        user_id: str, 
        code: str, 
        code_type: str
    ) -> VerificationCodes:
        return await self.model.get_or_none(
            user_id=user_id,
            code=code,
            type=code_type,
            status="pending",
            is_used=False
        )
    
    async def verify_code(
        self, 
        user_id: str, 
        code: str, 
        code_type: str
    ) -> bool:
        verification_code = await self.get_valid_code(user_id, code, code_type)
        
        if not verification_code:
            return {
                "success": False,
                "message": "Invalid verification code"
            }
        
        if verification_code.is_expired():
            await verification_code.mark_as_expired()
            return False
        
        await verification_code.mark_as_used()
        return {
            "success": True,
            "message": "Verification code is valid"
        }
    
    async def get_user_codes(
        self, 
        user_id: str, 
        code_type: str = None,
        only_valid: bool = True
    ) -> list[VerificationCodes]:
        query = self.model.filter(user_id=user_id)
        
        if code_type:
            query = query.filter(type=code_type)
        
        if only_valid:
            query = query.filter(status="pending", is_used=False)
        
        return await query.all()
    
    async def cleanup_expired_codes(self, hours_old: int = 24):
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_old)
        
        expired_codes = await self.model.filter(
            created_at__lt=cutoff_time,
            status="pending"
        ).all()
        
        for code in expired_codes:
            await code.mark_as_expired()
        
        return len(expired_codes)
    
    async def resend_code(
        self, 
        user_id: str, 
        code_type: str,
        identifier: str = None,
        expires_in_minutes: int = 15
    ) -> VerificationCodes:
        await self.invalidate_user_codes(user_id, code_type)
        return await self.create_verification_code(
            user_id=user_id,
            code_type=code_type,
            identifier=identifier,
            expires_in_minutes=expires_in_minutes
        )
    
    async def invalidate_user_codes(self, user_id: str, code_type: str):
        active_codes = await self.get_user_codes(user_id, code_type, only_valid=True)
        
        for code in active_codes:
            await code.mark_as_expired()

def get_verification_repo():
    return VerificationRepository()