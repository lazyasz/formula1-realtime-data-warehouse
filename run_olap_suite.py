"""
Executes and validates all 12 OLAP Queries against the Formula 1 Data Warehouse SQLite instance.
"""

import sqlite3
import pandas as pd
import re

DB_PATH = "f1_warehouse.db"
SQL_FILE = "olap_queries.sql"

def run_all_queries():
    conn = sqlite3.connect(DB_PATH)
    with open(SQL_FILE, "r") as f:
        content = f.read()

    # Match queries based on pattern -- QUERY <N>:
    pattern = r"(-- QUERY \d+:.*?)(?=(?:-- QUERY \d+:|\Z))"
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        lines = match.strip().split("\n")
        header = lines[0].replace("--", "").strip()
        
        # Extract SQL
        sql_lines = []
        for line in lines:
            if not line.strip().startswith("--"):
                sql_lines.append(line)
        sql_query = "\n".join(sql_lines).strip()
        
        if not sql_query:
            continue

        print(f"\n================================================================================")
        print(f"  {header}")
        print(f"================================================================================")
        try:
            df = pd.read_sql_query(sql_query, conn)
            print(df.head(10).to_string(index=False))
            print(f"[Total Rows Returned: {len(df)}]")
        except Exception as e:
            print(f"Error executing query: {e}")

    conn.close()

if __name__ == "__main__":
    run_all_queries()
