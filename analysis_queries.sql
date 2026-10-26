-- ============ Personal Finance: Key SQL queries (interview me ye dikhao) ============

-- 1) Monthly income, expense, savings aur savings rate
SELECT month,
       SUM(CASE WHEN txn_type = 'credit' THEN amount ELSE 0 END)                         AS income,
       SUM(CASE WHEN txn_type = 'debit'  THEN amount ELSE 0 END)                         AS expense,
       SUM(CASE WHEN txn_type = 'credit' THEN amount ELSE -amount END)                   AS savings,
       ROUND(100.0 * SUM(CASE WHEN txn_type = 'credit' THEN amount ELSE -amount END)
             / SUM(CASE WHEN txn_type = 'credit' THEN amount ELSE 0 END), 1)             AS savings_rate_pct
FROM transactions
GROUP BY month
ORDER BY month;

-- 2) Category-wise spending with share of total (window function)
SELECT category,
       ROUND(SUM(amount), 0) AS total_spent,
       ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 1) AS pct_of_total
FROM transactions
WHERE txn_type = 'debit'
GROUP BY category
ORDER BY total_spent DESC;

-- 3) Month-over-month expense change (LAG window function)
WITH monthly AS (
    SELECT month, SUM(amount) AS expense
    FROM transactions WHERE txn_type = 'debit'
    GROUP BY month
)
SELECT month, ROUND(expense, 0) AS expense,
       ROUND(expense - LAG(expense) OVER (ORDER BY month), 0) AS change_vs_last_month,
       ROUND(100.0 * (expense - LAG(expense) OVER (ORDER BY month))
             / LAG(expense) OVER (ORDER BY month), 1)         AS pct_change
FROM monthly;

-- 4) Budget vs actual (latest month) - JOIN
SELECT b.category, b.monthly_limit,
       ROUND(COALESCE(SUM(t.amount), 0), 0) AS spent,
       CASE WHEN SUM(t.amount) > b.monthly_limit THEN 'OVER BUDGET' ELSE 'OK' END AS status
FROM budgets b
LEFT JOIN transactions t
       ON t.category = b.category
      AND t.txn_type = 'debit'
      AND t.month = (SELECT MAX(month) FROM transactions)
GROUP BY b.category, b.monthly_limit;

-- 5) 3-month moving average of expenses
WITH monthly AS (
    SELECT month, SUM(amount) AS expense FROM transactions
    WHERE txn_type = 'debit' GROUP BY month
)
SELECT month, ROUND(expense, 0) AS expense,
       ROUND(AVG(expense) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0) AS moving_avg_3m
FROM monthly;

-- 6) Top 5 biggest single expenses
SELECT txn_date, description, category, amount
FROM transactions WHERE txn_type = 'debit' AND category NOT IN ('Rent', 'Investment')
ORDER BY amount DESC LIMIT 5;
