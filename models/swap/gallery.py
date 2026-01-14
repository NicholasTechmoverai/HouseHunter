from tortoise import fields, Model
from uuid import uuid4

from models.defaults.gallery import BaseGallery

related_fields = {
    "apartment_complex": "models.ApartmentComplex",
    "block": "models.Block",
    "unit": "models.Unit",

}

class ApartmentGallery(BaseGallery):
    apartment = fields.ForeignKeyField(
        related_fields["apartment_complex"],
        related_name="gallery",
        null=True,
        on_delete=fields.CASCADE
    )
    block = fields.ForeignKeyField(
        related_fields["block"],
        related_name="gallery",
        null=True,
        on_delete=fields.CASCADE
    )
    unit = fields.ForeignKeyField(
        related_fields["unit"],
        related_name="gallery",
        null=True,
        on_delete=fields.CASCADE
    )
   
    class Meta:
        table = "apartment_gallery"
