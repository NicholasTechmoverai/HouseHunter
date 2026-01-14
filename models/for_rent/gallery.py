from tortoise import fields, Model
from uuid import uuid4

from models.defaults.gallery import BaseGallery

related_fields = {
    "rental_complex": "models.RentalComplex",
}

class RentalGallery(BaseGallery):
    rental = fields.ForeignKeyField(
        "models.RentalComplex",
        related_name="gallery",
        on_delete=fields.CASCADE
    )
    class Meta:
        table = "rental_gallery"
