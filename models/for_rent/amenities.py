from models.defaults.amenities import BaseAmenity
from tortoise import fields, Model

class RentalAmenity(BaseAmenity):
    rental = fields.ForeignKeyField(
        "models.RentalComplex",
        related_name="amenities",
        on_delete=fields.CASCADE
    )
    category = fields.ForeignKeyField(
        "models.AmenityCategory",
        related_name="categories",
        null=True,
        on_delete=fields.SET_NULL
    )
    

    class Meta:
        table = "rental_amenities"
        ordering = ["sort_order", "name"]