import random
from tortoise import fields, Model
from random_word import RandomWords
from tortoise.validators import MinLengthValidator, MaxLengthValidator
from models.defaults.property_catogories import PropertyCategory


related_fields = {
    "user": "models.User",
    "apartment_complex": "models.ApartmentComplex",
    "manager": "models.User",
    "amenities": "models.ApartmentAmenity",
    "rules": "models.ApartmentRules",
    "gallery": "models.ApartmentGallery",
}


class ApartmentComplex(Model):
    id = fields.CharField(pk=True, max_length=36)
    name = fields.CharField(max_length=200, default=None)
    description = fields.TextField(null=True)
    profile_picture = fields.CharField(max_length=500, null=True)
    theme_color = fields.CharField(max_length=7, default="#FFFFFF")
    year_built = fields.IntField(null=True)


    country = fields.CharField(max_length=100)
    county = fields.CharField(max_length=100)
    state = fields.CharField(max_length=100)
    city = fields.CharField(max_length=100)
    zip_code = fields.CharField(max_length=20)
    address = fields.TextField()
    latitude = fields.FloatField(null=True, index=True)
    longitude = fields.FloatField(null=True, index=True)
    contact_number = fields.CharField(max_length=20, null=True)
    
    category = fields.IntEnumField(PropertyCategory, default=PropertyCategory.APARTMENT)

   
    publisher = fields.ForeignKeyField(
        related_fields["user"],
        related_name="owned_apartments",
        on_delete=fields.CASCADE
    )
    
    managers = fields.ForeignKeyField(
        related_fields["manager"],
        related_name="managed_apartments",
        through="apartment_managers"
    )
    #gallery from apartment gallery
    #rules from apartment rules
    #amenities from apartment amenities
    
    
    total_units = fields.IntField(default=None, null=True)
    total_floors = fields.IntField(default=1)

    is_published = fields.BooleanField(default=False, index=True)
    is_active = fields.BooleanField(default=True)
    is_verified = fields.BooleanField(default=False, index=True)
    is_featured = fields.BooleanField(default=False, index=True)
    is_deleted = fields.BooleanField(default=False, index=True)
    is_blocked = fields.BooleanField(default=False, index=True)
    is_open_for_rent = fields.BooleanField(default=True,index=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    
    average_rating = fields.IntField(null=True, default=None, index=True)

    reviews_count = fields.IntField(default=None, null=True)

    class Meta:
        table = "apartment_complexes"

    @staticmethod
    async def generate_unique_id():
        # from models.apartment_complex import ApartmentComplex
        while True:
            new_id = f"AP-{random.randint(100000, 999999)}"
            exists = await ApartmentComplex.exists(id=new_id)
            if not exists:
                return new_id

    @staticmethod
    def generate_random_name():
        rw = RandomWords()
        word = rw.get_random_word() or "Residence"
        return f"{word.title()} Apartments"

    async def save(self, *args, **kwargs):
        if not self.id:
            self.id = await self.generate_unique_id()

        if not self.name:
            self.name = self.generate_random_name()

        await super().save(*args, **kwargs)
