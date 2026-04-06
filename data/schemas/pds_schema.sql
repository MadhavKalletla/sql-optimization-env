-- data/schemas/pds_schema.sql
CREATE TABLE IF NOT EXISTS ration_card_beneficiaries (
    card_id         TEXT        PRIMARY KEY,
    household_head  TEXT        NOT NULL,
    state_code      CHAR(2)     NOT NULL,
    district_code   CHAR(3)     NOT NULL,
    block_code      CHAR(5),
    village_code    CHAR(7),
    card_type       TEXT        NOT NULL,
    members_count   INTEGER     DEFAULT 1,
    aadhar_linked   INTEGER     DEFAULT 0,
    mobile_number   TEXT,
    created_at      DATE,
    last_updated    DATE
);

CREATE TABLE IF NOT EXISTS pds_allotments (
    allotment_id        INTEGER     PRIMARY KEY AUTOINCREMENT,
    card_id             TEXT        NOT NULL,
    month_year          TEXT        NOT NULL,
    commodity           TEXT        NOT NULL,
    entitled_qty_kg     DECIMAL(6,2),
    offtake_qty_kg      DECIMAL(6,2) DEFAULT 0,
    fair_shop_code      TEXT,
    offtake_date        DATE
);
