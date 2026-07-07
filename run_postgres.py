import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'Walmart.csv')
CLEAN_CSV_PATH = os.path.join(BASE_DIR, 'walmart_clean_data.csv')
DB_URL = "postgresql+psycopg2://postgres:x0000@localhost:5432/walmart_db"
ARTIFACT_PATH = "/Users/kapishverma/.gemini/antigravity/brain/6f5fb3e1-f188-4d05-bb3a-6eb86fbd7e4c/postgres_results.md"

def clean_data():
    print("Step 1: Reading and cleaning Walmart data...")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Source file {CSV_PATH} not found!")

    df = pd.read_csv(CSV_PATH, encoding_errors='ignore')
    print(f"Loaded {df.shape[0]} rows and {df.shape[1]} columns.")

    # Drop duplicates
    initial_rows = df.shape[0]
    df.drop_duplicates(inplace=True)
    duplicate_rows = initial_rows - df.shape[0]
    if duplicate_rows > 0:
        print(f"Removed {duplicate_rows} duplicate rows.")

    # Drop rows with missing values
    non_null_rows = df.shape[0]
    df.dropna(inplace=True)
    null_rows = non_null_rows - df.shape[0]
    if null_rows > 0:
        print(f"Removed {null_rows} rows with missing values.")

    # Clean unit_price column
    df['unit_price'] = df['unit_price'].astype(str).str.replace('$', '', regex=False).astype(float)

    # Feature Engineering: calculate total revenue
    df['total'] = df['unit_price'] * df['quantity']

    # Lowercase column names
    df.columns = df.columns.str.lower()

    # Save cleaned data to CSV
    df.to_csv(CLEAN_CSV_PATH, index=False)
    print(f"Cleaned data saved to {CLEAN_CSV_PATH}")
    print(f"Final shape: {df.shape[0]} rows and {df.shape[1]} columns.")
    return df

def setup_postgres(df):
    print("\nStep 2: Loading cleaned data into PostgreSQL database...")
    engine = create_engine(DB_URL)
    # Load DataFrame to PostgreSQL table 'walmart'
    df.to_sql(name='walmart', con=engine, if_exists='replace', index=False)
    print("Data loaded successfully into PostgreSQL table 'walmart'.")
    engine.dispose()

# Query Definition
queries = [
    {
        "id": 1,
        "title": "Payment Method Analysis",
        "description": "Find different payment methods, the number of transactions, and the total quantity of items sold.",
        "sql": """
SELECT 
     payment_method,
     COUNT(*) as no_payments,
     SUM(quantity) as no_qty_sold
FROM walmart
GROUP BY payment_method;
"""
    },
    {
        "id": 2,
        "title": "Highest-Rated Product Category per Branch",
        "description": "Identify the highest-rated category in each branch, displaying the branch, category, and average rating.",
        "sql": """
SELECT branch, category, ROUND(avg_rating::numeric, 2) AS avg_rating
FROM
(	SELECT 
		branch,
		category,
		AVG(rating) as avg_rating,
		RANK() OVER(PARTITION BY branch ORDER BY AVG(rating) DESC) as rank
	FROM walmart
	GROUP BY 1, 2
) AS subquery
WHERE rank = 1;
"""
    },
    {
        "id": 3,
        "title": "Busiest Day of the Week per Branch",
        "description": "Identify the busiest day for each branch based on the total number of transactions.",
        "sql": """
SELECT branch, day_name, no_transactions
FROM
	(SELECT 
		branch,
		TO_CHAR(TO_DATE(date, 'DD/MM/YY'), 'Day') as day_name,
		COUNT(*) as no_transactions,
		RANK() OVER(PARTITION BY branch ORDER BY COUNT(*) DESC) as rank
	FROM walmart
	GROUP BY 1, 2
	) AS subquery
WHERE rank = 1;
"""
    },
    {
        "id": 4,
        "title": "Total Quantity Sold per Payment Method",
        "description": "Calculate the total quantity of items sold per payment method.",
        "sql": """
SELECT 
	 payment_method,
	 SUM(quantity) as no_qty_sold
FROM walmart
GROUP BY payment_method;
"""
    },
    {
        "id": 5,
        "title": "Category Rating Statistics per City",
        "description": "Determine the average, minimum, and maximum rating of product categories for each city.",
        "sql": """
SELECT 
	city,
	category,
	MIN(rating) as min_rating,
	MAX(rating) as max_rating,
	ROUND(AVG(rating)::numeric, 2) as avg_rating
FROM walmart
GROUP BY 1, 2;
"""
    },
    {
        "id": 6,
        "title": "Total Profit per Category",
        "description": "Calculate the total profit for each category (defined as `total * profit_margin`) ordered from highest profit to lowest.",
        "sql": """
SELECT 
	category,
	ROUND(SUM(total)::numeric, 2) as total_revenue,
	ROUND(SUM(total * profit_margin)::numeric, 2) as profit
FROM walmart
GROUP BY 1
ORDER BY profit DESC;
"""
    },
    {
        "id": 7,
        "title": "Most Common Payment Method per Branch",
        "description": "Determine the most common payment method for each branch.",
        "sql": """
WITH cte 
AS
(SELECT 
	branch,
	payment_method,
	COUNT(*) as total_trans,
	RANK() OVER(PARTITION BY branch ORDER BY COUNT(*) DESC) as rank
FROM walmart
GROUP BY 1, 2
)
SELECT branch, payment_method AS preferred_payment_method
FROM cte
WHERE rank = 1;
"""
    },
    {
        "id": 8,
        "title": "Transactions by Hourly Shifts (Morning, Afternoon, Evening)",
        "description": "Categorize sales transactions into three shifts (Morning: < 12, Afternoon: 12-17, Evening: > 17) and display the number of invoices per branch and shift.",
        "sql": """
SELECT
	branch,
	CASE 
		WHEN EXTRACT(HOUR FROM(time::time)) < 12 THEN 'Morning'
		WHEN EXTRACT(HOUR FROM(time::time)) BETWEEN 12 AND 17 THEN 'Afternoon'
		ELSE 'Evening'
	END day_time,
	COUNT(*) AS num_invoices
FROM walmart
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
"""
    },
    {
        "id": 9,
        "title": "Top 5 Branches with Highest Revenue Decrease Ratio (2022 vs 2023)",
        "description": "Identify the 5 branches with the highest decrease ratio in revenue comparing the year 2023 to 2022.",
        "sql": """
WITH revenue_2022
AS
(
	SELECT 
		branch,
		SUM(total) as revenue
	FROM walmart
	WHERE EXTRACT(YEAR FROM TO_DATE(date, 'DD/MM/YY')) = 2022
	GROUP BY 1
),

revenue_2023
AS
(

	SELECT 
		branch,
		SUM(total) as revenue
	FROM walmart
	WHERE EXTRACT(YEAR FROM TO_DATE(date, 'DD/MM/YY')) = 2023
	GROUP BY 1
)

SELECT 
	ls.branch,
	ROUND(ls.revenue::numeric, 2) as last_year_revenue,
	ROUND(cs.revenue::numeric, 2) as cr_year_revenue,
	ROUND(
		(ls.revenue - cs.revenue)::numeric/
		ls.revenue::numeric * 100, 
		2) as rev_dec_ratio
FROM revenue_2022 as ls
JOIN
revenue_2023 as cs
ON ls.branch = cs.branch
WHERE 
	ls.revenue > cs.revenue
ORDER BY 4 DESC
LIMIT 5;
"""
    }
]

