from tortoise import fields, Model
from uuid import uuid4

from models.defaults.property_pricing import BasePricing,ExtraFees

related_fields = {
    "rental_complex": "models.RentalComplex",
}

class RentalPricingExtraFees(ExtraFees):
    pricing = fields.ForeignKeyField(
        "models.RentalPricing",
        related_name="fees",
        on_delete=fields.CASCADE
    )

    class Meta:
        table = "rental_extra_fee"


class RentalPricing(BasePricing):

    fees: fields.ReverseRelation["RentalPricingExtraFees"]

    class Meta:
        table = "rental_pricing"



