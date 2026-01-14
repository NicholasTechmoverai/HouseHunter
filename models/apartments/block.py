from tortoise import fields, Model
from uuid import uuid4
from typing import Optional

related_fields = {
    "apartment_complex": "models.ApartmentComplex",
    "amenities": "models.ApartmentAmenity",
    "rules": "models.ApartmentRules",
    "gallery": "models.ApartmentGallery",
    "pricing": "models.ApartmentPricing",
}


class Block(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    code = fields.CharField(max_length=50, default=None, index=True)
    name = fields.CharField(max_length=200, default=None, index=True)
    description = fields.TextField(null=True)
    profile_picture = fields.CharField(max_length=500, null=True)
    theme_color = fields.CharField(max_length=7, default="#FFFFFF")
    year_built = fields.IntField(null=True)
    
    apartment_complex = fields.ForeignKeyField(
        related_fields["apartment_complex"],
        related_name="blocks",
        on_delete=fields.CASCADE
    )
    #gallery
    #rules
    #amenities
    
    price = fields.ForeignKeyField(
        related_fields["pricing"],
        related_name="block_price",
        null=True,
        on_delete=fields.SET_NULL
    )
    
    total_floors = fields.IntField(default=1)
    total_units = fields.IntField(default=0)
    units_available = fields.IntField(default=0)
    
    is_active = fields.BooleanField(default=True, index=True)
    is_under_maintenance = fields.BooleanField(default=False, index=True)
    maintenance_notes = fields.TextField(null=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "apartment_blocks"
        unique_together = (("apartment_complex", "code"),)
        ordering = ["code"]
        
    @staticmethod
    async def generate_unique_code(apartment_complex_id: str, prefix: str = "BLOCK") -> str:
        existing_blocks = await Block.filter(
            apartment_complex_id=apartment_complex_id
        ).values_list("code", flat=True)
        
        if not existing_blocks:
            return f"{prefix}-A"
        
        suffixes = []
        for code in existing_blocks:
            if code and f"{prefix}-" in code:
                suffix = code.split(f"{prefix}-")[-1]
                if suffix and suffix.isalpha() and len(suffix) == 1:
                    suffixes.append(suffix.upper())
        
        if not suffixes:
            return f"{prefix}-A"
        
        used_letters = set(suffixes)
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        for letter in alphabet:
            if letter not in used_letters:
                return f"{prefix}-{letter}"
        
        for letter1 in alphabet:
            for letter2 in alphabet:
                combined = f"{letter1}{letter2}"
                if combined not in used_letters:
                    return f"{prefix}-{combined}"
        
        numeric = 1
        while True:
            code = f"{prefix}-{numeric}"
            if code not in existing_blocks:
                return code
            numeric += 1

    async def save(self, *args, **kwargs):
        if not self.code and self.apartment_complex_id:
            self.code = await self.generate_unique_code(
                apartment_complex_id=self.apartment_complex_id
            )
        
        if not self.name and self.code:
            self.name = f"{self.code} Building"
        
        if self.units_available > self.total_units:
            self.units_available = self.total_units
        
        await super().save(*args, **kwargs)
    
    # @classmethod
    # async def create_block(
    #     cls,
    #     apartment_complex_id: str,
    #     total_floors: int = 1,
    #     total_units: int = 0,
    #     **kwargs
    # ) -> "Block":
    #     """
    #     Factory method to create a new block with proper defaults.
        
    #     Args:
    #         apartment_complex_id: ID of the parent complex
    #         total_floors: Number of floors in the block
    #         total_units: Total units in the block
    #         **kwargs: Additional block attributes
            
    #     Returns:
    #         Created Block instance
    #     """
    #     block = cls(
    #         apartment_complex_id=apartment_complex_id,
    #         total_floors=total_floors,
    #         total_units=total_units,
    #         units_available=total_units,  # Initially all units are available
    #         **kwargs
    #     )
    #     await block.save()
    #     return block
    
    # async def update_unit_counts(self, total_units: Optional[int] = None):
    #     """
    #     Update unit counts for the block.
        
    #     Args:
    #         total_units: New total units (optional)
    #     """
    #     if total_units is not None:
    #         self.total_units = total_units
    #         # Adjust available units if needed
    #         if self.units_available > total_units:
    #             self.units_available = total_units
        
    #     await self.save(update_fields=["total_units", "units_available", "updated_at"])
    
    # async def add_special_amenity(self, amenity_id: str):
    #     """Add a special amenity to this block."""
    #     from .models import ApartmentAmenity
        
    #     amenity = await ApartmentAmenity.get(id=amenity_id)
        
    #     # Check if already added
    #     existing = await self.special_amenities.filter(id=amenity_id).exists()
    #     if not existing:
    #         await self.special_amenities.add(amenity)
    
    # async def get_block_summary(self) -> dict:
    #     """
    #     Get summary information about the block.
        
    #     Returns:
    #         Dictionary with block summary
    #     """
    #     amenities_count = await self.special_amenities.all().count()
    #     gallery_count = await self.gallery.all().count()
        
    #     return {
    #         "id": str(self.id),
    #         "code": self.code,
    #         "name": self.name,
    #         "total_floors": self.total_floors,
    #         "total_units": self.total_units,
    #         "units_available": self.units_available,
    #         "occupancy_rate": (
    #             ((self.total_units - self.units_available) / self.total_units * 100)
    #             if self.total_units > 0 else 0
    #         ),
    #         "special_amenities_count": amenities_count,
    #         "gallery_count": gallery_count,
    #         "is_under_maintenance": self.is_under_maintenance,
    #         "year_built": self.year_built,
    #     }
    
    # def __str__(self):
    #     return f"{self.code} - {self.name or 'Unnamed Block'}"