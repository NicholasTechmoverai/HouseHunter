from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "rental_pricing" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "rent" DECIMAL(12,2)   DEFAULT 0,
    "rent_frequency" VARCHAR(10) NOT NULL  DEFAULT 'monthly',
    "minimum_lease_months" INT NOT NULL  DEFAULT 1,
    "deposit_amount" DECIMAL(12,2) NOT NULL  DEFAULT 0,
    "deposit_months" INT NOT NULL  DEFAULT 0,
    "is_deposit_refundable" BOOL NOT NULL  DEFAULT True,
    "discount" DECIMAL(12,2) NOT NULL  DEFAULT 0,
    "currency" VARCHAR(10) NOT NULL  DEFAULT 'KES',
    "sort_order" INT NOT NULL  DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "rental_pricing"."rent_frequency" IS 'DAILY: daily\nWEEKLY: weekly\nMONTHLY: monthly\nNINE_MONTHLY: three_quarterly\nQUARTERLY: quarterly\nSEMIANNUAL: halfyearly\nYEARLY: yearly';
CREATE TABLE IF NOT EXISTS "rental_extra_fee" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "code" VARCHAR(50) NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "amount" DECIMAL(12,2),
    "currency" VARCHAR(10) NOT NULL  DEFAULT 'KES',
    "is_included" BOOL NOT NULL  DEFAULT False,
    "sort_order" INT NOT NULL  DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "pricing_id" UUID NOT NULL REFERENCES "rental_pricing" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "amenity_categories" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "slug" VARCHAR(50)  UNIQUE,
    "description" TEXT,
    "is_free" BOOL,
    "icon" VARCHAR(100),
    "sort_order" INT NOT NULL  DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "apartment_amenities" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "slug" VARCHAR(50),
    "description" TEXT,
    "icon" VARCHAR(100),
    "sort_order" INT NOT NULL  DEFAULT 0,
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "category_id" UUID REFERENCES "amenity_categories" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_apartment_a_name_87ebcb" ON "apartment_amenities" ("name");
CREATE INDEX IF NOT EXISTS "idx_apartment_a_is_feat_5f8de7" ON "apartment_amenities" ("is_featured");
CREATE TABLE IF NOT EXISTS "geo_locations" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "lat" DOUBLE PRECISION NOT NULL,
    "lon" DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_geo_locatio_lat_310128" ON "geo_locations" ("lat");
CREATE INDEX IF NOT EXISTS "idx_geo_locatio_lon_ac0b8a" ON "geo_locations" ("lon");
CREATE INDEX IF NOT EXISTS "idx_geo_locatio_lat_14ffdc" ON "geo_locations" ("lat", "lon");
CREATE TABLE IF NOT EXISTS "users" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "deleted_at" TIMESTAMPTZ,
    "last_password_changed" TIMESTAMPTZ,
    "password_changed_count" INT NOT NULL  DEFAULT 0,
    "email_changed_at" TIMESTAMPTZ,
    "phone_changed_at" TIMESTAMPTZ,
    "id" UUID NOT NULL  PRIMARY KEY,
    "public_id" VARCHAR(12)  UNIQUE,
    "oauth_providers" JSONB NOT NULL,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255),
    "password_salt" VARCHAR(255),
    "mfa_enabled" BOOL NOT NULL  DEFAULT False,
    "mfa_secret" VARCHAR(255),
    "mfa_backup_codes" JSONB,
    "failed_login_attempts" INT NOT NULL  DEFAULT 0,
    "locked_until" TIMESTAMPTZ,
    "username" VARCHAR(30)  UNIQUE,
    "display_name" VARCHAR(100),
    "first_name" VARCHAR(50) NOT NULL,
    "last_name" VARCHAR(50) NOT NULL,
    "middle_name" VARCHAR(50),
    "date_of_birth" DATE,
    "gender" SMALLINT,
    "email_verified" BOOL NOT NULL  DEFAULT False,
    "email_verified_at" TIMESTAMPTZ,
    "phone_number" VARCHAR(20)  UNIQUE,
    "phone_country_code" VARCHAR(5) NOT NULL  DEFAULT '+254',
    "phone_verified" BOOL NOT NULL  DEFAULT False,
    "phone_verified_at" TIMESTAMPTZ,
    "secondary_email" VARCHAR(255),
    "secondary_phone" VARCHAR(20),
    "country" VARCHAR(2) NOT NULL  DEFAULT 'KE',
    "timezone" VARCHAR(50) NOT NULL  DEFAULT 'Africa/Nairobi',
    "locale" VARCHAR(10) NOT NULL  DEFAULT 'en-KE',
    "currency" VARCHAR(3) NOT NULL  DEFAULT 'KES',
    "account_type" SMALLINT NOT NULL  DEFAULT 1,
    "account_type_set_at" TIMESTAMPTZ,
    "status" SMALLINT NOT NULL  DEFAULT 0,
    "activated_status_at" TIMESTAMPTZ,
    "last_login" TIMESTAMPTZ,
    "last_login_ip" VARCHAR(45),
    "last_active" TIMESTAMPTZ,
    "preferences" JSONB NOT NULL,
    "consent_given" BOOL NOT NULL  DEFAULT False,
    "consent_given_at" TIMESTAMPTZ,
    "gdpr_consents" JSONB,
    "data_processing_consent" BOOL NOT NULL  DEFAULT False,
    "signup_source" VARCHAR(50),
    "signup_ip" VARCHAR(45),
    "signup_user_agent" TEXT,
    "utm_source" VARCHAR(100),
    "utm_medium" VARCHAR(100),
    "referral_code" VARCHAR(20)  UNIQUE,
    "profile_picture" TEXT NOT NULL,
    "profile_picture_thumbnail" TEXT NOT NULL,
    "profile_banner" TEXT,
    "verification_level" INT NOT NULL  DEFAULT 0,
    "id_verified" BOOL NOT NULL  DEFAULT False,
    "id_verified_at" TIMESTAMPTZ,
    "id_document_type" VARCHAR(50),
    "id_document_number" VARCHAR(50),
    "account_tier" VARCHAR(20) NOT NULL  DEFAULT 'basic',
    "daily_rate_limit" INT NOT NULL  DEFAULT 100,
    "monthly_request_limit" INT NOT NULL  DEFAULT 1000,
    "bio" TEXT,
    "tagline" VARCHAR(200),
    "website" VARCHAR(255),
    "occupation" VARCHAR(100),
    "company" VARCHAR(100),
    "job_title" VARCHAR(100),
    "industry" VARCHAR(100),
    "current_city" VARCHAR(100),
    "current_country" VARCHAR(100),
    "current_state" VARCHAR(100),
    "current_postal_code" VARCHAR(20),
    "current_address" TEXT,
    "home_city" VARCHAR(100),
    "home_country" VARCHAR(100),
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "social_links" JSONB NOT NULL,
    "profile_views" INT NOT NULL  DEFAULT 0,
    "property_views" INT NOT NULL  DEFAULT 0,
    "search_count" INT NOT NULL  DEFAULT 0,
    "wallet_balance" DECIMAL(12,2) NOT NULL  DEFAULT 0,
    "total_spent" DECIMAL(12,2) NOT NULL  DEFAULT 0,
    "total_earned" DECIMAL(12,2) NOT NULL  DEFAULT 0,
    "subscription_tier" VARCHAR(50),
    "subscription_start" TIMESTAMPTZ,
    "subscription_end" TIMESTAMPTZ,
    "subscription_auto_renew" BOOL NOT NULL  DEFAULT False,
    "categories_of_interest" JSONB NOT NULL,
    "referred_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_users_current_9130c8" ON "users" ("current_city");
