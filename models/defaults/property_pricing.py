from tortoise import fields, Model
from uuid import uuid4
from enum import Enum

class RentFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NINE_MONTHLY = "three_quarterly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "halfyearly"
    YEARLY = "yearly"



class BasePricing(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    rent = fields.DecimalField(max_digits=12, decimal_places=2,default=0, null=True)
    rent_frequency = fields.CharEnumField(RentFrequency, default=RentFrequency.MONTHLY, max_length=10)
    minimum_lease_months = fields.IntField(default=1)

    deposit_amount = fields.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_months = fields.IntField(default=0)
    is_deposit_refundable = fields.BooleanField(default=True)
    
    discount = fields.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = fields.CharField(max_length=10, default="KES")  

    sort_order = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["sort_order", "created_at"]



class ExtraFees(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    code = fields.CharField(max_length=50)      # water, electricity, internet, custom
    name = fields.CharField(max_length=100)    # Water, Electricity, Parking
    amount = fields.DecimalField(max_digits=12, decimal_places=2,null=True)
    currency = fields.CharField(max_length=10, default="KES")
    # description =  fields.CharField(max_length=500) 
    is_included = fields.BooleanField(default=False)
    sort_order = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
 
    class Meta:
        abstract = True
        ordering = ["sort_order", "created_at"]
    

