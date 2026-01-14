from tortoise import fields, Model
from models.defaults.rules import BaseRules

class RentalRules(BaseRules):
    rental = fields.ForeignKeyField(
        "models.RentalComplex",
        related_name="rules",
        on_delete=fields.CASCADE
    )

    class Meta:
        table = "rental_rules"
