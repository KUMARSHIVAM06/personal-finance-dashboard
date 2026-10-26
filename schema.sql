-- Personal Finance Dashboard: Database schema
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS budgets;

CREATE TABLE transactions (
    txn_id      INTEGER PRIMARY KEY,
    txn_date    TEXT    NOT NULL,          -- YYYY-MM-DD
    description TEXT    NOT NULL,
    amount      REAL    NOT NULL CHECK (amount > 0),
    txn_type    TEXT    NOT NULL CHECK (txn_type IN ('credit', 'debit')),
    category    TEXT    NOT NULL,
    month       TEXT    NOT NULL           -- YYYY-MM
);

CREATE TABLE budgets (
    category      TEXT PRIMARY KEY,
    monthly_limit REAL NOT NULL
);

-- Index: dashboard queries month aur category pe filter karti hain, isliye fast lookup
CREATE INDEX idx_txn_month    ON transactions(month);
CREATE INDEX idx_txn_category ON transactions(category);
