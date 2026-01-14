from tortoise import fields, Model
from uuid import uuid4

from models.defaults.property_pricing import BasePricing

related_fields = {
    "apartment_complex": "models.ApartmentComplex",
}

class ApartmentPricing(BasePricing):
    apartment = fields.ForeignKeyField(
        related_fields["apartment_complex"],
        related_name="pricing",
        on_delete=fields.CASCADE
    )

    class Meta:
        table = "unit_pricing"