def main():
    # 1. Clean the CSV
    try:
        df = clean_data()
    except Exception as e:
        print(f"Error cleaning data: {e}")
        return

    # 2. Setup PostgreSQL
    try:
        setup_postgres(df)
    except Exception as e:
        print(f"Error loading data to PostgreSQL: {e}")
        return

    # 3. Connect and execute queries
    print("\nExecuting queries on PostgreSQL...")
    engine = create_engine(DB_URL)
    
    # Initialize markdown content
    md = [
        "# Walmart SQL Analysis - PostgreSQL Execution Results",
        "",
        "This artifact presents the results of the 9 key business problem SQL queries executed against the **PostgreSQL database server** running locally on port 5432.",
        "",
        "## Table of Contents",
        ""
    ]

    # Generate TOC
    for q in queries:
        md.append(f"- [{q['id']}. {q['title']}](#{q['title'].lower().replace(' ', '-').replace('(', '').replace(')', '').replace(',', '')})")
    
    md.append("")

    # Run queries and format as markdown
    for q in queries:
        md.append(f"## {q['id']}. {q['title']}")
        md.append(f"**Business Goal**: {q['description']}")
        md.append("")
        md.append("```sql")
        md.append(q['sql'].strip())
        md.append("```")
        md.append("")
        
        try:
            res_df = pd.read_sql_query(q['sql'], engine)
            
            # For long query results (Q5 and Q8), limit to top 20 for readability in artifact
            if q['id'] == 8 and len(res_df) > 30:
                md.append("> [ Mollified Output ]")
                md.append(f"> Showing the top 20 rows of {len(res_df)} total rows. Run the script directly to see the full set of results.")
                md.append("")
                table_md = res_df.head(20).to_markdown(index=False)
            elif q['id'] == 5 and len(res_df) > 30:
                md.append("> [ Mollified Output ]")
                md.append(f"> Showing the top 20 rows of {len(res_df)} total rows. Run the script directly to see the full set of results.")
                md.append("")
                table_md = res_df.head(20).to_markdown(index=False)
            else:
                table_md = res_df.to_markdown(index=False)
                
            md.append(table_md)
        except Exception as e:
            md.append(f"**Error executing query**: {e}")
            print(f"Error executing Q{q['id']}: {e}")
            
        md.append("")
        md.append("---")
        md.append("")

    engine.dispose()

    # Write artifact file
    os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
    with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Results written to artifact at {ARTIFACT_PATH}")

if __name__ == "__main__":
    main()
