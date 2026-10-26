# Power BI report banane ke steps

1. **Get Data → Text/CSV** → `data/clean_transactions.csv` select karo. (Ya *Get Data → ODBC/SQLite* se `finance.db` connect karo.)
2. Power Query me `txn_date` ka type **Date**, `amount` ka **Decimal** set karo → Close & Apply.
3. **Date table** banao (Modeling → New table):
   ```DAX
   Calendar = CALENDAR(MIN(clean_transactions[txn_date]), MAX(clean_transactions[txn_date]))
   ```
   Calendar[Date] ko txn_date se relationship do.
4. **DAX measures** (New measure):
   ```DAX
   Total Income  = CALCULATE(SUM(clean_transactions[amount]), clean_transactions[txn_type] = "credit")
   Total Expense = CALCULATE(SUM(clean_transactions[amount]), clean_transactions[txn_type] = "debit")
   Savings       = [Total Income] - [Total Expense]
   Savings Rate  = DIVIDE([Savings], [Total Income])
   Expense MoM % = VAR prev = CALCULATE([Total Expense], DATEADD(Calendar[Date], -1, MONTH))
                   RETURN DIVIDE([Total Expense] - prev, prev)
   ```
5. **Visuals:**
   - 4 **Card** visuals: Income, Expense, Savings, Savings Rate
   - **Line chart**: X = month, Y = Income, Expense, Savings
   - **Donut chart**: Legend = category, Values = Total Expense
   - **Clustered bar**: category vs Total Expense
   - **Slicer**: month aur category
   - **Table**: recent transactions
6. Conditional formatting: Savings Rate < 20% ho to red.
7. File → Save as `Personal_Finance_Dashboard.pbix`. Screenshot leke GitHub README me daal do.

**Refresh:** Power BI Desktop me *Refresh* dabao; pipeline dobara chalane ke baad naya data aa jata hai. Power BI Service me *Scheduled Refresh* set kar sakte ho (gateway ke saath).
