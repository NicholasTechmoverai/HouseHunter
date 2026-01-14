from tortoise import fields, Model
from uuid import uuid4
from typing import Optional
from enum import Enum

related_fields = {
    "apartment_complex": "models.ApartmentComplex",
    "amenities": "models.ApartmentAmenity",
    "rules": "models.ApartmentRules",
    "gallery": "models.ApartmentGallery",
    "block": "models.Block",
    "pricing": "models.ApartmentPricing",
    "user": "models.User"
}


class UnitStatus(str, Enum):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    UNDER_MAINTENANCE = "under_maintenance"
    RESERVED = "reserved"
    RENTED = "rented"


class Unit(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    code = fields.CharField(max_length=50, null=True, index=True)
    name = fields.CharField(max_length=200, null=True, index=True)
    description = fields.TextField(null=True)
    profile_picture = fields.CharField(max_length=500, null=True)
    theme_color = fields.CharField(max_length=7, default="#FFFFFF")
    year_built = fields.IntField(null=True)
    
    floor_number = fields.IntField(default=1)
    unit_number = fields.IntField(default=1)
    wing_or_section = fields.CharField(max_length=50, null=True)
    
    area_sqft = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    number_of_bedrooms = fields.IntField(default=1)
    number_of_bathrooms = fields.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    has_balcony = fields.BooleanField(default=False)
    has_terrace = fields.BooleanField(default=False)
    floor_plan_url = fields.CharField(max_length=500, null=True)
    
    block = fields.ForeignKeyField(
        related_fields["block"],
        related_name="units",
        on_delete=fields.CASCADE
    )
    
    price = fields.ForeignKeyField(
        related_fields["pricing"],
        related_name="pricing",
        null=True,
        on_delete=fields.SET_NULL
    )
    
    # current_tenant = fields.ForeignKeyField(
    #     related_fields["user"],
    #     related_name="rented_units",
    #     null=True,
    #     on_delete=fields.SET_NULL
    # )
    
    # current_owner = fields.ForeignKeyField(
    #     related_fields["user"],
    #     related_name="owned_units",
    #     null=True,
    #     on_delete=fields.SET_NULL
    # )
    
    
    status = fields.CharEnumField(
        UnitStatus,
        default=UnitStatus.VACANT,
        max_length=20,
        index=True
    )
    
    is_active = fields.BooleanField(default=True, index=True)
    is_under_maintenance = fields.BooleanField(default=False, index=True)
    maintenance_notes = fields.TextField(null=True)
    
    available_from = fields.DatetimeField(null=True)
    available_to = fields.DatetimeField(null=True)
    minimum_lease_months = fields.IntField(default=1)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    last_occupied_at = fields.DatetimeField(null=True)

    class Meta:
        table = "apartment_units"
        unique_together = (("block", "code"),)
        ordering = ["block", "floor_number", "unit_number"]
        indexes = [
            ("status", "is_active"),
            ("block_id", "floor_number"),
            ("area_sqft",),
            ("number_of_bedrooms",),
        ]
        
    @staticmethod
    async def generate_unique_code(block_id: str, block_code: Optional[str] = None) -> str:
        if not block_code:
            from .block import Block
            block = await Block.get(id=block_id)
            block_code = block.code
        
        existing_units = await Unit.filter(
            block_id=block_id
        ).values_list("code", flat=True)
        
        existing_codes = set(existing_units)
        
        for floor in range(1, 100):
            for unit in range(1, 100):
                code = f"{block_code}-{floor}{unit:02d}"
                if code not in existing_codes:
                    return code
        
        counter = 1
        while True:
            code = f"{block_code}-U{counter:03d}"
            if code not in existing_codes:
                return code
            counter += 1
    
    @staticmethod
    async def generate_unit_name(code: str, block_name: str) -> str:
        return f"Unit {code} - {block_name}"
    
    async def save(self, *args, **kwargs):
        if not self.code and self.block_id:
            block = await self.block
            self.code = await self.generate_unique_code(
                block_id=str(self.block_id),
                block_code=block.code
            )
        
        if not self.name and self.code and self.block_id:
            block = await self.block
            self.name = await self.generate_unit_name(self.code, block.name)
        
        if self.code and not self.unit_number:
            try:
                numeric_part = ''.join(filter(str.isdigit, self.code))
                if numeric_part:
                    self.unit_number = int(numeric_part[-2:])
            except (ValueError, IndexError):
                pass
        
        if self.is_under_maintenance and self.status != UnitStatus.UNDER_MAINTENANCE:
            self.status = UnitStatus.UNDER_MAINTENANCE
        elif not self.is_under_maintenance and self.status == UnitStatus.UNDER_MAINTENANCE:
            self.status = UnitStatus.VACANT
        
        if self.status == UnitStatus.OCCUPIED and not self.last_occupied_at:
            self.last_occupied_at = fields.timezone.now()
        
        await super().save(*args, **kwargs)
    
    @classmethod
    async def create_unit(
        cls,
        block_id: str,
        floor_number: int = 1,
        area_sqft: Optional[float] = None,
        number_of_bedrooms: int = 1,
        **kwargs
    ) -> "Unit":
        unit = cls(
            block_id=block_id,
            floor_number=floor_number,
            area_sqft=area_sqft,
            number_of_bedrooms=number_of_bedrooms,
            **kwargs
        )
        await unit.save()
        return unit
    
    async def update_status(self, new_status: UnitStatus, notes: Optional[str] = None):
        valid_transitions = {
            UnitStatus.VACANT: [UnitStatus.OCCUPIED, UnitStatus.RESERVED, UnitStatus.UNDER_MAINTENANCE],
            UnitStatus.OCCUPIED: [UnitStatus.VACANT, UnitStatus.UNDER_MAINTENANCE],
            UnitStatus.UNDER_MAINTENANCE: [UnitStatus.VACANT],
            UnitStatus.RESERVED: [UnitStatus.OCCUPIED, UnitStatus.VACANT],
            UnitStatus.RENTED: [UnitStatus.VACANT, UnitStatus.OCCUPIED],
        }
        
        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        self.status = new_status
        self.is_under_maintenance = new_status == UnitStatus.UNDER_MAINTENANCE
        
        if notes:
            self.maintenance_notes = notes
        
        await self.save(update_fields=["status", "is_under_maintenance", "maintenance_notes", "updated_at"])
    
    async def get_unit_details(self) -> dict:
        block = await self.block
        amenities_count = await self.special_amenities.all().count()
        gallery_count = await self.gallery.all().count()
        
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "status": self.status.value,
            "block": {
                "id": str(block.id),
                "code": block.code,
                "name": block.name,
            },
            "location": {
                "floor": self.floor_number,
                "unit_number": self.unit_number,
                "wing": self.wing_or_section,
            },
            "specifications": {
                "area_sqft": float(self.area_sqft) if self.area_sqft else None,
                "bedrooms": self.number_of_bedrooms,
                "bathrooms": float(self.number_of_bathrooms),
                "has_balcony": self.has_balcony,
                "has_terrace": self.has_terrace,
            },
            "amenities_count": amenities_count,
            "gallery_count": gallery_count,
            "is_under_maintenance": self.is_under_maintenance,
            "year_built": self.year_built,
            "available_from": self.available_from.isoformat() if self.available_from else None,
            "available_to": self.available_to.isoformat() if self.available_to else None,
        }
    
    async def assign_to_tenant(self, tenant_id: str, start_date: Optional[str] = None):
        from datetime import datetime
        
        self.current_tenant_id = tenant_id
        self.status = UnitStatus.OCCUPIED
        
        if start_date:
            self.last_occupied_at = datetime.fromisoformat(start_date)
        else:
            self.last_occupied_at = fields.timezone.now()
        
        await self.save()
    
    def __str__(self):
        return f"{self.code} - {self.name or 'Unit'}"