"""
Personal Finance Dashboard - Data Pipeline (ETL)
------------------------------------------------
Extract  -> transactions aate hain (bank API simulate / CSV upload)
Transform-> cleaning, categorisation, duplicates hatana, month column
Load     -> SQLite database (finance.db) me store

Run:  python data_pipeline.py
"""
import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
DB_PATH = BASE / "finance.db"
RAW_CSV = BASE / "data" / "raw_transactions.csv"

# Keyword based auto-categorisation (description -> category)
CATEGORY_RULES = {
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "dominos"],
    "Groceries": ["bigbasket", "blinkit", "dmart", "grocery"],
    "Transport": ["uber", "ola", "petrol", "metro", "rapido"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio"],
    "Bills": ["electricity", "jio", "airtel", "wifi", "gas bill"],
    "Rent": ["rent"],
    "Entertainment": ["netflix", "spotify", "bookmyshow", "hotstar"],
    "Health": ["pharmacy", "apollo", "hospital", "gym"],
    "Salary": ["salary"],
    "Freelance": ["freelance", "upwork"],
    "Investment": ["sip", "mutual fund", "zerodha", "fd"],
}


def categorise(description: str) -> str:
    d = description.lower()
    for cat, keywords in CATEGORY_RULES.items():
        if any(k in d for k in keywords):
            return cat
    return "Other"


# ---------------- EXTRACT ----------------
def generate_raw_data(months: int = 12, seed: int = 42) -> pd.DataFrame:
    """Bank statement jaisa raw data simulate karta hai (12 months)."""
    random.seed(seed)
    today = date.today()
    month_starts = [d.date() for d in pd.date_range(end=today.replace(day=1), periods=months, freq="MS")]
    expense_templates = [
        ("Swiggy order", 150, 600, 10), ("Zomato order", 200, 700, 8),
        ("BigBasket grocery", 500, 2500, 4), ("Blinkit grocery", 100, 800, 6),
        ("Uber ride", 80, 450, 8), ("Petrol pump", 500, 1500, 3),
        ("Amazon purchase", 300, 4000, 3), ("Myntra order", 500, 3000, 1),
        ("Electricity bill", 800, 2000, 1), ("Jio recharge", 299, 299, 1),
        ("Netflix subscription", 199, 199, 1), ("Apollo pharmacy", 100, 900, 1),
        ("Cafe coffee", 120, 350, 4), ("Gym membership", 1000, 1000, 1),
    ]
    rows, tid = [], 1
    for month_start in month_starts:
        # Income
        rows.append([tid, month_start, "Salary credit ACME Pvt Ltd", 65000, "credit"]); tid += 1
        if random.random() < 0.5:
            rows.append([tid, month_start + timedelta(days=random.randint(5, 25)),
                         "Freelance payment Upwork", random.randint(5000, 15000), "credit"]); tid += 1
        # Fixed
        rows.append([tid, month_start + timedelta(days=2), "House rent", 15000, "debit"]); tid += 1
        rows.append([tid, month_start + timedelta(days=5), "SIP Mutual Fund", 5000, "debit"]); tid += 1
        # Variable expenses
        for desc, lo, hi, freq in expense_templates:
            for _ in range(random.randint(max(1, freq - 2), freq + 1)):
                amt = round(random.uniform(lo, hi), 2)
                rows.append([tid, month_start + timedelta(days=random.randint(0, 27)), desc, amt, "debit"]); tid += 1
    df = pd.DataFrame(rows, columns=["txn_id", "txn_date", "description", "amount", "txn_type"])
    df = df[df["txn_date"] <= today]                              # future dates nahi
    df["txn_id"] = range(1, len(df) + 1)
    # Real world dirty data: duplicates + missing values daal rahe hain
    df = pd.concat([df, df.sample(15, random_state=1)])          # duplicate rows
    df.loc[df.sample(8, random_state=2).index, "amount"] = None  # missing amount
    return df


# ---------------- TRANSFORM ----------------
def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates(subset="txn_id")
    df = df.dropna(subset=["amount"])
    df["txn_date"] = pd.to_datetime(df["txn_date"])
    df["description"] = df["description"].str.strip()
    df["category"] = df["description"].apply(categorise)
    df["month"] = df["txn_date"].dt.to_period("M").astype(str)
    df["amount"] = df["amount"].astype(float).round(2)
    print(f"[transform] {before} raw rows -> {len(df)} clean rows")
    return df.sort_values("txn_date")


# ---------------- LOAD ----------------
def load(df: pd.DataFrame, db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript((BASE / "sql" / "schema.sql").read_text())
    out = df.copy()
    out["txn_date"] = out["txn_date"].dt.strftime("%Y-%m-%d")
    out[["txn_id", "txn_date", "description", "amount", "txn_type", "category", "month"]] \
        .to_sql("transactions", conn, if_exists="append", index=False)
    conn.execute("INSERT OR REPLACE INTO budgets VALUES ('Food', 6000), ('Shopping', 5000), "
                 "('Transport', 4000), ('Entertainment', 1000), ('Groceries', 6000)")
    conn.commit()
    conn.close()
    print(f"[load] {len(df)} rows loaded into {db_path.name}")


def run_pipeline():
    RAW_CSV.parent.mkdir(exist_ok=True)
    raw = generate_raw_data()
    raw.to_csv(RAW_CSV, index=False)
    clean = transform(raw)
    clean.to_csv(BASE / "data" / "clean_transactions.csv", index=False)  # Power BI ke liye
    load(clean)


if __name__ == "__main__":
    run_pipeline()
