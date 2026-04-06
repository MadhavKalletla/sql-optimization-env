# data/seed_database.py
# Run once:  python -m data.seed_database --rows 100000

import sqlite3, random, string, datetime, argparse, calendar
from pathlib import Path

SEED = 42
random.seed(SEED)

STATES = {
    "01": "JK", "02": "HP", "03": "PB", "06": "HR", "07": "DL", "08": "RJ",
    "09": "UP", "10": "BR", "11": "SK", "12": "AR", "13": "NL", "14": "MN",
    "18": "AS", "19": "WB", "21": "OR", "22": "CG", "23": "MP", "24": "GJ",
    "27": "MH", "29": "KA", "32": "KL", "33": "TN", "36": "TG", "37": "AP",
}
STATE_CODES = list(STATES.keys())

HSN_CODES = [
    "0101", "0201", "0301", "1001", "1006", "1701",
    "2101", "2201", "3004", "4901", "6101", "7108",
    "8471", "8517", "9018", "9401",
]
GST_RATES = [0, 5, 12, 18, 28]


def random_gstin(state_code: str) -> str:
    pan = "".join(random.choices(string.ascii_uppercase, k=5))
    pan += "".join(random.choices(string.digits, k=4))
    pan += random.choice(string.ascii_uppercase)
    suffix = "1Z" + random.choice(string.ascii_uppercase + string.digits)
    return f"{state_code}{pan}{suffix}"


def random_pnr(idx: int) -> str:
    """Deterministic PNR based on index to guarantee uniqueness."""
    return f"{idx:010d}"


def random_date(start="2023-01-01", end="2025-12-31") -> str:
    s = datetime.date.fromisoformat(start)
    e = datetime.date.fromisoformat(end)
    delta = (e - s).days
    return str(s + datetime.timedelta(days=random.randint(0, delta)))


def random_railway_travel_date(year: int = 2025) -> str:
    month_pool = []
    for month, weight in (
        (1, 2), (2, 2), (3, 8), (4, 2), (5, 2), (6, 2),
        (7, 2), (8, 2), (9, 3), (10, 8), (11, 8), (12, 3),
    ):
        month_pool.extend([month] * weight)
    month = random.choice(month_pool)
    _, last = calendar.monthrange(year, month)
    day = random.randint(1, last)
    return f"{year}-{month:02d}-{day:02d}"


# ── GST ───────────────────────────────────────────────────────────────────
def seed_gst(conn, n_invoices: int):
    print(f"  Seeding GST: {n_invoices} invoices…")
    invoices, items = [], []

    for i in range(n_invoices):
        state = random.choice(STATE_CODES)
        supplier = random_gstin(state)
        buyer_state = random.choice(STATE_CODES)
        buyer = random_gstin(buyer_state)

        is_igst = state != buyer_state
        taxable = round(random.uniform(1000, 500000), 2)
        rate = random.choice(GST_RATES)
        tax = round(taxable * rate / 100, 2)

        cgst = 0 if is_igst else round(tax / 2, 2)
        sgst = 0 if is_igst else round(tax / 2, 2)
        igst = tax if is_igst else 0

        if (not is_igst) and rate > 0 and random.random() < 0.05:
            half = round(tax / 2, 2)
            max_delta = min(half - 0.01, tax * 0.2, 5000)
            if max_delta > 1:
                delta = round(random.uniform(1, max_delta), 2)
                if random.random() < 0.5:
                    cgst = round(half - delta, 2)
                else:
                    sgst = round(half - delta, 2)

        inv_id = f"INV{i:08d}"
        inv_date = random_date()

        invoices.append((
            inv_id, supplier, buyer, inv_date, "B2B",
            taxable, cgst, sgst, igst, 0, state,
            random.choice(HSN_CODES), "FILED",
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))

        for j in range(random.randint(1, 5)):
            item_taxable = round(taxable / random.randint(1, 5), 2)
            items.append((
                inv_id, f"Item {j+1}", random.choice(HSN_CODES),
                round(random.uniform(1, 100), 2),
                round(item_taxable / random.randint(1, 100), 2),
                item_taxable, rate,
            ))

    conn.executemany(
        "INSERT INTO gst_invoice_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        invoices,
    )
    conn.executemany(
        "INSERT INTO gst_invoice_items(invoice_id,item_description,hsn_code,"
        "quantity,unit_value,taxable_value,gst_rate) VALUES(?,?,?,?,?,?,?)",
        items,
    )
    conn.commit()
    print(f"    GST done: {len(invoices)} invoices, {len(items)} items")


