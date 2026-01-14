from models.defaults.amenities import BaseAmenity
from tortoise import fields, Model

related_fields = {
    "apartment_complex": "models.ApartmentComplex", 
    "rental_unit": "models.Unit",
    "amenity_category": "models.AmenityCategory",
    "rental_amenity": "models.RentalAmenity"
    }

class ApartmentAmenity(BaseAmenity):
    category = fields.ForeignKeyField(
        related_fields["amenity_category"],
        related_name="apart_amenities",
        null=True,
        on_delete=fields.SET_NULL
    )
    apartment_complexes = fields.ManyToManyField(
        related_fields["apartment_complex"],
        related_name="amenities",
        through="apartment_amenities_m2m"
    )

    class Meta:
        table = "apartment_amenities"
        ordering = ["sort_order", "name"]


