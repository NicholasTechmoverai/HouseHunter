from tortoise import fields, Model
from uuid import uuid4  
from models.defaults.rules import BaseRules

related_fields = {
    "apartment_complex": "models.ApartmentComplex",
}

class ApartmentRules(BaseRules):
    apartment = fields.ForeignKeyField(
        "models.ApartmentComplex",
        related_name="rules", 
        null=True,
        on_delete=fields.CASCADE
    )
    block = fields.ForeignKeyField(
        "models.Block",
        related_name="rules", 
        null=True,
        on_delete=fields.CASCADE
    )
    unit = fields.ForeignKeyField(
        "models.Unit",
        related_name="rules",
        null=True,
        on_delete=fields.CASCADE
    )


    class Meta:
        table = "apartment_rules"
