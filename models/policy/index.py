from tortoise.models import Model
from tortoise import fields
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import IntEnum


class PolicyType(IntEnum):
    """Types of policies"""
    PRIVACY = 1
    TERMS = 2
    COOKIE = 3
    ACCEPTABLE_USE = 4
    COMMUNITY_GUIDELINES = 5
    REFUND = 6
    CANCELLATION = 7
    SHIPPING = 8
    SERVICE = 9
    LEGAL = 10
    SAFETY = 11
    ACCESSIBILITY = 12
    ENVIRONMENTAL = 13
    ETHICS = 14
    DATA_PROCESSING = 15
    SECURITY = 16
    COMPLIANCE = 17


class PolicyStatus(IntEnum):
    """Status of policies"""
    DRAFT = 1
    ACTIVE = 2
    INACTIVE = 3
    ARCHIVED = 4
    DELETED = 5
    PENDING_REVIEW = 6
    UNDER_REVISION = 7


class PolicyAudience(IntEnum):
    """Target audience for policies"""
    ALL_USERS = 1
    REGISTERED_USERS = 2
    ADMINISTRATORS = 3
    EMPLOYEES = 4
    PARTNERS = 5
    CUSTOMERS = 6
    SUPPLIERS = 7
    PUBLIC = 8
    INTERNAL = 9
    EXTERNAL = 10


class PolicyRegion(IntEnum):
    """Geographic regions for policies"""
    GLOBAL = 1
    NORTH_AMERICA = 2
    EUROPE = 3
    ASIA_PACIFIC = 4
    AFRICA = 5
    LATIN_AMERICA = 6
    MIDDLE_EAST = 7
    EU = 8
    UK = 9
    USA = 10
    CALIFORNIA = 11  # For CCPA
    GDPR = 12        # For GDPR compliance


class PolicyLanguage(IntEnum):
    """Supported languages for policies"""
    ENGLISH = 1
    SPANISH = 2
    FRENCH = 3
    GERMAN = 4
    CHINESE = 5
    JAPANESE = 6
    ARABIC = 7
    PORTUGUESE = 8
    RUSSIAN = 9
    ITALIAN = 10
    KOREAN = 11
    HINDI = 12
    SWAHILI = 13
    LOCAL = 14       # Local language based on region