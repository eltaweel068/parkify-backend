-- ============================================================
--  Parkify – Supabase / PostgreSQL Schema
--  Run this in the Supabase SQL Editor to create all tables.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    phone           VARCHAR(50),
    password_hash   VARCHAR(255),
    role            VARCHAR(20)  NOT NULL DEFAULT 'user',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    gender          VARCHAR(20),
    address         TEXT,
    profile_photo   TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ── cars ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cars (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    license_plate   VARCHAR(50)  NOT NULL,
    make            VARCHAR(100),
    model           VARCHAR(100),
    color           VARCHAR(50),
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cars_user_id ON cars(user_id);

-- ── payment_methods ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payment_methods (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    method_type     VARCHAR(50) NOT NULL,
    last_four       VARCHAR(4),
    card_holder     VARCHAR(255),
    expiry          VARCHAR(10),
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pm_user_id ON payment_methods(user_id);

-- ── parkings ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parkings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    address         TEXT NOT NULL,
    city            VARCHAR(100),
    country         VARCHAR(100) NOT NULL DEFAULT 'Egypt',
    parking_type    VARCHAR(50)  NOT NULL DEFAULT 'covered',
    total_slots     INTEGER      NOT NULL,
    available_slots INTEGER      NOT NULL,
    occupied_slots  INTEGER      NOT NULL DEFAULT 0,
    is_full         BOOLEAN      NOT NULL DEFAULT FALSE,
    rate_per_hour   DOUBLE PRECISION NOT NULL,
    currency        VARCHAR(10)  NOT NULL DEFAULT 'EGP',
    amenities       TEXT[]       NOT NULL DEFAULT '{}',
    images          TEXT[]       NOT NULL DEFAULT '{}',
    rating          DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    review_count    INTEGER      NOT NULL DEFAULT 0,
    is_24_7         BOOLEAN      NOT NULL DEFAULT TRUE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    device_key      VARCHAR(255),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── parking_slots ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parking_slots (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parking_id              UUID NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    slot_number             VARCHAR(50) NOT NULL,
    floor                   INTEGER     NOT NULL DEFAULT 1,
    section                 VARCHAR(50),
    status                  VARCHAR(20) NOT NULL DEFAULT 'available',
    is_handicap             BOOLEAN     NOT NULL DEFAULT FALSE,
    is_ev_charging          BOOLEAN     NOT NULL DEFAULT FALSE,
    current_vehicle_plate   VARCHAR(50),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slots_parking_id   ON parking_slots(parking_id);
CREATE INDEX IF NOT EXISTS idx_slots_status        ON parking_slots(status);

-- ── bookings ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bookings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    parking_id      UUID NOT NULL REFERENCES parkings(id),
    slot_id         UUID NOT NULL REFERENCES parking_slots(id),
    vehicle_plate   VARCHAR(50)      NOT NULL,
    start_time      TIMESTAMPTZ      NOT NULL,
    end_time        TIMESTAMPTZ      NOT NULL,
    actual_exit_time TIMESTAMPTZ,
    status          VARCHAR(20)      NOT NULL DEFAULT 'confirmed',
    total_hours     DOUBLE PRECISION NOT NULL,
    amount          DOUBLE PRECISION NOT NULL,
    fees            DOUBLE PRECISION NOT NULL DEFAULT 0,
    total_amount    DOUBLE PRECISION NOT NULL,
    currency        VARCHAR(10)      NOT NULL DEFAULT 'EGP',
    payment_status  VARCHAR(20)      NOT NULL DEFAULT 'pending',
    payment_method  VARCHAR(50)      NOT NULL DEFAULT 'card',
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bookings_user_id    ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_parking_id ON bookings(parking_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status     ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_plate      ON bookings(vehicle_plate);

-- ── favorites ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS favorites (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parking_id  UUID NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, parking_id)
);

-- ── notifications ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL,
    message             TEXT         NOT NULL,
    notification_type   VARCHAR(50)  NOT NULL,
    is_read             BOOLEAN      NOT NULL DEFAULT FALSE,
    data                JSONB,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notif_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notif_is_read ON notifications(is_read);

-- ── alerts ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parking_id  UUID NOT NULL REFERENCES parkings(id),
    alert_type  VARCHAR(50)  NOT NULL,
    severity    VARCHAR(20)  NOT NULL,
    message     TEXT         NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'active',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_alerts_parking_id ON alerts(parking_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status     ON alerts(status);

-- ── vehicle_logs ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vehicle_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parking_id      UUID NOT NULL REFERENCES parkings(id),
    vehicle_plate   VARCHAR(50) NOT NULL,
    action          VARCHAR(20) NOT NULL,
    gate            VARCHAR(100),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    plate_image     TEXT,
    confidence      DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_vlogs_parking_id ON vehicle_logs(parking_id);
CREATE INDEX IF NOT EXISTS idx_vlogs_plate      ON vehicle_logs(vehicle_plate);

-- ── support_tickets ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS support_tickets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    subject     VARCHAR(255) NOT NULL,
    message     TEXT         NOT NULL,
    category    VARCHAR(50)  NOT NULL DEFAULT 'general',
    status      VARCHAR(20)  NOT NULL DEFAULT 'open',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ
);

-- ── spot_watchers ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS spot_watchers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parking_id  UUID NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(parking_id, user_id)
);

-- ── reset_codes ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reset_codes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255),
    phone       VARCHAR(50),
    code        VARCHAR(10)  NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ  NOT NULL,
    is_used     BOOLEAN      NOT NULL DEFAULT FALSE
);
