from tortoise import Tortoise

async def init_models():
    await Tortoise.init(models={
        'models': [
            "app.models.apartments",
            "app.models.for_rent",
            "app.models.universal",
            "app.models.user",
            # ... other models
        ]
    })