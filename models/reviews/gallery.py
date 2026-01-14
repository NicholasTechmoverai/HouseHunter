from tortoise import fields, Model
from uuid import uuid4

from models.defaults.gallery import BaseGallery

related_fields = {
    "review": "models.Review",
    "reply": "models.ReviewReply",
}

class ReviewGallery(BaseGallery):
    review = fields.ForeignKeyField(
        related_fields["review"],
        related_name="review",
        null=True,
        on_delete=fields.CASCADE
    )
    review_reply = fields.ForeignKeyField(
        related_fields["reply"],
        related_name="review",
        null=True,
        on_delete=fields.CASCADE
    )
   
    class Meta:
        table = "reviews_gallery"
