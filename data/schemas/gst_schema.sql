-- data/schemas/gst_schema.sql
CREATE TABLE IF NOT EXISTS gst_invoice_records (
    invoice_id      TEXT        PRIMARY KEY,
    gstin_supplier  TEXT        NOT NULL,
    gstin_buyer     TEXT        NOT NULL,
    invoice_date    DATE        NOT NULL,
    invoice_type    TEXT        DEFAULT 'B2B',
    taxable_value   DECIMAL(15,2),
    cgst_amount     DECIMAL(10,2),
    sgst_amount     DECIMAL(10,2),
    igst_amount     DECIMAL(10,2),
    cess_amount     DECIMAL(10,2) DEFAULT 0.0,
    state_code      CHAR(2)     NOT NULL,
    hsn_code        TEXT,
    filing_status   TEXT        DEFAULT 'FILED',
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gst_invoice_items (
    item_id             INTEGER     PRIMARY KEY AUTOINCREMENT,
    invoice_id          TEXT        NOT NULL REFERENCES gst_invoice_records(invoice_id),
    item_description    TEXT,
    hsn_code            TEXT,
    quantity            DECIMAL(10,3),
    unit_value          DECIMAL(12,2),
    taxable_value       DECIMAL(15,2),
    gst_rate            DECIMAL(5,2)
);
