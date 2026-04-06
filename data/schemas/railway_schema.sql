-- data/schemas/railway_schema.sql
CREATE TABLE IF NOT EXISTS railway_trains (
    train_no        TEXT        PRIMARY KEY,
    train_name      TEXT        NOT NULL,
    source_station  CHAR(5)     NOT NULL,
    dest_station    CHAR(5)     NOT NULL,
    total_seats     INTEGER     DEFAULT 72,
    class_type      TEXT        DEFAULT '3A'
);

CREATE TABLE IF NOT EXISTS railway_pnr_bookings (
    pnr_number      TEXT        PRIMARY KEY,
    train_no        TEXT        NOT NULL REFERENCES railway_trains(train_no),
    journey_date    DATE        NOT NULL,
    passenger_name  TEXT        NOT NULL,
    passenger_age   INTEGER,
    gender          CHAR(1),
    booking_status  TEXT        DEFAULT 'CNF',
    class_type      TEXT        NOT NULL,
    seat_no         TEXT,
    fare_amount     DECIMAL(8,2),
    booking_time    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    booked_via      TEXT        DEFAULT 'WEB'
);
