from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
import json
from enum import IntEnum
from datetime import datetime, timedelta

from ..defaults.index import TimestampMixin


class SearchQueryType(IntEnum):
    PROPERTY = 1
    JOB = 2
    PRODUCT = 3
    SERVICE = 4
    USER = 5
    CONTENT = 6


class SearchSource(IntEnum):
    WEB = 1
    MOBILE = 2
    API = 3
    BOT = 4


class SearchStatus(IntEnum):
    ACTIVE = 1
    SAVED = 2
    DELETED = 3
    EXPIRED = 4


class UserSearch(Model, TimestampMixin):
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    user = fields.ForeignKeyField(
        'models.User',
        related_name='searches',
        null=True,
        on_delete=fields.SET_NULL,
        index=True
    )
    
    search_id = fields.CharField(max_length=50, unique=True, index=True)
    
    query_type = fields.IntEnumField(
        SearchQueryType, 
        default=SearchQueryType.PROPERTY,
        index=True
    )
    
    search_text = fields.CharField(max_length=500, null=True)
    
    filters = fields.JSONField(default=dict)
    
    location_data = fields.JSONField(default=dict)
    
    sort_by = fields.CharField(max_length=50, default='relevance')
    sort_order = fields.CharField(max_length=10, default='desc')
    
    page = fields.IntField(default=1, validators=[MinValueValidator(1)])
    page_size = fields.IntField(default=20, validators=[
        MinValueValidator(1),
        MaxValueValidator(100)
    ])
    
    result_count = fields.IntField(default=0)
    total_pages = fields.IntField(default=0)
    total_results = fields.IntField(default=0)
    
    last_executed = fields.DatetimeField(null=True)
    execution_count = fields.IntField(default=0)
    average_execution_time = fields.FloatField(default=0)
    
    status = fields.IntEnumField(SearchStatus, default=SearchStatus.ACTIVE)
    is_saved = fields.BooleanField(default=False)
    is_alert = fields.BooleanField(default=False)
    
    alert_frequency = fields.CharField(max_length=20, null=True)
    last_alert_sent = fields.DatetimeField(null=True)
    next_alert_at = fields.DatetimeField(null=True)
    
    source = fields.IntEnumField(SearchSource, default=SearchSource.WEB)
    user_agent = fields.TextField(null=True)
    ip_address = fields.CharField(max_length=45, null=True)
    
    device_info = fields.JSONField(default=dict)
    
    referrer_url = fields.TextField(null=True)
    search_session_id = fields.CharField(max_length=100, null=True, index=True)
    
    tags = fields.JSONField(default=list)
    
    metadata = fields.JSONField(default=dict)
    
    results_preview = fields.JSONField(default=list)
    
    cost_estimate_min = fields.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True
    )
    cost_estimate_max = fields.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True
    )
    
    is_advanced = fields.BooleanField(default=False)
    filter_count = fields.IntField(default=0)
    
    confidence_score = fields.FloatField(default=0)
    relevance_feedback = fields.JSONField(default=dict)
    
    shared_with = fields.JSONField(default=list)
    
    notes = fields.TextField(null=True)
    
    expiration_date = fields.DatetimeField(null=True)
    
    last_modified_by = fields.ForeignKeyField(
        'models.User',
        related_name='modified_searches',
        null=True,
        on_delete=fields.SET_NULL
    )

    class Meta:
        table = "user_searches"
        indexes = [
            ("user_id", "status"),
            ("user_id", "is_saved"),
            ("user_id", "query_type"),
            ("search_id",),
            ("search_session_id",),
            ("last_executed",),
            ("next_alert_at",),
            ("status", "expiration_date"),
            ("user_id", "created_at"),
            ("search_text",),
        ]
        ordering = ["-last_executed"]

    @property
    def has_filters(self) -> bool:
        return bool(self.filters) and len(self.filters) > 0

    @property
    def is_expired(self) -> bool:
        if not self.expiration_date:
            return False
        return datetime.utcnow() > self.expiration_date

    @property
    def search_url(self) -> str:
        base_url = "/search"
        params = []
        
        if self.search_text:
            params.append(f"q={self.search_text}")
        
        if self.filters:
            for key, value in self.filters.items():
                if isinstance(value, list):
                    for item in value:
                        params.append(f"{key}={item}")
                else:
                    params.append(f"{key}={value}")
        
        params.append(f"sort={self.sort_by}")
        params.append(f"order={self.sort_order}")
        
        return f"{base_url}?{'&'.join(params)}"

    async def execute_search(self, save_results: bool = False):
        self.last_executed = datetime.utcnow()
        self.execution_count += 1
        
        if save_results and self.result_count > 0:
            self.results_preview = await self.get_top_results(5)
        
        await self.save(update_fields=[
            "last_executed", 
            "execution_count", 
            "results_preview"
        ])

    async def get_top_results(self, count: int = 5) -> List[Dict[str, Any]]:
        return []

    async def save_search(self, name: Optional[str] = None):
        self.is_saved = True
        self.status = SearchStatus.SAVED
        
        if name and not self.search_text:
            self.search_text = name
        
        await self.save(update_fields=["is_saved", "status", "search_text"])

    async def create_alert(self, frequency: str = "daily"):
        self.is_alert = True
        self.alert_frequency = frequency
        self.next_alert_at = self.calculate_next_alert_time()
        
        await self.save(update_fields=[
            "is_alert", 
            "alert_frequency", 
            "next_alert_at"
        ])

    def calculate_next_alert_time(self) -> datetime:
        now = datetime.utcnow()
        
        if self.alert_frequency == "realtime":
            return now
        elif self.alert_frequency == "hourly":
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif self.alert_frequency == "daily":
            return now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif self.alert_frequency == "weekly":
            return now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=7)
        else:
            return now + timedelta(days=1)

    async def update_results_count(self, count: int, total: Optional[int] = None):
        self.result_count = count
        
        if total:
            self.total_results = total
            self.total_pages = (total + self.page_size - 1) // self.page_size
        
        await self.save(update_fields=[
            "result_count", 
            "total_results", 
            "total_pages"
        ])

    async def increment_filter_count(self):
        self.filter_count = len(self.filters) if self.filters else 0
        self.is_advanced = self.filter_count > 3
        
        await self.save(update_fields=["filter_count", "is_advanced"])

    async def share_with_users(self, user_ids: List[str]):
        if not self.shared_with:
            self.shared_with = []
        
        for user_id in user_ids:
            if user_id not in self.shared_with:
                self.shared_with.append(user_id)
        
        await self.save(update_fields=["shared_with"])

    async def add_tag(self, tag: str):
        if not self.tags:
            self.tags = []
        
        if tag not in self.tags:
            self.tags.append(tag)
        
        await self.save(update_fields=["tags"])

    async def update_relevance_feedback(self, item_id: str, relevant: bool):
        if not self.relevance_feedback:
            self.relevance_feedback = {"positive": [], "negative": []}
        
        if relevant:
            if item_id not in self.relevance_feedback["positive"]:
                self.relevance_feedback["positive"].append(item_id)
            if item_id in self.relevance_feedback["negative"]:
                self.relevance_feedback["negative"].remove(item_id)
        else:
            if item_id not in self.relevance_feedback["negative"]:
                self.relevance_feedback["negative"].append(item_id)
            if item_id in self.relevance_feedback["positive"]:
                self.relevance_feedback["positive"].remove(item_id)
        
        await self.save(update_fields=["relevance_feedback"])

    @classmethod
    async def find_similar_searches(
        cls, 
        user_id: str, 
        query_text: str, 
        filters: Dict[str, Any], 
        max_results: int = 5
    ) -> List['UserSearch']:
        return await cls.filter(
            user_id=user_id,
            search_text__icontains=query_text[:50],
            status=SearchStatus.ACTIVE
        ).order_by("-last_executed").limit(max_results)

    async def duplicate_search(self, new_user_id: Optional[str] = None) -> 'UserSearch':
        new_search = await UserSearch.create(
            user_id=new_user_id if new_user_id else self.user_id,
            search_text=self.search_text,
            query_type=self.query_type,
            filters=self.filters.copy() if self.filters else {},
            location_data=self.location_data.copy() if self.location_data else {},
            sort_by=self.sort_by,
            sort_order=self.sort_order,
            page=self.page,
            page_size=self.page_size,
            source=self.source,
            device_info=self.device_info.copy() if self.device_info else {},
            tags=self.tags.copy() if self.tags else []
        )
        
        return new_search

    async def expire_search(self):
        self.status = SearchStatus.EXPIRED
        self.expiration_date = datetime.utcnow()
        
        await self.save(update_fields=["status", "expiration_date"])


    @property
    def filter_summary(self) -> Dict[str, str]:
        if not isinstance(self.filters, dict) or not self.filters:
            return {}

        summary: Dict[str, str] = {}

        for key, value in self.filters.items():
            try:
                if value is None:
                    summary[key] = "none"

                elif isinstance(value, (list, tuple, set)):
                    summary[key] = f"{len(value)} items"

                elif isinstance(value, dict):
                    summary[key] = f"{len(value)} fields"

                else:
                    summary[key] = str(value)

            except Exception:
                summary[key] = "invalid"

        return summary
