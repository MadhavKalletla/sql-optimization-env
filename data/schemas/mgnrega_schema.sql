-- data/schemas/mgnrega_schema.sql
CREATE TABLE IF NOT EXISTS mgnrega_workers (
    worker_id       TEXT        PRIMARY KEY,
    worker_name     TEXT        NOT NULL,
    state_code      CHAR(2)     NOT NULL,
    district_code   CHAR(3)     NOT NULL,
    gram_panchayat  TEXT,
    job_card_no     TEXT        UNIQUE,
    aadhar_no       TEXT,
    bank_account    TEXT,
    ifsc_code       TEXT,
    wage_rate       DECIMAL(6,2) DEFAULT 200.0
);

CREATE TABLE IF NOT EXISTS mgnrega_attendance (
    attendance_id   INTEGER     PRIMARY KEY AUTOINCREMENT,
    worker_id       TEXT        NOT NULL,
    work_date       DATE        NOT NULL,
    project_code    TEXT        NOT NULL,
    days_worked     DECIMAL(3,1) DEFAULT 1.0,
    muster_roll_no  TEXT,
    verified        INTEGER     DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mgnrega_payments (
    payment_id      INTEGER     PRIMARY KEY AUTOINCREMENT,
    worker_id       TEXT        NOT NULL,
    payment_month   TEXT        NOT NULL,
    days_worked     DECIMAL(5,1),
    amount_due      DECIMAL(8,2),
    amount_paid     DECIMAL(8,2) DEFAULT 0,
    payment_date    DATE,
    utr_number      TEXT
);