CREATE INDEX IF NOT EXISTS "idx_users_current_d24214" ON "users" ("current_country");
CREATE INDEX IF NOT EXISTS "idx_users_occupat_d81092" ON "users" ("occupation");
CREATE INDEX IF NOT EXISTS "idx_users_subscri_bedf56" ON "users" ("subscription_tier");
CREATE INDEX IF NOT EXISTS "idx_users_wallet__e581f6" ON "users" ("wallet_balance");
CREATE INDEX IF NOT EXISTS "idx_users_latitud_ae583a" ON "users" ("latitude", "longitude");
COMMENT ON COLUMN "users"."gender" IS 'MALE: 1\nFEMALE: 2\nNON_BINARY: 3\nPREFER_NOT_TO_SAY: 4\nOTHER: 5';
COMMENT ON COLUMN "users"."account_type" IS 'PERSONAL: 1\nBUSINESS: 2\nAGENT: 3\nADMIN: 4';
COMMENT ON COLUMN "users"."status" IS 'UNVERIFIED: 0\nACTIVE: 1\nSUSPENDED: 2\nDEACTIVATED: 3\nDELETED: 4\nBANNED: 5';
CREATE TABLE IF NOT EXISTS "apartment_complexes" (
    "id" VARCHAR(36) NOT NULL  PRIMARY KEY,
    "name" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "profile_picture" VARCHAR(500),
    "theme_color" VARCHAR(7) NOT NULL  DEFAULT '#FFFFFF',
    "year_built" INT,
    "country" VARCHAR(100) NOT NULL,
    "county" VARCHAR(100) NOT NULL,
    "state" VARCHAR(100) NOT NULL,
    "city" VARCHAR(100) NOT NULL,
    "zip_code" VARCHAR(20) NOT NULL,
    "address" TEXT NOT NULL,
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "contact_number" VARCHAR(20),
    "category" SMALLINT NOT NULL  DEFAULT 20,
    "total_units" INT,
    "total_floors" INT NOT NULL  DEFAULT 1,
    "is_published" BOOL NOT NULL  DEFAULT False,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_verified" BOOL NOT NULL  DEFAULT False,
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "is_blocked" BOOL NOT NULL  DEFAULT False,
    "is_open_for_rent" BOOL NOT NULL  DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "average_rating" INT,
    "reviews_count" INT,
    "managers_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "publisher_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_apartment_c_latitud_498429" ON "apartment_complexes" ("latitude");
CREATE INDEX IF NOT EXISTS "idx_apartment_c_longitu_1d0eb8" ON "apartment_complexes" ("longitude");
CREATE INDEX IF NOT EXISTS "idx_apartment_c_is_publ_8ed56b" ON "apartment_complexes" ("is_published");
CREATE INDEX IF NOT EXISTS "idx_apartment_c_is_veri_5f3294" ON "apartment_complexes" ("is_verified");
CREATE INDEX IF NOT EXISTS "idx_apartment_c_is_feat_1573c4" ON "apartment_complexes" ("is_featured");
CREATE INDEX IF NOT EXISTS "idx_apartment_c_is_dele_7544e5" ON "apartment_complexes" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_apartment_c_is_bloc_011d59" ON "apartment_complexes" ("is_blocked");
CREATE INDEX IF NOT EXISTS "idx_apartment_c_is_open_28c153" ON "apartment_complexes" ("is_open_for_rent");
CREATE INDEX IF NOT EXISTS "idx_apartment_c_average_e3d5e9" ON "apartment_complexes" ("average_rating");
COMMENT ON COLUMN "apartment_complexes"."category" IS 'SINGLE_ROOM: 1\nDOUBLE_ROOM: 2\nBEDSITTER: 3\nSTUDIO: 4\nONE_BEDROOM: 10\nTWO_BEDROOM: 11\nTHREE_BEDROOM: 12\nFOUR_BEDROOM: 13\nFIVE_BEDROOM: 14\nAPARTMENT: 20\nMAISONETTE: 21\nBUNGALOW: 22\nMANSION: 23\nVILLA: 24\nPENTHOUSE: 25\nHOSTEL_ROOM: 30\nSHARED_ROOM: 31\nAIRBNB_ROOM: 32\nGUEST_HOUSE: 33\nSERVICED_APARTMENT: 34\nHOTEL_ROOM: 35\nLODGE: 36\nSHOP: 40\nSUPERMARKET_SPACE: 41\nMALL_UNIT: 42\nOFFICE_SPACE: 43\nWAREHOUSE: 44\nINDUSTRIAL_SPACE: 45\nRESTAURANT_SPACE: 46\nSHOWROOM: 47';
CREATE TABLE IF NOT EXISTS "unit_pricing" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "rent" DECIMAL(12,2)   DEFAULT 0,
    "rent_frequency" VARCHAR(10) NOT NULL  DEFAULT 'monthly',
    "minimum_lease_months" INT NOT NULL  DEFAULT 1,
    "deposit_amount" DECIMAL(12,2) NOT NULL  DEFAULT 0,
    "deposit_months" INT NOT NULL  DEFAULT 0,
    "is_deposit_refundable" BOOL NOT NULL  DEFAULT True,
    "discount" DECIMAL(12,2) NOT NULL  DEFAULT 0,
    "currency" VARCHAR(10) NOT NULL  DEFAULT 'KES',
    "sort_order" INT NOT NULL  DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "apartment_id" VARCHAR(36) NOT NULL REFERENCES "apartment_complexes" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "unit_pricing"."rent_frequency" IS 'DAILY: daily\nWEEKLY: weekly\nMONTHLY: monthly\nNINE_MONTHLY: three_quarterly\nQUARTERLY: quarterly\nSEMIANNUAL: halfyearly\nYEARLY: yearly';
CREATE TABLE IF NOT EXISTS "apartment_blocks" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "code" VARCHAR(50) NOT NULL,
    "name" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "profile_picture" VARCHAR(500),
    "theme_color" VARCHAR(7) NOT NULL  DEFAULT '#FFFFFF',
    "year_built" INT,
    "total_floors" INT NOT NULL  DEFAULT 1,
    "total_units" INT NOT NULL  DEFAULT 0,
    "units_available" INT NOT NULL  DEFAULT 0,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_under_maintenance" BOOL NOT NULL  DEFAULT False,
    "maintenance_notes" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "apartment_complex_id" VARCHAR(36) NOT NULL REFERENCES "apartment_complexes" ("id") ON DELETE CASCADE,
    "price_id" UUID REFERENCES "unit_pricing" ("id") ON DELETE SET NULL,
    CONSTRAINT "uid_apartment_b_apartme_d442a0" UNIQUE ("apartment_complex_id", "code")
);
CREATE INDEX IF NOT EXISTS "idx_apartment_b_code_a03240" ON "apartment_blocks" ("code");
CREATE INDEX IF NOT EXISTS "idx_apartment_b_name_e4f534" ON "apartment_blocks" ("name");
CREATE INDEX IF NOT EXISTS "idx_apartment_b_is_acti_448b5a" ON "apartment_blocks" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_apartment_b_is_unde_8f29ea" ON "apartment_blocks" ("is_under_maintenance");
CREATE TABLE IF NOT EXISTS "apartment_units" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "code" VARCHAR(50),
    "name" VARCHAR(200),
    "description" TEXT,
    "profile_picture" VARCHAR(500),
    "theme_color" VARCHAR(7) NOT NULL  DEFAULT '#FFFFFF',
    "year_built" INT,
    "floor_number" INT NOT NULL  DEFAULT 1,
    "unit_number" INT NOT NULL  DEFAULT 1,
    "wing_or_section" VARCHAR(50),
    "area_sqft" DECIMAL(10,2),
    "number_of_bedrooms" INT NOT NULL  DEFAULT 1,
    "number_of_bathrooms" DECIMAL(3,1) NOT NULL  DEFAULT 1,
    "has_balcony" BOOL NOT NULL  DEFAULT False,
    "has_terrace" BOOL NOT NULL  DEFAULT False,
    "floor_plan_url" VARCHAR(500),
    "status" VARCHAR(20) NOT NULL  DEFAULT 'vacant',
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_under_maintenance" BOOL NOT NULL  DEFAULT False,
    "maintenance_notes" TEXT,
    "available_from" TIMESTAMPTZ,
    "available_to" TIMESTAMPTZ,
    "minimum_lease_months" INT NOT NULL  DEFAULT 1,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "last_occupied_at" TIMESTAMPTZ,
    "block_id" UUID NOT NULL REFERENCES "apartment_blocks" ("id") ON DELETE CASCADE,
    "price_id" UUID REFERENCES "unit_pricing" ("id") ON DELETE SET NULL,
    CONSTRAINT "uid_apartment_u_block_i_6ced57" UNIQUE ("block_id", "code")
);
CREATE INDEX IF NOT EXISTS "idx_apartment_u_code_af1f47" ON "apartment_units" ("code");
CREATE INDEX IF NOT EXISTS "idx_apartment_u_name_c3511c" ON "apartment_units" ("name");
CREATE INDEX IF NOT EXISTS "idx_apartment_u_status_c255f4" ON "apartment_units" ("status");
CREATE INDEX IF NOT EXISTS "idx_apartment_u_is_acti_a930eb" ON "apartment_units" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_apartment_u_is_unde_c1f2eb" ON "apartment_units" ("is_under_maintenance");
CREATE INDEX IF NOT EXISTS "idx_apartment_u_status_447432" ON "apartment_units" ("status", "is_active");
CREATE INDEX IF NOT EXISTS "idx_apartment_u_block_i_7dc41d" ON "apartment_units" ("block_id", "floor_number");
CREATE INDEX IF NOT EXISTS "idx_apartment_u_area_sq_43fd7c" ON "apartment_units" ("area_sqft");
CREATE INDEX IF NOT EXISTS "idx_apartment_u_number__d39713" ON "apartment_units" ("number_of_bedrooms");
COMMENT ON COLUMN "apartment_units"."status" IS 'VACANT: vacant\nOCCUPIED: occupied\nUNDER_MAINTENANCE: under_maintenance\nRESERVED: reserved\nRENTED: rented';
CREATE TABLE IF NOT EXISTS "apartment_gallery" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(200),
    "description" TEXT,
    "image_url" VARCHAR(500) NOT NULL,
    "file_type" VARCHAR(8) NOT NULL  DEFAULT 'image',
    "mime_type" VARCHAR(100),
    "file_size" DOUBLE PRECISION,
    "is_primary" BOOL NOT NULL  DEFAULT False,
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "sort_order" INT NOT NULL  DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "apartment_id" VARCHAR(36) REFERENCES "apartment_complexes" ("id") ON DELETE CASCADE,
    "block_id" UUID REFERENCES "apartment_blocks" ("id") ON DELETE CASCADE,
    "unit_id" UUID REFERENCES "apartment_units" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "apartment_gallery"."file_type" IS 'IMAGE: image\nDOCUMENT: document\nPDF: pdf\nVIDEO: video\nAUDIO: audio\nOTHER: other';