# ── PDS ───────────────────────────────────────────────────────────────────
def seed_pds(conn, n_cards: int):
    print(f"  Seeding PDS: {n_cards} ration cards…")
    CARD_TYPES = ["APL", "BPL", "AAY", "PHH"]
    COMMODITIES = ["RICE", "WHEAT", "SUGAR", "OIL"]
    cards, allotments = [], []

    for i in range(n_cards):
        state = random.choice(STATE_CODES)
        card_id = f"RC{random.randint(2020,2025)}{state}{i:07d}"
        ctype = random.choice(CARD_TYPES)
        cards.append((
            card_id, f"Household_{i}", state,
            f"{random.randint(1,30):03d}", None, None,
            ctype, random.randint(1, 8), random.randint(0, 1),
            None, random_date("2020-01-01", "2022-12-31"), None,
        ))

        for month_offset in range(random.randint(1, 24)):
            yr = 2024 + month_offset // 12
            mo = (month_offset % 12) + 1
            month_year = f"{yr}-{mo:02d}"
            for commodity in random.sample(COMMODITIES, k=random.randint(1, 3)):
                entitled = round(random.uniform(5, 35), 1)
                allotments.append((
                    card_id, month_year, commodity, entitled,
                    round(entitled * random.uniform(0.7, 1.0), 1),
                    f"FS{random.randint(10000,99999)}", None,
                ))

    conn.executemany(
        "INSERT INTO ration_card_beneficiaries VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        cards,
    )
    conn.executemany(
        "INSERT INTO pds_allotments(card_id,month_year,commodity,"
        "entitled_qty_kg,offtake_qty_kg,fair_shop_code,offtake_date) "
        "VALUES(?,?,?,?,?,?,?)",
        allotments,
    )
    conn.commit()
    print(f"    PDS done: {len(cards)} cards, {len(allotments)} allotments")


# ── Railway ───────────────────────────────────────────────────────────────
def seed_railway(conn, n_bookings: int):
    print(f"  Seeding Railway: {n_bookings} bookings…")
    TRAINS = [
        ("12001", "BHOPAL EXP", "NDLS", "BPL", 72, "2A"),
        ("12951", "RAJDHANI", "NDLS", "BCT", 48, "1A"),
        ("17031", "HYDERABAD EXP", "NZB", "HYB", 72, "SL"),
        ("12723", "TELANGANA EXP", "SC", "NDLS", 72, "3A"),
        ("16093", "LUCKNOW EXP", "LKO", "MAS", 60, "SL"),
    ]
    conn.executemany("INSERT INTO railway_trains VALUES(?,?,?,?,?,?)", TRAINS)

    STATUSES = ["CNF"] * 70 + [f"WL/{i}" for i in range(1, 15)] + [f"RAC/{i}" for i in range(1, 6)]
    CLASSES = ["1A", "2A", "3A", "SL", "CC"]
    bookings = []

    for i in range(n_bookings):
        train = random.choice(TRAINS)
        bookings.append((
            random_pnr(i), train[0],
            random_railway_travel_date(2025),
            f"Passenger_{i}", random.randint(5, 80),
            random.choice(["M", "F"]),
            random.choice(STATUSES),
            random.choice(CLASSES),
            f"{random.randint(1,72)}",
            round(random.uniform(200, 3500), 2),
            None, random.choice(["WEB", "APP", "TATKAL", "COUNTER"]),
        ))

    conn.executemany(
        "INSERT INTO railway_pnr_bookings VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        bookings,
    )
    conn.commit()
    print(f"    Railway done: {len(bookings)} bookings")


