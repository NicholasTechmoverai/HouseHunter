import os
from pathlib import Path
from tortoise import Tortoise
from .settings import settings
DB_URL = settings.DATABASE_URL 


MODEL_PATHS = [
    "models.apartment",
    "models.apartments",
    "models.for_rent",
    "models.universal",
    "models.defaults",
    "models.user",
    "models.house_agents",
    "models.reviews",
    "models.policy",
    "models.swap",
    "models.auth",
]

TORTOISE_ORM = {
    "connections": {"default": DB_URL},
    "apps": {
        "models": {
            "models": MODEL_PATHS + ["aerich.models"],
            "default_connection": "default",
        }
    },
}

class Config:
    BASE_DIR = Path(__file__).parent.parent  # Points to: HouseHunter/app
    UPLOADS_DIR = BASE_DIR / "uploads"

    UPLOAD_BASE = "uploads"
    PROPERTY_PATH = os.path.join(UPLOAD_BASE, "property")
    USER_PATH = os.path.join(UPLOAD_BASE, "users")
    RENTALS_PATH = os.path.join(UPLOAD_BASE, "rentals")

    DB_URL = settings.DATABASE_URL 
    REDIS_URL: str | None = settings.REDIS_URL


    TORTOISE_ORM = TORTOISE_ORM

    @classmethod
    async def init_db(cls, app):
        """Initialize Tortoise ORM with the config"""
        try:
            print(f"Initializing database with URL: {cls.DB_URL}")
            print(f"Model paths: {MODEL_PATHS}")
            
            await Tortoise.init(config=cls.TORTOISE_ORM)
            # await Tortoise.generate_schemas()
            
            print(f"✓ Tortoise initialized: {Tortoise._inited}")
            print(f"✓ Available apps: {list(Tortoise.apps.keys())}")
            
            conn = Tortoise.get_connection("default")
            print(f"✓ Database connection established: {conn}")

            print("✓ Database initialization complete")
            
        except Exception as e:
            print(f"✗ Error initializing database: {e}")
            import traceback
            traceback.print_exc()
            raise e

    @classmethod
    async def close_db(cls):
        """Close database connections"""
        await Tortoise.close_connections()
        print("✓ Database connections closed")
        
    
    #aerich init -t core.config.TORTOISE_ORM  -> to initiliaze aerich
    #aerich init-db
    #aerich migrate -> to create migration files
    #aerich upgrade -> to apply the migration files
    #aerich downgrade -> to revert the migration files


    
    """
    Enhanced database initialization with detailed debugging for schema generation errors.
    This version includes monkey-patching of Tortoise ORM's Field methods to provide
    comprehensive debug information when schema generation fails, especially for Enum fields.
    """
    # @classmethod
    # async def init_db(cls, app):
    #     """
    #     Initialize database with enhanced debugging for schema generation errors.
    #     """
    #     try:
    #         print("🔧 Initializing database...")
            
    #         await Tortoise.init(
    #             db_url=cls.DB_URL,
    #             modules={"models": cls.MODEL_PATHS},
    #         )
            
    #         # Enhanced monkey-patch with better error detection
    #         original_validate = Field.validate
    #         original_to_db_value = Field.to_db_value
            
    #         def debug_validate(self, value):
    #             """
    #             Debug wrapper for field validation.
    #             """
    #             try:
    #                 # Check if value has .value attribute (like Enums)
    #                 if hasattr(value, 'value'):
    #                     print(f"  DEBUG: Validating value with .value attribute: {value} -> {value.value}")
    #                     if isinstance(value.value, int):
    #                         print(f"  ⚠️ WARNING: {type(value).__name__} with .value = {value.value} (int)")
                    
    #                 return original_validate(self, value)
    #             except Exception as e:
    #                 print(f"\n🚨 VALIDATION ERROR in field: {self.__class__.__name__}")
    #                 print(f"   Value: {repr(value)}")
    #                 print(f"   Value type: {type(value).__name__}")
    #                 if hasattr(value, 'value'):
    #                     print(f"   value.value: {value.value} (type: {type(value.value).__name__})")
    #                 raise
            
    #         def debug_to_db_value(self, value, model):
    #             """
    #             Debug wrapper for to_db_value.
    #             """
    #             try:
    #                 # Extra debugging for problematic cases
    #                 field_name = getattr(self, 'model_field_name', 'unknown')
                    
    #                 # Check for enum-like values
    #                 if hasattr(value, 'value') and isinstance(value.value, int):
    #                     print(f"\n🔍 DEBUG: {model.__name__}.{field_name}")
    #                     print(f"   Processing enum-like value: {value}")
    #                     print(f"   .value attribute: {value.value} (type: {type(value.value).__name__})")
                    
    #                 return original_to_db_value(self, value, model)
    #             except Exception as e:
    #                 print(f"\n" + "="*80)
    #                 print("🚨 SCHEMA GENERATION ERROR")
    #                 print("="*80)
    #                 print(f"📝 Model: {model.__name__}")
    #                 print(f"📁 Module: {model.__module__}")
    #                 print(f"🔤 Field: {getattr(self, 'model_field_name', 'unknown')}")
    #                 print(f"📊 Field Type: {self.__class__.__name__}")
    #                 print(f"💾 Value: {repr(value)}")
    #                 print(f"📐 Value Type: {type(value).__name__}")
                    
    #                 if hasattr(value, '__class__'):
    #                     print(f"🎯 Value class: {value.__class__.__name__}")
    #                     print(f"🎯 Value module: {value.__class__.__module__}")
                    
    #                 if hasattr(value, 'value'):
    #                     print(f"🔍 value.value: {value.value} (type: {type(value.value).__name__})")
                    
    #                 # Get the actual field object from the model
    #                 field_name = getattr(self, 'model_field_name', None)
    #                 if field_name:
    #                     field_obj = model._meta.fields_map.get(field_name)
    #                     if field_obj:
    #                         print(f"\n🔍 FIELD DETAILS:")
    #                         print(f"   Field type in model: {field_obj.field_type}")
    #                         print(f"   Default: {getattr(field_obj, 'default', 'Not set')}")
    #                         print(f"   Nullable: {getattr(field_obj, 'null', False)}")
    #                         print(f"   Max length: {getattr(field_obj, 'max_length', 'N/A')}")
                    
    #                 print("\n💡 SUGGESTED FIX:")
    #                 if hasattr(value, 'value') and isinstance(value.value, int):
    #                     print("   This appears to be an Enum member.")
    #                     print("   For IntEnumField, use: default=Status.ACTIVE.value")
    #                     print("   For CharField with Enum, use: default='ACTIVE'")
                    
    #                 print("="*80)
    #                 raise
            
    #         # Apply the debug patches
    #         Field.validate = debug_validate
    #         Field.to_db_value = debug_to_db_value
            
    #         print("\n🔨 Generating database schemas...")
            
    #         await Tortoise.generate_schemas()
            
    #         # Restore original methods
    #         Field.validate = original_validate
    #         Field.to_db_value = original_to_db_value
            
    #         print("✅ Database initialized successfully!")
            
    #     except Exception as e:
    #         print(f"❌ Database initialization failed: {e}")
            
    #         # Restore original methods on error
    #         if 'original_validate' in locals():
    #             Field.validate = original_validate
    #         if 'original_to_db_value' in locals():
    #             Field.to_db_value = original_to_db_value
                
    #         raise