from tortoise import fields, Model
from uuid import uuid4

class BaseRules(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    title = fields.CharField(max_length=200, null=True)
    description = fields.TextField(null=True)
    is_mandatory = fields.BooleanField(default=True)  # enforce rules
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["title"]
