from tortoise import BaseDBAsyncClient


from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    ALTER TABLE users
        DROP COLUMN IF EXISTS latitude,
        DROP COLUMN IF EXISTS longitude,
        DROP COLUMN IF EXISTS current_state;

    ALTER TABLE users
        ADD COLUMN IF NOT EXISTS current_city VARCHAR(100),
        ADD COLUMN IF NOT EXISTS current_county VARCHAR(100),
        ADD COLUMN IF NOT EXISTS current_country VARCHAR(100),
        ADD COLUMN IF NOT EXISTS current_postal_code VARCHAR(20),
        ADD COLUMN IF NOT EXISTS current_address TEXT,
        ADD COLUMN IF NOT EXISTS current_latitude DOUBLE PRECISION,
        ADD COLUMN IF NOT EXISTS current_longitude DOUBLE PRECISION,

        ADD COLUMN IF NOT EXISTS home_city VARCHAR(100),
        ADD COLUMN IF NOT EXISTS home_county VARCHAR(100),
        ADD COLUMN IF NOT EXISTS home_country VARCHAR(100),
        ADD COLUMN IF NOT EXISTS home_latitude DOUBLE PRECISION,
        ADD COLUMN IF NOT EXISTS home_longitude DOUBLE PRECISION;

    CREATE INDEX IF NOT EXISTS idx_users_home_lat_lng
        ON users (home_latitude, home_longitude);
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    DROP INDEX IF EXISTS idx_users_home_lat_lng;

    ALTER TABLE users
        DROP COLUMN IF EXISTS current_city,
        DROP COLUMN IF EXISTS current_county,
        DROP COLUMN IF EXISTS current_country,
        DROP COLUMN IF EXISTS current_postal_code,
        DROP COLUMN IF EXISTS current_address,
        DROP COLUMN IF EXISTS current_latitude,
        DROP COLUMN IF EXISTS current_longitude,
        DROP COLUMN IF EXISTS home_city,
        DROP COLUMN IF EXISTS home_county,
        DROP COLUMN IF EXISTS home_country,
        DROP COLUMN IF EXISTS home_latitude,
        DROP COLUMN IF EXISTS home_longitude;

    ALTER TABLE users
        ADD COLUMN latitude DOUBLE PRECISION,
        ADD COLUMN longitude DOUBLE PRECISION,
        ADD COLUMN current_state VARCHAR(100);
    """
