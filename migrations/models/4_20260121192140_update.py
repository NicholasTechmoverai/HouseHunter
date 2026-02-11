from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_users_home_la_0cd7d1";
        ALTER TABLE "rental_extra_fee" ADD "description" VARCHAR(500) NOT NULL;
        CREATE TABLE IF NOT EXISTS "agents" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "deleted_at" TIMESTAMPTZ,
    "id" UUID NOT NULL  PRIMARY KEY,
    "agency_name" VARCHAR(200),
    "agency_type" VARCHAR(19) NOT NULL  DEFAULT 'individual',
    "agency_id" VARCHAR(100),
    "tax_id" VARCHAR(50),
    "public_id" VARCHAR(50) NOT NULL UNIQUE,
    "license_number" VARCHAR(100),
    "license_status" VARCHAR(10) NOT NULL  DEFAULT 'unlicensed',
    "license_expiry_date" DATE,
    "office_phone" VARCHAR(20),
    "mobile_phone" VARCHAR(20),
    "whatsapp_number" VARCHAR(20),
    "secondary_email" VARCHAR(255),
    "country" VARCHAR(100) NOT NULL,
    "state" VARCHAR(100) NOT NULL,
    "county" VARCHAR(100),
    "city" VARCHAR(100) NOT NULL,
    "address" TEXT,
    "postal_code" VARCHAR(20),
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "website" VARCHAR(255),
    "facebook_url" VARCHAR(255),
    "instagram_url" VARCHAR(255),
    "linkedin_url" VARCHAR(255),
    "twitter_url" VARCHAR(255),
    "years_of_experience" INT NOT NULL  DEFAULT 0,
    "specialization" JSONB NOT NULL,
    "languages" JSONB NOT NULL,
    "bio" TEXT,
    "certifications" JSONB NOT NULL,
    "permissions" JSONB NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_verified" BOOL NOT NULL  DEFAULT False,
    "verification_status" VARCHAR(10) NOT NULL  DEFAULT 'unverified',
    "verification_date" TIMESTAMPTZ,
    "is_suspended" BOOL NOT NULL  DEFAULT False,
    "suspension_reason" TEXT,
    "suspension_until" TIMESTAMPTZ,
    "last_login_ip" VARCHAR(45),
    "last_activity" TIMESTAMPTZ,
    "activity_log" JSONB NOT NULL,
    "login_count" INT NOT NULL  DEFAULT 0,
    "total_listings" INT NOT NULL  DEFAULT 0,
    "active_listings" INT NOT NULL  DEFAULT 0,
    "sold_listings" INT NOT NULL  DEFAULT 0,
    "rented_listings" INT NOT NULL  DEFAULT 0,
    "total_commission" DECIMAL(12,2) NOT NULL  DEFAULT 0,
    "average_rating" DOUBLE PRECISION NOT NULL  DEFAULT 0,
    "review_count" INT NOT NULL  DEFAULT 0,
    "commission_rate" DECIMAL(5,2) NOT NULL  DEFAULT 0,
    "payment_method" JSONB,
    "bank_account_details" JSONB,
    "notification_preferences" JSONB NOT NULL,
    "working_hours" JSONB NOT NULL,
    "profile_picture" VARCHAR(500),
    "license_document" VARCHAR(500),
    "id_document" VARCHAR(500),
    "other_documents" JSONB NOT NULL,
    "user_id" UUID NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_agents_user_id_2779f1" ON "agents" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_agents_public__a26e22" ON "agents" ("public_id");
CREATE INDEX IF NOT EXISTS "idx_agents_license_61ac53" ON "agents" ("license_number");
CREATE INDEX IF NOT EXISTS "idx_agents_agency__fe2657" ON "agents" ("agency_name");
CREATE INDEX IF NOT EXISTS "idx_agents_city_ae97e2" ON "agents" ("city", "state");
CREATE INDEX IF NOT EXISTS "idx_agents_is_acti_7d9352" ON "agents" ("is_active", "is_verified");
CREATE INDEX IF NOT EXISTS "idx_agents_verific_4667df" ON "agents" ("verification_status");
CREATE INDEX IF NOT EXISTS "idx_agents_average_d55dfe" ON "agents" ("average_rating");
CREATE INDEX IF NOT EXISTS "idx_agents_total_l_5654bd" ON "agents" ("total_listings");
COMMENT ON COLUMN "agents"."agency_type" IS 'INDIVIDUAL: individual\nBROKERAGE: brokerage\nREALTY_COMPANY: realty_company\nPROPERTY_MANAGEMENT: property_management';
COMMENT ON COLUMN "agents"."license_status" IS 'UNLICENSED: unlicensed\nLICENSED: licensed\nEXPIRED: expired\nSUSPENDED: suspended';
COMMENT ON COLUMN "agents"."verification_status" IS 'UNVERIFIED: unverified\nPENDING: pending\nVERIFIED: verified\nREJECTED: rejected';
        CREATE INDEX "idx_users_home_la_601c51" ON "users" ("home_latitude", "home_longitude");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_users_home_la_601c51";
        ALTER TABLE "rental_extra_fee" DROP COLUMN "description";
        DROP TABLE IF EXISTS "agents";
        CREATE INDEX "idx_users_home_la_0cd7d1" ON "users" ("home_latitude", "home_    longitude");"""
