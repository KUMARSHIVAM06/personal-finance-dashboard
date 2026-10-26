# Personal Finance Dashboard
**Tech:** Python · Flask · SQL (SQLite) · Power BI · Chart.js

Real-time dashboard jo income, expense aur savings track karta hai. Backend Flask REST API hai, data SQL database me rehta hai, aur frontend har 10 second me API se data sync karta hai. Same clean data Power BI me bhi load hota hai.

## Architecture
```
Bank statement / CSV / manual entry
        │  (Extract)
        ▼
data_pipeline.py ── clean, dedupe, auto-categorise ── (Transform)
        │  (Load)
        ▼
finance.db (SQLite: transactions, budgets)
        │
        ├──► app.py (Flask REST API: /api/summary, /api/monthly-trend, ...)
        │          └──► templates/index.html (Chart.js, auto-refresh 10s)
        └──► data/clean_transactions.csv ──► Power BI report
```

## Run kaise kare
```bash
pip install -r requirements.txt
python data_pipeline.py     # data generate + clean + DB me load
python app.py               # browser: http://127.0.0.1:5000
```

## API endpoints
| Method | Endpoint | Kaam |
|---|---|---|
| GET | `/api/summary?month=YYYY-MM` | KPI: income, expense, savings, savings rate |
| GET | `/api/monthly-trend` | Har month ka income/expense/savings |
| GET | `/api/category-breakdown` | Category-wise kharcha |
| GET | `/api/budget-status` | Budget vs actual |
| GET | `/api/transactions?limit=10` | Recent transactions |
| POST | `/api/transactions` | Naya transaction (auto-category) |

Example:
```bash
curl -X POST http://127.0.0.1:5000/api/transactions -H "Content-Type: application/json" \
     -d '{"description":"Swiggy order","amount":350,"txn_type":"debit"}'
```

## Files
- `data_pipeline.py` – ETL pipeline (extract → transform → load)
- `app.py` – Flask REST API
- `templates/index.html` – dashboard UI
- `sql/schema.sql` – tables + indexes
- `sql/analysis_queries.sql` – window functions, CTE, JOIN wali analysis queries
- `POWER_BI_GUIDE.md` – Power BI report step by step
- `data/` – raw aur clean CSV
