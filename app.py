"""
Personal Finance Dashboard - Flask backend (REST API)
Run:
    python data_pipeline.py      # pehli baar database banane ke liye
    python app.py                # http://127.0.0.1:5000 kholo
"""
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, request, render_template

from data_pipeline import categorise, DB_PATH, run_pipeline

app = Flask(__name__)


def query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return rows


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.get("/api/summary")
def summary():
    """KPI cards: total income, expense, savings, savings rate."""
    month = request.args.get("month")
    where, params = ("WHERE month = ?", (month,)) if month else ("", ())
    r = query(f"""
        SELECT ROUND(SUM(CASE WHEN txn_type='credit' THEN amount ELSE 0 END),0) AS income,
               ROUND(SUM(CASE WHEN txn_type='debit'  THEN amount ELSE 0 END),0) AS expense
        FROM transactions {where}""", params)[0]
    income, expense = r["income"] or 0, r["expense"] or 0
    r["savings"] = income - expense
    r["savings_rate"] = round(100 * r["savings"] / income, 1) if income else 0
    return jsonify(r)


@app.get("/api/monthly-trend")
def monthly_trend():
    return jsonify(query("""
        SELECT month,
               ROUND(SUM(CASE WHEN txn_type='credit' THEN amount ELSE 0 END),0) AS income,
               ROUND(SUM(CASE WHEN txn_type='debit'  THEN amount ELSE 0 END),0) AS expense,
               ROUND(SUM(CASE WHEN txn_type='credit' THEN amount ELSE -amount END),0) AS savings
        FROM transactions GROUP BY month ORDER BY month"""))


@app.get("/api/category-breakdown")
def category_breakdown():
    month = request.args.get("month")
    extra, params = ("AND month = ?", (month,)) if month else ("", ())
    return jsonify(query(f"""
        SELECT category, ROUND(SUM(amount),0) AS total
        FROM transactions WHERE txn_type='debit' {extra}
        GROUP BY category ORDER BY total DESC""", params))


@app.get("/api/budget-status")
def budget_status():
    return jsonify(query("""
        SELECT b.category, b.monthly_limit, ROUND(COALESCE(SUM(t.amount),0),0) AS spent
        FROM budgets b LEFT JOIN transactions t
          ON t.category=b.category AND t.txn_type='debit'
         AND t.month=(SELECT MAX(month) FROM transactions)
        GROUP BY b.category, b.monthly_limit"""))


@app.get("/api/months")
def months():
    return jsonify([r["month"] for r in query(
        "SELECT DISTINCT month FROM transactions ORDER BY month DESC")])


@app.get("/api/transactions")
def recent_transactions():
    limit = min(int(request.args.get("limit", 10)), 100)
    return jsonify(query("SELECT * FROM transactions ORDER BY txn_date DESC, txn_id DESC LIMIT ?", (limit,)))


@app.post("/api/transactions")
def add_transaction():
    """Naya transaction add karo -> dashboard auto refresh me turant dikhega."""
    data = request.get_json(force=True)
    try:
        amount = float(data["amount"])
        txn_type = data["txn_type"]
        description = str(data["description"]).strip()
        assert amount > 0 and txn_type in ("credit", "debit") and description
    except (KeyError, ValueError, AssertionError):
        return jsonify({"error": "description, amount (>0), txn_type (credit/debit) required"}), 400
    txn_date = data.get("txn_date") or date.today().isoformat()
    category = data.get("category") or categorise(description)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO transactions (txn_date, description, amount, txn_type, category, month) "
        "VALUES (?,?,?,?,?,?)", (txn_date, description, amount, txn_type, category, txn_date[:7]))
    conn.commit()
    conn.close()
    return jsonify({"txn_id": cur.lastrowid, "category": category}), 201


if __name__ == "__main__":
    if not Path(DB_PATH).exists():
        run_pipeline()
    app.run(debug=True)