CREATE TABLE IF NOT EXISTS "apartment_rules" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(200),
    "description" TEXT,
    "is_mandatory" BOOL NOT NULL  DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "apartment_id" VARCHAR(36) REFERENCES "apartment_complexes" ("id") ON DELETE CASCADE,
    "block_id" UUID REFERENCES "apartment_blocks" ("id") ON DELETE CASCADE,
    "unit_id" UUID REFERENCES "apartment_units" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "rentals" (
    "id" VARCHAR(36) NOT NULL  PRIMARY KEY,
    "public_id" VARCHAR(36) NOT NULL UNIQUE,
    "title" VARCHAR(200) NOT NULL,
    "slug" VARCHAR(255)  UNIQUE,
    "description" TEXT NOT NULL,
    "profile_picture" VARCHAR(500),
    "theme_color" VARCHAR(7) NOT NULL  DEFAULT '#FFFFFF',
    "year_built" INT,
    "lot_size" INT,
    "floor_number" SMALLINT,
    "country" VARCHAR(100),
    "county" VARCHAR(100),
    "state" VARCHAR(100),
    "city" VARCHAR(100),
    "zip_code" VARCHAR(20),
    "address" TEXT,
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "contact_number" VARCHAR(20),
    "category" SMALLINT NOT NULL  DEFAULT 20,
    "price" DECIMAL(12,2),
    "bedrooms" INT NOT NULL  DEFAULT 1,
    "bathrooms" DECIMAL(3,1) NOT NULL  DEFAULT 1,
    "area_sqft" DECIMAL(10,2),
    "is_available" BOOL NOT NULL  DEFAULT True,
    "available_from" TIMESTAMPTZ,
    "status" VARCHAR(17) NOT NULL  DEFAULT 'draft',
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "is_verified" BOOL NOT NULL  DEFAULT False,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "verified_at" TIMESTAMPTZ,
    "deleted_at" TIMESTAMPTZ,
    "rejection_reason" TEXT,
    "search_vector" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "pricing_id" UUID REFERENCES "rental_pricing" ("id") ON DELETE CASCADE,
    "publisher_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_rentals_public__5cbd46" ON "rentals" ("public_id");
CREATE INDEX IF NOT EXISTS "idx_rentals_slug_9d2939" ON "rentals" ("slug");
CREATE INDEX IF NOT EXISTS "idx_rentals_latitud_87ab02" ON "rentals" ("latitude");
CREATE INDEX IF NOT EXISTS "idx_rentals_longitu_cff232" ON "rentals" ("longitude");
CREATE INDEX IF NOT EXISTS "idx_rentals_is_avai_0e03ba" ON "rentals" ("is_available");
CREATE INDEX IF NOT EXISTS "idx_rentals_status_3e7956" ON "rentals" ("status");
CREATE INDEX IF NOT EXISTS "idx_rentals_is_feat_7d9325" ON "rentals" ("is_featured");
CREATE INDEX IF NOT EXISTS "idx_rentals_is_veri_2707f5" ON "rentals" ("is_verified");
CREATE INDEX IF NOT EXISTS "idx_rentals_is_dele_230c86" ON "rentals" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_rentals_city_daba0a" ON "rentals" ("city", "price");
CREATE INDEX IF NOT EXISTS "idx_rentals_city_cb5940" ON "rentals" ("city", "category", "is_available");
CREATE INDEX IF NOT EXISTS "idx_rentals_price_6f5aa3" ON "rentals" ("price", "bedrooms");
CREATE INDEX IF NOT EXISTS "idx_rentals_created_c95ebf" ON "rentals" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_rentals_is_feat_8354df" ON "rentals" ("is_featured", "is_available");
CREATE INDEX IF NOT EXISTS "idx_rentals_status_684c86" ON "rentals" ("status", "is_available");
COMMENT ON COLUMN "rentals"."category" IS 'SINGLE_ROOM: 1\nDOUBLE_ROOM: 2\nBEDSITTER: 3\nSTUDIO: 4\nONE_BEDROOM: 10\nTWO_BEDROOM: 11\nTHREE_BEDROOM: 12\nFOUR_BEDROOM: 13\nFIVE_BEDROOM: 14\nAPARTMENT: 20\nMAISONETTE: 21\nBUNGALOW: 22\nMANSION: 23\nVILLA: 24\nPENTHOUSE: 25\nHOSTEL_ROOM: 30\nSHARED_ROOM: 31\nAIRBNB_ROOM: 32\nGUEST_HOUSE: 33\nSERVICED_APARTMENT: 34\nHOTEL_ROOM: 35\nLODGE: 36\nSHOP: 40\nSUPERMARKET_SPACE: 41\nMALL_UNIT: 42\nOFFICE_SPACE: 43\nWAREHOUSE: 44\nINDUSTRIAL_SPACE: 45\nRESTAURANT_SPACE: 46\nSHOWROOM: 47';
COMMENT ON COLUMN "rentals"."status" IS 'VACANT: vacant\nOCCUPIED: occupied\nUNDER_MAINTENANCE: under_maintenance\nRESERVED: reserved\nRENTED: rented\nDRAFT: draft\nPENDING_REVIEW: pending_review\nREJECTED: rejected';
CREATE TABLE IF NOT EXISTS "rental_amenities" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "slug" VARCHAR(50),
    "description" TEXT,
    "icon" VARCHAR(100),
    "sort_order" INT NOT NULL  DEFAULT 0,
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "category_id" UUID REFERENCES "amenity_categories" ("id") ON DELETE SET NULL,
    "rental_id" VARCHAR(36) NOT NULL REFERENCES "rentals" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_rental_amen_name_4ffdb6" ON "rental_amenities" ("name");
CREATE INDEX IF NOT EXISTS "idx_rental_amen_is_feat_1beaaf" ON "rental_amenities" ("is_featured");
CREATE TABLE IF NOT EXISTS "rental_gallery" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(200),
    "description" TEXT,
    "image_url" VARCHAR(500) NOT NULL,
    "file_type" VARCHAR(8) NOT NULL  DEFAULT 'image',
    "mime_type" VARCHAR(100),
    "file_size" DOUBLE PRECISION,
    "is_primary" BOOL NOT NULL  DEFAULT False,
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "sort_order" INT NOT NULL  DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "rental_id" VARCHAR(36) NOT NULL REFERENCES "rentals" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "rental_gallery"."file_type" IS 'IMAGE: image\nDOCUMENT: document\nPDF: pdf\nVIDEO: video\nAUDIO: audio\nOTHER: other';
CREATE TABLE IF NOT EXISTS "rental_rules" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(200),
    "description" TEXT,
    "is_mandatory" BOOL NOT NULL  DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "rental_id" VARCHAR(36) NOT NULL REFERENCES "rentals" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "documents" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "deleted_at" TIMESTAMPTZ,
    "id" UUID NOT NULL  PRIMARY KEY,
    "document_type" SMALLINT NOT NULL,
    "document_number" VARCHAR(100),
    "original_filename" VARCHAR(255) NOT NULL,
    "file_path" TEXT NOT NULL,
    "file_url" TEXT NOT NULL,
    "file_size" BIGINT NOT NULL  DEFAULT 0,
    "mime_type" VARCHAR(100),
    "file_hash" VARCHAR(64),
    "pages" INT NOT NULL  DEFAULT 1,
    "width" INT,
    "height" INT,
    "uploaded_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMPTZ,
    "verification_status" SMALLINT NOT NULL  DEFAULT 0,
    "document_status" SMALLINT NOT NULL  DEFAULT 1,
    "verification_notes" TEXT,
    "rejection_reason" TEXT,
    "metadata" JSONB NOT NULL,
    "verified_at" TIMESTAMPTZ,
    "ocr_data" JSONB,
    "extracted_data" JSONB,
    "is_primary" BOOL NOT NULL  DEFAULT False,
    "is_public" BOOL NOT NULL  DEFAULT False,
    "access_token" VARCHAR(64)  UNIQUE,
    "access_expires_at" TIMESTAMPTZ,
    "watermark_text" VARCHAR(255),
    "storage_provider" VARCHAR(50) NOT NULL  DEFAULT 'local',
    "storage_bucket" VARCHAR(100),
    "storage_key" VARCHAR(255),
    "thumbnail_path" TEXT,
    "thumbnail_url" TEXT,
    "uploaded_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_documents_documen_9db149" ON "documents" ("document_type");
CREATE INDEX IF NOT EXISTS "idx_documents_documen_c66a82" ON "documents" ("document_number");
CREATE INDEX IF NOT EXISTS "idx_documents_file_ha_9281f6" ON "documents" ("file_hash");
CREATE INDEX IF NOT EXISTS "idx_documents_expires_6c639b" ON "documents" ("expires_at");
CREATE INDEX IF NOT EXISTS "idx_documents_verific_281309" ON "documents" ("verification_status");
CREATE INDEX IF NOT EXISTS "idx_documents_documen_99e01c" ON "documents" ("document_status");
CREATE INDEX IF NOT EXISTS "idx_documents_is_prim_c62ca4" ON "documents" ("is_primary");
CREATE INDEX IF NOT EXISTS "idx_documents_access__8a0051" ON "documents" ("access_token");
CREATE INDEX IF NOT EXISTS "idx_documents_uploade_d90d22" ON "documents" ("uploaded_by_id", "document_type");
CREATE INDEX IF NOT EXISTS "idx_documents_uploade_8aa208" ON "documents" ("uploaded_by_id", "verification_status");
CREATE INDEX IF NOT EXISTS "idx_documents_uploade_bcac43" ON "documents" ("uploaded_by_id", "is_primary");
CREATE INDEX IF NOT EXISTS "idx_documents_expires_ea66af" ON "documents" ("expires_at", "document_status");
COMMENT ON COLUMN "documents"."document_type" IS 'NATIONAL_ID: 1\nPASSPORT: 2\nDRIVERS_LICENSE: 3\nBUSINESS_LICENSE: 4\nTAX_CERTIFICATE: 5\nUTILITY_BILL: 6\nBANK_STATEMENT: 7\nCONTRACT: 8\nCERTIFICATE: 9\nOTHER: 10';
COMMENT ON COLUMN "documents"."verification_status" IS 'PENDING: 0\nVERIFIED: 1\nREJECTED: 2\nEXPIRED: 3\nSUSPENDED: 4\nUNDER_REVIEW: 5';
COMMENT ON COLUMN "documents"."document_status" IS 'UPLOADED: 1\nPROCESSING: 2\nPROCESSED: 3\nFAILED: 4\nDELETED: 5';
CREATE TABLE IF NOT EXISTS "policy_documents" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "policy_code" VARCHAR(50) NOT NULL UNIQUE,
    "title" VARCHAR(200) NOT NULL,
    "short_title" VARCHAR(100),
    "policy_type" SMALLINT NOT NULL,
    "version" VARCHAR(20) NOT NULL  DEFAULT '1.0',
    "version_number" INT NOT NULL  DEFAULT 1,
    "content" TEXT NOT NULL,
    "summary" TEXT,
    "changelog" TEXT,
    "audience" SMALLINT NOT NULL  DEFAULT 1,
    "regions" JSONB NOT NULL,
    "languages" JSONB NOT NULL,
    "status" SMALLINT NOT NULL  DEFAULT 1,
    "effective_date" DATE NOT NULL,
    "expiration_date" DATE,
    "review_frequency" VARCHAR(50) NOT NULL  DEFAULT 'annual',
    "next_review_date" DATE,
    "is_mandatory" BOOL NOT NULL  DEFAULT True,
    "min_age_requirement" INT,
    "requires_explicit_consent" BOOL NOT NULL  DEFAULT False,
    "related_policies" JSONB NOT NULL,
    "compliance_standards" JSONB NOT NULL,
    "risk_level" VARCHAR(20) NOT NULL  DEFAULT 'medium',
    "view_count" INT NOT NULL  DEFAULT 0,
    "accept_count" INT NOT NULL  DEFAULT 0,
    "decline_count" INT NOT NULL  DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "published_at" TIMESTAMPTZ,
    "archived_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "tags" JSONB NOT NULL,
    "approved_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "legal_review_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "previous_version_id" UUID REFERENCES "policy_documents" ("id") ON DELETE SET NULL,
    "published_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_policy_docu_policy__72fac0" ON "policy_documents" ("policy_code");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_policy__dc6c21" ON "policy_documents" ("policy_type");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_version_b1f28b" ON "policy_documents" ("version_number");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_audienc_c35bcc" ON "policy_documents" ("audience");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_status_41caff" ON "policy_documents" ("status");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_effecti_97bdd4" ON "policy_documents" ("effective_date");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_expirat_b464f6" ON "policy_documents" ("expiration_date");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_next_re_296f5b" ON "policy_documents" ("next_review_date");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_is_mand_57abe0" ON "policy_documents" ("is_mandatory");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_view_co_79658e" ON "policy_documents" ("view_count");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_accept__ab3df5" ON "policy_documents" ("accept_count");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_created_05fa89" ON "policy_documents" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_publish_f21377" ON "policy_documents" ("published_at");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_policy__37dedd" ON "policy_documents" ("policy_type", "status");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_policy__492d29" ON "policy_documents" ("policy_type", "effective_date");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_status_498a45" ON "policy_documents" ("status", "effective_date");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_audienc_b3ab44" ON "policy_documents" ("audience", "status");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_version_5b6e7c" ON "policy_documents" ("version_number", "policy_type");
CREATE INDEX IF NOT EXISTS "idx_policy_docu_effecti_047f95" ON "policy_documents" ("effective_date", "expiration_date");
COMMENT ON COLUMN "policy_documents"."policy_type" IS 'PRIVACY: 1\nTERMS: 2\nCOOKIE: 3\nACCEPTABLE_USE: 4\nCOMMUNITY_GUIDELINES: 5\nREFUND: 6\nCANCELLATION: 7\nSHIPPING: 8\nSERVICE: 9\nLEGAL: 10\nSAFETY: 11\nACCESSIBILITY: 12\nENVIRONMENTAL: 13\nETHICS: 14\nDATA_PROCESSING: 15\nSECURITY: 16\nCOMPLIANCE: 17';
COMMENT ON COLUMN "policy_documents"."audience" IS 'ALL_USERS: 1\nREGISTERED_USERS: 2\nADMINISTRATORS: 3\nEMPLOYEES: 4\nPARTNERS: 5\nCUSTOMERS: 6\nSUPPLIERS: 7\nPUBLIC: 8\nINTERNAL: 9\nEXTERNAL: 10';
COMMENT ON COLUMN "policy_documents"."status" IS 'DRAFT: 1\nACTIVE: 2\nINACTIVE: 3\nARCHIVED: 4\nDELETED: 5\nPENDING_REVIEW: 6\nUNDER_REVISION: 7';
COMMENT ON TABLE "policy_documents" IS 'Main policy document model.';
CREATE TABLE IF NOT EXISTS "user_notifications" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" UUID NOT NULL  PRIMARY KEY,
    "notification_id" VARCHAR(50) NOT NULL UNIQUE,
    "notification_type" SMALLINT NOT NULL  DEFAULT 1,
    "category" SMALLINT NOT NULL  DEFAULT 9,
    "priority" SMALLINT NOT NULL  DEFAULT 2,
    "status" SMALLINT NOT NULL  DEFAULT 1,
    "channels" JSONB NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "message" TEXT NOT NULL,
    "short_message" VARCHAR(160),
    "data" JSONB NOT NULL,
    "action_url" TEXT,
    "action_label" VARCHAR(50),
    "deep_link" TEXT,
    "web_url" TEXT,
    "icon" VARCHAR(100),
    "image_url" TEXT,
    "sender_type" VARCHAR(50),
    "related_entity_type" VARCHAR(50),
    "related_entity_id" VARCHAR(100),
    "group_key" VARCHAR(100),
    "read_at" TIMESTAMPTZ,
    "delivered_at" TIMESTAMPTZ,
    "clicked_at" TIMESTAMPTZ,
    "acknowledged_at" TIMESTAMPTZ,
    "expires_at" TIMESTAMPTZ,
    "scheduled_for" TIMESTAMPTZ,
    "sent_at" TIMESTAMPTZ,
    "delivery_attempts" INT NOT NULL  DEFAULT 0,
    "max_attempts" INT NOT NULL  DEFAULT 3,
    "delivery_errors" JSONB NOT NULL,
    "device_tokens" JSONB NOT NULL,
    "email_addresses" JSONB NOT NULL,
    "phone_numbers" JSONB NOT NULL,
    "template_id" VARCHAR(100),
    "template_variables" JSONB NOT NULL,
    "locale" VARCHAR(10) NOT NULL  DEFAULT 'en',
    "metadata" JSONB NOT NULL,
    "tags" JSONB NOT NULL,
    "silent" BOOL NOT NULL  DEFAULT False,
    "badge_count" INT NOT NULL  DEFAULT 1,
    "campaign_id" VARCHAR(100),
    "batch_id" VARCHAR(100),
    "read_receipt_requested" BOOL NOT NULL  DEFAULT False,
    "requires_acknowledgment" BOOL NOT NULL  DEFAULT False,
    "cost" DECIMAL(10,4) NOT NULL  DEFAULT 0,
    "user_preferences_override" JSONB NOT NULL,
    "is_test" BOOL NOT NULL  DEFAULT False,
    "is_bulk" BOOL NOT NULL  DEFAULT False,
    "analytics_data" JSONB NOT NULL,
    "sender_id_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "user_id" UUID REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_user_notifi_notific_db0a65" ON "user_notifications" ("notification_id");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_notific_9e363c" ON "user_notifications" ("notification_type");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_categor_23a998" ON "user_notifications" ("category");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_priorit_815256" ON "user_notifications" ("priority");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_status_0678be" ON "user_notifications" ("status");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_group_k_d111e3" ON "user_notifications" ("group_key");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_schedul_ee91ea" ON "user_notifications" ("scheduled_for");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_campaig_de40b4" ON "user_notifications" ("campaign_id");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_batch_i_15b245" ON "user_notifications" ("batch_id");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_user_id_625de7" ON "user_notifications" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_user_id_1ccae8" ON "user_notifications" ("user_id", "status");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_user_id_d2abfb" ON "user_notifications" ("user_id", "read_at");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_user_id_55c5cb" ON "user_notifications" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_schedul_698fce" ON "user_notifications" ("scheduled_for", "status");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_priorit_56e05e" ON "user_notifications" ("priority", "status");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_categor_5cca1a" ON "user_notifications" ("category", "status");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_expires_af11eb" ON "user_notifications" ("expires_at", "status");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_user_id_73a899" ON "user_notifications" ("user_id", "notification_type", "status");
CREATE INDEX IF NOT EXISTS "idx_user_notifi_related_1e9ad2" ON "user_notifications" ("related_entity_type", "related_entity_id");
COMMENT ON COLUMN "user_notifications"."notification_type" IS 'SYSTEM: 1\nUSER: 2\nPROPERTY: 3\nTRANSACTION: 4\nSECURITY: 5\nMARKETING: 6\nSOCIAL: 7\nSUPPORT: 8\nALERT: 9\nREMINDER: 10';
COMMENT ON COLUMN "user_notifications"."category" IS 'ACCOUNT: 1\nSECURITY: 2\nPROPERTY: 3\nPAYMENT: 4\nBOOKING: 5\nMESSAGE: 6\nREVIEW: 7\nPROMOTION: 8\nSYSTEM: 9\nSOCIAL: 10';
COMMENT ON COLUMN "user_notifications"."priority" IS 'LOW: 1\nNORMAL: 2\nHIGH: 3\nURGENT: 4\nCRITICAL: 5';
COMMENT ON COLUMN "user_notifications"."status" IS 'PENDING: 1\nSENT: 2\nDELIVERED: 3\nREAD: 4\nCLICKED: 5\nFAILED: 6\nARCHIVED: 7\nEXPIRED: 8';
CREATE TABLE IF NOT EXISTS "user_searches" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" UUID NOT NULL  PRIMARY KEY,
    "search_id" VARCHAR(50) NOT NULL UNIQUE,
    "query_type" SMALLINT NOT NULL  DEFAULT 1,
    "search_text" VARCHAR(500),
    "filters" JSONB NOT NULL,
    "location_data" JSONB NOT NULL,
    "sort_by" VARCHAR(50) NOT NULL  DEFAULT 'relevance',
    "sort_order" VARCHAR(10) NOT NULL  DEFAULT 'desc',
    "page" INT NOT NULL  DEFAULT 1,
    "page_size" INT NOT NULL  DEFAULT 20,
    "result_count" INT NOT NULL  DEFAULT 0,
    "total_pages" INT NOT NULL  DEFAULT 0,
    "total_results" INT NOT NULL  DEFAULT 0,
    "last_executed" TIMESTAMPTZ,
    "execution_count" INT NOT NULL  DEFAULT 0,
    "average_execution_time" DOUBLE PRECISION NOT NULL  DEFAULT 0,
    "status" SMALLINT NOT NULL  DEFAULT 1,
    "is_saved" BOOL NOT NULL  DEFAULT False,
    "is_alert" BOOL NOT NULL  DEFAULT False,
    "alert_frequency" VARCHAR(20),
    "last_alert_sent" TIMESTAMPTZ,
    "next_alert_at" TIMESTAMPTZ,
    "source" SMALLINT NOT NULL  DEFAULT 1,
    "user_agent" TEXT,
    "ip_address" VARCHAR(45),
    "device_info" JSONB NOT NULL,
    "referrer_url" TEXT,
    "search_session_id" VARCHAR(100),
    "tags" JSONB NOT NULL,
    "metadata" JSONB NOT NULL,
    "results_preview" JSONB NOT NULL,
    "cost_estimate_min" DECIMAL(12,2),
    "cost_estimate_max" DECIMAL(12,2),
    "is_advanced" BOOL NOT NULL  DEFAULT False,
    "filter_count" INT NOT NULL  DEFAULT 0,
    "confidence_score" DOUBLE PRECISION NOT NULL  DEFAULT 0,
    "relevance_feedback" JSONB NOT NULL,
    "shared_with" JSONB NOT NULL,
    "notes" TEXT,
    "expiration_date" TIMESTAMPTZ,
    "last_modified_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_user_search_search__c3a4d4" ON "user_searches" ("search_id");
CREATE INDEX IF NOT EXISTS "idx_user_search_query_t_2e4e6f" ON "user_searches" ("query_type");
CREATE INDEX IF NOT EXISTS "idx_user_search_search__1a1a8d" ON "user_searches" ("search_session_id");
CREATE INDEX IF NOT EXISTS "idx_user_search_user_id_704422" ON "user_searches" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_user_search_user_id_61a394" ON "user_searches" ("user_id", "status");
CREATE INDEX IF NOT EXISTS "idx_user_search_user_id_c44862" ON "user_searches" ("user_id", "is_saved");
CREATE INDEX IF NOT EXISTS "idx_user_search_user_id_a84768" ON "user_searches" ("user_id", "query_type");
CREATE INDEX IF NOT EXISTS "idx_user_search_last_ex_49d92b" ON "user_searches" ("last_executed");
CREATE INDEX IF NOT EXISTS "idx_user_search_next_al_e7d1f3" ON "user_searches" ("next_alert_at");
CREATE INDEX IF NOT EXISTS "idx_user_search_status_f42ec8" ON "user_searches" ("status", "expiration_date");
CREATE INDEX IF NOT EXISTS "idx_user_search_user_id_3c3d5d" ON "user_searches" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_user_search_search__dbbccb" ON "user_searches" ("search_text");
COMMENT ON COLUMN "user_searches"."query_type" IS 'PROPERTY: 1\nJOB: 2\nPRODUCT: 3\nSERVICE: 4\nUSER: 5\nCONTENT: 6';
COMMENT ON COLUMN "user_searches"."status" IS 'ACTIVE: 1\nSAVED: 2\nDELETED: 3\nEXPIRED: 4';
COMMENT ON COLUMN "user_searches"."source" IS 'WEB: 1\nMOBILE: 2\nAPI: 3\nBOT: 4';
CREATE TABLE IF NOT EXISTS "admin_users" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "deleted_at" TIMESTAMPTZ,
    "admin_level" SMALLINT NOT NULL  DEFAULT 4,
    "employee_id" VARCHAR(50) NOT NULL UNIQUE,
    "permissions" JSONB NOT NULL,
    "department" VARCHAR(100),
    "job_title" VARCHAR(100),
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_suspended" BOOL NOT NULL  DEFAULT False,
    "suspension_reason" TEXT,
    "suspension_until" TIMESTAMPTZ,
    "admin_preferences" JSONB NOT NULL,
    "last_login_ip" VARCHAR(45),
    "last_activity" TIMESTAMPTZ,
    "activity_log" JSONB NOT NULL,
    "session_timeout" INT NOT NULL  DEFAULT 30,
    "mfa_required" BOOL NOT NULL  DEFAULT True,
    "assigned_teams" JSONB NOT NULL,
    "allowed_ips" JSONB NOT NULL,
    "allowed_countries" JSONB NOT NULL,
    "access_hours_start" TIMETZ,
    "access_hours_end" TIMETZ,
    "actions_taken" INT NOT NULL  DEFAULT 0,
    "tickets_resolved" INT NOT NULL  DEFAULT 0,
    "reports_generated" INT NOT NULL  DEFAULT 0,
    "user_id" UUID NOT NULL  PRIMARY KEY REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_admin_users_employe_d1791a" ON "admin_users" ("employee_id");
CREATE INDEX IF NOT EXISTS "idx_admin_users_departm_1221ea" ON "admin_users" ("department");
CREATE INDEX IF NOT EXISTS "idx_admin_users_admin_l_684e98" ON "admin_users" ("admin_level");
CREATE INDEX IF NOT EXISTS "idx_admin_users_is_acti_7f16a8" ON "admin_users" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_admin_users_is_dele_212dae" ON "admin_users" ("is_deleted", "is_active");
COMMENT ON COLUMN "admin_users"."admin_level" IS 'SUPER_ADMIN: 1\nADMIN: 2\nMODERATOR: 3\nSUPPORT: 4\nANALYST: 5';
CREATE TABLE IF NOT EXISTS "reviews" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "review_type" SMALLINT NOT NULL,
    "item_id" VARCHAR(100) NOT NULL,
    "rating" INT NOT NULL  DEFAULT 1,
    "title" VARCHAR(200),
    "content" TEXT NOT NULL,
    "pros" JSONB NOT NULL,
    "cons" JSONB NOT NULL,
    "is_edited" BOOL NOT NULL  DEFAULT False,
    "edited_at" TIMESTAMPTZ,
    "is_verified_purchase" BOOL NOT NULL  DEFAULT False,
    "verification_data" JSONB,
    "status" SMALLINT NOT NULL  DEFAULT 2,
    "moderated_at" TIMESTAMPTZ,
    "moderation_notes" TEXT,
    "rejection_reason" TEXT,
    "helpful_count" INT NOT NULL  DEFAULT 0,
    "not_helpful_count" INT NOT NULL  DEFAULT 0,
    "reply_count" INT NOT NULL  DEFAULT 0,
    "report_count" INT NOT NULL  DEFAULT 0,
    "reported_by" JSONB NOT NULL,
    "report_reason" TEXT,
    "liked_by" JSONB NOT NULL,
    "disliked_by" JSONB NOT NULL,
    "likes_count" INT NOT NULL  DEFAULT 0,
    "dislike_count" INT NOT NULL  DEFAULT 0,
    "metadata" JSONB NOT NULL,
    "tags" JSONB NOT NULL,
    "first_experience_date" DATE,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "published_at" TIMESTAMPTZ,
    "deleted_at" TIMESTAMPTZ,
    "is_anonymous" BOOL NOT NULL  DEFAULT False,
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "is_editor_pick" BOOL NOT NULL  DEFAULT False,
    "language" VARCHAR(10) NOT NULL  DEFAULT 'en',
    "item_owner_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "reviewer_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_reviews_review__503a9d" ON "reviews" ("review_type");
CREATE INDEX IF NOT EXISTS "idx_reviews_item_id_1c217e" ON "reviews" ("item_id");
CREATE INDEX IF NOT EXISTS "idx_reviews_rating_33cb40" ON "reviews" ("rating");
CREATE INDEX IF NOT EXISTS "idx_reviews_is_veri_0662f5" ON "reviews" ("is_verified_purchase");
CREATE INDEX IF NOT EXISTS "idx_reviews_status_48b720" ON "reviews" ("status");
CREATE INDEX IF NOT EXISTS "idx_reviews_helpful_ad0d5b" ON "reviews" ("helpful_count");
CREATE INDEX IF NOT EXISTS "idx_reviews_created_d4b678" ON "reviews" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_reviews_publish_53a604" ON "reviews" ("published_at");
CREATE INDEX IF NOT EXISTS "idx_reviews_is_anon_4c7029" ON "reviews" ("is_anonymous");
CREATE INDEX IF NOT EXISTS "idx_reviews_is_feat_5327e3" ON "reviews" ("is_featured");
CREATE INDEX IF NOT EXISTS "idx_reviews_is_edit_e1c74d" ON "reviews" ("is_editor_pick");
CREATE INDEX IF NOT EXISTS "idx_reviews_item_ow_6d1006" ON "reviews" ("item_owner_id");
CREATE INDEX IF NOT EXISTS "idx_reviews_reviewe_f1b91e" ON "reviews" ("reviewer_id");
CREATE INDEX IF NOT EXISTS "idx_reviews_reviewe_6d0f08" ON "reviews" ("reviewer_id", "review_type", "item_id");
CREATE INDEX IF NOT EXISTS "idx_reviews_item_id_5e61e9" ON "reviews" ("item_id", "review_type", "status");
CREATE INDEX IF NOT EXISTS "idx_reviews_item_id_929031" ON "reviews" ("item_id", "review_type", "rating");
CREATE INDEX IF NOT EXISTS "idx_reviews_item_id_467d1c" ON "reviews" ("item_id", "review_type", "created_at");
CREATE INDEX IF NOT EXISTS "idx_reviews_rating_233902" ON "reviews" ("rating", "status");
CREATE INDEX IF NOT EXISTS "idx_reviews_helpful_388179" ON "reviews" ("helpful_count", "status");
CREATE INDEX IF NOT EXISTS "idx_reviews_is_feat_bbd50d" ON "reviews" ("is_featured", "status");
CREATE INDEX IF NOT EXISTS "idx_reviews_publish_bce6c9" ON "reviews" ("published_at", "status");
CREATE INDEX IF NOT EXISTS "idx_reviews_item_ow_b8a325" ON "reviews" ("item_owner_id", "status");
COMMENT ON COLUMN "reviews"."review_type" IS 'PROPERTY: 1\nRENTAL: 2\nSWAP: 3\nLANDLORD: 4\nTENANT: 5\nSERVICE: 6\nPRODUCT: 7\nCOMPANY: 8\nAGENT: 9\nCONTRACTOR: 10\nEVENT: 11\nCONTENT: 12';
COMMENT ON COLUMN "reviews"."status" IS 'PENDING: 1\nAPPROVED: 2\nREJECTED: 3\nHIDDEN: 4\nDELETED: 5\nREPORTED: 6\nEDITED: 7';
COMMENT ON TABLE "reviews" IS 'Abstract base model for reviews and ratings.';
CREATE TABLE IF NOT EXISTS "review_replies" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "content" TEXT NOT NULL,
    "status" SMALLINT NOT NULL  DEFAULT 1,
    "moderated_at" TIMESTAMPTZ,
    "moderation_notes" TEXT,
    "likes_count" INT NOT NULL  DEFAULT 0,
    "helpful_count" INT NOT NULL  DEFAULT 0,
    "report_count" INT NOT NULL  DEFAULT 0,
    "reported_by" JSONB NOT NULL,
    "is_author_response" BOOL NOT NULL  DEFAULT False,
    "is_edited" BOOL NOT NULL  DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMPTZ,
    "edit_history" JSONB NOT NULL,
    "author_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "parent_reply_id" UUID NOT NULL REFERENCES "review_replies" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_review_repl_status_d42281" ON "review_replies" ("status");
CREATE INDEX IF NOT EXISTS "idx_review_repl_likes_c_2b891c" ON "review_replies" ("likes_count");
CREATE INDEX IF NOT EXISTS "idx_review_repl_helpful_c3a442" ON "review_replies" ("helpful_count");
CREATE INDEX IF NOT EXISTS "idx_review_repl_is_auth_2fef82" ON "review_replies" ("is_author_response");
CREATE INDEX IF NOT EXISTS "idx_review_repl_is_edit_4bdfbf" ON "review_replies" ("is_edited");
CREATE INDEX IF NOT EXISTS "idx_review_repl_created_21633a" ON "review_replies" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_review_repl_author__48f5f5" ON "review_replies" ("author_id");
CREATE INDEX IF NOT EXISTS "idx_review_repl_parent__0ca941" ON "review_replies" ("parent_reply_id");
CREATE INDEX IF NOT EXISTS "idx_review_repl_author__a7a10f" ON "review_replies" ("author_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_review_repl_parent__f61a08" ON "review_replies" ("parent_reply_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_review_repl_is_auth_e8aac6" ON "review_replies" ("is_author_response", "status");
CREATE INDEX IF NOT EXISTS "idx_review_repl_likes_c_42eef1" ON "review_replies" ("likes_count", "created_at");
COMMENT ON COLUMN "review_replies"."status" IS 'ACTIVE: 1\nDELETED: 2\nHIDDEN: 3\nREPORTED: 4\nEDITED: 5';
COMMENT ON TABLE "review_replies" IS 'Model for replies to reviews.';
CREATE TABLE IF NOT EXISTS "reviews_gallery" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(200),
    "description" TEXT,
    "image_url" VARCHAR(500) NOT NULL,
    "file_type" VARCHAR(8) NOT NULL  DEFAULT 'image',
    "mime_type" VARCHAR(100),
    "file_size" DOUBLE PRECISION,
    "is_primary" BOOL NOT NULL  DEFAULT False,
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "sort_order" INT NOT NULL  DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "review_id" UUID REFERENCES "reviews" ("id") ON DELETE CASCADE,
    "review_reply_id" UUID REFERENCES "review_replies" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "reviews_gallery"."file_type" IS 'IMAGE: image\nDOCUMENT: document\nPDF: pdf\nVIDEO: video\nAUDIO: audio\nOTHER: other';
CREATE TABLE IF NOT EXISTS "policy_acceptances" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "accepted_version" VARCHAR(20) NOT NULL,
    "ip_address" VARCHAR(45),
    "user_agent" TEXT,
    "accepted_via" VARCHAR(50) NOT NULL  DEFAULT 'web',
    "consent_type" VARCHAR(50) NOT NULL  DEFAULT 'explicit',
    "consent_level" VARCHAR(50) NOT NULL  DEFAULT 'full',
    "withdrawn_at" TIMESTAMPTZ,
    "withdrawal_reason" TEXT,
    "withdrawal_ip" VARCHAR(45),
    "accepted_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "metadata" JSONB NOT NULL,
    "policy_id" UUID NOT NULL REFERENCES "policy_documents" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_policy_acce_user_id_045fd1" UNIQUE ("user_id", "policy_id", "accepted_version")
);
CREATE INDEX IF NOT EXISTS "idx_policy_acce_accepte_76a58e" ON "policy_acceptances" ("accepted_at");
CREATE INDEX IF NOT EXISTS "idx_policy_acce_policy__58ce8b" ON "policy_acceptances" ("policy_id");
CREATE INDEX IF NOT EXISTS "idx_policy_acce_user_id_ea0def" ON "policy_acceptances" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_policy_acce_user_id_3594ff" ON "policy_acceptances" ("user_id", "policy_id");
CREATE INDEX IF NOT EXISTS "idx_policy_acce_user_id_e29f0d" ON "policy_acceptances" ("user_id", "accepted_at");
CREATE INDEX IF NOT EXISTS "idx_policy_acce_policy__67a836" ON "policy_acceptances" ("policy_id", "accepted_at");
CREATE INDEX IF NOT EXISTS "idx_policy_acce_user_id_379c34" ON "policy_acceptances" ("user_id", "withdrawn_at");
COMMENT ON TABLE "policy_acceptances" IS 'Tracks user acceptance of policies.';
CREATE TABLE IF NOT EXISTS "house_swap_listings" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "listing_code" VARCHAR(50) NOT NULL UNIQUE,
    "title" VARCHAR(200) NOT NULL,
    "desired_locations" JSONB NOT NULL,
    "desired_property_types" JSONB NOT NULL,
    "desired_amenities" JSONB NOT NULL,
    "swap_type" SMALLINT NOT NULL  DEFAULT 1,
    "min_swap_duration" INT NOT NULL  DEFAULT 1,
    "max_swap_duration" INT,
    "preferred_duration" INT NOT NULL  DEFAULT 7,
    "availability_type" SMALLINT NOT NULL  DEFAULT 1,
    "available_from" DATE,
    "available_to" DATE,
    "blackout_dates" JSONB NOT NULL,
    "advance_notice_days" INT NOT NULL  DEFAULT 14,
    "allows_pets" BOOL NOT NULL  DEFAULT False,
    "allows_smoking" BOOL NOT NULL  DEFAULT False,
    "allows_children" BOOL NOT NULL  DEFAULT True,
    "allows_events" BOOL NOT NULL  DEFAULT False,
    "max_guests" INT NOT NULL  DEFAULT 2,
    "cleaning_fee" DECIMAL(10,2),
    "security_deposit" DECIMAL(10,2),
    "status" SMALLINT NOT NULL  DEFAULT 1,
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "is_verified" BOOL NOT NULL  DEFAULT False,
    "view_count" INT NOT NULL  DEFAULT 0,
    "inquiry_count" INT NOT NULL  DEFAULT 0,
    "offer_count" INT NOT NULL  DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "published_at" TIMESTAMPTZ,
    "expires_at" TIMESTAMPTZ,
    "description" TEXT NOT NULL,
    "house_rules" JSONB NOT NULL,
    "neighborhood_info" TEXT,
    "transportation_info" TEXT,
    "tags" JSONB NOT NULL,
    "apartment_id" VARCHAR(36) REFERENCES "apartment_complexes" ("id") ON DELETE CASCADE,
    "owner_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "rental_id" VARCHAR(36) REFERENCES "rentals" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_house_swap__listing_849368" ON "house_swap_listings" ("listing_code");
CREATE INDEX IF NOT EXISTS "idx_house_swap__swap_ty_75b0dd" ON "house_swap_listings" ("swap_type");
CREATE INDEX IF NOT EXISTS "idx_house_swap__availab_565e62" ON "house_swap_listings" ("available_from");
CREATE INDEX IF NOT EXISTS "idx_house_swap__availab_a1df8d" ON "house_swap_listings" ("available_to");
CREATE INDEX IF NOT EXISTS "idx_house_swap__allows__30ef3c" ON "house_swap_listings" ("allows_pets");
CREATE INDEX IF NOT EXISTS "idx_house_swap__allows__17eda1" ON "house_swap_listings" ("allows_smoking");
CREATE INDEX IF NOT EXISTS "idx_house_swap__allows__4c86d9" ON "house_swap_listings" ("allows_children");
CREATE INDEX IF NOT EXISTS "idx_house_swap__allows__fd0c62" ON "house_swap_listings" ("allows_events");
CREATE INDEX IF NOT EXISTS "idx_house_swap__status_10edd8" ON "house_swap_listings" ("status");
CREATE INDEX IF NOT EXISTS "idx_house_swap__is_feat_26e34a" ON "house_swap_listings" ("is_featured");
CREATE INDEX IF NOT EXISTS "idx_house_swap__is_veri_b38a71" ON "house_swap_listings" ("is_verified");
CREATE INDEX IF NOT EXISTS "idx_house_swap__view_co_b1c8b6" ON "house_swap_listings" ("view_count");
CREATE INDEX IF NOT EXISTS "idx_house_swap__created_e0f2a1" ON "house_swap_listings" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_house_swap__publish_8cd042" ON "house_swap_listings" ("published_at");
CREATE INDEX IF NOT EXISTS "idx_house_swap__expires_557361" ON "house_swap_listings" ("expires_at");
CREATE INDEX IF NOT EXISTS "idx_house_swap__apartme_0033a6" ON "house_swap_listings" ("apartment_id");
CREATE INDEX IF NOT EXISTS "idx_house_swap__owner_i_4882c9" ON "house_swap_listings" ("owner_id");
CREATE INDEX IF NOT EXISTS "idx_house_swap__rental__f884de" ON "house_swap_listings" ("rental_id");
CREATE INDEX IF NOT EXISTS "idx_house_swap__owner_i_ff434b" ON "house_swap_listings" ("owner_id", "status");
CREATE INDEX IF NOT EXISTS "idx_house_swap__swap_ty_96efef" ON "house_swap_listings" ("swap_type", "status");
CREATE INDEX IF NOT EXISTS "idx_house_swap__availab_413a8e" ON "house_swap_listings" ("available_from", "available_to");
CREATE INDEX IF NOT EXISTS "idx_house_swap__allows__5f13f2" ON "house_swap_listings" ("allows_pets", "status");
CREATE INDEX IF NOT EXISTS "idx_house_swap__is_feat_fe4b25" ON "house_swap_listings" ("is_featured", "status");
COMMENT ON COLUMN "house_swap_listings"."swap_type" IS 'SIMULTANEOUS: 1\nNON_SIMULTANEOUS: 2\nHOSPITALITY: 3\nRENTAL: 4\nLONG_TERM: 5\nSHORT_TERM: 6';
COMMENT ON COLUMN "house_swap_listings"."availability_type" IS 'FLEXIBLE: 1\nSPECIFIC_DATES: 2\nSEASONAL: 3\nWEEKENDS_ONLY: 4\nWEEKDAYS_ONLY: 5';
COMMENT ON COLUMN "house_swap_listings"."status" IS 'DRAFT: 1\nACTIVE: 2\nPENDING: 3\nRESERVED: 4\nCONFIRMED: 5\nIN_PROGRESS: 6\nCOMPLETED: 7\nCANCELLED: 8\nEXPIRED: 9\nARCHIVED: 10';
CREATE TABLE IF NOT EXISTS "sawap_amenities" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "slug" VARCHAR(50),
    "description" TEXT,
    "icon" VARCHAR(100),
    "sort_order" INT NOT NULL  DEFAULT 0,
    "is_featured" BOOL NOT NULL  DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "category_id" UUID REFERENCES "amenity_categories" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_sawap_ameni_name_0de94d" ON "sawap_amenities" ("name");
CREATE INDEX IF NOT EXISTS "idx_sawap_ameni_is_feat_67a571" ON "sawap_amenities" ("is_featured");
CREATE TABLE IF NOT EXISTS "swap_offers" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "offer_code" VARCHAR(50)  UNIQUE,
    "proposed_start_date" DATE NOT NULL,
    "proposed_end_date" DATE NOT NULL,
    "proposed_duration" INT NOT NULL,
    "status" SMALLINT NOT NULL,
    "message" TEXT,
    "special_requests" JSONB NOT NULL,
    "proposed_rent" DECIMAL(10,2),
    "proposed_cleaning_fee" DECIMAL(10,2),
    "proposed_security_deposit" DECIMAL(10,2),
    "responded_at" TIMESTAMPTZ,
    "response_message" TEXT,
    "expires_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "counter_to_offer_id" UUID REFERENCES "swap_offers" ("id") ON DELETE SET NULL,
    "from_user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "offering_listing_id" UUID NOT NULL REFERENCES "house_swap_listings" ("id") ON DELETE CASCADE,
    "target_listing_id" UUID NOT NULL REFERENCES "house_swap_listings" ("id") ON DELETE CASCADE,
    "to_user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_swap_offers_offer_c_555347" ON "swap_offers" ("offer_code");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_propose_d6f0f0" ON "swap_offers" ("proposed_start_date");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_propose_242285" ON "swap_offers" ("proposed_end_date");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_status_d1044a" ON "swap_offers" ("status");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_expires_0a12ed" ON "swap_offers" ("expires_at");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_created_7308e9" ON "swap_offers" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_from_us_e81959" ON "swap_offers" ("from_user_id");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_offerin_804276" ON "swap_offers" ("offering_listing_id");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_target__378fb0" ON "swap_offers" ("target_listing_id");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_to_user_d99adf" ON "swap_offers" ("to_user_id");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_from_us_c06ed5" ON "swap_offers" ("from_user_id", "status");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_to_user_f71383" ON "swap_offers" ("to_user_id", "status");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_target__00d1b4" ON "swap_offers" ("target_listing_id", "status");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_propose_ac2513" ON "swap_offers" ("proposed_start_date", "proposed_end_date");
CREATE INDEX IF NOT EXISTS "idx_swap_offers_expires_ea4f19" ON "swap_offers" ("expires_at", "status");
COMMENT ON COLUMN "swap_offers"."status" IS 'PENDING: 1\nACCEPTED: 2\nCOUNTER_OFFER: 3\nREJECTED: 4\nEXPIRED: 5\nWITHDRAWN: 6\nCONFIRMED: 7\nCANCELLED: 8';
CREATE TABLE IF NOT EXISTS "swap_agreements" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "agreement_code" VARCHAR(50) NOT NULL UNIQUE,
    "start_date" DATE NOT NULL,
    "end_date" DATE NOT NULL,
    "total_days" INT NOT NULL,
    "monetary_exchange" BOOL NOT NULL  DEFAULT False,
    "amount" DECIMAL(10,2),
    "security_deposit_amount" DECIMAL(10,2),
    "status" SMALLINT NOT NULL  DEFAULT 1,
    "party_a_signed_at" TIMESTAMPTZ,
    "party_b_signed_at" TIMESTAMPTZ,
    "fully_signed_at" TIMESTAMPTZ,
    "insurance_provided" BOOL NOT NULL  DEFAULT False,
    "insurance_details" JSONB,
    "platform_fee" DECIMAL(10,2),
    "platform_fee_paid" BOOL NOT NULL  DEFAULT False,
    "agreement_document_url" TEXT,
    "terms_accepted" JSONB NOT NULL,
    "cancellation_reason" TEXT,
    "completed_at" TIMESTAMPTZ,
    "completion_notes" TEXT,
    "rating_by_a_to_b" INT,
    "rating_by_b_to_a" INT,
    "review_by_a" TEXT,
    "review_by_b" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "cancellation_initiated_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "party_a_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "party_b_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "property_a_id" UUID NOT NULL REFERENCES "house_swap_listings" ("id") ON DELETE CASCADE,
    "property_b_id" UUID NOT NULL REFERENCES "house_swap_listings" ("id") ON DELETE CASCADE,
    "originating_offer_id" UUID NOT NULL UNIQUE REFERENCES "swap_offers" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_agreeme_62bf79" ON "swap_agreements" ("agreement_code");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_start_d_1c1c7f" ON "swap_agreements" ("start_date");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_end_dat_f2f0be" ON "swap_agreements" ("end_date");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_status_4df924" ON "swap_agreements" ("status");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_created_5a5dac" ON "swap_agreements" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_party_a_fffa61" ON "swap_agreements" ("party_a_id");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_party_b_53adca" ON "swap_agreements" ("party_b_id");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_propert_a914b0" ON "swap_agreements" ("property_a_id");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_propert_a3ff3b" ON "swap_agreements" ("property_b_id");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_origina_6c61ee" ON "swap_agreements" ("originating_offer_id");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_party_a_1c9fe9" ON "swap_agreements" ("party_a_id", "status");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_party_b_2a23da" ON "swap_agreements" ("party_b_id", "status");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_start_d_7c561d" ON "swap_agreements" ("start_date", "end_date");
CREATE INDEX IF NOT EXISTS "idx_swap_agreem_status_6fd9e9" ON "swap_agreements" ("status", "start_date");
COMMENT ON COLUMN "swap_agreements"."status" IS 'DRAFT: 1\nPENDING_SIGNATURES: 2\nSIGNED: 3\nACTIVE: 4\nCOMPLETED: 5\nCANCELLED: 6\nDISPUTED: 7';
CREATE TABLE IF NOT EXISTS "verification_codes" (
    "id" VARCHAR(36) NOT NULL  PRIMARY KEY,
    "code" VARCHAR(10) NOT NULL,
    "type" VARCHAR(16) NOT NULL,
    "identifier" VARCHAR(255),
    "is_used" BOOL NOT NULL  DEFAULT False,
    "used_at" TIMESTAMPTZ,
    "expires_at" TIMESTAMPTZ,
    "status" VARCHAR(7) NOT NULL  DEFAULT 'pending',
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_verificatio_code_c9b369" ON "verification_codes" ("code");
CREATE INDEX IF NOT EXISTS "idx_verificatio_type_0dc762" ON "verification_codes" ("type");
CREATE INDEX IF NOT EXISTS "idx_verificatio_is_used_d4b6c1" ON "verification_codes" ("is_used");
CREATE INDEX IF NOT EXISTS "idx_verificatio_status_09841e" ON "verification_codes" ("status");
CREATE INDEX IF NOT EXISTS "idx_verificatio_type_23f92c" ON "verification_codes" ("type", "status", "expires_at");
CREATE INDEX IF NOT EXISTS "idx_verificatio_user_id_650566" ON "verification_codes" ("user_id", "type", "status");
CREATE INDEX IF NOT EXISTS "idx_verificatio_code_2706db" ON "verification_codes" ("code", "type", "status");
COMMENT ON COLUMN "verification_codes"."type" IS 'EMAIL: email\nPHONE: phone\nPASSWORD_RESET: password_reset\nTWO_FACTOR_AUTH: two_factor_auth\nACCOUNT_RECOVERY: account_recovery\nEMAIL_CHANGE: email_change';
COMMENT ON COLUMN "verification_codes"."status" IS 'PENDING: pending\nUSED: used\nEXPIRED: expired';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "apartment_amenities_m2m" (
    "apartment_amenities_id" UUID NOT NULL REFERENCES "apartment_amenities" ("id") ON DELETE CASCADE,
    "apartmentcomplex_id" VARCHAR(36) NOT NULL REFERENCES "apartment_complexes" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "rental_managers" (
    "rentals_id" VARCHAR(36) NOT NULL REFERENCES "rentals" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "apartment_amenities_m2m" (
    "sawap_amenities_id" UUID NOT NULL REFERENCES "sawap_amenities" ("id") ON DELETE CASCADE,
    "swapoffer_id" UUID NOT NULL REFERENCES "swap_offers" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