# ── MGNREGA ──────────────────────────────────────────────────────────────
def seed_mgnrega(conn, n_workers: int):
    print(f"  Seeding MGNREGA: {n_workers} workers…")
    WAGE_RATES = {"MH": 273, "TG": 257, "KA": 309, "TN": 294, "AP": 257, "UP": 213, "BR": 194}
    workers, attendance, payments = [], [], []

    for i in range(n_workers):
        state = random.choice(list(WAGE_RATES.keys()))
        worker_id = f"WK{state}{i:07d}"
        wage = WAGE_RATES[state]
        workers.append((
            worker_id, f"Worker_{i}", state,
            f"{random.randint(1,30):03d}",
            f"GP{random.randint(1000,9999)}",
            f"JC{state}{i:08d}", None, None, None, wage,
        ))

        n_days = random.randint(0, 150)
        for d in range(n_days):
            work_date = random_date("2024-04-01", "2025-03-31")
            attendance.append((
                worker_id, work_date,
                f"PROJ{random.randint(10000,99999)}",
                random.choice([0.5, 1.0]),
                f"MR{random.randint(10000,99999)}", 1,
            ))

        for m in range(12):
            yr = 2024 + m // 12
            mo = (m % 12) + 4
            if mo > 12:
                mo -= 12
                yr += 1
            days = round(random.uniform(0, 25), 1)
            amount_due = round(days * wage, 2)
            amount_paid = amount_due if random.random() > 0.1 else 0
            payments.append((
                worker_id, f"{yr}-{mo:02d}", days,
                amount_due, amount_paid,
                random_date(f"{yr}-{mo:02d}-01", f"{yr}-{mo:02d}-28") if amount_paid > 0 else None,
                f"UTR{random.randint(100000000,999999999)}" if amount_paid > 0 else None,
            ))

    conn.executemany("INSERT INTO mgnrega_workers VALUES(?,?,?,?,?,?,?,?,?,?)", workers)
    conn.executemany(
        "INSERT INTO mgnrega_attendance(worker_id,work_date,project_code,"
        "days_worked,muster_roll_no,verified) VALUES(?,?,?,?,?,?)",
        attendance,
    )
    conn.executemany(
        "INSERT INTO mgnrega_payments(worker_id,payment_month,days_worked,"
        "amount_due,amount_paid,payment_date,utr_number) VALUES(?,?,?,?,?,?,?)",
        payments,
    )
    conn.commit()
    print(f"    MGNREGA done: {len(workers)} workers, {len(attendance)} attendance, {len(payments)} payments")


# ── Schema creation ───────────────────────────────────────────────────────
def create_all_tables(conn):
    schema_dir = Path(__file__).resolve().parent / "schemas"
    for sql_file in ["gst_schema.sql", "pds_schema.sql", "railway_schema.sql", "mgnrega_schema.sql"]:
        with open(schema_dir / sql_file) as f:
            conn.executescript(f.read())


# ── Main seeder ───────────────────────────────────────────────────────────
def seed_database(db: str, rows: int):
    random.seed(SEED)  # Reset seed for determinism
    Path(db).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    create_all_tables(conn)

    seed_gst(conn, rows)
    seed_pds(conn, rows // 5)
    seed_railway(conn, rows)
    seed_mgnrega(conn, rows // 3)

    conn.close()
    print(f"✅ Database seeded: {db}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument("--db", default="data/fixtures/benchmark_seed42.db")
    args = parser.parse_args()
    seed_database(args.db, args.rows)


if __name__ == "__main__":
    main()
